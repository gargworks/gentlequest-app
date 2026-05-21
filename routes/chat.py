"""
Chat and chat_stream endpoints.
Extracted from app.py monolith.
"""

import json
import os
import re as _re
import time

from flask import Blueprint, Response, current_app, g, jsonify, request

from extensions import limiter
from models import Message

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/api/chat", methods=["POST"])
@limiter.limit("30 per minute")
def chat():
    """Enhanced chat endpoint with geography-specific crisis detection"""
    try:
        from helpers.chat_helpers import _process_chat_message
        from helpers.crisis_helpers import (
            _run_crisis_watchdog,
            get_country_from_request,
            get_crisis_response_and_resources,
        )
        from helpers.session_helpers import (
            _get_conversation_count,
            _get_or_create_session,
            _increment_conversation_count,
            _log_analytics_event,
            _log_chat_request,
            background_executor,
        )

        _t0 = time.monotonic()
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Message is required"}), 400

        session_id = _get_or_create_session()
        user_message = data["message"].strip()

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        if len(user_message) > 5000:
            return jsonify({"error": "Message too long (max 5000 characters)"}), 400

        # Detect first-time vs returning user (lightweight query)
        # Tri-state: True/False on success, None if DB query fails (skip greeting behavior).
        try:
            _is_first_message = Message.query.filter_by(
                session_id=session_id, is_user=True
            ).first() is None
        except Exception as _first_msg_exc:
            current_app.logger.warning(
                "first_message_lookup_failed session_id=%s err=%s",
                session_id, _first_msg_exc,
            )
            _is_first_message = None

        # Get country from request
        country = get_country_from_request(request)

        _t1 = time.monotonic()
        # Process message with AI provider.
        # When _is_first_message is None (DB lookup failed), skip first-time greeting
        # behavior rather than fall through to True.
        ai_response, risk_level, tool_calls = _process_chat_message(
            user_message, session_id, is_first_message=bool(_is_first_message)
        )
        _t2 = time.monotonic()

        # Get geography-specific crisis data
        crisis_data = get_crisis_response_and_resources(risk_level, country)

        # Parallel Watchdog: Start deep clinical analysis in background (Scaling Crisis Detection)
        background_executor.submit(_run_crisis_watchdog, current_app._get_current_object(), user_message, session_id, risk_level)

        # Extract exercise data from tool calls (if any)
        exercise_data = {}
        for tc in tool_calls:
            result = tc.get("result", {})
            # Handle both intervention_type and exercise_type (agent_tools vs legacy)
            ex_type = result.get("intervention_type") or result.get("exercise_type")
            if result.get("interactive") and ex_type:
                exercise_data = {
                    "interactive": True,
                    "exercise_type": ex_type,  # Normalize to exercise_type for Flutter
                    "exercise": result.get("exercise"),
                    "offer_stage": result.get("offer_stage", 1),  # Include stage for debugging
                    "function_call_source": tc.get("source", "gemini"),  # Track if Gemini or fallback
                }
                break  # Only include first exercise

        _t3 = time.monotonic()
        response_data = {
            "response": ai_response,
            "risk_level": risk_level,
            "crisis_detected": risk_level == "crisis",
            "crisis_level": risk_level,
            "session_id": session_id,
            "crisis_msg": crisis_data["crisis_msg"],
            "crisis_numbers": crisis_data["crisis_numbers"],
            "is_first_conversation": _is_first_message,
            "conversation_count": _get_conversation_count(session_id),
        }

        # Increment conversation_count on first message of each conversation
        if _is_first_message:
            background_executor.submit(
                _increment_conversation_count, current_app._get_current_object(), session_id
            )

        # Server-side behavioral event (fire-and-forget)
        _evt_type = "first_chat_message" if _is_first_message else "chat_message"
        background_executor.submit(
            _log_analytics_event, current_app._get_current_object(),
            session_id, _evt_type, {
                "message_length": len(user_message),
                "response_length": len(ai_response),
                "latency_ms": round((_t3 - _t0) * 1000),
                "has_exercise": bool(exercise_data),
            }
        )

        # Include timing only when ?debug=1
        if request.args.get("debug") == "1":
            response_data["_debug_timing"] = {
                "setup_ms": round((_t1 - _t0) * 1000),
                "llm_ms": round((_t2 - _t1) * 1000),
                "post_ms": round((_t3 - _t2) * 1000),
                "total_ms": round((_t3 - _t0) * 1000),
                "inner": getattr(g, '_gemini_perf', {}),
            }

        # Merge exercise data if present
        if exercise_data:
            response_data.update(exercise_data)

        # Log request/response for training data
        _latency = round((_t3 - _t0) * 1000)
        _model = os.environ.get("AI_PROVIDER", "gemini")
        background_executor.submit(
            _log_chat_request, session_id, len(user_message),
            len(ai_response), _latency, 200, _model,
        )

        # --- SSE streaming mode: ?stream=true ---
        if request.args.get("stream") == "true":
            def _sse_generator():
                def sse(obj):
                    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

                # 1. Meta event (crisis, session, exercise data)
                meta = {
                    "type": "meta",
                    "session_id": session_id,
                    "risk_level": risk_level,
                    "crisis_msg": crisis_data["crisis_msg"],
                    "crisis_numbers": crisis_data["crisis_numbers"],
                    "is_first_conversation": _is_first_message,
                }
                if exercise_data:
                    meta.update(exercise_data)
                yield sse(meta)

                # 2. Stream response text as token events
                text = ai_response or ""
                if "\n" in text:
                    chunks = text.split("\n")
                    joiner = "\n"
                else:
                    parts = [p for p in _re.split(r"(?<=[.!?])\s+", text) if p]
                    if len(parts) <= 1:
                        chunks = text.split(" ")
                        joiner = " "
                    else:
                        chunks = [
                            p + (" " if i < len(parts) - 1 else "")
                            for i, p in enumerate(parts)
                        ]
                        joiner = ""

                for idx, ch in enumerate(chunks):
                    yield sse({
                        "type": "token",
                        "text": (joiner + ch) if (idx > 0 and joiner) else ch,
                    })

                # 3. Done signal
                yield sse({"type": "done"})

            return Response(
                _sse_generator(),
                headers={
                    "Content-Type": "text/event-stream",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )

        return (
            jsonify(response_data),
            200,
        )

    except Exception as e:
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            raise  # Let global error handlers handle 413, 429, etc.
        import traceback
        current_app.logger.error(f"Chat endpoint error: {e}")
        _err_latency = round((time.monotonic() - _t0) * 1000) if '_t0' in dir() else 0
        _data = data if 'data' in dir() else None
        try:
            from helpers.session_helpers import _log_chat_request, background_executor
            background_executor.submit(
                _log_chat_request, _data.get("session_id", "") if _data else "",
                len(_data.get("message", "")) if _data else 0, 0, _err_latency, 500,
            )
        except Exception:
            pass
        trace = traceback.format_exc() if current_app.config.get("ENVIRONMENT") == "local" else None
        return jsonify({"error": "Internal server error", "trace": trace}), 500


@chat_bp.route("/api/chat_stream", methods=["GET"])
def chat_stream():
    """Server-Sent Events (SSE) streaming endpoint for chat responses.
    Accepts query params: message (required), country (optional), session_id (optional)
    Streams JSON objects with a 'type' field: 'meta', 'token', 'done', 'error'.
    """
    try:
        from typing import List

        from crisis_detection import detect_crisis_level
        from helpers.chat_helpers import _process_chat_message
        from helpers.crisis_helpers import (
            _run_crisis_watchdog,
            get_crisis_response_and_resources,
        )
        from helpers.session_helpers import (
            _get_or_create_session,
            background_executor,
        )

        message = (request.args.get("message") or "").strip()
        if not message:
            return jsonify({"error": "Message is required"}), 400

        if len(message) > 5000:
            return jsonify({"error": "Message too long (max 5000 characters)"}), 400

        # Session handling: prefer provided session_id (from web EventSource cannot set headers)
        session_id = request.args.get("session_id") or _get_or_create_session()

        # Detect first-time user for warm greeting
        # Graceful fallback: if DB is down, assume first message (safe default)
        try:
            _is_first_msg = Message.query.filter_by(
                session_id=session_id, is_user=True
            ).first() is None
        except Exception:
            _is_first_msg = True

        # Country for geo-specific crisis resources (sanitize to alpha, max 10 chars)
        _raw_country = request.args.get("country") or "generic"
        country = "".join(c for c in _raw_country[:10] if c.isalpha()).lower() or "generic"

        # Crisis detection first
        risk_level = detect_crisis_level(message)
        crisis_data = get_crisis_response_and_resources(risk_level, country)

        # Parallel Watchdog: Start deep clinical analysis in background (Scaling Crisis Detection)
        background_executor.submit(_run_crisis_watchdog, current_app._get_current_object(), message, session_id, risk_level)

        # Generate AI response with tool support (function calling)
        full_text, actual_risk, tool_calls = _process_chat_message(
            message, session_id, is_first_message=_is_first_msg,
        )
        # Use detected risk level from the response if available
        if actual_risk:
            risk_level = actual_risk

        # Extract exercise data from tool calls (if any)
        exercise_data = {}
        for tc in tool_calls:
            result = tc.get("result", {})
            # Handle both intervention_type and exercise_type
            ex_type = result.get("intervention_type") or result.get("exercise_type")
            if result.get("interactive") and ex_type:
                exercise_data = {
                    "interactive": True,
                    "exercise_type": ex_type,
                    "exercise": result.get("exercise"),
                }
                break

        def stream_generator():
            import json as _json

            def sse(obj: dict):
                data = _json.dumps(obj, ensure_ascii=False)
                return f"data: {data}\n\n"

            # Send initial metadata (risk/crisis info, session, and exercise data)
            meta_event = {
                "type": "meta",
                "session_id": session_id,
                "risk_level": risk_level,
                "crisis_msg": crisis_data.get("crisis_msg"),
                "crisis_numbers": crisis_data.get("crisis_numbers", []),
                "is_first_conversation": _is_first_msg,
            }
            # Include exercise data in meta if present
            if exercise_data:
                meta_event.update(exercise_data)
            yield sse(meta_event)

            # Chunk the AI response for progressive reveal
            text = full_text or ""
            # Prefer newline splits, then sentence-ish (preserving spaces), then words
            chunks: List[str]
            joiner = ""
            if "\n" in text:
                chunks = text.split("\n")
                joiner = "\n"
            else:
                parts = [p for p in _re.split(r"(?<=[.!?])\s+", text) if p]
                if len(parts) <= 1:
                    chunks = text.split(" ")
                    joiner = " "
                else:
                    # Re-attach a single space that was consumed by the split for all but the last part.
                    chunks = [
                        p + (" " if i < len(parts) - 1 else "")
                        for i, p in enumerate(parts)
                    ]

            try:
                for idx, ch in enumerate(chunks):
                    yield sse(
                        {
                            "type": "token",
                            "text": (joiner + ch) if (idx > 0 and joiner) else ch,
                        }
                    )
                    # Small human-like pacing
                    delay_ms = max(60, min(220, int(len(ch.strip()) * 12)))
                    time.sleep(delay_ms / 1000.0)

                # Done signal
                yield sse({"type": "done"})
            except GeneratorExit:
                # Client disconnected mid-stream — stop yielding immediately
                return

        headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "text/event-stream",
            "Connection": "keep-alive",
        }
        return Response(stream_generator(), headers=headers)

    except Exception as e:
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            raise
        current_app.logger.error(f"Chat stream error: {e}")
        return jsonify({"error": "Internal server error"}), 500
