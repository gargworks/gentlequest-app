"""
Early logging setup + Sentry initialization.

LOG_FORMAT=json switches to structured JSON logs suitable for Cloud Run / Render
aggregators. Fields emitted: timestamp, level, logger, message, module, line,
plus request_id / session_id / route / elapsed_ms when present on `flask.g`.
"""

import logging
import os
from typing import Any, Dict

import sentry_sdk
from flask import Flask, g, has_request_context, request
from pythonjsonlogger import jsonlogger
from sentry_sdk.integrations.flask import FlaskIntegration

from config.settings import Config


class _RequestContextJsonFormatter(jsonlogger.JsonFormatter):
    """JSON formatter that injects Flask request/session fields when available."""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:  # noqa: D401
        super().add_fields(log_record, record, message_dict)
        log_record.setdefault("level", record.levelname)
        log_record.setdefault("logger", record.name)

        if has_request_context():
            try:
                log_record["route"] = request.path
                log_record["method"] = request.method
                rid = getattr(g, "request_id", None)
                if rid:
                    log_record["request_id"] = rid
                sid = request.headers.get("X-Session-ID")
                if sid:
                    log_record["session_id"] = sid
            except Exception:
                pass


def _sentry_scrub_pii(event: Dict[str, Any], hint: Dict[str, Any]) -> Dict[str, Any]:
    """Drop raw message bodies from Sentry events (PII mitigation)."""
    try:
        req = event.get("request") or {}
        data = req.get("data")
        if data:
            # Replace request body with a fixed placeholder
            req["data"] = "<scrubbed>"
        # Scrub extra context keys that commonly hold user content
        extra = event.get("extra") or {}
        for k in list(extra.keys()):
            if any(tok in k.lower() for tok in ("message", "content", "prompt", "body")):
                extra[k] = "<scrubbed>"
    except Exception:
        pass
    return event


def configure_logging(app: Flask) -> None:
    """Set log level + handler. If LOG_FORMAT=json, attach JSON formatter."""
    try:
        level_name = str(app.config.get("LOG_LEVEL", "INFO")).upper()
        level = getattr(logging, level_name, logging.INFO)
        app.logger.setLevel(level)

        log_format = (os.getenv("LOG_FORMAT") or "").lower()

        if not any(isinstance(h, logging.StreamHandler) for h in app.logger.handlers):
            sh = logging.StreamHandler()
            sh.setLevel(level)
            if log_format == "json":
                formatter: logging.Formatter = _RequestContextJsonFormatter(
                    "%(asctime)s %(levelname)s %(name)s %(module)s %(lineno)d %(message)s"
                )
            else:
                formatter = logging.Formatter(
                    "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
                )
            sh.setFormatter(formatter)
            app.logger.addHandler(sh)
    except Exception:
        pass


def init_sentry(app: Flask) -> None:
    """Initialize Sentry SDK if SENTRY_DSN_BACKEND is configured. Non-fatal.

    Uses `before_send=_sentry_scrub_pii` to strip request bodies / message
    fields before sending events upstream.
    """
    try:
        dsn = os.getenv("SENTRY_DSN_BACKEND", "").strip()
        if dsn:
            sentry_sdk.init(
                dsn=dsn,
                integrations=[FlaskIntegration()],
                traces_sample_rate=float(
                    os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0") or 0
                ),
                profiles_sample_rate=float(
                    os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0") or 0
                ),
                environment=Config.ENVIRONMENT,
                release=Config.VERSION,
                before_send=_sentry_scrub_pii,  # type: ignore[arg-type]
                send_default_pii=False,
            )
            app.logger.info("Sentry initialized for backend")
    except Exception as e:
        app.logger.warning(f"Sentry init failed: {e}")
