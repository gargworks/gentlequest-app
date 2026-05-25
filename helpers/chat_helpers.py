"""
Chat processing helpers: LLM calls, safety layers, failover chain,
conversation logging, and tool call tracking.
Extracted from app.py monolith.
"""

import atexit
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Tuple

from flask import Flask, current_app

from crisis_detection import detect_crisis_level
from helpers.health_helpers import _detect_platform
from models import Message, db
from providers.alert_manager import AlertManager

# ── Layer 2 safety executor ─────────────────────────────────────────
# Dedicated small pool so we don't head-of-line block behind crisis
# watchdog / memory summarization tasks on background_executor.
_safety_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="layer2-safety")
atexit.register(lambda: _safety_executor.shutdown(wait=False))
_SAFETY_TIMEOUT_SECONDS = float(os.environ.get("SAFETY_TIMEOUT_SECONDS", "5"))


# ── LLM JSON call (background analysis) ─────────────────────────────

def _call_llm_json(prompt: str, system_prompt: str = None) -> str:
    """
    Directly call Gemini for structured data (skips chat persona/history).
    Used for background analysis like crisis watchdog.
    Attempts multiple models in order of preference/speed.
    """
    import warnings as _w
    _w.filterwarnings("ignore", message=".*google.generativeai.*", category=FutureWarning)
    import os

    import google.generativeai as genai

    api_keys = (os.getenv("GEMINI_API_KEY") or "").split(",")
    if not api_keys[0]:
        return "{}"
        
    # Simple rotation for background tasks
    import random
    api_key = random.choice(api_keys).strip()
    
    # Fallback chain: Newest/Fastest -> Stable
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]
    
    full_content = prompt
    if system_prompt:
        full_content = f"{system_prompt}\n\n{prompt}"
    
    try:
        genai.configure(api_key=api_key)
        
        last_error = None
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(full_content, request_options={"timeout": 60})
                if response and hasattr(response, "text"):
                    return response.text
            except Exception as e:
                # Capture error and try next model
                last_error = e
                continue
                
        # If we get here, all models failed
        if last_error:
            print(f"DEBUG: All models failed in _call_llm_json. Last error: {last_error}")
            
        return "{}"
    except Exception as e:
        print(f"DEBUG: _call_llm_json setup error: {e}")
        return "{}"



# ── Layer 2 safety verification ───────────────────────────────────

def _apply_layer_2_safety(
    user_message: str,
    ai_response: str,
    session_id: str,
    risk_level: str,
) -> Tuple[str, bool]:
    """Run Layer 2 supervisor check with a tight timeout.

    Returns (final_response, was_blocked).
    - was_blocked=True means helper already wrote the BLOCKED_UNSAFE audit row;
      caller MUST NOT call _log_conversation again for this turn.
    - On timeout or any exception: fail open (return original, blocked=False),
      matching providers/safety.py's own fail-open contract.
    - Skipped for empty responses.
    """
    if not ai_response:
        return ai_response, False

    # Lazy import keeps the existing test patch path
    # `@patch('providers.safety.check_safety_llm')` working unchanged.
    from concurrent.futures import TimeoutError as FuturesTimeoutError

    from providers.safety import check_safety_llm

    future = _safety_executor.submit(check_safety_llm, user_message, ai_response)
    try:
        is_safe, safety_msg = future.result(timeout=_SAFETY_TIMEOUT_SECONDS)
    except FuturesTimeoutError:
        current_app.logger.warning(
            f"Layer 2 safety timeout after {_SAFETY_TIMEOUT_SECONDS}s — "
            f"fail open (session={session_id})"
        )
        return ai_response, False
    except Exception as exc:
        current_app.logger.warning(f"Layer 2 safety error — fail open: {exc}")
        return ai_response, False

    if not is_safe:
        current_app.logger.warning(f"Guardrail Layer 2 Block: {safety_msg[:100]}")
        _log_conversation(
            session_id,
            user_message,
            f"BLOCKED_UNSAFE: {safety_msg}",
            risk_level,
        )
        return safety_msg, True

    return ai_response, False



# ── Main chat message processing ──────────────────────────────────

