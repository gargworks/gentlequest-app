# AI Capabilities Architecture Spec

> **Purpose:** Living technical specification for AI capabilities. Works across Antigravity, Cursor, Windsurf.  
> **Last Updated:** 2025-12-25

### Related Documents
- [AI_AGENTS_ASSESSMENT.md](./AI_AGENTS_ASSESSMENT.md) — Decision record: why we chose this approach
- [STRATEGIC_AI_CAPABILITIES_ROADMAP.md](./STRATEGIC_AI_CAPABILITIES_ROADMAP.md) — Business value & investor narrative

---

## Current Ecosystem Health

### ✅ What We Have (Foundation Ready)

| Component | Status | Location |
|-----------|--------|----------|
| **Data Models** | ✅ Healthy | `models.py` |
| **Mood Tracking** | ✅ API exists | `/api/mood_entry`, `mood_entries` table |
| **Self Assessment** | ✅ API exists | `/api/self_assessment`, `self_assessment_entries` table |
| **Conversation Logs** | ✅ Stored | `conversation_logs` table |
| **Crisis Detection** | ✅ Keyword-based | `crisis_detection.py`, `crisis_events` table |
| **Session Management** | ✅ Working | `user_sessions` table |
| **Function Calling** | ✅ **WORKING** | `providers/gemini.py`, 3/3 success |
| **Smart Tools** | ✅ Implemented | `providers/agent_tools.py` |

### ⏳ Deployed (Minimal Version)

| Feature | Status | Notes |
|---------|--------|-------|
| `get_wellness_intervention()` | ✅ Working | 3/3 success rate |
| Smart intervention selection | ✅ Working | Selects based on issue/intensity |
| Interactive exercises | ✅ Working | Breathing, grounding exercises |

### 🔄 To Be Added Incrementally

| Feature | Status | Blocker |
|---------|--------|---------|
| **System Prompt** | ❌ Removed | Complex prompts break function calling |
| **Memory Context** | ❌ Removed | Needs isolated testing |
| **Conversation History** | ❌ Removed | Needs isolated testing |
| **`record_interaction_outcome()`** | ⏳ Defined | Not yet tested |
| **pgvector/Embeddings** | ⏳ Not started | Phase II |

---

## Phase I: Function Calling
### Current Status: ✅ WORKING (Minimal Version)

### What It Enables

Luna can execute actions instead of just suggesting them:

```
User: "I'm feeling anxious"
Luna: → Calls log_mood(level=2, emotion="anxious")
      → Calls get_breathing_exercise(type="calm")
      → Returns interactive content
```

### Core Functions to Implement

| Function | Purpose | DB Table |
|----------|---------|----------|
| `log_mood(level, emotion, note)` | Auto-track moods from conversation | `mood_entries` |
| `get_breathing_exercise(type)` | Return structured breathing exercise | None (static) |
| `get_grounding_exercise()` | Return 5-4-3-2-1 grounding | None (static) |
| `get_journal_prompt(topic?)` | Return reflective prompt | None (static) |
| `get_mood_history(days?)` | Retrieve user's mood trends | `mood_entries` |
| `schedule_checkin(time)` | Schedule follow-up | NEW: `scheduled_checkins` |

### Technical Implementation

**File:** `providers/gemini.py`

> **⚠️ CRITICAL REQUIREMENTS DISCOVERED (Dec 2024):**
> 1. Schema types MUST be UPPERCASE: `OBJECT`, `STRING`, `NUMBER`, `BOOLEAN`
> 2. Do NOT use `tool_config` parameter - it breaks function calling
> 3. Keep prompts simple - complex system prompts interfere with function calls
> 4. Model: `gemini-2.5-flash` works best for agentic use cases

```python
# ✅ CORRECT: Tool declarations for Gemini (uppercase types!)
WELLNESS_TOOLS_CONFIG = {
    "function_declarations": [
        {
            "name": "get_wellness_intervention",
            "description": "Get a wellness exercise. MUST be called when user mentions anxiety, stress, panic, sleep issues, sadness, or feeling overwhelmed.",
            "parameters": {
                "type": "OBJECT",  # ← MUST be uppercase!
                "properties": {
                    "issue": {
                        "type": "STRING",  # ← MUST be uppercase!
                        "description": "The issue: anxiety, stress, panic, sleep, sadness, overwhelmed",
                        "enum": ["anxiety", "stress", "panic", "sleep", "sadness", "overwhelmed"]
                    },
                    "intensity": {
                        "type": "STRING",  # ← MUST be uppercase!
                        "description": "Severity: mild, moderate, or severe",
                        "enum": ["mild", "moderate", "severe"]
                    }
                },
                "required": ["issue", "intensity"]
            }
        }
    ]
}

# ✅ CORRECT: Calling the model (NO tool_config!)
model = genai.GenerativeModel("gemini-2.5-flash", tools=[WELLNESS_TOOLS_CONFIG])
response = model.generate_content(message)  # Simple prompt, no tool_config

# ❌ WRONG: These break function calling
# response = model.generate_content(message, tool_config={"function_calling_config": {"mode": "any"}})
```

