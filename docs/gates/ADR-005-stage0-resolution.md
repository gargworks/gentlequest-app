# ADR-005 (retroactive close, 2026-08-18): Stage 0 exit gate resolution

**Original gate:** `BILLION_DOLLAR_ROADMAP.md` Stage 0, verbatim per the pre-existing
Aug-8 gate — 4+/day web installs sustained 3 consecutive days, OR ≥20 non-direct
GA4 users, OR any unprompted human voice, deadline 2026-08-08. Stated kill rule:
*"none of the three by 2026-08-08 → freeze to portfolio mode per ADR-005, closing
ADR written. No extension, no partial credit."*

**What actually happened, found on audit 2026-08-18:**
- Criterion (i): the counting instrument (`~/.local/share/gentlequest/logs/funnel_snapshot.log`)
  stopped writing on 2026-07-23, 16 days before the deadline, and was never resumed.
  Unmeasured through the gate — which the plan's own rule ("unmeasurable = FAILED")
  scores as FAILED, not unknown.
- Criterion (ii): measured, FAILED (1/20 non-direct GA4 users as of the deadline window).
- Criterion (iii): measured, FAILED (0 valid human-voice ledger entries).
- **No closing ADR was written at the time.** The stated kill rule did not fire.
  Work continued past the deadline into Stage 1 (companion loop, Fable features,
  v1.6.0 ship) without a documented pass or fail.

**Resolution (this entry):** Stage 0 as originally gated FAILED on 2026-08-08 by
the plan's own written rule. This is recorded honestly, not re-litigated to a pass.
The freeze-to-portfolio consequence is **not** retroactively imposed — the product
kept moving and has since produced real, independently-verified traction (see
ADR-006). The gap is closed by documenting it, not by pretending it didn't happen
or by unwinding shipped work. Going forward, Stage 1's own gate (2026-10-08) is
the live, binding checkpoint — see ADR-006 for its first half.

**Standing fix:** cross-stage invariant #7 (gate artifacts must not be Mac-local)
was violated by the dead local log. Any future daily counter must write to a
non-Mac-local store (DB row, off-Mac copy) or it will silently die again.
