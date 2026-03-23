import os
import re
import random
import threading
import time
import hashlib
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta

# Store conversations with timestamp for cleanup
conversations: Dict[str, List[dict]] = {}
CONVERSATION_TIMEOUT = timedelta(hours=1)  # Clear conversations older than 1 hour

# ============================================================================
# AGENTIC WELLNESS TOOLS (Smart, Context-Aware)
# ============================================================================

WELLNESS_TOOLS_CONFIG = {
    "function_declarations": [
        {
            "name": "get_wellness_intervention",
            "description": "Get a wellness exercise. MUST be called when user mentions anxiety, stress, panic, sleep issues, sadness, or feeling overwhelmed.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "issue": {
                        "type": "STRING",
                        "description": "The issue: anxiety, stress, panic, sleep, sadness, overwhelmed, or fatigue",
                        "enum": [
                            "anxiety",
                            "stress",
                            "panic",
                            "sleep",
                            "sadness",
                            "overwhelmed",
                            "fatigue",
                        ],
                    },
                    "intensity": {
                        "type": "STRING",
                        "description": "Severity: mild, moderate, or severe",
                        "enum": ["mild", "moderate", "severe"],
                    },
                },
                "required": ["issue", "intensity"],
            },
        },
        {
            "name": "record_interaction_outcome",
            "description": "Record the outcome of a wellness intervention to help Alex learn what works for this user. Call this when the user completes an exercise or provides feedback.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "intervention_id": {
                        "type": "STRING",
                        "description": "ID of the intervention",
                    },
                    "completed": {
                        "type": "BOOLEAN",
                        "description": "Whether user completed it",
                    },
                    "effectiveness_rating": {
                        "type": "NUMBER",
                        "description": "Effectiveness 0.0-1.0",
                    },
                    "user_feedback": {
                        "type": "STRING",
                        "description": "User feedback",
                    },
                },
                "required": ["intervention_id", "completed"],
            },
        },
    ]
}


# Flag to enable/disable function calling (for gradual rollout)
FUNCTION_CALLING_ENABLED = (
    os.getenv("ENABLE_FUNCTION_CALLING", "true").lower() == "true"
)

# ---------- Gemini multi-key + resilience helpers (single-file, surgical) ----------


# Parse keys from env with minimal churn: support CSV in GEMINI_API_KEY and alias GEMINI_API_KEYS
def _parse_api_keys() -> List[str]:
    keys: List[str] = []
    raw_primary = os.getenv("GEMINI_API_KEY") or ""
    raw_alias = os.getenv("GEMINI_API_KEYS") or ""
    # CSV support in both vars
    parts: List[str] = []
    parts += [p.strip() for p in raw_primary.split(",") if p.strip()]
    parts += [p.strip() for p in raw_alias.split(",") if p.strip()]
    # De-duplicate while preserving order
    seen = set()
    for k in parts:
        if k not in seen:
            seen.add(k)
            keys.append(k)
    return keys


_GEMINI_KEYS: List[str] = _parse_api_keys()

# Round-robin pointer
_key_lock = threading.Lock()
_key_index = 0

# ── Model cache: reuse GenerativeModel across requests (OPT-2) ──
# Keyed by (key_index, model_name). Falls back to fresh creation on any error.
import google.generativeai as genai

_model_cache: Dict[Tuple[int, str], Any] = {}
_configured_key_idx: Optional[int] = None

def _get_cached_model(key_idx: int, model_name: str, system_prompt: str,
                      tools=None):
    """Return a cached GenerativeModel, or create + cache a new one."""
    global _configured_key_idx
    cache_key = (key_idx, model_name)

    # Re-configure SDK only when the key actually changes
    if _configured_key_idx != key_idx:
        genai.configure(api_key=_GEMINI_KEYS[key_idx])
        _configured_key_idx = key_idx
        _model_cache.clear()  # keys changed — stale models

    if cache_key not in _model_cache:
        kwargs = {"model_name": model_name, "system_instruction": system_prompt}
        if tools:
            kwargs["tools"] = tools
        _model_cache[cache_key] = genai.GenerativeModel(**kwargs)

    return _model_cache[cache_key]


def _next_key_index() -> int:
    global _key_index
    with _key_lock:
        idx = _key_index
        if _GEMINI_KEYS:
            _key_index = (_key_index + 1) % len(_GEMINI_KEYS)
        return idx


# In-memory blocklist to skip exhausted keys for a while
_BLOCK_TTL_HOURS = 6
_blocked_until: Dict[int, datetime] = {}

# Last-good model per key for snappier first token
_last_good_model: Dict[int, str] = {}


