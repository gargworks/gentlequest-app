# Response Quality & UX - Idea Seed
> **Created:** December 27, 2025  
> **Status:** ⏸️ DEFERRED — LLM already handles this naturally  
> **Decision:** Dec 27, 2025 — Validated during testing; not needed for v0.2/v0.3  
> **Potential Value:** HIGH (if problem resurfaces)

---

## 📌 Decision Note (Dec 27, 2025)

**Observation:** When asked "give me quick status", Claude automatically:
- Formatted output with emojis and clear sections
- Gave concise bullet points
- Identified critical issues
- Suggested next actions
- Used plain language alongside technical terms

**Conclusion:** The LLM naturally adapts to user's prompt style. No custom prompts needed.

**Decision:** Keep this idea documented for observation. If users report confusion in Week 1-2 interviews, revisit. Otherwise, leave as-is.

---

## 🧐 Problem Assessment

### What's Happening Now
- Claude reads raw data from `.brain/` (JSON, markdown)
- Claude presents it **as-is** with technical terms
- Terms like "FA-001", "triggers", "event_types" are insider language

### The Audience Problem

| Audience | Current UX | Ideal UX |
|----------|------------|----------|
| **Power user (you)** | ✅ Works | ✅ Works |
| **New developer** | ⚠️ Confusing | Plain language |
| **Non-technical founder** | ❌ Intimidating | Simple dashboards |

### Why This Matters
- Nucleus aims to be "The Core of Your AI Agents" — not just for experts
- Jargon creates friction for newcomers
- Better UX = faster adoption = stronger network effects (if we build Phase B)

---

## 💡 Proposed Solutions

### Option 1: Better MCP Prompts
**Effort:** Low | **Impact:** High

Add pre-built prompts that guide Claude to respond in human-friendly language:

```python
@mcp.prompt()
def sprint_summary():
    """Get a human-friendly sprint summary"""
    return """
    Read my brain state and give me a simple summary:
    - What am I working on this week?
    - What's done vs pending?
    - Any blockers?
    
    Use plain language, no technical jargon.
    Format for a busy founder who has 30 seconds to read this.
    """

@mcp.prompt()
def daily_standup():
    """Get a quick daily status"""
    return """
    Check my brain and answer:
    1. What did I accomplish yesterday?
    2. What's on my plate today?
    3. Anything stuck?
    
    Keep it under 5 bullet points. Plain English.
    """
```

**Pros:**
- Simple to implement
- User chooses prompt → controls complexity level
- No schema changes needed

**Cons:**
- Relies on user knowing prompts exist
- Each prompt is manual

---

### Option 2: Agent-Friendly Artifacts
**Effort:** Low | **Impact:** Medium

Format artifacts with a **"Plain English Summary"** section at the top:

```markdown
# Sprint Summary

> **TL;DR:** You're hardening your AI system. 5 fixes needed, 0 done yet.
> Focus on retry limits and stuck detection first.

---

## Details (Technical)

### FA-001: Max Retries
...
```

**Pros:**
- Works immediately (Claude reads the TL;DR)
- Self-documenting
- Good for investor-facing artifacts too

**Cons:**
- Requires updating artifact templates
- Manual effort to write TL;DRs

---

### Option 3: Persona Modes
**Effort:** Medium | **Impact:** High

Add a `persona` field to `state.json`:

```json
{
  "user_preferences": {
    "persona": "founder",
    "response_style": "concise",
    "jargon_level": "minimal"
  }
}
```

Then tools can adapt:
- `"persona": "founder"` → High-level summaries
- `"persona": "developer"` → Technical details
- `"persona": "investor"` → Metrics and milestones

**Pros:**
- Automatic adaptation
- Set once, works everywhere
- Personalized experience

**Cons:**
- More complex implementation
- Need to update all tools
- Testing across personas

---

## 📊 Comparison Matrix

| Feature | Effort | Impact | Risk | Recommended Phase |
|---------|--------|--------|------|-------------------|
| Better MCP Prompts | Low | High | Low | v0.3 |
| TL;DR in artifacts | Low | Medium | Low | v0.3 |
| Persona modes | Medium | High | Medium | v0.4+ |

---

## 🔄 Next Steps (When Ready to Implement)

1. **Gather user feedback** — Ask in interviews: "Was the output too technical?"
2. **Prototype prompts** — Add 2-3 human-friendly prompts to v0.3
3. **Template update** — Add TL;DR section to artifact templates
4. **Persona RFC** — Write spec if persona mode shows demand

---

## ⚠️ Disclaimer

> **This is a seed idea.** Do NOT implement without:
> 1. User feedback validating the problem
> 2. Prioritization against other backlog items
> 3. Technical reassessment of effort/impact

---

*Captured during mcp-server-nucleus v0.2.3 testing*
