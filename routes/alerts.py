"""
Counselor Alert triage endpoints (Phase H).

Endpoints:
- POST /api/alerts/<id>/triage      — advance triage_state
- GET  /api/alerts/<id>/audit       — full state-change history
- GET  /api/alerts/history          — filtered list (state, severity, date)
- GET  /api/alerts/stream           — SSE real-time stream (simple polling under test)

All endpoints require `X-Counselor-Id` header (set by the clinical dashboard auth
layer). A request without it returns 401.
"""

import json
import time
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    request,
    stream_with_context,
)

from extensions import limiter
from helpers.alert_triage import is_valid_transition, next_states
from models import AlertAcknowledgment, CounselorAlert, db

alerts_bp = Blueprint("alerts_v2", __name__)


def _counselor_id() -> str:
    return (request.headers.get("X-Counselor-Id") or "").strip()


def _require_counselor():
    cid = _counselor_id()
    if not cid:
        return None, (jsonify({"error": "X-Counselor-Id header required"}), 401)
    return cid, None


def _alert_to_dict(alert: CounselorAlert) -> dict:
    return {
        "id": alert.id,
        "session_id": alert.session_id,
        "severity": alert.severity,
        "risk_keywords": alert.risk_keywords,
        "triage_state": getattr(alert, "triage_state", "new") or "new",
        "sent_at": alert.sent_at.isoformat() if alert.sent_at else None,
        "acknowledged_at": (
            alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
        ),
        "acknowledged_by": alert.acknowledged_by,
        "email_sent": bool(alert.email_sent),
        "sms_sent": bool(alert.sms_sent),
    }


# ---------------------------------------------------------------------------
# POST /api/alerts/<id>/triage
# ---------------------------------------------------------------------------

@alerts_bp.route("/api/alerts/<int:alert_id>/triage", methods=["POST"])
@limiter.limit("60 per minute")
def triage_alert(alert_id: int):
    """Advance an alert's triage_state and write an AlertAcknowledgment audit row."""
    cid, err = _require_counselor()
    if err:
        return err

    body = request.get_json(silent=True) or {}
    target = (body.get("target_state") or "").strip().lower()
    notes = body.get("notes") or ""

    alert = CounselorAlert.query.get(alert_id)
    if not alert:
        return jsonify({"error": "Alert not found"}), 404

    current = (getattr(alert, "triage_state", None) or "new").lower()
    if not is_valid_transition(current, target):
        return jsonify({
            "error": "Illegal transition",
            "current": current,
            "target": target,
            "allowed_next": sorted(next_states(current)),
        }), 400

    # Apply transition
    alert.triage_state = target
    if target == "acknowledged" and not alert.acknowledged_at:
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = cid

    # Audit trail row
    audit = AlertAcknowledgment(
        alert_id=alert.id,
        counselor_id=cid,
        action_taken=f"{current}->{target}",
        response_notes=notes,
    )
    db.session.add(audit)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"triage commit failed: {e}")
        return jsonify({"error": "Failed to commit triage"}), 500

    return jsonify({
        "ok": True,
        "alert": _alert_to_dict(alert),
        "audit_id": audit.id,
    }), 200


# ---------------------------------------------------------------------------
# GET /api/alerts/<id>/audit
# ---------------------------------------------------------------------------

@alerts_bp.route("/api/alerts/<int:alert_id>/audit", methods=["GET"])
@limiter.limit("60 per minute")
def alert_audit(alert_id: int):
    """Full state-change + note history for an alert."""
    _, err = _require_counselor()
    if err:
        return err

    alert = CounselorAlert.query.get(alert_id)
    if not alert:
        return jsonify({"error": "Alert not found"}), 404

    rows = (
        AlertAcknowledgment.query
        .filter_by(alert_id=alert_id)
        .order_by(AlertAcknowledgment.responded_at.asc())
        .all()
    )
    return jsonify({
        "alert": _alert_to_dict(alert),
        "audit": [
            {
                "id": r.id,
                "counselor_id": r.counselor_id,
                "action_taken": r.action_taken,
                "notes": r.response_notes,
                "responded_at": r.responded_at.isoformat() if r.responded_at else None,
            }
            for r in rows
        ],
    }), 200


