
# Walkthrough: Nucleus Agent Runtime v2 (Context Factory)

> **Date:** 2026-01-11
> **Status:** ✅ Completed
> **Target:** `mcp-server-nucleus`

## 🎯 Goal
Upgrade the Nucleus Agent Runtime (NAR) with **Dynamic Context Injection** (RAG-lite).
This enables agents to automatically access relevant project documentation based on the user's intent, without requiring massive static prompts.

## 🛠 Changes Implemented

### 1. Context Rules Schema (`context_rules.json`)
- Defined a JSON schema mapping **Keywords** to **File Paths**.
- Initial Rules:
  - `deploy`, `cloud run` -> `cloudbuild.yaml`, `DEPLOYMENT.md`
  - `database`, `schema` -> `DATABASE_SCHEMA.md`
  - `api`, `endpoint` -> `OPENAPI_SPEC.md`

### 2. Context Factory Upgrade (`factory.py`)
- Implemented `_resolve_dynamic_context(intent)`.
- **Logic:**
  1. Scans `context_rules.json`.
  2. Matches intent keywords.
  3. Reads file contents (with 10k char limit).
  4. Injects into System Prompt under `# DYNAMIC CONTEXT INJECTION`.

## ✅ Verification
- **Test Script**: `tests/test_context_injection.py` (Created & Passed).
- **Results**:
  - `deploy` intent -> Injected proper `cloudbuild.yaml` context.
  - `hello` intent -> Clean prompt (no noise).

## 🚀 Impact
- **Smarter Agents**: They know the infrastructure without being told.
- **Cheaper Calls**: We don't load the entire wiki every time.
- **Maintainable**: Just update `context_rules.json` to teach the AI new tricks.
