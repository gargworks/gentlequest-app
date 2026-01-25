# Archived Items - Deferred Work Log
> **Date:** 2026-01-06  
> **Reason:** Rabbit Hole Closure - PEFS Phase 1

---

## Purpose

This log tracks work that was **intentionally deferred** (not forgotten, not failed).  
Each item has a clear reason and a planned revisit date/condition.

---

## Item 1: MCP Failure Bug (Dec 28)

**Original Issue:**
- MCP Nucleus tools caused blank responses
- Error: "model output must contain either output text or tool calls"
- Occurred after changing NUCLEAR_BRAIN_PATH env var

**Workaround:**
- Direct file access works
- Users can access brain via `view_file` instead of MCP tools

**Why Deferred:**
- Workaround is sufficient for current use
- Deep debugging = time sink with high rabbit-hole risk
- Not blocking any critical workflows
- Better to batch technical debt fixes in dedicated sprint

**Action Taken:**
- Documented in `.brain/artifacts/test/mcp_failure_report.md`
- Moved to `/deferred/technical_debt/mcp_blank_response_bug.md`

**Revisit Condition:**
- v0.5.0 "Hardening Sprint" (planned)
- OR if 3+ users report similar issue
- OR if workaround stops working

**Status:** ✅ ARCHIVED (Not forgotten, strategically deferred)

---

## Item 2: GentleQuest Test Checklists

**Original Issue:**
- Multiple test checklists exist
- Status unclear (which are done? which are pending?)
- Files: `marathon_checklist.md`, `dogfood_log.md`, `cold_start_test_results.md`

**Why Deferred:**
- GentleQuest is live and working in production
- No critical bugs reported
- Unclear status = needs audit first, not ad-hoc testing
- Better to batch all QA audits together

**Action Taken:**
- Moved all to `/deferred/gentlequest_qa_audit/`
- Created `_README.md` in that folder explaining status

**Revisit Condition:**
- Next GentleQuest feature sprint
- OR if production issues emerge
- OR when doing "Test Coverage Audit" (future task)

**Status:** ✅ ARCHIVED (Audit needed before action)

---

## Item 3: Marketing Strategy Threads

**Original Issues:**
- Reddit Marketing Strategy (pivoted, not executed)
- Marketing Voice refinement (hook chosen, not posted)
- Build in Public planning (multiple threads)

**Why Deferred:**
- Too many strategy threads = analysis paralysis
- Execution beats strategy
- Better to learn from ONE post than plan 10 posts

**Action Taken:**
- Archived all strategy docs to `/deferred/marketing_strategy/`
- Kept ONE action: "Build in Public #1" scheduled for Jan 9

**Philosophy:**
> "Ship one post, learn from reality, iterate. Strategy without execution is procrastination."

**Revisit Condition:**
- After first 5 "Build in Public" posts
- THEN review strategy based on what actually worked

**Status:** ✅ ARCHIVED (Execution prioritized over planning)

---

## Item 4: E2E UX Testing Checklist

**Original Issue:**
- Created checklist to test PyPI → Claude Desktop pipeline
- Never executed

**Why KILLED (not archived):**
- Package already shipped to PyPI (v0.3.2)
- Already in production for 2+ weeks
- Zero bug reports from users
- Manual E2E test at this point = theatre, not value

**Action Taken:**
- **DELETED** `e2e_ux_checklist.md`
- Trusting user feedback over formal QA

**Rationale:**
> "Perfect is enemy of good. Users ARE the E2E test."

**Status:** ❌ KILLED (Not coming back)

---

## Archive Directory Structure

```
/deferred/
├── technical_debt/
│   └── mcp_blank_response_bug.md
├── gentlequest_qa_audit/
│   ├── _README.md
│   ├── marathon_checklist.md
│   ├── dogfood_log.md
│   └── cold_start_test_results.md
└── marketing_strategy/
    ├── reddit_marketing_strategy.md
    ├── marketing_voice_refinement.md
    └── build_in_public_planning.md
```

---

## Closure Metrics

| Category | Count | Method |
|:---------|:------|:-------|
| Archived | 3 items | Clear revisit condition |
| Killed | 1 item | Permanent deletion |
| Scheduled | 4 actions | Calendar reminders |
| Total Closed | 8 rabbit holes | 100% closure rate |

**Mental Load:** HIGH → LOW  
**Guilt:** Present → Removed  
**Open Loops:** 8 → 0

---

## Next Review

**When:** v0.5.0 planning (estimated Feb 2026)  
**What:** Review all `/deferred/` items, decide:
- Still relevant?
- Revisit condition met?
- Archive permanently or action?

**Owner:** Nightly Agent (will surface aged deferred items automatically once PEFS Phase 2 is built)