def _process_chat_message(
    message: str,
    session_id: str,
    is_first_message: bool = False,
    user_nickname: str | None = None,
    user_pronoun: str | None = None,
    user_tone: str | None = None,
    user_greeting_style: str | None = None,
) -> Tuple[str, str, List[Dict]]:
    """Process chat message with AI provider and crisis detection.

    When using Gemini, this enables function calling for wellness tools.

    user_nickname / user_pronoun / user_tone are optional personalisation
    fields sent by the GentleQuest Flutter client (see audit §4 + §6 in
    `.brain/audits/2026-05-24_gq_v1.3.0_honesty_audit.md`). They are
    pre-sanitised in routes/chat.py and threaded through to the Gemini
    system-prompt builder.

    Returns:
        Tuple of (ai_response, risk_level, tool_calls)
    """
    try:
        from flask import current_app  # Force local scope to fix UnboundLocalError
        # Detect crisis level FIRST
        risk_level = detect_crisis_level(message)
        
        # Guardrail Layer 1: Immediate Crisis Blocking
        if risk_level == "crisis":
             # Use the function defined in this file (available at runtime)
             from helpers.crisis_helpers import get_crisis_response_and_resources
             crisis_data = get_crisis_response_and_resources(risk_level)
             crisis_msg = crisis_data.get("crisis_msg", "Please seek help immediately.")
             
             _log_conversation(session_id, message, f"BLOCKED_CRISIS: {crisis_msg}", risk_level)
             # Return early with crisis message and no tool calls
             return crisis_msg, risk_level, []

        # Check if we should use function calling (Gemini only, non-crisis)
        ai_provider = os.environ.get("AI_PROVIDER", "gemini").lower()
        use_function_calling = (
            ai_provider == "gemini"
            and risk_level != "crisis"
            and os.environ.get("ENABLE_FUNCTION_CALLING", "true").lower() == "true"
        )



        tool_calls = []
        layer2_blocked = False

        if use_function_calling:
            # Use function calling enabled response
            from providers.gemini import get_gemini_response_with_tools

            ai_response, tool_calls = get_gemini_response_with_tools(
                message,
                session_id,
                risk_level,
                is_first_message=is_first_message,
                user_nickname=user_nickname,
                user_pronoun=user_pronoun,
                user_tone=user_tone,
                user_greeting_style=user_greeting_style,
            )

            # Guardrail Layer 2: Output Safety Verification (sync, tight timeout).
            # Sync is required so unsafe output never reaches the user; the
            # outer SAFETY_TIMEOUT_SECONDS bound + fail-open keep latency capped.
            ai_response, layer2_blocked = _apply_layer_2_safety(
                message, ai_response, session_id, risk_level
            )

            # KEYWORD FALLBACK: If Gemini didn't call function but should have
            # This ensures wellness interventions ALWAYS trigger when needed.
            # Skip when Layer 2 blocked — injecting a wellness tool result on top
            # of a safety block would surface ambiguous UI.
            #
            # 2026-05-21 audit fix — also skip when the message reads as a VENT
            # (social/relational complaint) rather than an internal-feeling
            # disclosure. The audit caught "today was the worst, my friend
            # ghosted me again" getting a canned 4-7-8 breathing offer because
            # the LLM didn't tool-call and the fallback fired on weak signals.
            # Vents need listening, not an intervention.
            VENT_MARKERS = (
                "ghost", "ghosted", "ghosting",
                "my friend", "my mom", "my dad", "my parent", "my partner",
                "my boyfriend", "my girlfriend", "my brother", "my sister",
                "my roommate", "my boss", "my teacher", "they told me",
                "they said", "told me to", "argued with", "fought with",
                "fight with", "fights with",
            )
            looks_like_vent = any(m in message.lower() for m in VENT_MARKERS)
            if not layer2_blocked and not tool_calls and not looks_like_vent:
                msg_lower = message.lower()
                
                # Detect wellness issues
                issue = None
                intensity = "moderate"  # Default
                
                # Check for severity indicators
                if any(word in msg_lower for word in ["very", "really", "so", "extremely", "severe"]):
                    intensity = "severe"
                elif any(word in msg_lower for word in ["little", "bit", "slightly", "mild"]):
                    intensity = "mild"
                
                # Detect issue type
                if any(word in msg_lower for word in ["anxious", "anxiety", "nervous", "worried", "panic"]):
                    issue = "anxiety"
                elif any(word in msg_lower for word in ["stressed", "stress", "overwhelmed", "pressure"]):
                    issue = "stress"  
                elif any(word in msg_lower for word in ["sad", "depressed", "down", "lonely", "hopeless"]):
                    issue = "sadness"
                elif any(word in msg_lower for word in ["tired", "exhausted", "sleep", "insomnia", "can't sleep"]):
                    issue = "sleep"
                
                # If we detected an issue, manually inject the tool call
                if issue:
                    from providers.agent_tools import execute_tool
                    # Removed shadowing import

                    result = execute_tool(
                        "get_wellness_intervention",
                        {"issue": issue, "intensity": intensity},
                        session_id
                    )
                    tool_calls = [{
                        "name": "get_wellness_intervention",
                        "args": {"issue": issue, "intensity": intensity},
                        "result": result,
                        "source": "keyword_fallback"  # Track that this was fallback, not Gemini
                    }]
                    current_app.logger.info(f"💡 Keyword fallback triggered: {issue}/{intensity}")
        else:
            # Regular response with failover
            ai_response, _used_provider = _get_ai_response_with_failover(
                message, session_id, risk_level
            )

            # Guardrail Layer 2: Output Safety Verification (sync, tight timeout)
            ai_response, layer2_blocked = _apply_layer_2_safety(
                message, ai_response, session_id, risk_level
            )

        # Log conversation (helper already wrote a BLOCKED_UNSAFE audit row if it blocked)
        if not layer2_blocked:
            _log_conversation(session_id, message, ai_response, risk_level)

        # Log tool calls for audit (if any)
        if tool_calls:
            _log_tool_calls(session_id, tool_calls)

        # Store memory for long-term context (non-blocking)
        try:
            from providers.memory import (
                MEMORY_ENABLED,
                summarize_interaction_llm,
            )

            if MEMORY_ENABLED:
                # Run memory extraction in background thread with app context
                def _async_mem_worker(app_ctx, sess_id, u_msg, a_resp):
                    with app_ctx.app_context():
                        summarize_interaction_llm(sess_id, u_msg, a_resp)

                threading.Thread(
                    target=_async_mem_worker,
                    args=(current_app._get_current_object(), session_id, message, ai_response)
                ).start()
        except Exception:
            pass  # Non-critical, continue if memory fails

        return ai_response, risk_level, tool_calls

    except Exception as e:
        # Use current_app for logging in request context
        from flask import current_app

        current_app.logger.error(f"Message processing error: {e}")
        return (
            "I'm having trouble processing your message right now. Please try again.",
            "low",
            [],
        )



