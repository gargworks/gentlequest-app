import base64
import json
import os
import tempfile
from datetime import datetime

from models import PushToken, db

CRISIS_CATEGORY = "crisis_followup"
PASSIVE_CATEGORIES = {"daily_checkin", "weekly_review", "gentle_return"}
INVALID_TOKEN_REASONS = {"Unregistered", "BadDeviceToken", "DeviceTokenNotForTopic", "NotRegistered"}


def _apns_payload(title, body, category, collapse_key):
    aps = {
        "alert": {"title": title, "body": body},
        "sound": "default",
        "category": category,
    }
    if category == CRISIS_CATEGORY:
        aps["interruption-level"] = "critical"
        aps["sound"] = {"critical": 1, "name": "default", "volume": 1.0}
    elif category in PASSIVE_CATEGORIES:
        aps["interruption-level"] = "passive"
    payload = {"aps": aps}
    if collapse_key:
        payload["collapse_key"] = collapse_key
    return payload


def _apns_client():
    from apns2.client import APNsClient
    from apns2.credentials import TokenCredentials

    key_path = os.getenv("APNS_AUTH_KEY_PATH")
    auth_key_base64 = os.getenv("APNS_AUTH_KEY_BASE64")
    if not key_path and auth_key_base64:
        fh = tempfile.NamedTemporaryFile(delete=False, suffix=".p8")
        fh.write(base64.b64decode(auth_key_base64))
        fh.close()
        key_path = fh.name
    if not all([key_path, os.getenv("APNS_KEY_ID"), os.getenv("APNS_TEAM_ID"), os.getenv("APNS_BUNDLE_ID")]):
        return None
    credentials = TokenCredentials(
        auth_key_path=key_path,
        auth_key_id=os.getenv("APNS_KEY_ID"),
        team_id=os.getenv("APNS_TEAM_ID"),
    )
    use_sandbox = os.getenv("APNS_ENVIRONMENT", "production") == "sandbox"
    return APNsClient(credentials=credentials, use_sandbox=use_sandbox)


def _send_ios(token, title, body, category, collapse_key):
    from apns2.payload import Payload

    client = _apns_client()
    if not client:
        return {"sent": False, "reason": "apns_not_configured"}
    payload_dict = _apns_payload(title, body, category, collapse_key)
    payload = Payload(custom=payload_dict, alert=payload_dict["aps"]["alert"], sound="default")
    response = client.send_notification(token.token, payload, os.getenv("APNS_BUNDLE_ID"))
    reason = getattr(response, "reason", None)
    status = getattr(response, "status", None)
    if status in {400, 404, 410} or reason in INVALID_TOKEN_REASONS:
        token.revoked_at = datetime.utcnow()
        db.session.add(token)
        return {"sent": False, "reason": reason or str(status)}
    return {"sent": True}


def _fcm_message(token, title, body, category, collapse_key):
    from firebase_admin import messaging

    android_config = messaging.AndroidConfig(collapse_key=collapse_key) if collapse_key else None
    return messaging.Message(
        token=token.token,
        notification=messaging.Notification(title=title, body=body),
        data={"category": category},
        android=android_config,
    )


def _send_android(token, title, body, category, collapse_key):
    import firebase_admin
    from firebase_admin import credentials, messaging

    if not firebase_admin._apps:
        service_account = os.getenv("FCM_SERVICE_ACCOUNT_JSON")
        if not service_account:
            return {"sent": False, "reason": "fcm_not_configured"}
        try:
            if service_account.strip().startswith("{"):
                info = json.loads(service_account)
            else:
                try:
                    info = json.loads(base64.b64decode(service_account).decode("utf-8"))
                except Exception:
                    with open(service_account) as fh:
                        info = json.load(fh)
            firebase_admin.initialize_app(credentials.Certificate(info))
        except Exception as exc:
            return {"sent": False, "reason": f"fcm_config_error:{exc}"}
    try:
        messaging.send(_fcm_message(token, title, body, category, collapse_key))
    except Exception as exc:
        code = getattr(exc, "code", "") or getattr(exc, "error_code", "")
        reason = code or exc.__class__.__name__
        if reason in INVALID_TOKEN_REASONS or "not-found" in str(reason).lower() or "unregistered" in str(reason).lower():
            token.revoked_at = datetime.utcnow()
            db.session.add(token)
        return {"sent": False, "reason": reason}
    return {"sent": True}


def send_push(session_id, title, body, *, category="generic", collapse_key=None) -> dict:
    tokens = PushToken.query.filter_by(session_id=session_id, revoked_at=None).all()
    result = {"sent": 0, "failed": [], "skipped": []}
    for token in tokens:
        if token.platform == "ios":
            outcome = _send_ios(token, title, body, category, collapse_key)
        elif token.platform == "android":
            outcome = _send_android(token, title, body, category, collapse_key)
        elif token.platform == "web":
            result["skipped"].append({"token": token.token, "platform": "web", "reason": "web_push_skipped"})
            continue
        else:
            outcome = {"sent": False, "reason": "unsupported_platform"}
        if outcome.get("sent"):
            result["sent"] += 1
        else:
            result["failed"].append({"token": token.token, "platform": token.platform, "reason": outcome.get("reason", "unknown")})
    db.session.commit()
    return result
