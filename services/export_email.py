import base64
import json
import os
from datetime import datetime, timedelta, timezone

import requests
from flask import render_template

SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"
FROM_EMAIL = os.getenv("EXPORT_EMAIL_FROM", "hi@eidetic.works")


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if not local or not domain:
        return "***"
    if len(local) == 1:
        masked_local = f"{local}***"
    else:
        masked_local = f"{local[0]}***{local[-1]}"
    return f"{masked_local}@{domain}"


def send_user_export_email(email: str, bundle: dict) -> dict:
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key or not email:
        return {"sent": False, "reason": "not_configured" if not api_key else "missing_email"}

    exported_at = datetime.now(timezone.utc)
    expires_at = exported_at + timedelta(hours=24)
    export_json = json.dumps(bundle, indent=2, sort_keys=True, default=str)
    html = render_template(
        "email/data_export.html",
        exported_at=exported_at.isoformat(),
        expires_at=expires_at.isoformat(),
    )
    payload = {
        "personalizations": [{"to": [{"email": email}]}],
        "from": {"email": FROM_EMAIL, "name": "GentleQuest"},
        "subject": "Your GentleQuest data export is ready",
        "content": [{"type": "text/html", "value": html}],
        "attachments": [
            {
                "content": base64.b64encode(export_json.encode("utf-8")).decode("ascii"),
                "type": "application/json",
                "filename": "gentlequest-data-export.json",
                "disposition": "attachment",
            }
        ],
    }
    response = requests.post(
        SENDGRID_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    return {"sent": True, "email": mask_email(email)}
