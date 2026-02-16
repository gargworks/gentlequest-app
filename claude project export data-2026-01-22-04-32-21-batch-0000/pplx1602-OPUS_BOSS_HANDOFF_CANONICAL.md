# OPUS BOSS HANDOFF — CANONICAL

**Audience:** Windsurf Opus (“Boss”) — take over decisions, improvements, and future work.  
**Scope window:** Feb 9 → Feb 16, 2026 (pull older context only if it explains a decision).  
**Repo/workspace:** `/Users/lokeshgarg/ai-mvp-backend/`.  
**Canonical intent:** One file that Opus can read first, then drill down into appendices for deeper specs.  

---

## 0) Latest status (as of Feb 16)

We now have a **complete Design Thinking orchestration system** implemented as prompt artifacts that run inside a Sequential Thinking MCP loop framework, with multiple rigor levels and strong enforcement against slack/amnesia/fake convergence. [cite:1227]

### 0.1 What is done
- Five usable prompt artifacts exist in repo root, covering quick usage through exhaustive research-grade execution. [cite:1227]
- The system supports the core requirement: “1000+ turns if needed, new data each loop via search, plan-first, converge by delta.” [cite:1227]
- A deterministic hardening layer exists (atomic claims + evidence ledger + deterministic delta audit) to eliminate gaming of convergence and prevent amnesia in long runs. [cite:1227]

### 0.2 What is not yet proven
- No full end-to-end battle test has been logged on a real problem with measured turns/tokens/time to confirm estimates and practicality of convergence. [cite:1227]

---

## 1) Deliverables (what files exist)

All listed below are present in `/Users/lokeshgarg/ai-mvp-backend/`. [cite:1227]

### 1.1 Core prompt suite (Design Thinking)
1. `DESIGN_THINKING_QUICK_START.md` — minimal template for fast use. [cite:1227]
2. `DESIGN_THINKING_SEQUENTIAL_PROMPT.md` — full system (more detailed rules + structure). [cite:1227]
3. `DESIGN_THINKING_MESH_MAPPING.md` — conceptual/theory mapping (DT ↔ mesh/aggregator). [cite:1227]
4. `DESIGN_THINKING_EXHAUSTIVE_FLASH_KILLER.md` — research-grade enforcement to force Flash depth. [cite:1227]
5. `DESIGN_THINKING_EXHAUSTIVE_HARD_DETERMINISTIC_PROTOCOL.md` — deterministic protocol version (anti-gaming). [cite:1227]

### 1.2 Primary source framework (IIP)
- `docs/iip_reference/derived/IIP_MIRO_FULL_CONTEXT_EXPANDED.md` — canonical “8-stage IIP design thinking steps” source translated into loopable prompts. [cite:1227]

---

## 2) What this system must do (anchor intent)

The system was built to satisfy:
- Run many turns (even 1000+) without stopping early. [cite:1227]
- Every loop injects NEW info via internet/repo/doc search and adds new questions/context. [cite:1227]
- Show a plan first, then stop and wait for explicit approval. [cite:1227]
- Use a convergence rule (“delta”) so completion is measurable rather than vibes-based. [cite:1227]
- Enforce compliance: no slacking, no amnesia, no hand-wavy conclusions. [cite:1227]

---

## 3) Architecture in one page

### 3.1 Sequential Thinking MCP = loop engine
- Each design thinking stage executes as a set of loops. [cite:1227]
- Each loop requires: fresh searches → evidence logging → stage artifact update → delta audit → next-loop plan. [cite:1227]

### 3.2 8-stage IIP model
Stages execute in order unless explicitly skipped:
1. Problem Finding & POV
2. Research Plan
3. Personas / Synthesis
4. Solution Blueprints (SCAMPER)
5. Experimentation Plan
6. Business Model Canvas
7. MVE Planning
8. Reflection & Final Synthesis

These stages come from the IIP expanded reference. [cite:1227]

### 3.3 Rigor dial
We support multiple rigor profiles so cost/depth is chosen upfront:
- SPRINT (fast)
- STANDARD (default)
- DEEP (higher confidence)
- EXHAUSTIVE (research-grade)

We did this because one protocol cannot be optimal for feature decisions and company-direction decisions simultaneously. [cite:1227]

---

## 4) Evolution (latest → earlier)

