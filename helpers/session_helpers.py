"""
Session management, analytics event logging, and background executor.
Extracted from app.py monolith to break circular 'from app import ...' dependencies.
"""

import atexit
import json
import logging
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from flask import request, current_app

from models import db

# ── Background Executor ─────────────────────────────────────────────
background_executor = ThreadPoolExecutor(max_workers=5)
atexit.register(lambda: background_executor.shutdown(wait=True))


# ── Chat request JSONL log ──────────────────────────────────────────
_CHAT_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".brain", "ledger", "chat_requests.jsonl",
)
_chat_log_lock = threading.Lock()


def _log_chat_request(
    session_id: str,
    prompt_len: int,
    response_len: int,
    latency_ms: int,
    status: int,
    model: str = "",
):
    """Append a single chat request/response record to chat_requests.jsonl."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "prompt_len": prompt_len,
        "response_len": response_len,
        "latency_ms": latency_ms,
        "status": status,
        "model": model,
    }
    try:
        with _chat_log_lock:
            with open(_CHAT_LOG_PATH, "a") as f:
                f.write(json.dumps(record) + "\n")
    except Exception:
        logging.getLogger(__name__).debug("chat request log write failed", exc_info=True)


# ── Session helpers ─────────────────────────────────────────────────

def _get_or_create_session() -> str:
    """Get or create user session with proper error handling"""
    session_id = request.headers.get("X-Session-ID")

    if not session_id:
        session_id = str(uuid.uuid4())
    else:
        try:
            uuid.UUID(session_id)
        except ValueError:
            session_id = str(uuid.uuid4())

    try:
        from models import UserSession

        session = db.session.get(UserSession, session_id)

        if not session:
            new_session = UserSession(id=session_id)
            db.session.add(new_session)
            db.session.commit()
        else:
            _app = current_app._get_current_object()
            background_executor.submit(_update_session_last_active, _app, session_id)

    except Exception as e:
        current_app.logger.error(f"Session management error: {e}")

    return session_id


def _update_session_last_active(app_ctx, session_id: str):
    """Background: update session last_active timestamp."""
    try:
        with app_ctx.app_context():
            from models import UserSession
            session = db.session.get(UserSession, session_id)
            if session:
                session.last_active = datetime.utcnow()
                db.session.commit()
    except Exception:
        pass  # Non-critical — stale timestamp is acceptable


def _get_conversation_count(session_id: str) -> int:
    """Get the conversation count for a session (lightweight query)."""
    try:
        from models import UserSession
        session = db.session.get(UserSession, session_id)
        return (session.conversation_count or 0) if session else 0
    except Exception:
        return 0


def _increment_conversation_count(app_ctx, session_id: str):
    """Background: increment conversation_count on UserSession."""
    try:
        with app_ctx.app_context():
            from models import UserSession
            session = db.session.get(UserSession, session_id)
            if session:
                session.conversation_count = (session.conversation_count or 0) + 1
                db.session.commit()
    except Exception:
        pass  # Non-critical


# ── Analytics event logging ─────────────────────────────────────────

def _log_analytics_event(app_ctx, session_id: str, event_type: str, metadata: dict = None):
    """Background: log a behavioral event to analytics_events table."""
    try:
        with app_ctx.app_context():
            from models import AnalyticsEvent
            event = AnalyticsEvent(
                session_id=session_id,
                event_type=event_type,
                event_metadata=metadata or {},
            )
            db.session.add(event)
            db.session.commit()
    except Exception:
        pass  # Non-critical — analytics should never block
