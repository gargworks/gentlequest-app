# Verification Rule: Negative Claims Only
> **Version:** 1.0  
> **Date:** December 28, 2025  
> **Rule:** Verify before negative claims. Positive claims have built-in evidence.

---

## The One Rule

> **Before saying "doesn't", "can't", "broken", "missing", "need to build" — verify first.**

---

## Why Narrow Scope

| Claim Type | Has Evidence? | Action |
|------------|---------------|--------|
| "X exists" | ✅ Tool shows file | No extra check |
| "Command works" | ✅ Output visible | No extra check |
| **"X doesn't exist"** | ❌ Can't show absence | **Verify** |
| **"This is broken"** | ⚠️ Might be user error | **Verify** |
| **"We need to build Y"** | ❌ Assumes Y missing | **Verify** |

---

## User Challenge

When agent makes negative claim without evidence:

> **"Are you sure? Show me."**

---

## Usage Log

| Date | Agent | Claim | Verified? | Outcome |
|------|-------|-------|-----------|---------|
| 2025-12-28 | TECH-DIRECTOR | "init command missing" | ❌ No | False alarm (it existed) |

---

## MCP Release Assessment

### Could This Be Part of Nucleus?

| Option | How | Complexity |
|--------|-----|------------|
| **A. Prompt guidance** | Add rule to `synthesizer.md` | Low |
| **B. Agent pattern** | Include in `patterns.md` | Low |
| **C. MCP tool** | `brain_verify_claim()` tool | Medium |

### Current Status

- [x] Rule defined
- [ ] Log usage during dogfood
- [ ] Assess if worth shipping

### Decision Point

**After 1 week of dogfood:** Did this rule prevent false alarms?  
**If yes:** Add to `BRAIN_PRODUCT_V1/agents/synthesizer.md` as standard guidance.

---

*Keep it simple. One rule. Narrow scope.*
