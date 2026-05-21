"""Passwordless magic-link auth for cross-device session continuity.

The goal isn't to gate the app behind a login wall — anonymous use stays
fully supported. The goal is to give a user who started on web (or any
device) a way to continue their conversation on mobile (or any other
device) without losing journal entries / chat history.

Endpoints:
  POST /api/auth/magic-link        { email }            → 202 (always)
  POST /api/auth/verify            { token }            → 200 { user, session_id } | 400
  GET  /api/auth/me                X-Session-ID header  → 200 { user } | 200 { user: null }

Token mechanics:
  - 32 byte url-safe random string ("raw"), sent to the user via email
    embedded in a `gentlequest://auth/verify?token=<raw>` deep link.
  - Stored server-side as SHA-256(raw); the raw string is never
    persisted, so a DB leak can't be replayed.
  - 15-minute expiry. Single-use (used_at sentinel set on verify).
  - On verify, the existing X-Session-ID (if any) is *linked* to the
    user account so the device's pre-login history stays intact. If the
    user already has a session, we keep the device's session_id and
    just record the user_id binding — multi-device support is
    server-side and not part of this Phase 1.

Email delivery: in production point EMAIL_BACKEND env var at a real
provider (SendGrid / Resend / Postmark). In dev we log the magic-link
URL to stdout so QA can copy-paste during testing.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional

from flask import Blueprint, current_app, jsonify, request
from flask_limiter.util import get_remote_address

from models import AuthToken, User, db
from helpers.session_helpers import _get_or_create_session


logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

# Single-use token lifetime. 15 minutes is the standard
# magic-link window — long enough to switch apps + check email,
# short enough that a leaked token is mostly worthless.
TOKEN_TTL = timedelta(minutes=15)

# Deep-link scheme matches the iOS / Android scheme registered in
# Info.plist / AndroidManifest.xml (see flutter_app config).
DEEP_LINK_SCHEME = "gentlequest"


# ─── Helpers ────────────────────────────────────────────────────────


_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _build_magic_link(raw_token: str) -> str:
    return f"{DEEP_LINK_SCHEME}://auth/verify?token={raw_token}"


def _send_magic_link_email(email: str, raw_token: str) -> None:
    """Dev: log to stdout. Prod: swap for SendGrid/Resend/Postmark.

    Kept intentionally tiny — production wiring is configuration, not
    code: read EMAIL_BACKEND + EMAIL_API_KEY, fork on backend, send.
    Until that's wired we want the dev experience to be obvious so
    nobody silently fails the flow during QA.
    """
    link = _build_magic_link(raw_token)
    backend = os.environ.get("EMAIL_BACKEND", "stdout").lower()
    if backend in ("", "stdout", "console", "dev"):
        # Print to whatever stream `flask run` is writing to. Dev only.
        msg = (
            "\n────────────────────────────────────────────────\n"
            f"[auth] magic link for {email}:\n  {link}\n"
            "(expires in 15 minutes · single use)\n"
            "────────────────────────────────────────────────\n"
        )
        print(msg, flush=True)
        logger.info("magic_link.sent_stdout email=%s", email)
        return
    # FUTURE WORK: wire SendGrid / Resend / Postmark here. The backend
    # env var is the switch; keep this function the single integration
    # point so the route code never knows about the provider.
    logger.warning(
        "magic_link.unsupported_backend backend=%s falling_back_to_stdout",
        backend,
    )
    print(f"[auth] magic link for {email}: {link}", flush=True)


# ─── Routes ─────────────────────────────────────────────────────────


@auth_bp.route("/api/auth/magic-link", methods=["POST"])
def request_magic_link():
    """Request a one-time login link for an email.

    Returns 202 unconditionally regardless of whether the email exists
    — leaking which emails have accounts is a textbook auth pitfall.
    """
    data = request.get_json(silent=True) or {}
    email_raw = data.get("email")
    if not email_raw or not isinstance(email_raw, str):
        return jsonify({"error": "email is required"}), 400
    email = _normalize_email(email_raw)
    if not _EMAIL_RE.match(email):
        return jsonify({"error": "email format invalid"}), 400

    # Find or create user lazily. We don't require the user to "sign up"
    # — signing in IS sign-up for first-time emails.
    user = User.query.filter_by(email=email).first()
    if user is None:
        # Bind to the current device's anonymous session so any
        # pre-login journal entries / chat history stay attached.
        current_session_id = _get_or_create_session()
        user = User(email=email, session_id=current_session_id)
        db.session.add(user)
        db.session.flush()  # populate user.id

    raw = secrets.token_urlsafe(32)
    token = AuthToken(
        user_id=user.id,
        token_hash=_hash_token(raw),
        email=email,
        expires_at=datetime.utcnow() + TOKEN_TTL,
    )
    db.session.add(token)
    db.session.commit()

    try:
        _send_magic_link_email(email, raw)
    except Exception:  # noqa: BLE001
        # Don't reveal the failure to the caller — that's an info leak.
        # Log + bail; the row is harmless (15-minute TTL, never used).
        logger.exception("magic_link.email_send_failed email=%s", email)

    return jsonify({"status": "sent"}), 202


@auth_bp.route("/api/auth/verify", methods=["POST"])
def verify_magic_link():
    """Verify a token and bind the user to the current device session.

    Returns:
      200 { user: {id, email}, session_id }  on success
      400 { error }                          on invalid / expired / used
    """
    data = request.get_json(silent=True) or {}
    raw = data.get("token")
    if not raw or not isinstance(raw, str):
        return jsonify({"error": "token is required"}), 400

    token_hash = _hash_token(raw.strip())
    token = AuthToken.query.filter_by(token_hash=token_hash).first()
    if token is None:
        return jsonify({"error": "invalid token"}), 400
    if token.used_at is not None:
        return jsonify({"error": "token already used"}), 400
    if datetime.utcnow() > token.expires_at:
        return jsonify({"error": "token expired"}), 400

    user = db.session.get(User, token.user_id)
    if user is None or user.deleted_at is not None:
        return jsonify({"error": "account no longer active"}), 400

    # Bind this device's session to the user account. The verifying device
    # is the one that received the magic-link email and completed the auth,
    # so we always re-bind to it — Phase 1 picks last-bound-device wins.
    # Proper multi-device sync (one user_id → many device session_ids) is
    # Phase 2 and lives in a separate device_sessions table; until then,
    # signing in on a second device "moves" the account to that device.
    # Any device that wants to re-attach just signs in again with the
    # same email.
    current_session_id = _get_or_create_session()
    user.session_id = current_session_id
    token.used_at = datetime.utcnow()
    db.session.commit()

    return jsonify(
        {
            "user": {"id": user.id, "email": user.email},
            "session_id": current_session_id,
        }
    ), 200


@auth_bp.route("/api/auth/me", methods=["GET"])
def whoami():
    """Return the user bound to the current X-Session-ID, if any.

    Anonymous sessions return {user: null} — a 200, not a 401, because
    anonymous use is a first-class state, not an auth failure.
    """
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return jsonify({"user": None}), 200
    user: Optional[User] = (
        User.query.filter_by(session_id=session_id, deleted_at=None).first()
    )
    if user is None:
        return jsonify({"user": None}), 200
    return jsonify(
        {"user": {"id": user.id, "email": user.email}}
    ), 200
