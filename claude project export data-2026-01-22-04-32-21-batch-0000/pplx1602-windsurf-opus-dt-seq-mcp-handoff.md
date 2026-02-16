# WINDSURF OPUS HANDOFF — Design Thinking via Sequential Thinking MCP (pplx1602)

**Audience:** Windsurf Opus ("Boss") — take over decisions, improvements, and future work.  
**Scope window:** Feb 9 → Feb 16, 2026 (with light refresher context before Feb 9 only if it explains a decision).  
**Primary repo/workspace:** `/Users/lokeshgarg/ai-mvp-backend/`.  

---

## 0) Latest status (as of Feb 16)

We now have a **complete Design Thinking orchestration system** implemented as prompt artifacts that run inside a Sequential Thinking MCP loop framework, with multiple rigor levels and strong enforcement against slack/amnesia/fake convergence. [cite:1217]

### 0.1 What is “done”
- Five usable prompt artifacts exist in repo root, covering quick usage through exhaustive research-grade execution. [cite:1217]
- The system supports the core requirement: *“1000+ turns if needed, new data each loop via search, plan-first, converge by delta.”* [cite:1217]
- A deterministic hardening layer exists (atomic claims + evidence ledger + deterministic delta audit) to eliminate gaming of convergence and prevent amnesia in long runs. [cite:1217]

### 0.2 What is not yet proven
- We have not run a full end-to-end battle test on a real problem with full logging of turns/tokens/time to confirm the estimates and validate that convergence is practical at the chosen rigor level. [cite:1217]

---

## 1) Deliverables (what files exist)

All listed below are present in `/Users/lokeshgarg/ai-mvp-backend/`. [cite:1217]

### 1.1 Core prompt suite (Design Thinking)
1. `DESIGN_THINKING_QUICK_START.md` — minimal template for fast use. [cite:1217]
2. `DESIGN_THINKING_SEQUENTIAL_PROMPT.md` — full system (more detailed rules + structure). [cite:1217]
3. `DESIGN_THINKING_MESH_MAPPING.md` — conceptual/theory mapping (DT ↔ mesh/aggregator). [cite:1217]
4. `DESIGN_THINKING_EXHAUSTIVE_FLASH_KILLER.md` — research-grade enforcement to force Flash depth. [cite:1217]
5. `DESIGN_THINKING_EXHAUSTIVE_HARD_DETERMINISTIC_PROTOCOL.md` — deterministic protocol version (anti-gaming). [cite:1217]

### 1.2 Primary source framework (IIP)
- `docs/iip_reference/derived/IIP_MIRO_FULL_CONTEXT_EXPANDED.md` — the canonical “8-stage IIP design thinking steps” source we translated into loopable prompts. [cite:1220]

---

## 2) The original intent (what this system must do)

### 2.1 Anchor intent (operationalized)
The system was designed to satisfy these requirements:
- Run **many turns** (even 1000+) if needed, without stopping early. 
- In each loop: do **internet/repo/doc search** (tool calls) and inject *new* context/questions. 
- Show a **plan first**, then wait for explicit approval. 
- Use a **convergence rule** (“delta”) so the agent cannot claim completion without measurable stability.
- Enforce compliance: no slacking, no amnesia, no “hand-wavy conclusions.”

### 2.2 Why we built this
- Fast models often produce plausible output quickly but drift, forget early evidence, and “declare convergence” prematurely without defensible methodology.
- The goal is to make the reasoning quality **a function of process** (enforced) rather than **a function of model tier** (expensive).

---

## 3) System architecture (how it works)

### 3.1 Core mechanism: Sequential Thinking MCP as a loop engine
- Each design thinking stage is executed as **a set of loops**.
- Each loop must include (a) fresh searches, (b) evidence logging, (c) an update to the stage artifact, (d) a delta calculation, and (e) a next-loop plan.
- Stage completion is allowed only after convergence gates pass.

### 3.2 Stage model: the 8 IIP stages
The system executes these stages in order (unless the user explicitly skips):
1. Problem Finding & POV
2. Research Plan
3. Personas / Synthesis
4. Solution Blueprints (SCAMPER)
5. Experimentation Plan
6. Business Model Canvas
7. MVE Planning
8. Reflection & Final Synthesis

This is sourced from the IIP expanded Miro reference. [cite:1220]

### 3.3 Rigor dial (time/token control)
We created multiple “rigor” profiles so the user can choose cost/depth upfront:
- SPRINT (fast)
- STANDARD (default)
- DEEP (high confidence)
- EXHAUSTIVE (research-grade)

The system was built this way because *one prompt cannot be optimal* for both feature-level decisions and company-direction decisions.

---

## 4) Evolution timeline (latest → earlier)

### 4.1 Phase 3 — Deterministic hardening (anti-gaming)
**Problem discovered:** “delta” can be gamed if it’s defined as semantic similarity or any subjective measure.

**Fix:** We introduced three enforcement patches and merged them into a hard protocol:

1) **Atomic Claim Tracking**
- Convert “Current Best Answer” from prose into Atomic Claims with stable IDs:
  - `CXX: [claim] | Reason | Evidence: [E-IDs] | Confidence H/M/L | Status`
- Define “meaningful change” ONLY as:
  - add/remove claim ID, change decision content, change evidence binding, change confidence tier, or change status.

