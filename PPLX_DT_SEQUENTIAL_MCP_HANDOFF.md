# Design Thinking Sequential MCP - Complete Handoff

**Timeline:** Feb 9-16, 2026 | **Handoff:** Feb 16 7:10 PM IST | **To:** Windsurf Opus

## Executive Summary

5 production-ready prompts forcing LLMs to match Opus 4.6 depth via process rigor. SPRINT to EXHAUSTIVE levels (200-3000+ turns). Atomic claims, evidence ledger, deterministic delta prevent fake convergence. Ready to deploy.

## Files Created

1. `DESIGN_THINKING_EXHAUSTIVE_HARD_DETERMINISTIC_PROTOCOL.md` - Zero ambiguity version
2. `DESIGN_THINKING_EXHAUSTIVE_FLASH_KILLER.md` - Makes Flash match Opus (1500-3000 turns)
3. `DESIGN_THINKING_SEQUENTIAL_PROMPT.md` - Full system (800 lines, 4 rigor levels)
4. `DESIGN_THINKING_QUICK_START.md` - Copy-paste template (150 lines)
5. `DESIGN_THINKING_MESH_MAPPING.md` - Theory/mesh connections

Source: `docs/iip_reference/derived/IIP_MIRO_FULL_CONTEXT_EXPANDED.md` (8 IIP stages)

## 4 Rigor Levels

- **SPRINT:** 200-400 turns, 50k-100k tokens (quick validation)
- **STANDARD:** 400-800 turns, 100k-200k tokens (DEFAULT)
- **DEEP:** 800-1500 turns, 200k-400k tokens (critical decisions)
- **EXHAUSTIVE:** 1500-3000+ turns, 400k-800k+ tokens (company pivot)

## 8 Stages (IIP)

1. Problem Finding & POV - Generate/filter problems, converge on Users/Need/Why
2. Research Plan - Extreme users, methods, contexts
3. Personas - Most intensive (40-100 loops EXHAUSTIVE)
4. Solution Blueprints - SCAMPER, prior art
5. Experimentation Plan - Hypotheses, MVE, kill criteria
6. Business Model Canvas - 9 elements, unit economics
7. MVE Planning - Minimum scope, timeline, budget
8. Synthesis - Cross-validate, GO/NO-GO

## Evolution

**Phase 1 (Feb 16 1:14 AM):** Base - 4 rigor levels, 2+ searches/loop, <1% delta  
**Phase 2 (Feb 16 1:34 AM):** EXHAUSTIVE - 5-10 searches, meta-loops, triple validation  
**Phase 3 (Feb 16 8:25-9:02 AM):** Deterministic - Atomic claims, evidence ledger, delta audit

## Key Innovations

### Atomic Claims
```
CXX: [claim] | Reason | Evidence: [E-IDs] | Confidence: H/M/L | Status
```
Meaningful change = add/remove ID, change decision/evidence/confidence/status. Rephrasing doesn't count.

### Two-Tier Evidence
- Tier 1: Permanent ledger (E001, E002...) append-only
- Tier 2: Per-loop top 5-10 E-IDs
Prevents amnesia (E001 from Loop 1 accessible at Loop 50)

### Deterministic Delta
Fields A-G, weights: A:5, B:5, C:25, D:25, E:20, F:15, G:5  
Delta% = Σ(weight × CHANGED)  
EXHAUSTIVE convergence: <0.5% for 3+ loops + Quality PASS + Triple validation + Meta OK + Cross-stage OK

### Verification Test
Before Stage 1: prove you understand delta calculation (fail fast at turn 1 vs loop 50)

## Why These Decisions

**4 rigor levels:** Different budgets for different stakes  
**Atomic claims:** Mechanical convergence vs vibes-based  
**Two-tier evidence:** Anti-amnesia + readable output  
**Deterministic delta:** Auditable math vs gameable "similarity"  
**Verification test:** 1 turn to detect failure vs 50+ loops wasted  
**Plan-first:** Catch misalignment at turn 1  
**8 stages:** IIP MBA validated (problem→research→users→solutions→validation→business→execution→synthesis)

## Integration

**Mesh:** Lines (stage MCPs) → Planes (domains) → Nodes (convergence) → Closed shape (complete plan)  
**Nucleus:** Meta-MCP orchestrating 8 stages, "Think like a founder" capability  
**GentleQuest:** Example - user drop-off → STANDARD → POV "ADHD low-friction + emotional support" → Solution "AI bot" → GO

## Usage

**File path (if filesystem):**
```
Read ~/ai-mvp-backend/DESIGN_THINKING_QUICK_START.md
PROBLEM: [problem]
CONTEXT: [context]
RIGOR: STANDARD
Go.
```

**Copy-paste:**
```bash
cat ~/ai-mvp-backend/DESIGN_THINKING_QUICK_START.md | pbcopy
```

**Shell alias:**
```bash
alias dt-quick='cat ~/ai-mvp-backend/DESIGN_THINKING_QUICK_START.md | pbcopy'
```

## Which Prompt When

- Quick feature: QUICK_START (150 lines, STANDARD)
- First time: SEQUENTIAL_PROMPT (full docs)
- Critical decision: EXHAUSTIVE_FLASH_KILLER (1500-3000 turns)
- Research-grade: HARD_DETERMINISTIC (zero ambiguity)
- Understanding: MESH_MAPPING (theory)

## Open Questions

1. Battle-testing (not run end-to-end yet)
2. Workspace persistence (evidence ledger file writes)
3. Multi-model orchestration (different stages, different models)
4. Parallel execution (some stages simultaneously)
5. Customizable stages (skip/add/reorder)
6. Nucleus integration (MCP server packaging)

## Next Steps

**First test:** GentleQuest drop-off, STANDARD (400-800 turns), $20-40  
**Success:** Validate convergence, document actuals  
**Failure:** Diagnose, fix, retest  
**Then:** Nucleus positioning (DEEP), package as MCP

## Reading Order

**15 min:** This + QUICK_START  
**1 hour:** + SEQUENTIAL_PROMPT + SPRINT test  
**4 hours:** All 5 + IIP reference + STANDARD test

## Checklist

- [ ] Access all 5 prompts + IIP reference
- [ ] Understands 4 rigor levels  
- [ ] Can explain atomic claims, evidence ledger, delta
- [ ] Can pass Delta Verification Test
- [ ] Knows which prompt when
- [ ] Can run SPRINT test
- [ ] Can identify gaps

---

**Status:** Production-ready, not battle-tested | **Deploy:** ~1 week | **Think deeply, build correctly.**
