# 🏛️ Decision Log (ADR)

> **Purpose:** To record *why* we made major decisions, so we don't repeat mistakes when context is lost.

---

## [001] Release Safety Protocol
**Date:** 2026-01-04
**Context:**  Rushed release of Nucleus v0.3.1 contained a critical bug (ignored `tasks.json`) due to lack of testing.
**Decision:** Adopt a "Safety Sandwich" protocol.
- **Nucleus:** Mandatory manual "fresh install" test before PyPI upload. No CI automation yet (avoiding over-engineering).
- **GentleQuest:** Mandatory "Crisis Guardrail" test before deploy (Safety Critical).
**Status:** Accepted & Documented in `.agent/workflows/`.

---

## [002] Workflow Strategy: Single Thread + Brain
**Date:** 2026-01-04
**Context:** User (part-time, ADHD) struggled with the friction of managing 9+ optimized agent threads.
**Decision:** Consolidate to **One Active "Genesis" Thread**.
- **The Brain:** Holds all state/context/tasks.
- **The Thread:** The "Command Center" for execution.
- **Reasoning:** Reduces executive function load. Use specific threads only when context limits require a reset.
**Status:** Adopted.

---

## [003] Nucleus Scope Definition
**Date:** 2026-01-04
**Context:** Discussion on adding "Autopilot" features vs. keeping it simple.
**Decision:** Define strictly phased approach.
- **Phase 1 (Now):** "The Brain" (Context Management).
- **Phase 2 (Roadmap):** "Autopilot" (Background Daemon).
**Reasoning:** Avoids scope creep. Focus on optimizing the "Human-in-the-loop" experience first.
**Status:** Accepted.