def _debug_enabled() -> bool:
    return (os.getenv("AI_DEBUG_LOGS") or "").lower() == "true"


def _debug(*args):
    if _debug_enabled():
        print("[gemini]", *args)


def _should_rotate_key(err: Exception) -> bool:
    """Rotate only on quota/auth/rate-limit/permission errors."""
    msg = ""
    try:
        msg = (str(err) or "").lower()
    except Exception:
        pass
    if any(
        tok in msg
        for tok in (
            "quota",
            "rate limit",
            "ratelimit",
            "permission",
            "unauthorized",
            "forbidden",
            "api key",
            "key invalid",
            "invalid key",
            "exceeded",
        )
    ):
        return True
    status = getattr(err, "status", None) or getattr(err, "code", None)
    if status in (401, 403, 429):
        return True
    # Explicit string 429
    if "429" in msg:
        return True
    return False


def cleanup_old_conversations():
    """Remove conversations that are older than the timeout"""
    current_time = datetime.now()
    to_remove = []
    for session_id in conversations:
        if conversations[session_id]:
            last_message_time = conversations[session_id][-1].get("timestamp")
            if (
                last_message_time
                and current_time - last_message_time > CONVERSATION_TIMEOUT
            ):
                to_remove.append(session_id)

    for session_id in to_remove:
        del conversations[session_id]