# ── Logging helpers ──────────────────────────────────────────────

def _log_tool_calls(session_id: str, tool_calls: List[Dict]) -> None:
    """Log tool calls for audit purposes."""
    try:
        from flask import current_app

        for tc in tool_calls:
            current_app.logger.info(
                f"tool_call session={session_id} name={tc.get('name')} "
                f"success={tc.get('result', {}).get('success', False)}"
            )
    except Exception as exc:
        logging.warning(f"Tool call logging failed: {exc}")


def _log_conversation(
    session_id: str, user_message: str, ai_response: str, risk_level: str
) -> None:
    """Log conversation to database using Message table"""
    try:
        from flask import current_app

        # 1. Save User Message
        user_msg_entry = Message(
            session_id=session_id,
            content=user_message,
            is_user=True,
            risk_level=risk_level, # Log risk with user message too? Or just generic.
            timestamp=datetime.utcnow()
        )
        db.session.add(user_msg_entry)

        # 2. Save AI Response
        ai_msg_entry = Message(
            session_id=session_id,
            content=ai_response,
            is_user=False,
            risk_level=risk_level,
            timestamp=datetime.utcnow()
        )
        db.session.add(ai_msg_entry)
        
        db.session.commit()

        # Trigger Counselor Alert for High/Crisis risks
        # AlertManager handles deduplication
        if risk_level in ["high", "crisis"]:
             AlertManager.create_alert(
                session_id=session_id,
                trigger_message=user_message,
                risk_level=risk_level,
                risk_score=1.0 if risk_level == "crisis" else 0.8,
                keywords=["chat_risk_detected"]
            )

    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Failed to log conversation: {e}")


def _convert_risk_level_to_score(risk_level: str) -> float:
    """Convert risk level string to numeric score"""
    risk_mapping = {"low": 0.0, "medium": 0.5, "high": 0.8, "crisis": 1.0}
    return risk_mapping.get(risk_level.lower(), 0.0)



# ── Fallback HTML ────────────────────────────────────────────────

def _get_fallback_html(app: Flask) -> str:
    """Generate fallback HTML page with environment info"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>GentleQuest – AI Mental Health Assistant</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .api-link {{ display: block; margin: 10px 0; padding: 10px; background: #f0f0f0; text-decoration: none; color: #333; }}
            .api-link:hover {{ background: #e0e0e0; }}
            .env-info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>AI Mental Health Assistant</h1>
            <div class="env-info">
                <h3>Environment Information</h3>
                <p><strong>Environment:</strong> {app.config.get('ENVIRONMENT')}</p>
                <p><strong>Platform:</strong> {_detect_platform()}</p>
                <p><strong>Port:</strong> {app.config.get('PORT')}</p>
                <p><strong>Static Folder:</strong> {app.static_folder}</p>
                <p><strong>Static Folder Exists:</strong> {os.path.exists(app.static_folder)}</p>
                <p><strong>Index.html Exists:</strong> {os.path.exists(os.path.join(app.static_folder, 'index.html'))}</p>
            </div>
            <p>The Flutter web app is not available. Here are the API endpoints:</p>
            <a href="/api/health" class="api-link">Health Check</a>
            <a href="/api/deploy-test" class="api-link">Deploy Test</a>
            <a href="/api/enterprise/metrics" class="api-link">Metrics</a>
        </div>
    </body>
    </html>
    """



