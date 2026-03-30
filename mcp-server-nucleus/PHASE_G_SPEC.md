### Phase G – Reliability Policy Surface (Minimal Scope)

**Goal:** Expose the autonomous policy engine from Phase F in a small, legible way so operators can see what Nucleus "intends" to do for each incident type and control its autonomy level.

This is a UX/visibility layer on top of Phases E–F, not a new healing engine.

---

## 1. CLI Policy Report (Single Command)

**Objective:** Provide a single CLI entrypoint that summarizes current policy and outcomes per incident type.

**Requirements:**
- Add an npm script and underlying Python entrypoint, for example:
  - `npm run incident:policy` → `python3 scripts/incident-controller.py --policy-report`
- Implement `--policy-report` in `incident-controller.py` to print a concise table, e.g.:

  For each incident type (e.g. `dead_pipeline`, `critical_error_rate`):
  - `incident_type`
  - `total_incidents`
  - `success / partial / failed / unknown` counts
  - `current_cooldown_minutes` (effective, after policy adaptation)
  - `auto_actions_enabled` summary (e.g. `restart_collector: on`, `disable_command: off`)

- The output should be human-readable but also easy to parse if needed (e.g. aligned columns or simple JSON option).

**Exit check:** Running `npm run incident:policy` on a system with a few incidents shows a clear, per-incident-type summary consistent with `policy_state.json` and incident JSON files.

---

## 2. Plain-Language "Intent" Summary

**Objective:** Help humans understand, in one glance, what the controller plans to do on the *next* incident of each type.

**Requirements:**
- Extend the policy report to include a one-line plain-English description per incident type, for example:

  - `dead_pipeline`: "If commands drop to zero for 6h, I will restart the collector (cooldown 20m), restart metrics pipeline, generate an incident report, and post to Slack."
  - `critical_error_rate`: "If error rate >25% for N minutes, I will generate a report and post to Slack; auto-restart is currently DISABLED after repeated failures."

- These sentences should be derived from:
  - Playbook definitions (actions, thresholds).
  - Current policy state (cooldowns, enabled/disabled flags).

**Exit check:** For each incident type, the printed intent summary matches the actual playbook + policy configuration, as verified by reading the underlying config/state.

---

## 3. Minimal Operator Controls (Config-Level)

**Objective:** Allow operators to set clear bounds on autonomy without touching Python.

**Requirements:**
- In `.brain/config/nucleus.yaml`, add a small `policy.autonomy` block, for example:

  ```yaml
  policy:
    autonomy_mode: "observe_only"  # or "infra_only", "infra_and_app"
    hard_limits:
      allow_disable_command: false
      allow_restart_collector: true
      allow_restart_metrics_pipeline: true
  ```

- Wire the controller so that:
  - `autonomy_mode: observe_only` → no actions are executed; incidents are detected, logged, and reported only.
  - `infra_only` → infra restarts allowed (collector, metrics pipeline), but no app/command disabling.
  - `infra_and_app` → full set of actions allowed, subject to existing safety rails.
  - `hard_limits` act as absolute guards that policy adaptation cannot override.

**Exit check:**
- Changing `autonomy_mode` and `hard_limits` in `nucleus.yaml` visibly changes the policy report and actual behavior (e.g. restarts suppressed in observe-only mode).

---

## 4. Documentation and Status

**Objective:** Make the new surface understandable and keep the roadmap in sync.

**Requirements:**
- In `TELEMETRY_PIPELINE_README.md`:
  - Add a short "Phase G – Reliability Policy Surface" subsection after Phase F.
  - Document:
    - How to run `npm run incident:policy`.
    - How to read the policy report and intent summaries.
    - How `policy.autonomy` and `hard_limits` interact with the Phase F policy engine.
- In `CURRENT_STATUS.md`:
  - Add a Phase G row describing the Reliability Policy Surface.
  - Mark Phase G as completed when CLI, autonomy modes, and docs are done.

**Exit criteria for Phase G (minimal scope):**
- `npm run incident:policy` prints:
  - Per-incident-type stats.
  - Current effective cooldowns and action flags.
  - A one-line intent summary.
- Updating `policy.autonomy` and `hard_limits` in `nucleus.yaml` changes both behavior and the policy report in the expected ways.
- Phase E–F behaviors remain intact; Phase G only exposes and constrains the existing brain.
