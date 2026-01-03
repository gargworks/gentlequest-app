# MCP Nucleus Tool Failure Report

**Date:** 2025-12-28T06:23:16+05:30  
**Severity:** CRITICAL  
**Status:** BLOCKING COLD START TESTS

---

## Issue Summary

MCP Nucleus tools are causing blank/empty responses and preventing test execution.

## Timeline

### ✅ Initial Success (Day 0 - ~06:01 IST)
All 5 tests passed successfully:
- `brain_get_state()` ✅
- `brain_list_artifacts()` ✅
- `brain_emit_event()` ✅
- `brain_write_artifact()` ✅
- `brain_get_triggers()` ✅

### ❌ Subsequent Failures (~06:06 IST onwards)

**Attempt 1:** User asked "what's focus today"
- Tried to call `brain_get_state()`
- Result: Blank response, agent execution terminated

**Attempt 2:** User asked "what can we do to gentlequest"
- Tried to call `brain_get_state()`
- Result: Blank response, agent execution terminated

**Attempt 3:** Cold start test attempt (~06:23 IST)
- Tried to call `brain_get_state()`
- Result: Multiple consecutive "model output must contain either output text or tool calls" errors
- 10+ consecutive failures

## Error Pattern

```
Error: model output must contain either output text or tool calls, 
these cannot both be empty, please try again
```

This error repeated 10+ times in a row when attempting to call MCP tools.

## Configuration Context

**MCP Config Change:**
Between successful Day 0 tests and failures, the brain path was changed:
- **Original:** `/Users/lokeshgarg/ai-mvp-backend/.brain` (worked)
- **New:** `/Users/lokeshgarg/dogfood-brain/.brain` (failing)

**MCP Server Config:**
```json
"nucleus": {
  "command": "python3.11",
  "args": ["-m", "mcp_server_nucleus"],
  "env": {
    "NUCLEAR_BRAIN_PATH": "/Users/lokeshgarg/dogfood-brain/.brain"
  }
}
```

## Hypotheses

### Hypothesis 1: Server Restart Required
MCP server may need restart after `NUCLEAR_BRAIN_PATH` environment variable change.

### Hypothesis 2: Empty Brain Initialization Issue
The new brain path `/Users/lokeshgarg/dogfood-brain/.brain` may not exist or may need initialization.

### Hypothesis 3: MCP State Corruption
Some internal MCP state may have become corrupted after initial successful use.

### Hypothesis 4: Model/Tool Interaction Bug
There may be a bug in how the AI model interacts with MCP tools after the first successful session.

## Workaround Used

Switched to direct file access:
```python
view_file("/Users/lokeshgarg/ai-mvp-backend/.brain/ledger/state.json")
```

This worked and allowed reading brain state without MCP tools.

## Impact Assessment

**Severity:** HIGH
- Blocks cold start testing
- Prevents dogfooding of actual MCP functionality
- Reduces confidence in MCP reliability

**User Experience:**
- Frustrating blank responses
- Multiple retry attempts needed
- Had to resort to workarounds

## Recommended Actions

1. **Immediate:** Restart MCP server connection
2. **Verify:** Check if `/Users/lokeshgarg/dogfood-brain/.brain` exists
3. **Test:** Try MCP tools with original brain path to isolate issue
4. **Debug:** Add logging to MCP server to capture failure details
5. **Document:** Add this failure to dogfood_log.md as Day 0 addendum

## Dogfooding Value

**This is exactly why we dogfood!** 🎯

Found critical reliability issue:
- Tools work once, then fail
- No clear error messages
- Silent failures with blank responses
- Configuration changes may not take effect without restart

This would be a terrible user experience for real customers.

---

**Next Steps:** Need to diagnose root cause before proceeding with cold start tests.