def get_gemini_response(
    message, mode="mental_health", session_id=None, risk_level=None
):
    """Get response from Gemini API with conversation history, with model-first fallback and smart multi-key rotation."""
    try:
        if not _GEMINI_KEYS:
            print("Gemini API key not found")
            return "Configuration error: Gemini API key not found"

        # Initialize or get conversation history
        if session_id not in conversations:
            conversations[session_id] = []

        # Clean up old conversations periodically
        cleanup_old_conversations()

        # For crisis-related messages, clear history to avoid AI learning crisis resources
        crisis_keywords = [
            "die",
            "suicide",
            "kill myself",
            "end my life",
            "take my life",
            "want to die",
        ]
        is_crisis_message = any(
            keyword in (message or "").lower() for keyword in crisis_keywords
        )

        if is_crisis_message:
            history = []
            conversations[session_id] = []
        else:
            history = conversations[session_id]

        # Prepare the prompt with context based on risk level
        if risk_level == "crisis":
            system_message = """You are Alex, a wellness AI companion for high school students.
            The user is in crisis and needs immediate emotional support.
            Respond with empathy, understanding, and emotional support ONLY.
            Do NOT mention any crisis resources, helpline numbers, or specific actions.
            Focus on emotional support and being present with the user.
            Crisis resources will be provided separately by the system."""
        else:
            system_message = """You are Alex, a wellness AI companion for high school students.
            Your personality: warm, genuine, never clinical. You talk like a caring older sibling.
            Keep responses short (2-4 sentences). Ask follow-up questions to show you care.
            If the user seems distressed, provide emotional support and suggest healthy coping strategies.

            ABSOLUTE RULE: You must NEVER mention any crisis helpline numbers, phone numbers, or specific resources.
            Examples of what NOT to mention: 988, 111, 741741, "National Suicide Prevention Lifeline", "Crisis Text Line", etc.
            Crisis resources will be provided separately by the system.
            Focus ONLY on emotional support, understanding, and general guidance.
            If you mention any crisis resources, you are violating this rule."""

        # Build the conversation context
        conversation_context = ""
        if history:
            conversation_context = "\n".join(
                [
                    f"{'User' if msg['is_user'] else 'Assistant'}: {msg['content']}"
                    for msg in history[-5:]
                ]
            )
            conversation_context = f"\nPrevious conversation:\n{conversation_context}\n"

        prompt = f"{system_message}\n{conversation_context}\nUser: {message}"

        # Model fallback order (best first) - use broadly compatible identifiers
        # Prefer newer 2.5 flash models, then 2.0, then stable 1.5 variants, then older names
        default_models = [
            "gemini-3.1-flash-lite-preview",  # 500 RPD free tier
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
        ]

        # Outer loop over keys with hierarchal fallback (Primary -> Backup 1 -> Backup 2...)
        # User requested "first key is always default" (Ephemeral Backup Strategy)
        start_idx = 0 
        last_error = None
        
        # Exponential backoff multiplier
        backoff_delay = 1.0

        for k_off in range(len(_GEMINI_KEYS)):
            key_idx = (start_idx + k_off) % len(_GEMINI_KEYS)

            # Skip blocked keys within TTL window (Resilience)
            until = _blocked_until.get(key_idx)
            if until and datetime.now() < until:
                _debug(f"skip_blocked key_index={key_idx} until={until}")
                continue

            api_key = _GEMINI_KEYS[key_idx]
            try:
                # _debug(f"using_key_index={key_idx}")

                # Build model order, trying last-good first if present
                models_order = list(default_models)
                if key_idx in _last_good_model:
                    lgm = _last_good_model[key_idx]
                    if lgm in models_order:
                        models_order = [lgm] + [m for m in models_order if m != lgm]

                for model_name in models_order:
                    try:
                        # Try Nucleus DualEngineLLM first, fallback to native google.generativeai
                        response = None
                        try:
                            from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
                            llm = DualEngineLLM(model_name, api_key=api_key)
                            response = llm.generate_content(prompt)
                        except ImportError:
                            # Fallback to native google.generativeai when mcp_server_nucleus unavailable
                            import google.generativeai as genai
                            genai.configure(api_key=api_key)
                            model = genai.GenerativeModel(model_name)
                            response = model.generate_content(prompt)
                        
                        if not response or not getattr(response, "text", None):
                            _debug(f"empty_response model={model_name}")
                            last_error = ValueError("empty response")
                            # Try next model within same key
                            continue

                        # Build cleaned response
                        if risk_level == "crisis":
                            cleaned_response = """I hear how much pain you're in, and it takes incredible strength to express these feelings. Please know that you're not alone, and there are people who want to help you through this difficult time.

Your feelings are valid, and it's okay to not be okay. You don't have to carry this burden alone. There are people who care about you and want to support you.

Please remember that these intense feelings can pass, and there is hope for things to get better. You deserve support and care."""
                        else:
                            cleaned_response = response.text

                        # Clean up formatting
                        cleaned_response = re.sub(
                            r"\n\s*\n\s*\n", "\n\n", cleaned_response
                        ).strip()

                        # Store conversation
                        history.append(
                            {
                                "content": message,
                                "is_user": True,
                                "timestamp": datetime.now(),
                            }
                        )
                        history.append(
                            {
                                "content": cleaned_response,
                                "is_user": False,
                                "timestamp": datetime.now(),
                            }
                        )
                        conversations[session_id] = history

                        # Update last-good model for this key
                        _last_good_model[key_idx] = model_name

                        return cleaned_response
                    except Exception as e_model:
                        rotate = _should_rotate_key(e_model)
                        _debug(
                            f"model_error model={model_name} rotate={rotate} err={e_model}"
                        )
                        last_error = e_model
                        if rotate:
                            # Block this key for TTL and rotate to next key
                            _blocked_until[key_idx] = datetime.now() + timedelta(
                                hours=_BLOCK_TTL_HOURS
                            )
                            _debug(
                                f"block_key key_index={key_idx} ttl_hours={_BLOCK_TTL_HOURS}"
                            )
                            # Exponential Backoff Sleep before next key attempt
                            time.sleep(backoff_delay)
                            backoff_delay *= 2  # Double the wait for next attempt
                            break
                        # else: try next model under same key
                        continue

            except Exception as e_key:
                # Configuration or immediate key-scope errors
                rotate = _should_rotate_key(e_key)
                _debug(
                    f"key_scope_error key_index={key_idx} rotate={rotate} err={e_key}"
                )
                last_error = e_key
                if rotate:
                    _blocked_until[key_idx] = datetime.now() + timedelta(
                        hours=_BLOCK_TTL_HOURS
                    )
                    _debug(
                        f"block_key key_index={key_idx} ttl_hours={_BLOCK_TTL_HOURS}"
                    )
                    # Exponential Backoff Sleep before next key attempt
                    time.sleep(backoff_delay)
                    backoff_delay *= 2

            # Small jitter when rotating keys to avoid synchronized spikes
            time.sleep(random.uniform(0.05, 0.2))

        # If all keys/models failed
        if last_error:
            return "I'm having trouble connecting to my AI services. Please try again in a moment."
        return "I'm having trouble connecting to my AI services. Please try again in a moment."

    except Exception as e:
        print(f"Unexpected Gemini API error: {str(e)}")
        return "I'm having trouble connecting to my AI services. Please try again in a moment."


# ============================================================================
# FUNCTION CALLING RESPONSE HANDLER
# ============================================================================