### 4.1 Deterministic hardening (anti-gaming)
**Problem discovered:** delta can be gamed if defined as semantic similarity or any subjective measure. [cite:1227]

**Fix:** three enforcement patches merged into a hard protocol: [cite:1227]

1) Atomic Claim Tracking
- Convert answers into Atomic Claims with stable IDs:
  - `CXX: [claim] | Reason | Evidence: [E-IDs] | Confidence H/M/L | Status`
- Meaningful change ONLY: add/remove claim ID; change decision content; change evidence binding; change confidence tier; change status. [cite:1227]

2) Two-tier Evidence Ledger (anti-amnesia)
- Tier 1: append-only ledger (permanent E-IDs). [cite:1227]
- Tier 2: per-loop evidence register referencing Tier 1 IDs. [cite:1227]

3) Deterministic Delta Audit
- Delta computed via weighted field-diff on Loop Artifact fields A–G:
  - A:5, B:5, C:25, D:25, E:20, F:15, G:5. [cite:1227]
- If a change is claimed, show Before/After diff; if no diff, no change permitted. [cite:1227]

### 4.2 EXHAUSTIVE “Flash → Opus 4.6” forcing function
We added: higher search intensity per loop, adversarial evidence hunts, triple validation, Socratic depth, meta-loops, and compliance checkpoints so shallow completion is impossible. [cite:1227]

### 4.3 Base prompt suite
We translated the 8-stage IIP DT framework into a Sequential Thinking MCP-friendly prompt suite (quick template + full template + conceptual mesh mapping). [cite:1227]

---

## 5) How Opus should run it (operational playbook)

### 5.1 Which file to pick
- Default: `DESIGN_THINKING_QUICK_START.md` for most product problems. [cite:1227]
- Correctness > cost: `DESIGN_THINKING_EXHAUSTIVE_HARD_DETERMINISTIC_PROTOCOL.md`. [cite:1227]
- Flash-depth forcing: `DESIGN_THINKING_EXHAUSTIVE_FLASH_KILLER.md`. [cite:1227]

### 5.2 Standard execution pattern
1) Read the chosen prompt file. [cite:1227]
2) Fill PROBLEM and CONTEXT (workspace paths + relevant docs). [cite:1227]
3) Produce execution plan and STOP. [cite:1227]
4) Wait for user “APPROVED”. [cite:1227]
5) Run loops with required searches + evidence logging + delta. [cite:1227]
6) Declare convergence only when all gates pass. [cite:1227]

### 5.3 First recommended battle test
Run a STANDARD rigor test on a medium-stakes decision (e.g., retention drop-off) to validate loop counts, quality trend, enforcement strictness, and actionability. [cite:1227]

---

## 6) What Opus should decide next (future calls)

### 6.1 Make persistence real
If filesystem MCP is available, implement a standard output convention:
- write/append `evidence_ledger.jsonl` and `assumptions_ledger.jsonl` each loop or checkpoint,
- write a stage summary file after each stage convergence. [cite:1227]

### 6.2 Canonical EXHAUSTIVE baseline
We have two EXHAUSTIVE variants:
- Flash-Killer (strict; delta may remain subjective unless combined with deterministic patching),
- Hard-Deterministic (most auditable, anti-gaming). [cite:1227]

Opus should decide which becomes canonical and version the other as optional. [cite:1227]

### 6.3 Versioning
Introduce semantic version tags in filenames and a changelog once battle-tested. [cite:1227]

---

## 7) What we still need from the user (to finalize mega-context)

To finalize the complete mega context Opus can operate from without questions, we need:
1) First real test problem (1 sentence) + workspace path + relevant docs.
2) Optimization priority: speed vs correctness vs lowest token cost.
3) Hard constraints (e.g., “always write ledgers to disk”, “prefer repo search before web”). [cite:1227]

---

# APPENDIX A — Full spec reference

This canonical doc is the entrypoint. For the full “spec-like” handoff (complete text), refer to the original file:

- `/Users/lokeshgarg/ai-mvp-backend/claude project export data-2026-01-22-04-32-21-batch-0000/pplx1602-design-thinking-sequential-mcp-handoff.md`

Below is an excerpt of that spec (kept here for convenience); when in doubt, treat the original file above as the authoritative appendix.

---

## Appendix A.1 — Spec excerpt

