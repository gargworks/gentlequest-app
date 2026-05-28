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

from flask import Blueprint, current_app, jsonify, redirect, request

from extensions import limiter
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

# Smart-redirect wrapper: the email link points here (HTTPS, opens
# cleanly in any client/browser/preview), and this route sniffs the
# User-Agent to either deep-link into the mobile app or land on the
# Flutter web build. Solves the "desktop user clicks email link →
# gentlequest:// scheme is unrecognised by the browser → dead end"
# bug flagged by the cross-platform audit.
WEB_AUTH_VERIFY_URL = "https://app.gentlequest.app/auth/verify"
REDIRECT_ROUTER_BASE = "https://nucleus.gentlequest.app/auth/redirect"

# UA substrings that identify a mobile device where the native app
# (with the gentlequest:// scheme registered) is likely installed.
# Case-insensitive substring match — keep this list narrow; false
# positives just send a desktop user to a broken scheme handler.
_MOBILE_UA_MARKERS = ("iphone", "ipad", "ipod", "android")


# ─── Helpers ────────────────────────────────────────────────────────


_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _build_magic_link(raw_token: str) -> str:
    """The canonical link embedded in the magic-link email.

    Previously this was the raw `gentlequest://` deep link — which the
    cross-platform audit caught as a dead-end for desktop users: their
    browser doesn't know the custom scheme. We now ship an HTTPS wrapper
    that resolves at runtime (`/auth/redirect`) based on User-Agent:
    mobile → deep link into the app, desktop/other → Flutter web build.
    Both routes call the same `/api/auth/verify` POST endpoint, so the
    server-side single-use semantics are unchanged.
    """
    return f"{REDIRECT_ROUTER_BASE}?token={raw_token}"


def _is_mobile_user_agent(ua: str) -> bool:
    """True if the UA looks like a mobile device that should deep-link."""
    if not ua:
        return False
    ua_lower = ua.lower()
    return any(marker in ua_lower for marker in _MOBILE_UA_MARKERS)


def _send_magic_link_email(email: str, raw_token: str) -> None:
    """Send the magic-link email via the configured backend.

    Env var routing:
      EMAIL_BACKEND=resend   + RESEND_API_KEY      → Resend HTTP API
      EMAIL_BACKEND=sendgrid + SENDGRID_API_KEY    → SendGrid v3 API
      EMAIL_BACKEND=postmark + POSTMARK_TOKEN      → Postmark email API
      (anything else, incl. unset)                 → stdout (dev)

    Optional env vars (all backends):
      EMAIL_FROM           default 'GentleQuest <hello@gentlequest.app>'
      EMAIL_REPLY_TO       (omitted if unset)

    Returns silently on success or failure — caller already handles the
    info-leak constraint (response is 202 regardless). Failures are
    logged + emitted to stdout as a last-resort fallback so a single
    misconfigured deploy doesn't silently brick every sign-in.
    """
    link = _build_magic_link(raw_token)
    backend = os.environ.get("EMAIL_BACKEND", "stdout").lower().strip()

    if backend in ("", "stdout", "console", "dev"):
        _print_magic_link_dev(email, link)
        return

    subject, html, text = _render_magic_link_email(link)
    from_addr = os.environ.get(
        "EMAIL_FROM", "GentleQuest <hello@gentlequest.app>"
    )
    reply_to = os.environ.get("EMAIL_REPLY_TO")

    try:
        if backend == "resend":
            _send_via_resend(
                from_addr=from_addr,
                to=email,
                subject=subject,
                html=html,
                text=text,
                reply_to=reply_to,
            )
        elif backend == "sendgrid":
            _send_via_sendgrid(
                from_addr=from_addr,
                to=email,
                subject=subject,
                html=html,
                text=text,
                reply_to=reply_to,
            )
        elif backend == "postmark":
            _send_via_postmark(
                from_addr=from_addr,
                to=email,
                subject=subject,
                html=html,
                text=text,
                reply_to=reply_to,
            )
        else:
            logger.warning(
                "magic_link.unsupported_backend backend=%s falling_back_to_stdout",
                backend,
            )
            _print_magic_link_dev(email, link)
            return
        logger.info("magic_link.sent backend=%s email=%s", backend, email)
    except Exception:  # noqa: BLE001
        # Don't break the auth flow on email infra failure — log loudly,
        # print to stdout so the QA / on-call can recover the link
        # manually. Caller still responds 202 to avoid leaking info.
        logger.exception(
            "magic_link.send_failed backend=%s email=%s", backend, email
        )
        _print_magic_link_dev(email, link, prefix="[auth FALLBACK]")


