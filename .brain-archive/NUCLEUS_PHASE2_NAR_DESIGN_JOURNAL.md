
# Design Journal: Nucleus Agent Runtime (NAR) Upgrade (Phase 2)

> **Date:** 2026-01-11
> **Focus:** Context Factory v2 & Dynamic RAG

## 🧠 The Problem
Currently, `ContextFactory` loads a static System Prompt for each persona.
- If I ask the `Architect` to "Review the database schema", it has to *ask me* where the schema is, or I have to paste it.
- **Vision:** The Factory should *detect* "Database" intent and *inject* `docs/schema.md` automatically.

## 🏗 The Solution: Dynamic Context Injection
We will upgrade `factory.py` to support **Context Rules**.

### 1. The Context Manifest
Define `context_rules.json` (or inside `factory.py` for now):
```json
{
  "keywords": ["database", "schema", "sql"],
  "inject": ["docs/architecture/DATABASE_SCHEMA.md"]
},
{
  "keywords": ["deploy", "cloud run", "build"],
  "inject": ["cloudbuild.yaml", "docs/infra/DEPLOYMENT.md"]
}
```

### 2. Factory Upgrade
Update `create_context` loop:
1. **Classify Intent** (Existing).
2. **Scan Knowledge Rules**: Check message against keywords.
3. **Load Content**: Read valid paths found in rules.
4. **Inject**: Append to System Prompt under `## Dynamic Context`.

### 3. Benefits
- **Zero-Shot Accuracy**: Agent knows the schema before speaking.
- **Token Efficiency**: Only load relevant docs, not the whole wiki.
- **Consistency**: Always sees the latest `cloudbuild.yaml` when asked about deploy.

## 🛠 Implementation Plan
1. **Define Schema**: Add `CONTEXT_RULES` constant to `factory.py`.
2. **Implement `_resolve_dynamic_context(message)`**: Returns string of injected content.
3. **Update `create_context`**: Call resolver and append to prompt.
4. **Verify**: Test with a "deploy" query and check if `cloudbuild.yaml` is present in the prompt.
