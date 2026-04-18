"""
Global error handlers + request-id middleware.
Extracted from app.py monolith.
"""

import time
import uuid

import sentry_sdk
from flask import Flask, g, jsonify, render_template, request


def register_request_id_middleware(app: Flask) -> None:
    """Attach a request ID and latency timer on each request; emit headers."""

    @app.before_request
    def _attach_request_id():
        try:
            g.request_start = time.monotonic()
            rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
            g.request_id = rid
            try:
                sentry_sdk.set_tag("request_id", rid)
            except Exception:
                pass
        except Exception:
            pass

    @app.after_request
    def _add_request_id_header(resp):
        try:
            rid = getattr(g, "request_id", None)
            if rid:
                resp.headers["X-Request-ID"] = rid
            start = getattr(g, "request_start", None)
            if start:
                elapsed_ms = int((time.monotonic() - start) * 1000)
                resp.headers["X-Response-Time"] = str(elapsed_ms)
                if elapsed_ms > 5000 and request.path.startswith("/api/"):
                    app.logger.warning(
                        f"Slow request: {request.method} {request.path} {elapsed_ms}ms"
                    )
        except Exception:
            pass
        return resp


def register_error_handlers(app: Flask) -> None:
    """Register 404/405/413/429/500 handlers — JSON for API, HTML for browser."""

    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        return render_template("landing.html"), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(413)
    def handle_413(e):
        return (
            jsonify({"error": "Request too large", "max_bytes": 5 * 1024 * 1024}),
            413,
        )

    @app.errorhandler(429)
    def handle_429(e):
        return (
            jsonify({"error": "Rate limit exceeded", "retry_after": e.description}),
            429,
        )

    @app.errorhandler(500)
    def handle_500(e):
        app.logger.error(f"Internal error: {e}")
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500
        return "Internal server error", 500