def _print_magic_link_dev(email: str, link: str, prefix: str = "[auth]") -> None:
    """Pretty-print the magic link to stdout for dev / fallback recovery."""
    msg = (
        "\n────────────────────────────────────────────────\n"
        f"{prefix} magic link for {email}:\n  {link}\n"
        "(expires in 15 minutes · single use)\n"
        "────────────────────────────────────────────────\n"
    )
    print(msg, flush=True)


def _render_magic_link_email(link: str) -> tuple[str, str, str]:
    """Returns (subject, html, plain_text) for the magic-link email.

    Copy intentionally short + warm — matches the in-app "wellness
    companion" tone, not a transactional bank-style email.
    """
    subject = "Your sign-in link for GentleQuest"
    safe_link = link  # Already URL-safe; embed as-is in plain HTML.
    html = (
        '<!doctype html><html><body style="font-family:-apple-system,'
        'Segoe UI,sans-serif;max-width:520px;margin:32px auto;color:#1f1b3a;'
        'line-height:1.5;">'
        '<h2 style="font-weight:800;letter-spacing:-0.3px;">'
        "Hey — let's get you signed in.</h2>"
        '<p style="font-size:15px;">Tap the button below to finish '
        "signing in. It only works once and expires in 15 minutes.</p>"
        f'<p style="margin:24px 0;"><a href="{safe_link}" '
        'style="background:#5853eb;color:#fff;padding:12px 22px;'
        'border-radius:999px;text-decoration:none;font-weight:700;'
        f'display:inline-block;">Sign in to GentleQuest</a></p>'
        f'<p style="font-size:12px;color:#6b6890;">'
        "If the button doesn't work, copy and paste this link:<br>"
        f'<span style="word-break:break-all;">{safe_link}</span></p>'
        '<p style="font-size:12px;color:#6b6890;margin-top:32px;">'
        "If you didn't request this, you can ignore the email — no "
        "account changes have been made.</p>"
        "</body></html>"
    )
    text = (
        "Hey — let's get you signed in.\n\n"
        f"Sign in to GentleQuest: {link}\n\n"
        "This link works once and expires in 15 minutes.\n\n"
        "If you didn't request this, ignore this email — "
        "no account changes have been made."
    )
    return subject, html, text


def _send_via_resend(*, from_addr, to, subject, html, text, reply_to):
    """POST https://api.resend.com/emails — minimal HTTP integration.

    Resend was picked as the default modern provider: simple JSON API,
    free tier covers QA/onboarding, easy DNS setup. Swap providers by
    flipping EMAIL_BACKEND env var; no code change here required.
    """
    import json
    import urllib.request

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY not set")
    payload = {
        "from": from_addr,
        "to": [to],
        "subject": subject,
        "html": html,
        "text": text,
    }
    if reply_to:
        payload["reply_to"] = reply_to
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # Resend sits behind Cloudflare, which 403s the default
            # `Python-urllib/3.x` User-Agent (error 1010 — browser
            # signature ban). A plain UA gets through.
            "User-Agent": "GentleQuest-Backend/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status >= 300:
            raise RuntimeError(
                f"resend non-2xx status={resp.status} body={resp.read()[:200]!r}"
            )


def _send_via_sendgrid(*, from_addr, to, subject, html, text, reply_to):
    """POST https://api.sendgrid.com/v3/mail/send — minimal v3 integration."""
    import json
    import urllib.request

    api_key = os.environ.get("SENDGRID_API_KEY")
    if not api_key:
        raise RuntimeError("SENDGRID_API_KEY not set")
    # Parse "Name <addr@host>" or bare addr; SendGrid wants structured form.
    from_struct = _parse_email_addr(from_addr)
    payload = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": from_struct,
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text},
            {"type": "text/html", "value": html},
        ],
    }
    if reply_to:
        payload["reply_to"] = _parse_email_addr(reply_to)
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "GentleQuest-Backend/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status >= 300:
            raise RuntimeError(
                f"sendgrid non-2xx status={resp.status} body={resp.read()[:200]!r}"
            )


