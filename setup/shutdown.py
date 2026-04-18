"""
Graceful shutdown hooks.

Registers SIGTERM + SIGINT handlers that drain the shared background executor
and close Redis connections before the process exits.
"""

import signal
import sys
from typing import Optional

from flask import Flask

from helpers.session_helpers import background_executor


def _shutdown_background_executor(timeout_s: float = 5.0) -> None:
    """Wait up to `timeout_s` for in-flight background jobs to finish."""
    try:
        background_executor.shutdown(wait=True, cancel_futures=False)
    except TypeError:
        # Python < 3.9: cancel_futures kw not supported
        background_executor.shutdown(wait=True)
    except Exception:
        pass


def _close_redis(app: Flask) -> None:
    """Best-effort close of Redis connection held by flask-session."""
    try:
        redis_client = app.config.get("SESSION_REDIS")
        if redis_client is not None:
            close = getattr(redis_client, "close", None)
            if callable(close):
                close()
    except Exception:
        pass


def register_graceful_shutdown(app: Flask, timeout_s: float = 5.0) -> None:
    """Install SIGTERM + SIGINT handlers.

    Safe to call multiple times; subsequent calls overwrite prior handlers.
    In test environments (where the main thread isn't the runner thread)
    signal.signal() may raise ValueError — we swallow it.
    """
    def _handler(signum: int, frame: Optional[object]) -> None:
        app.logger.info(f"Received signal {signum}; draining background jobs")
        _shutdown_background_executor(timeout_s)
        _close_redis(app)
        app.logger.info("Shutdown complete; exiting")
        sys.exit(0)

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _handler)
        except (ValueError, OSError):
            # Not on main thread or platform doesn't allow — non-fatal
            pass
