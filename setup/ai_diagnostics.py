"""
AI provider startup diagnostics.
Extracted from app.py monolith.

`log_ai_startup_diagnostics(app)` emits a single INFO log line describing:
- AI_DEBUG_LOGS flag
- configured provider
- available API keys per provider
- resolved failover chain
"""

import os

from flask import Flask

from helpers.chat_helpers import _build_failover_chain, _provider_keys_available


def log_ai_startup_diagnostics(app: Flask) -> None:
    """Emit a startup INFO log line summarizing AI provider readiness."""
    try:
        debug_flag = (os.getenv("AI_DEBUG_LOGS") or "").lower() == "true"
        available = _provider_keys_available()
        configured = str(app.config.get("AI_PROVIDER", "gemini")).lower()

        chain = []
        try:
            with app.app_context():
                chain = _build_failover_chain()
        except Exception:
            # Best-effort chain without app context
            default_order = ["gemini", "openai", "perplexity"]
            if available.get(configured):
                chain.append(configured)
            for p in default_order:
                if available.get(p) and p not in chain:
                    chain.append(p)

        app.logger.info(
            f"AI startup: AI_DEBUG_LOGS={debug_flag} "
            f"configured={configured} available={available} "
            f"failover_chain={chain}"
        )
    except Exception as e_diag:
        app.logger.warning(f"AI startup diagnostics failed: {e_diag}")