def _send_via_postmark(*, from_addr, to, subject, html, text, reply_to):
    """POST https://api.postmarkapp.com/email — uses X-Postmark-Server-Token."""
    import json
    import urllib.request

    token = os.environ.get("POSTMARK_TOKEN")
    if not token:
        raise RuntimeError("POSTMARK_TOKEN not set")
    payload = {
        "From": from_addr,
        "To": to,
        "Subject": subject,
        "HtmlBody": html,
        "TextBody": text,
        "MessageStream": os.environ.get("POSTMARK_STREAM", "outbound"),
    }
    if reply_to:
        payload["ReplyTo"] = reply_to
    req = urllib.request.Request(
        "https://api.postmarkapp.com/email",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "X-Postmark-Server-Token": token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "GentleQuest-Backend/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status >= 300:
            raise RuntimeError(
                f"postmark non-2xx status={resp.status} body={resp.read()[:200]!r}"
            )


def _parse_email_addr(s: str) -> dict:
    """Convert 'Name <addr@host>' or 'addr@host' to {name, email}."""
    s = s.strip()
    if "<" in s and s.endswith(">"):
        name, _, rest = s.partition("<")
        return {"email": rest[:-1].strip(), "name": name.strip()}
    return {"email": s}


# ─── Routes ─────────────────────────────────────────────────────────


@auth_bp.route("/api/auth/magic-link", methods=["POST"])
@limiter.limit(
    # Per-email cap (prevents bombing one inbox) + per-IP cap (prevents
    # session-ID-rotation bypass). Both must trip to refuse. Catches the
    # email-enumeration + Resend-quota-exhaustion attack the audit flagged.
    "5 per hour;20 per day",
    key_func=lambda: (
        (request.get_json(silent=True) or {}).get("email", "anon").strip().lower()
    ),
)
@limiter.limit("30 per hour", key_func=lambda: request.remote_addr or "anon")
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
@limiter.limit("20 per minute;200 per hour")
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
    # Atomic single-use claim: only the first concurrent request that
    # finds `used_at IS NULL` AND `expires_at > NOW()` wins. Previously
    # two concurrent verifies could both pass the Python-side check
    # before either committed — now SQL serializes for us.
    now = datetime.utcnow()
    claimed = (
        AuthToken.query
        .filter(
            AuthToken.token_hash == token_hash,
            AuthToken.used_at.is_(None),
            AuthToken.expires_at > now,
        )
        .update({AuthToken.used_at: now}, synchronize_session=False)
    )
    if claimed == 0:
        # Single generic message — distinguishing invalid / used / expired
        # leaks token state to an attacker probing the endpoint. Same
        # response time regardless of which path matched.
        db.session.commit()
        return jsonify({"error": "invalid or expired token"}), 400
    token = AuthToken.query.filter_by(token_hash=token_hash).first()

    user = db.session.get(User, token.user_id) if token else None
    if user is None or user.deleted_at is not None:
        # Roll back the claim so the token isn't burned on an orphaned row
        db.session.rollback()
        return jsonify({"error": "invalid or expired token"}), 400

    # Phase 1.5 cross-device sync: instead of overwriting user.session_id
    # on each verify (last-device-wins, kicks the previous device out), we
    # treat user.session_id as the user's CANONICAL server-side session.
    # The verifying device adopts that canonical id for all subsequent
    # API calls. Result: every device signed into the same account hits
    # the same server-side rows (chat history, mood entries, assessments)
    # without needing a separate device_sessions junction table.
    #
    # If user.session_id is somehow null (data inconsistency from earlier
    # rows), fall back to binding the current device's session.
    _get_or_create_session()  # ensures the device's anon session exists
    if user.session_id is None:
        user.session_id = _get_or_create_session()
    canonical_session_id = user.session_id
    # token.used_at was already set atomically above by the claim UPDATE.
    db.session.commit()

    return jsonify(
        {
            "user": {"id": user.id, "email": user.email},
            "session_id": canonical_session_id,
        }
    ), 200


@auth_bp.route("/auth/redirect", methods=["GET"])
def auth_redirect_router():
    """Smart redirect from the magic-link email to the right surface.

    Note: deliberately mounted at `/auth/redirect` (no `/api/` prefix)
    because this URL is opened directly by an email client / web
    browser, not by the Flutter app's API client. It returns a 302
    `Location:` header — never JSON.

    UA-sniffing strategy:
      - iPhone / iPad / iPod / Android → 302 to `gentlequest://auth/verify?token=...`
        so the registered native scheme handler opens the installed app.
      - Anything else (desktop, mail-preview bot, unknown) → 302 to
        `https://gentlequest.app/auth/verify?token=...` so the Flutter
        web build can pick up the token from window.location and call
        the same `/api/auth/verify` POST endpoint.

    Token is round-tripped untouched. We don't peek at / validate it
    here — that's the verify endpoint's job, and doing it twice means
    the wrapper would burn the token before the client could spend it.
    """
    raw_token = request.args.get("token", "").strip()
    if not raw_token:
        # Missing token = link malformed or stripped by an email
        # client. Send the user to the marketing site rather than
        # dump them on a broken verify screen.
        return redirect("https://gentlequest.app/", code=302)

    ua = request.headers.get("User-Agent", "")
    if _is_mobile_user_agent(ua):
        target = f"{DEEP_LINK_SCHEME}://auth/verify?token={raw_token}"
        logger.info("auth_redirect.mobile ua=%s", ua[:80])
    else:
        target = f"{WEB_AUTH_VERIFY_URL}?token={raw_token}"
        logger.info("auth_redirect.web ua=%s", ua[:80])
    return redirect(target, code=302)


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


@auth_bp.route("/api/auth/signOut", methods=["POST"])
@limiter.limit(
    "10 per hour",
    key_func=lambda: (
        request.headers.get("X-Session-ID") or request.remote_addr or "anon"
    ),
)
def sign_out():
    """Revoke the server-side session→user binding for the current device.

    Why this exists: client-only sign-out leaves the User row pointing at
    the device's session_id. If the device is lost / stolen / handed off,
    the previous owner can't revoke the binding from another device.
    Posting here breaks the link server-side so subsequent requests under
    the same X-Session-ID are treated as anonymous.

    We deliberately do NOT delete the UserSession row — that would orphan
    chat history, journal entries, mood reflections etc. that are
    foreign-keyed to it. We only clear `User.session_id`, which severs
    the user↔session edge while leaving both endpoints intact. The user
    can re-bind a (possibly new) device session via a fresh magic-link.

    Returns 200 with {"status": "signed_out"} unconditionally — even if
    the X-Session-ID had no user binding (already anonymous). Same info-
    leak posture as the rest of this module: never reveal account state.

    Rate-limited at 10 per hour per session-id to prevent griefing
    (forcing repeated re-bindings on a victim account).
    """
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        # No session header → nothing to unbind. Anonymous is the natural
        # post-signout state, so report success.
        return jsonify({"status": "signed_out"}), 200

    user: Optional[User] = (
        User.query.filter_by(session_id=session_id, deleted_at=None).first()
    )
    if user is None:
        # Session id has no user binding (already anonymous, or never
        # signed in on this device). Idempotent — still 200.
        return jsonify({"status": "signed_out"}), 200

    # Sever the user→session edge. We leave the session row + the user
    # row themselves alone:
    #   - UserSession (id=session_id) still owns its content rows
    #     (journal, chat, mood, etc.) via the FK from those tables.
    #   - User row is preserved so a future magic-link re-binds the same
    #     account to whatever fresh session id the device adopts next.
    # Setting user.session_id = None is the lightest possible undo of
    # the bind that verify_magic_link performs.
    user.session_id = None
    db.session.commit()
    logger.info(
        "auth.sign_out user_id=%s session_id=%s", user.id, session_id
    )

    return jsonify({"status": "signed_out"}), 200
