# Architecture Decision Records (Index)

- ADR-001: Single codebase with environment detection — see `SINGLE_CODEBASE_GUIDE.md`
- ADR-002: Single-container deployment — see `SINGLE_CONTAINER_PLAN.md` / `DEPLOYMENT.md`
- ADR-003: Crisis detection parsing fix + env diffs — see `CRISIS_DETECTION_ANALYSIS.md`
- ADR-004: In-app quests verification is debug-only (prod-safe) — anchored in `ai_buddy_web/lib/dhiwise/presentation/wellness_dashboard_screen/wellness_dashboard_screen.dart`
- ADR-005: Stage 0 exit gate (Aug-8) — retroactively closed FAILED, no freeze imposed, work continued — see `docs/gates/ADR-005-stage0-resolution.md`
- ADR-006: Stage 1 exit-gate criterion (A), cumulative installs ≥250 — PASSED (209 native mobile + web, GA4/Firebase-verified) — see `docs/gates/ADR-006-stage1-installs-pass.md`

Notes:
- This index links to canonical sources to avoid duplication.
- When making consequential changes, add a bullet here with a short title and the source file link.
