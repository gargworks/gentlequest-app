### Phase H – Full Stack Health & Crash-Loop Defense (Single-Node)

**Goal:** Extend the autonomous incident brain from telemetry components to the
core Nucleus runtime on a single host. Prevent crash loops and bad boots from
silently killing an install; fail safe, self-stabilize, and document.

This phase is still infra-only: no GTM or business logic, just reliability.

> **Implementation:** Use `WINDSURF_PHASE_H_SUPER_PROMPT.md` in Windsurf to
> apply this spec safely and consistently.

---

## 1. Process & Container Watchdog

**Objective:** Continuously monitor core Nucleus processes/containers and
self-heal, with backoff, when they die.

**Requirements:**
- Define the "core stack" for a standard single-node install, e.g.:
  - Nucleus core server process / container.
  - Local DB (if used in this mode).
  - Queue/broker (if present).
  - Existing telemetry components (otel collector, Prometheus, Grafana, Jaeger).
- Implement a watchdog loop (can be integrated into `incident-controller.py`
  or a small companion script) that:
  - Periodically checks liveness for each core component (e.g. `docker ps`,
    PID checks, or HTTP health endpoints).
  - Emits incidents for:
    - `core_process_down`
    - `core_crash_loop` (see next section)
    - `db_unreachable`
    - `queue_unreachable`
  - Invokes appropriate playbooks for these incidents (restart, wait,
    escalate) using the existing controller.

**Exit check:** Killing the Nucleus core process or telemetry collector on a
single-node setup triggers detection, restart, and incident generation
without manual intervention.

---

## 2. Crash-Loop Detection and Backoff

**Objective:** Detect when a component is repeatedly crashing and stop making
things worse; back off and surface a clear incident instead of endless
restarts.

**Requirements:**
- For each monitored component, track recent restarts in policy state
  (e.g. timestamped list per component).
- Define crash-loop heuristics, e.g.:
  - More than `N` restarts in `M` minutes (configurable, with safe defaults).
- When crash-loop conditions are met:
  - Mark the component as `crash_looping` in policy state.
  - Stop auto-restarting that component for a cooldown window.
  - Generate a `crash_loop` incident with:
    - Component name.
    - Timestamps of recent restarts.
    - Last known logs or error codes (if cheaply accessible).
    - Suggested next steps for a human.
- Ensure these new incidents integrate with existing Phase F/G policy
  reporting and autonomy bounds.

**Exit check:** A misconfigured Nucleus core or telemetry component that
immediately crashes on start leads to a bounded number of restart attempts,
then a `crash_loop` incident and a pause, *not* an infinite restart storm.

---

## 3. Startup Smoke Tests & Bad-Boot Protection

**Objective:** Prevent a bad configuration or failed dependency from
"successfully" starting a broken system.

**Requirements:**
- Introduce a startup smoke test routine that can be run:
  - On Nucleus process start.
  - After configuration changes (especially Phase I rollouts later).
- The smoke test should verify, at minimum:
  - Prometheus reachable at the configured URL.
  - DB reachable and basic query works (if local DB is part of stack).
  - Queue/broker reachable (if used).
  - Otel collector listening on expected port.
  - Core Nucleus health endpoint (if available) returns healthy.
- If smoke test fails:
  - Do **not** mark the system healthy.
  - Optionally roll back to a last-known-good config (if already available
    from a future Phase I); otherwise:
    - Generate a `bad_boot` incident with details of which checks failed.
    - Enter a "degraded / not ready" mode where the system avoids serving
      production workloads until a human fixes config or dependencies.

**Exit check:** Introducing a deliberate misconfiguration (e.g. wrong DB
credentials) causes startup smoke tests to fail, a `bad_boot` incident to be
created, and the system to refuse to advertise itself as healthy.

---

## 4. Integration with Policy Engine and Surface

**Objective:** Make new health incidents first-class citizens in the
existing E/F/G engine.

**Requirements:**
- Define new incident types and playbooks for:
  - `core_process_down`
  - `core_crash_loop`
  - `db_unreachable`
  - `queue_unreachable`
  - `bad_boot`
- Ensure they:
  - Produce JSON incidents using the Phase F schema.
  - Participate in outcome evaluation where applicable (e.g., did a restart
    actually bring `core_process_down` back?).
  - Show up in `policy_state.json` and `incident:policy` reports with
    stats, cooldowns, and intent summaries.
- Respect existing autonomy modes and hard limits in `nucleus.yaml`:
  - For example, in `observe_only` mode, these incidents should still be
    detected and reported but not trigger restarts.

**Exit check:** Running `npm run incident:policy` after inducing these new
failures shows them as incident types with correct stats and intent
summaries; behavior respects autonomy bounds.

---

## 5. Documentation and Safety

**Objective:** Describe the new single-node reliability guarantees and
limits clearly.

**Requirements:**
- In `TELEMETRY_PIPELINE_README.md` (or a dedicated reliability doc):
  - Add a Phase H section describing:
    - What components are monitored.
    - How crash-loop detection works.
    - What startup smoke tests cover.
    - How this behaves under different autonomy modes.
- In `CURRENT_STATUS.md`:
  - Add a Phase H row summarizing "Full Stack Health & Crash-Loop Defense".
  - Mark it in-progress/complete when implemented and tested.
- Reiterate safety boundaries:
  - No destructive actions beyond restarts and safe mode toggles.
  - Crash-loop backoff is designed to prevent resource thrash, not to
    magically fix broken configs.

**Exit criteria for Phase H:**
- On a standard single-node Nucleus install, you can:
  - Kill core services and see them auto-restarted with incidents logged.
  - Introduce a crashy config and see bounded restarts followed by a
    `crash_loop` incident and backoff.
  - Introduce a dependency failure and see startup smoke tests block a
    "healthy" boot and emit a `bad_boot` incident.
- All behaviors are visible via incident JSON, policy reports, and docs,
  and respect autonomy modes + hard limits.