# ── AI provider failover chain ───────────────────────────────────

def _is_failure_response(text: str) -> bool:
    """Heuristic to detect unusable provider responses."""
    if not text:
        return True
    t = str(text).strip().lower()
    if not t:
        return True
    markers = (
        "configuration error:",
        "error generating response:",
        "i'm having trouble connecting to my ai services",
    )
    return any(m in t for m in markers)


def _is_quota_or_rate_limit_error(text: str) -> bool:
    """Detect when a provider error clearly indicates quota / rate limits.

    This inspects the final error text from a provider chain, so it matches both
    raw provider messages and wrapped forms like "Error generating response: ...".
    """
    if not text:
        return False
    t = str(text).strip().lower()
    if not t:
        return False
    tokens = (
        "quota exceeded",
        "quota",
        "rate limit",
        "ratelimit",
        "resource_exhausted",
        "resource exhausted",
        "429",
        "limit: 0",
    )
    return any(tok in t for tok in tokens)


def _parse_csv_env(val: str) -> List[str]:
    try:
        return [p.strip() for p in (val or "").split(",") if p.strip()]
    except Exception:
        return []


def _provider_keys_available() -> Dict[str, bool]:
    """Infer provider availability from environment variables."""
    import os as _os

    gem_keys = _parse_csv_env(_os.getenv("GEMINI_API_KEY") or "") + _parse_csv_env(
        _os.getenv("GEMINI_API_KEYS") or ""
    )
    has_gemini = len(gem_keys) > 0
    has_openai = bool((_os.getenv("OPENAI_API_KEY") or "").strip())
    has_pplx = bool(
        ((_os.getenv("PERPLEXITY_API_KEY") or _os.getenv("PPLX_API_KEY") or "").strip())
    )
    return {"gemini": has_gemini, "openai": has_openai, "perplexity": has_pplx}


def _build_failover_chain() -> List[str]:
    """Prefer configured provider if available, then gemini -> openai -> perplexity."""
    from flask import current_app

    available = _provider_keys_available()
    configured = str(current_app.config.get("AI_PROVIDER", "gemini")).lower()
    default_order = ["gemini", "openai", "perplexity"]
    chain: List[str] = []
    if available.get(configured):
        chain.append(configured)
    for p in default_order:
        if available.get(p) and p not in chain:
            chain.append(p)
    return chain or ["gemini"]


def _call_provider(
    provider: str, message: str, session_id: str, risk_level: str
) -> str:
    """Call providers with correct signatures and minimal side effects."""
    import os as _os

    from providers.gemini import get_gemini_response
    from providers.openai import get_openai_response
    from providers.perplexity import get_perplexity_response

    if provider == "gemini":
        return get_gemini_response(
            message, session_id=session_id, risk_level=risk_level
        )
    elif provider == "openai":
        return get_openai_response(message)
    elif provider == "perplexity":
        # Support alias if only PPLX_API_KEY is present at runtime
        if not (_os.getenv("PERPLEXITY_API_KEY") or "").strip():
            alt = (_os.getenv("PPLX_API_KEY") or "").strip()
            if alt:
                _os.environ["PERPLEXITY_API_KEY"] = alt
        return get_perplexity_response(message)
    else:
        return get_gemini_response(
            message, session_id=session_id, risk_level=risk_level
        )


def _get_ai_response_with_failover(
    message: str, session_id: str, risk_level: str
) -> Tuple[str, str]:
    """Try providers in order until a viable response is obtained. Returns (text, used_provider)."""
    chain = _build_failover_chain()
    last_err_text = None
    for prov in chain:
        try:
            resp = _call_provider(prov, message, session_id, risk_level)
            if not _is_failure_response(resp):
                return resp, prov
            last_err_text = resp
        except Exception as _e:
            last_err_text = f"Error generating response: {_e}"
            continue

    # All providers failed. If the last error clearly looks like a quota or
    # rate-limit issue (for example Gemini free-tier 429s), surface a
    # user-friendly "daily limit" style message instead of a vague failure.
    fallback = last_err_text
    if _is_quota_or_rate_limit_error(last_err_text or ""):
        fallback = "Today's AI chat limit has been reached. Please try again tomorrow."
    return (
        fallback
        or "I'm having trouble connecting to my AI services. Please try again in a moment."
    ), (chain[-1] if chain else "unknown")