**File:** `providers/agent_tools.py`

```python
def execute_tool(name: str, args: dict, session_id: str) -> dict:
    """Execute a function call from Gemini"""
    if name == "log_mood":
        return _log_mood(session_id, args)
    elif name == "get_breathing_exercise":
        return _get_breathing_exercise()
    # ... etc
```

### Guardrails (Clinical-Grade Safety)

| Guardrail | Implementation |
|-----------|----------------|
| **Never auto-escalate crisis** | Functions can log, not alert externally |
| **User consent for data** | All logging respects existing consent model |
| **No function calling in crisis** | Crisis mode bypasses tools, shows resources |
| **Rate limiting** | Max 5 tool calls per message |
| **Audit logging** | All function calls logged with session_id |

---

## Phase II: RAG/Memory (pgvector)

### What It Enables

Luna remembers conversations across sessions:

```
Week 1: "I'm stressed about my parents fighting"
Week 2: "I feel sad today"
Luna: "I remember you mentioned family stress last week. 
       Is that still affecting you?"
```

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│              PostgreSQL (Your Render DB)                  │
├──────────────────────────────────────────────────────────┤
│  conversation_logs (existing)                             │
│  ├── id, session_id, user_message, ai_response           │
│  └── embedding vector(768)  ← NEW COLUMN                 │
│                                                          │
│  memory_summaries (NEW TABLE)                            │
│  ├── id, session_id, summary_type                        │
│  ├── content (text), embedding (vector)                  │
│  └── created_at, expires_at                              │
└──────────────────────────────────────────────────────────┘
```

### Memory Types

| Type | What It Stores | Retention |
|------|----------------|-----------|
| **Episodic** | "User mentioned exam stress on Dec 24" | 30 days |
| **Emotional** | "User responds well to breathing exercises" | 90 days |
| **Preference** | "User prefers short responses" | Permanent |
| **Clinical** | "Sleep issues mentioned 5x this month" | 90 days |

### Implementation Steps

1. **Enable pgvector on Render** (one-time setup)
2. **Add embedding column** to `conversation_logs`
3. **Create `memory_summaries` table**
4. **Generate embeddings** using Gemini's embedding API (free)
5. **Retrieve relevant context** before generating responses

### Guardrails (Clinical-Grade Safety)

| Guardrail | Implementation |
|-----------|----------------|
| **Memory expiration** | Auto-purge per retention policy |
| **No medical diagnoses stored** | Memory is emotional, not clinical |
| **User can clear memory** | `/api/clear_memory` endpoint |
| **Encrypted at rest** | Render PostgreSQL encryption |
| **No PII in embeddings** | Summaries are abstracted |

---

## Expansion Roadmap

### Near-Term (After Phase I & II)

| Capability | Builds On | Value |
|------------|-----------|-------|
| **Pattern Detection** | Memory | "You tend to feel anxious on Sundays" |
| **Personalized Interventions** | Memory + Functions | "Breathing helped last time" |
| **Progress Tracking** | Memory | "You've been feeling better this week" |

### Enterprise (B2B)

| Capability | Builds On | Value |
|------------|-----------|-------|
| **Aggregate Analytics** | Memory | School-wide wellness trends |
| **Counselor Alerts** | Functions + Memory | Flag at-risk students |
| **Export for Clinicians** | Memory | Session summaries for therapists |

---

## Files to Create/Modify

### Phase I (Function Calling)

| File | Action | Purpose |
|------|--------|---------|
| `providers/tools.py` | CREATE | Tool execution logic |
| `providers/gemini.py` | MODIFY | Add tool declarations |
| `app.py` | MODIFY | Handle function call responses |

### Phase II (RAG/Memory)

| File | Action | Purpose |
|------|--------|---------|
| `providers/memory.py` | CREATE | Memory storage/retrieval |
| `providers/embeddings.py` | CREATE | Embedding generation |
| `models.py` | MODIFY | Add MemorySummary model |
| `app.py` | MODIFY | Inject memory context |

---

## Implementation Checklist

### Phase I: Function Calling ✅ COMPLETE
- [x] Create `providers/tools.py` with core functions
- [x] Add tool declarations to `gemini.py`
- [x] Modify chat endpoint to handle function calls
- [x] Add function call audit logging
- [x] Test with all function types
- [ ] Update Flutter UI for interactive responses

### Phase II: RAG/Memory ✅ COMPLETE
- [x] Enable pgvector extension (via init_memory_tables)
- [x] Add embedding generation (providers/embeddings.py)
- [x] Implement memory retrieval (providers/memory.py)
- [x] Add /api/clear_memory endpoint
- [x] Add /api/memory_status endpoint
- [ ] Implement memory retrieval
- [ ] Add memory context to prompts
- [ ] Add /api/clear_memory endpoint
- [ ] Test cross-session memory

---

*This spec is the source of truth for AI capabilities. Update as implementation progresses.*