2) **Two-tier Evidence Ledger (anti-amnesia)**
- Tier 1: append-only ledger (permanent E-IDs).
- Tier 2: per-loop evidence register referencing Tier 1 E-IDs.

3) **Deterministic Delta Audit**
- Delta computed via weighted field-diff on Loop Artifact fields A–G:
  - A:5, B:5, C:25, D:25, E:20, F:15, G:5.
- Whenever a change is claimed, require a Before/After diff (if no diff, no change allowed).

**Why this matters:** It removes the biggest failure mode: fake convergence by rephrasing.

### 4.2 Phase 2 — EXHAUSTIVE “Flash → Opus 4.6” forcing function
**Goal:** Make Gemini Flash compete with deep-thinking models using process constraints.

**Mechanisms added:**
- Higher search intensity per loop.
- Mandatory adversarial evidence hunt each loop.
- Triple validation requirement.
- Socratic depth requirement.
- Meta-loops and compliance checkpoints.

**Result:** A template that forces breadth + depth + self-challenge repeatedly, making shallow completion impossible.

### 4.3 Phase 1 — Base design thinking prompt suite
**Goal:** Translate the 8-stage IIP DT framework into a Sequential Thinking MCP-friendly prompt suite.

**Outputs:**
- Quick start template for fast usage.
- Full prompt for detailed operation.
- Mesh mapping doc to explain “why” and guide extensions.

---

## 5) Key design decisions (and how we addressed concerns)

### 5.1 Slack prevention (“whip”)
We used explicit protocol violations + restart instructions to remove optionality (“if you can, do X”).

### 5.2 Amnesia prevention
We recognized that long runs (50+ loops) will exceed context windows and therefore must use:
- permanent evidence IDs,
- append-only ledgers,
- explicit cross-loop references.

### 5.3 Adversarial integrity
We forced a contradiction hunt every loop so the system does not drift into confirmation bias.

### 5.4 Plan-first safety
We added a hard gate: execution plan must be produced before any loops, and the user must approve.

---

## 6) How Opus should use this (operational playbook)

### 6.1 Choosing the file
- Default: `DESIGN_THINKING_QUICK_START.md` for most product problems.
- When correctness matters more than cost: `DESIGN_THINKING_EXHAUSTIVE_HARD_DETERMINISTIC_PROTOCOL.md`.
- When you want “Flash depth forcing”: `DESIGN_THINKING_EXHAUSTIVE_FLASH_KILLER.md`.

### 6.2 Execution pattern
1) Read the chosen prompt file.  
2) Fill in PROBLEM and CONTEXT (workspace paths + relevant docs).  
3) Produce execution plan and STOP.  
4) Wait for user “APPROVED”.  
5) Run loops with required searches + evidence logging + delta.  
6) Only declare convergence when gates pass.

### 6.3 First recommended battle test
- Run a STANDARD rigor test on a medium-stakes decision (e.g., a retention drop-off) to validate:
  - real loop counts,
  - quality trend,
  - whether the enforcement is too heavy or too lax,
  - and whether the outputs are actionable.

---

## 7) What Opus should decide next (future calls)

### 7.1 Make persistence real
If filesystem MCP is available, Opus should implement a standard output convention:
- Write/append `evidence_ledger.jsonl` and `assumptions_ledger.jsonl` each loop or checkpoint.
- Write a stage summary file after each stage convergence.

### 7.2 Decide the canonical protocol
We now have two “EXHAUSTIVE” variants:
- Flash-Killer (very strict but still allows some subjectivity in delta unless combined with deterministic patching).
- Hard-Deterministic (most auditable, anti-gaming).

Opus should decide which one becomes the canonical EXHAUSTIVE baseline and version the other as optional.

### 7.3 Versioning and stability
- Introduce semantic version tags in filenames (e.g., `..._v0.1.md`) once battle-tested.
- Add a changelog section so future updates are explainable.

---

## 8) File index (quick reference)

### Repo root (Design Thinking)
- `/Users/lokeshgarg/ai-mvp-backend/DESIGN_THINKING_QUICK_START.md`
- `/Users/lokeshgarg/ai-mvp-backend/DESIGN_THINKING_SEQUENTIAL_PROMPT.md`
- `/Users/lokeshgarg/ai-mvp-backend/DESIGN_THINKING_MESH_MAPPING.md`
- `/Users/lokeshgarg/ai-mvp-backend/DESIGN_THINKING_EXHAUSTIVE_FLASH_KILLER.md`
- `/Users/lokeshgarg/ai-mvp-backend/DESIGN_THINKING_EXHAUSTIVE_HARD_DETERMINISTIC_PROTOCOL.md`

### IIP source
- `/Users/lokeshgarg/ai-mvp-backend/docs/iip_reference/derived/IIP_MIRO_FULL_CONTEXT_EXPANDED.md`

---

## 9) What I need from you (to make this handoff “complete-complete”)

To turn this into a final “mega context thread” that Opus can operate from without asking questions, I need:

1) The intended first real test problem (one sentence + workspace path + any relevant docs).
2) Whether Opus should optimize for: (a) speed, (b) correctness, or (c) lowest token cost.
3) Any explicit constraints for Opus (e.g., “never use web”, “always write ledgers to disk”, “prefer repo search first”).

---

**End of document.**