def get_gemini_response_with_tools(
    message: str, session_id: str, risk_level: str = "low", mode: str = "mental_health",
    is_first_message: bool = False,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Get response from Gemini with function calling enabled.

    Returns:
        Tuple of (response_text, list_of_tool_calls_executed)

    Note:
        - Crisis mode BYPASSES function calling for safety
        - Each tool call is logged for audit purposes
    """
    from providers.agent_tools import execute_tool, format_tool_result_for_response

    tool_calls_executed = []

    # GUARDRAIL: Crisis mode bypasses function calling entirely
    if risk_level == "crisis":
        _debug("crisis_mode: bypassing function calling")
        response = get_gemini_response(message, mode, session_id, risk_level)
        return response, []

    # If function calling is disabled, fall back to regular response
    if not FUNCTION_CALLING_ENABLED:
        response = get_gemini_response(message, mode, session_id, risk_level)
        return response, []

    try:
        if not _GEMINI_KEYS:
            return "Configuration error: Gemini API key not found", []

        # Build system prompt with tool awareness
        _first_message_preamble = ""
        if is_first_message:
            _first_message_preamble = """IMPORTANT — THIS IS THE USER'S VERY FIRST MESSAGE. They just installed the app and are trying it for the first time.
Be warm, personal, and inviting. Make them feel safe and welcome.
Start with something like: "Hey, I'm Alex — I'm really glad you're here. This is a safe space just for you. What's on your mind today?"
Keep it short (2-3 sentences max). Don't lecture. Don't list features. Just be human and present.
Make them want to come back tomorrow.

"""

        system_prompt = f"""{_first_message_preamble}You are Alex, a wellness AI companion for high school students.
Your personality: warm, genuine, never clinical. You talk like a caring older sibling — not a therapist, not a chatbot.
Keep responses short (2-4 sentences unless they need more). Ask follow-up questions to show you care.
Remember: they chose to open this app. That took courage. Honor that.

CRITICAL FUNCTION CALLING RULES - FOLLOW EXACTLY:

1. When user mentions anxiety/stressed/panic/overwhelmed/nervous:
   → IMMEDIATELY call get_wellness_intervention(issue="anxiety", intensity=...)
   → DO NOT just respond with text about breathing

2. When user mentions sadness/depressed/down/lonely:
   → IMMEDIATELY call get_wellness_intervention(issue="sadness", intensity=...)

3. When user mentions sleep/tired/can't sleep/insomnia:
   → IMMEDIATELY call get_wellness_intervention(issue="sleep", intensity=...)

INTENSITY GUIDE:
- "very", "really", "so", "extremely" = "severe"
- "feeling", "bit", "somewhat" = "moderate"
- "slightly", "little" = "mild"

EXAMPLE CORRECT BEHAVIOR:
User: "I'm feeling very anxious"
YOU: Call get_wellness_intervention(issue="anxiety", intensity="severe")
     Then add: "I hear you — that sounds really tough. Let's try something together that might help."

EXAMPLE WRONG BEHAVIOR:
User: "I'm stressed"
YOU: Just responding with "Try taking deep breaths..." ❌ WRONG!
     You MUST call the function FIRST!

After calling the function, be empathetic and warm. But CALL THE FUNCTION FIRST.

Available tools:
- get_wellness_intervention(issue, intensity) - Use this when user needs help
- record_interaction_outcome() - Use when they complete an exercise

DO NOT mention crisis hotlines - system handles that separately."""

        import time as _time
        _perf = {}
        _pt0 = _time.monotonic()

        # Get memory context (if available)
        memory_context = ""
        try:
            from providers.memory import get_memory_context_for_prompt, MEMORY_ENABLED

            if MEMORY_ENABLED:
                memory_context = get_memory_context_for_prompt(session_id, message)
                if memory_context:
                    memory_context = f"\n{memory_context}\n"
        except Exception as e:
            _debug(f"memory_context_error: {e}")
            # Rollback transaction to prevent cascade failures
            try:
                from models import db
                db.session.rollback()
            except:
                pass
        _pt1 = _time.monotonic()
        _perf["memory_ms"] = round((_pt1 - _pt0) * 1000)

        # Get conversation history from database (more reliable than in-memory)
        db_history = ""
        try:
            from providers.session_memory import get_recent_messages, format_history_for_prompt
            recent = get_recent_messages(session_id, limit=3)
            if recent:
                db_history = format_history_for_prompt(recent)
        except Exception as e:
            _debug(f"db_history_error: {e}")
        _pt2 = _time.monotonic()
        _perf["db_history_ms"] = round((_pt2 - _pt1) * 1000)

        # Minimal agentic context
        context_parts = []
        if memory_context:
            context_parts.append(memory_context)
        if db_history:
            context_parts.append(db_history)

        # Conversation count for relationship depth
        try:
            from models import db, UserSession
            _sess = db.session.get(UserSession, session_id)
            _conv_count = (_sess.conversation_count or 0) if _sess else 0
            if _conv_count > 1:
                context_parts.append(f"This is conversation #{_conv_count} with this user. Acknowledge the relationship naturally — you know each other.")
        except Exception:
            pass

        # Recent mood data for personalized responses
        try:
            from models import db, MoodEntry
            _recent_moods = db.session.query(MoodEntry).filter_by(
                session_id=session_id
            ).order_by(MoodEntry.timestamp.desc()).limit(3).all()
            if _recent_moods:
                _mood_lines = [f"level {m.mood_level}/5{' — ' + m.note if m.note else ''}" for m in _recent_moods]
                context_parts.append(f"User's recent mood logs (newest first): {'; '.join(_mood_lines)}. Weave this awareness into your response naturally.")
        except Exception:
            pass
        
        # Build prompt with minimal context
        if context_parts:
            full_prompt = f"{chr(10).join(context_parts)}{chr(10)}User: {message}"
        else:
            full_prompt = message

        # Configure API and create model with tools
        key_idx = 0
        if len(_GEMINI_KEYS) > 1 and session_id:
            try:
                hval = int(hashlib.sha256(session_id.encode("utf-8")).hexdigest(), 16)
                key_idx = hval % len(_GEMINI_KEYS)
            except Exception:
                key_idx = 0

        api_key = _GEMINI_KEYS[key_idx]
        
        # Use native SDK directly for minimal overhead (DualEngineLLM adds ~10s)
        _pt3 = _time.monotonic()
        _model_name = "gemini-3.1-flash-lite-preview"
        try:
            # OPT-2: Try cached model first (saves ~100-200ms on warm requests)
            model = _get_cached_model(key_idx, _model_name, system_prompt,
                                      tools=WELLNESS_TOOLS_CONFIG)
            response = model.generate_content(full_prompt)
        except Exception as _cache_err:
            _debug(f"Cached model failed ({_cache_err}), falling back to fresh")
            # Fallback: fresh model per-request (original behavior)
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name=_model_name,
                    tools=WELLNESS_TOOLS_CONFIG,
                    system_instruction=system_prompt
                )
                response = model.generate_content(full_prompt)
                # Evict bad cache entry so next request retries cache
                _model_cache.pop((key_idx, _model_name), None)
            except Exception as e:
                _debug(f"LLM call failed: {e}")
                # Fallback to text-only if tools fail (Safety)
                response = get_gemini_response(message, mode, session_id, risk_level)
                return response, []
        _pt4 = _time.monotonic()
        _perf["llm_ms"] = round((_pt4 - _pt3) * 1000)
        _perf["total_ms"] = round((_pt4 - _pt0) * 1000)
        _debug(f"PERF: {_perf}")
        # Stash inner timing on Flask g for endpoint to pick up
        try:
            from flask import g as _flask_g
            _flask_g._gemini_perf = _perf
        except Exception:
            pass

        if not response.candidates:
            _debug("no candidates in response")
            return get_gemini_response(message, mode, session_id, risk_level), []

        candidate = response.candidates[0]

        # Check if there are function calls
        # NEW SDK: Function calls are parts with function_call attribute
        function_calls_to_process = []
        text_parts = []

        for part in candidate.content.parts:
            # Check for function_call (native object in V1 SDK)
            if part.function_call:
                fc = part.function_call
                # Convert args to dict if not already
                # V1 SDK might return a Map or similar object, ensure it's a dict
                args = dict(fc.args) if fc.args else {}
                function_calls_to_process.append(
                    {"name": fc.name, "args": args}
                )
            elif part.text:
                text_parts.append(part.text)

        # Execute function calls (max 2 per response - guardrail)
        for fc in function_calls_to_process[:2]:
            _debug(f"executing_tool: {fc['name']} args={fc['args']}")
            result = execute_tool(fc["name"], fc["args"], session_id)

            tool_calls_executed.append(
                {
                    "name": fc["name"],
                    "args": fc["args"],
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            result_text = format_tool_result_for_response(fc["name"], result)
            if result_text:
                text_parts.append(result_text)

        # Combine all text parts
        final_response = " ".join(text_parts) if text_parts else "I'm here to listen."
        final_response = re.sub(r"\n\s*\n\s*\n", "\n\n", final_response).strip()

        return final_response, tool_calls_executed

    except Exception as e:
        _debug(f"function_calling_error: {e}")
        # Fallback to regular response on any error
        response = get_gemini_response(message, mode, session_id, risk_level)
        return response, []
