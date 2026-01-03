# MCP Value Evaluation Template
> **Purpose:** Critically assess whether MCP usage added value or created friction  
> **Use:** Apply this template for each use case / project to build honest evaluation data

---

## 📋 EVALUATION METADATA

| Field | Value |
|-------|-------|
| **Evaluation ID** | [eval-YYYYMMDD-XXX] |
| **Use Case** | [Brief description] |
| **Evaluator** | [Name] |
| **Date** | [Date] |
| **Duration Analyzed** | [Time period] |

---

## 1️⃣ BASELINE COMPARISON

### Without MCP, what would have happened?

| Metric | Without MCP | With MCP | Delta |
|--------|-------------|----------|-------|
| Time to complete | | | |
| Quality of output | | | |
| Context retained | | | |
| Friction experienced | | | |

### Would the task have succeeded without MCP?
- [ ] Yes, equally well
- [ ] Yes, but slower
- [ ] Yes, but lower quality
- [ ] No, MCP was essential

---

## 2️⃣ TIME ALLOCATION

### How was time spent?

| Activity | % of Time | Value Category |
|----------|-----------|----------------|
| Actual task work | | ✅ Core value |
| MCP tool calls | | 🟡 Evaluate |
| Explaining how MCP works | | ⚠️ Overhead |
| Setting up infrastructure | | ⚠️ Overhead |
| Debugging MCP issues | | ❌ Friction |
| Meta-discussion | | ⚠️ Overhead |

**Overhead Ratio:** [Core value %] vs [Overhead %]

---

## 3️⃣ TOOL USAGE ASSESSMENT

### Which tools were called?

| Tool | Calls | Necessary? | Value Added? |
|------|-------|------------|--------------|
| `brain_list_artifacts` | | | |
| `brain_read_artifact` | | | |
| `brain_write_artifact` | | | |
| `brain_get_state` | | | |
| `brain_update_state` | | | |
| `brain_emit_event` | | | |
| `brain_read_events` | | | |
| `brain_get_triggers` | | | |
| `brain_evaluate_triggers` | | | |
| `brain_trigger_agent` | | | |

### Tool Efficiency Score
- **Essential calls:** [X/total]
- **Wasteful calls:** [X/total]
- **Score:** [Essential / Total] × 100 = **X%**

---

## 4️⃣ OUTCOME ASSESSMENT

### What did the user actually get?

| Deliverable | Quality | MCP Required? |
|-------------|---------|---------------|
| | | |
| | | |
| | | |

### What was phantom work?
> "Phantom work = effort spent on things that don't actually work"

| Phantom Work | Time Spent | Why Phantom? |
|--------------|------------|--------------|
| | | |

---

## 5️⃣ LLM BEHAVIOR ANALYSIS

### Did the LLM exhibit problematic patterns?

| Pattern | Observed? | Example |
|---------|-----------|---------|
| Tool bias (used tools unnecessarily) | | |
| Infrastructure creep (built systems instead of doing work) | | |
| Over-explaining the meta | | |
| Hallucinated capabilities | | |
| Appropriate tool selection | | |

---

## 6️⃣ CONTEXT PERSISTENCE VALUE

### Did saved context get reused?

| Context Saved | Reused Later? | Value When Reused |
|---------------|---------------|-------------------|
| | | |

### Multi-Session Benefit Score
- **Sessions using saved context:** [X]
- **Context retrieval utility:** [High/Medium/Low/None]

---

## 7️⃣ VERDICT

### Overall Assessment

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Task completion speed | | |
| Output quality | | |
| User experience | | |
| Context persistence value | | |
| Overhead/friction | | |

### **FINAL VERDICT:**
- [ ] ✅ **HIGH VALUE** — MCP essential, significant improvement
- [ ] 🟡 **MODERATE VALUE** — Some benefit, some overhead
- [ ] ⚠️ **MARGINAL VALUE** — Could have done without
- [ ] ❌ **FRICTION** — MCP slowed things down

---

## 8️⃣ RECOMMENDATIONS

### What should change?

| Area | Recommendation | Priority |
|------|----------------|----------|
| MCP Tools | | |
| LLM Guidance | | |
| Use Case Fit | | |
| User Expectations | | |

---

## 9️⃣ QUOTES & EVIDENCE

> [Notable quote from the conversation]

> [Another quote]

---

*Template Version: 1.0 | December 27, 2025*
