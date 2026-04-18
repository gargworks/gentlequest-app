"""
Twilio SMS client with circuit-breaker + env-gated disable for dev/test.

Public API:
- send_sms(to: str, body: str) -> dict  \u2014 returns {ok: bool, sid?: str, error?: str}
- circuit_state() -> dict               \u2014 returns {open: bool, failures: int, last_failure: datetime|None}

Environment:
- TWILIO_DISABLED=true                  \u2014 Short-circuits to a fake success (dev/test default)
- TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER

Circuit breaker:
- 3 consecutive failures trips the breaker
- Auto-resets after 60 seconds
- While open, send_sms returns {ok: False, error: "circuit_open"} without calling Twilio
"""

import os
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

# Circuit-breaker state (module-level; single-process)
_LOCK = threading.Lock()
_FAILURE_COUNT = 0
_FAILURE_THRESHOLD = 3
_RESET_SECONDS = 60
_LAST_FAILURE: Optional[datetime] = None


def _is_disabled() -> bool:
    return (os.getenv("TWILIO_DISABLED", "").lower() == "true"
            or bool(os.getenv("PYTEST_CURRENT_TEST"))
            and os.getenv("TWILIO_FORCE_ENABLE") != "true")


def circuit_state() -> Dict[str, Any]:
    """Return the current circuit-breaker state."""
    with _LOCK:
        now = datetime.now(timezone.utc)
        is_open = (
            _FAILURE_COUNT >= _FAILURE_THRESHOLD
            and _LAST_FAILURE is not None
            and (now - _LAST_FAILURE) < timedelta(seconds=_RESET_SECONDS)
        )
        return {
            "open": is_open,
            "failures": _FAILURE_COUNT,
            "threshold": _FAILURE_THRESHOLD,
            "reset_seconds": _RESET_SECONDS,
            "last_failure": _LAST_FAILURE.isoformat() if _LAST_FAILURE else None,
        }


def _record_success() -> None:
    global _FAILURE_COUNT, _LAST_FAILURE
    with _LOCK:
        _FAILURE_COUNT = 0
        _LAST_FAILURE = None


def _record_failure() -> None:
    global _FAILURE_COUNT, _LAST_FAILURE
    with _LOCK:
        _FAILURE_COUNT += 1
        _LAST_FAILURE = datetime.now(timezone.utc)


def reset_circuit() -> None:
    """Force-reset the circuit breaker (mainly for tests)."""
    global _FAILURE_COUNT, _LAST_FAILURE
    with _LOCK:
        _FAILURE_COUNT = 0
        _LAST_FAILURE = None


def send_sms(to: str, body: str, max_retries: int = 2) -> Dict[str, Any]:
    """Send an SMS. Non-throwing.

    Returns one of:
    - {"ok": True, "sid": "..."}
    - {"ok": True, "mock": True} when TWILIO_DISABLED or in test mode
    - {"ok": False, "error": "circuit_open"}
    - {"ok": False, "error": "missing_credentials"}
    - {"ok": False, "error": "twilio_error: <msg>"}

    Privacy:
    - Caller is responsible for ensuring `body` contains no raw user message content.
    - Recommended: send a crisis-line number + resource codes only.
    """
    if _is_disabled():
        # Dev/test short-circuit — return a mock success
        return {"ok": True, "mock": True, "to": to[-4:] if to else ""}

    # Circuit-breaker check
    state = circuit_state()
    if state["open"]:
        # Check if reset window elapsed
        if _LAST_FAILURE and (
            datetime.now(timezone.utc) - _LAST_FAILURE
        ) >= timedelta(seconds=_RESET_SECONDS):
            reset_circuit()
        else:
            return {"ok": False, "error": "circuit_open"}

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not (account_sid and auth_token and from_number):
        return {"ok": False, "error": "missing_credentials"}

    # Lazy import to keep twilio optional
    try:
        from twilio.rest import Client  # type: ignore[import-not-found]
    except ImportError:
        return {"ok": False, "error": "twilio_package_missing"}

    last_err: Optional[str] = None
    for attempt in range(max_retries + 1):
        try:
            client = Client(account_sid, auth_token)
            msg = client.messages.create(body=body, from_=from_number, to=to)
            _record_success()
            return {"ok": True, "sid": msg.sid}
        except Exception as e:
            last_err = str(e)
            if attempt < max_retries:
                time.sleep(0.2 * (2 ** attempt))  # exponential backoff

    _record_failure()
    return {"ok": False, "error": f"twilio_error: {last_err}"}


__all__ = [
    "circuit_state",
    "reset_circuit",
    "send_sms",
]
