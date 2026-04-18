"""
Nuclear Brain / Telegram integration routes.
Extracted from app.py monolith. All endpoints live under /api/brain/* (plus /api/swarms).

register_brain_routes(app) is a no-op if brain_telegram import fails.
"""

import json
import os
import secrets
import traceback
from pathlib import Path

from flask import Flask, jsonify, request


def register_brain_routes(app: Flask) -> None:
    """Register Nuclear Brain Telegram endpoints. Non-fatal on failure."""
    try:
        from brain_telegram import (
            handle_sprint_command,
            load_state,
            process_telegram_message,
            send_telegram_alert,
        )

        TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

        @app.route("/api/brain/telegram/webhook", methods=["POST"])
        def brain_telegram_webhook():
            """Handle incoming Telegram updates for Nuclear Brain."""
            try:
                data = request.get_json()
                message = data.get("message", {})
                chat_id = str(message.get("chat", {}).get("id", ""))

                if chat_id != TG_CHAT_ID:
                    return jsonify({"ok": False, "error": "Unauthorized"}), 403

                response_text = process_telegram_message(message)
                send_telegram_alert(response_text)
                return jsonify({"ok": True})
            except Exception as e:
                app.logger.error(f"Telegram webhook error: {e}")
                return (
                    jsonify({"ok": False, "error": "Webhook processing failed"}),
                    500,
                )

        @app.route("/api/brain/status", methods=["GET"])
        def brain_status():
            """Get Nuclear Brain status via API."""
            try:
                state = load_state()
                return jsonify(state)
            except Exception as e:
                app.logger.error(f"Brain status error: {e}")
                return jsonify({"error": "Failed to load brain status"}), 500

        @app.route("/api/brain/alert", methods=["POST"])
        def brain_alert():
            """Send alert to founder's Telegram."""
            data = request.get_json() or {}
            msg = data.get("message", "Alert from Nuclear Brain")
            success = send_telegram_alert(msg)
            return jsonify({"ok": success})

        @app.route("/api/brain/sprint", methods=["POST"])
        def brain_sprint():
            """Start new sprint via API."""
            data = request.get_json() or {}
            goal = data.get("goal", "")
            if not goal:
                return jsonify({"error": "Goal required"}), 400
            result = handle_sprint_command(goal)
            send_telegram_alert(f"🚀 New Sprint Started via API\n\n{goal}")
            return jsonify({"ok": True, "message": result})

        @app.route("/api/swarms", methods=["GET"])
        def get_swarms():
            """Get active swarms state."""
            try:
                brain_path = Path(os.getenv("NUCLEUS_BRAIN_PATH", ".brain"))
                state_file = brain_path / "swarms" / "state.json"

                swarms_list = []
                if state_file.exists():
                    state = json.loads(state_file.read_text())
                    for mid, mdata in state.items():
                        mdata["session_id"] = mid
                        if "agents" not in mdata:
                            mdata["agents"] = [mdata.get("lead", "Unknown")]
                        swarms_list.append(mdata)

                return jsonify({"swarms": swarms_list})
            except Exception as e:
                app.logger.error(f"Failed to get swarms: {e}")
                return jsonify({"error": str(e)}), 500

        @app.route("/api/brain/sync", methods=["POST"])
        def brain_sync_state():
            """Sync local brain state to production."""
            try:
                state_data = request.get_json()
                if not state_data:
                    return jsonify({"error": "No data provided"}), 400

                brain_root = Path(app.root_path) / ".brain"
                ledger_dir = brain_root / "ledger"
                ledger_dir.mkdir(parents=True, exist_ok=True)

                save_path = ledger_dir / "state.json"
                with open(save_path, "w") as f:
                    json.dump(state_data, f, indent=4)

                app.logger.info(f"Brain state synced to {save_path}")
                return jsonify({"ok": True, "message": "State synced"})
            except Exception as e:
                app.logger.error(f"Sync failed: {e}")
                return jsonify({"ok": False, "error": str(e)}), 500

        app.logger.info("Nuclear Brain Telegram routes registered (/api/brain/*)")
    except Exception as e:
        app.logger.error(
            f"Brain Telegram routes failed to register: {e}\n{traceback.format_exc()}"
        )

    # Debug import probe — always registered (admin-only)
    @app.route("/api/brain/debug_import")
    def debug_brain_import():
        token = request.headers.get("X-Admin-Token") or ""
        expected = app.config.get("ADMIN_API_TOKEN") or ""
        if not expected or not secrets.compare_digest(token, expected):
            return jsonify({"error": "Unauthorized"}), 401
        try:
            import brain_telegram  # noqa: F401
            return (
                "Import Successful! If routes are 404, "
                "check route registration logic."
            )
        except Exception:
            return traceback.format_exc()