# ---------------------------------------------------------------------------
# GET /api/alerts/history
# ---------------------------------------------------------------------------

@alerts_bp.route("/api/alerts/triage/history", methods=["GET"])
@limiter.limit("60 per minute")
def alerts_history():
    """Filtered list of alerts — supports state, severity, since, until, limit.

    Note: path is /api/alerts/triage/history to avoid shadowing the legacy
    /api/alerts/history endpoint from app_alert_routes.py.
    """
    _, err = _require_counselor()
    if err:
        return err

    q = CounselorAlert.query

    state = (request.args.get("state") or "").strip().lower()
    if state:
        q = q.filter(CounselorAlert.triage_state == state)

    severity = (request.args.get("severity") or "").strip().lower()
    if severity:
        q = q.filter(CounselorAlert.severity == severity)

    since = request.args.get("since")
    if since:
        try:
            q = q.filter(CounselorAlert.sent_at >= datetime.fromisoformat(since))
        except ValueError:
            return jsonify({"error": "Invalid 'since' (ISO format required)"}), 400

    until = request.args.get("until")
    if until:
        try:
            q = q.filter(CounselorAlert.sent_at <= datetime.fromisoformat(until))
        except ValueError:
            return jsonify({"error": "Invalid 'until' (ISO format required)"}), 400

    try:
        limit = min(int(request.args.get("limit", 100)), 500)
    except ValueError:
        limit = 100

    q = q.order_by(CounselorAlert.sent_at.desc()).limit(limit)

    return jsonify({
        "alerts": [_alert_to_dict(a) for a in q.all()],
        "filters": {
            "state": state or None,
            "severity": severity or None,
            "since": since,
            "until": until,
            "limit": limit,
        },
    }), 200


# ---------------------------------------------------------------------------
# GET /api/alerts/stream  (SSE)
# ---------------------------------------------------------------------------

@alerts_bp.route("/api/alerts/stream", methods=["GET"])
@limiter.exempt
def alerts_stream():
    """Server-Sent Events: emit new alerts (triage_state='new') as they arrive.

    Implementation: polls the DB every 2s and emits diffs. For higher scale a
    proper pub/sub would be preferable, but this keeps the dependency surface
    minimal and is sufficient for the clinical-dashboard use case.

    In TESTING mode, the stream exits after one poll cycle so tests can assert.
    """
    cid, err = _require_counselor()
    if err:
        return err

    testing = bool(current_app.config.get("TESTING"))
    poll_interval = float(current_app.config.get("ALERTS_STREAM_POLL_SEC", 2.0))
    max_age = timedelta(minutes=10)

    def _gen():
        seen_ids: set = set()
        start = time.time()
        while True:
            try:
                cutoff = datetime.utcnow() - max_age
                rows = (
                    CounselorAlert.query
                    .filter(CounselorAlert.sent_at >= cutoff)
                    .filter(CounselorAlert.triage_state == "new")
                    .order_by(CounselorAlert.sent_at.desc())
                    .limit(50)
                    .all()
                )
                for a in rows:
                    if a.id in seen_ids:
                        continue
                    seen_ids.add(a.id)
                    payload = json.dumps(_alert_to_dict(a))
                    yield f"event: alert\ndata: {payload}\n\n"

                # Heartbeat every cycle so clients can detect broken pipes
                yield "event: heartbeat\ndata: {}\n\n"
            except Exception as e:
                current_app.logger.error(f"alerts/stream error: {e}")

            if testing:
                break
            time.sleep(poll_interval)
            if time.time() - start > 3600:
                # Close after 1h so connections don't live forever
                break

    return Response(
        stream_with_context(_gen()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
