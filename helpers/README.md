# `helpers/` — GentleQuest application helpers

Extracted from the `app.py` monolith. Every module here is unit-tested in
`tests/test_helpers_*.py` (see that directory for ~128 tests).

| Module | Purpose | Key exports |
|---|---|---|
| `session_helpers.py` | Session lifecycle, conversation counts, background executor, analytics + chat-request JSONL logging. | `background_executor`, `_get_or_create_session`, `_update_session_last_active`, `_get_conversation_count`, `_increment_conversation_count`, `_log_analytics_event`, `_log_chat_request` |
| `health_helpers.py` | Health-check probes for database, Redis, Ollama; platform detection. | `_check_database_health`, `_check_redis_health`, `_check_ollama_health`, `_detect_platform` |
| `crisis_helpers.py` | Geography-specific crisis resources, keyword-weighted crisis detection, IP→country resolution, crisis event logging, LLM watchdog. | `CRISIS_RESOURCES_BY_COUNTRY`, `_enhanced_crisis_detection`, `get_country_code_from_ip`, `get_country_from_request`, `get_crisis_response_and_resources`, `_log_crisis_detection`, `_run_crisis_watchdog` |
| `chat_helpers.py` | Chat processing: LLM calls, Layer-2 safety (fail-open with timeout), conversation/tool-call logging, AI provider failover chain, fallback HTML. | `_process_chat_message`, `_call_llm_json`, `_apply_layer_2_safety`, `_log_conversation`, `_log_tool_calls`, `_get_ai_response_with_failover`, `_build_failover_chain`, `_call_provider`, `_is_failure_response`, `_is_quota_or_rate_limit_error`, `_convert_risk_level_to_score`, `_get_fallback_html`, `_safety_executor` |
| `mood_helpers.py` | Mood analytics, personalized recommendations, retention-based purge. | `_get_personalized_recommendations`, `_get_default_recommendations`, `_analyze_mood_pattern`, `_purge_old_data_inner` |

## Conventions

- **Flask context:** helpers use `current_app` for config access. Functions that
  run in background threads take an explicit `app_ctx` parameter and wrap work
  in `with app_ctx.app_context():`.
- **Local imports inside functions:** used intentionally to avoid circular
  imports with `providers/`, `routes/`, and `app.py`.
- **Fail-open / non-blocking:** analytics, watchdog, and memory-summary work
  must never block or fail a user-facing request. Exceptions are logged and
  swallowed.
- **Re-exports:** `app.py` re-imports every public symbol from these modules so
  legacy `from app import _xyz` callers keep working.

## Testing

```bash
pytest tests/test_helpers_*.py -v
```

Each module has at least ~15 tests covering happy paths, error paths, and
boundary cases. See `tests/test_helpers_mood.py` for the pattern used when a
helper needs `app.app_context()` + in-memory sqlite.
