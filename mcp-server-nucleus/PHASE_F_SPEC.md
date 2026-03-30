### Phase F – Autonomous Policy Engine (Depth-First Moat Expansion)

**Goal:** Deepen the self-healing loop built in Phase E so Nucleus doesn’t just run playbooks, it *adapts* them based on its own incident history.

This phase is depth-first: no major new incident types, just turning existing ones into a small autonomous moat engine.

---

## 1. Incidents as a First-Class Data Model

**Objective:** Make every incident and action conform to a canonical schema so later phases can reason over them.

**Requirements:**
- Create `incidents/SCHEMA.md` documenting a stable schema, e.g.:
  - `id`
  - `type` (e.g. `dead_pipeline`, `critical_error_rate`)
  - `severity`
  - `detected_at`
  - `resolved_at` (nullable)
  - `resolution_status` (e.g. `success`, `partial`, `failed`, `unknown`)
  - `metrics_snapshot` (key/value or small JSON blob)
  - `actions` (list of `{name, started_at, completed_at, outcome, details}`)
- Update `incident-controller.py` so that:
  - Every new incident writes a machine-readable record alongside the Markdown report.
    - Suggested: `incidents/YYYY-MM/INCIDENT-<id>.json` following the schema.
  - `incidents/actions.log` entries are guaranteed to reference `incident_id` and action names from the schema.

**Exit check:** A small helper script can iterate over all incidents and validate that they conform to `SCHEMA.md` with no special cases.

---

## 2. Outcome-Aware Incidents (Did the Playbook Work?)

**Objective:** For each incident, record whether the applied playbook actually fixed the underlying symptom.

**Requirements:**
- In `incident-controller.py`:
  - After executing a playbook for an incident, schedule a follow-up evaluation after X minutes (per-incident-type configurable, default 10–15 minutes).
  - On evaluation, re-query Prometheus for the relevant metrics:
    - Example: for `dead_pipeline`, check that command rate is back above zero.
    - For `critical_error_rate`, check that error rate is below warning threshold.
  - Set `resolution_status` for that incident to one of:
    - `success` – metrics back in healthy range.
    - `partial` – metrics improved but still degraded.
    - `failed` – metrics still beyond critical thresholds.
    - `unknown` – evaluation could not be performed (e.g. Prometheus down).
  - Persist this status back into the incident JSON file and append a summary entry to `actions.log`.

**Exit check:** When you run `npm run incident:check` on a simulated failure and wait the configured delay, the corresponding incident file and log show a non-null `resolution_status`.

---

## 3. Tiny Policy Feedback Loops (No ML, Just Rules)

**Objective:** Let Nucleus adjust its own aggressiveness based on recent incident outcomes.

**Requirements:**
- Introduce a small, internal policy state file, e.g. `incidents/policy_state.json`, managed only by the controller.
- For each incident type and key action (e.g. `restart_collector` for `dead_pipeline`):
  - Compute rolling stats over the last N incidents (configurable, default 10):
    - `success_rate` for the current playbook.
    - Optional: average time-to-recovery.
  - Apply simple, explicit adaptation rules, for example:
    - If `success_rate >= 0.9` for `dead_pipeline` restarts:
      - Allow shorter cooldown for `restart_collector` (e.g. 20 minutes instead of 30) within a safe minimum.
    - If `success_rate <= 0.5` for `critical_error_rate` restarts:
      - Automatically disable auto-restart for that incident type.
      - Downgrade to "document + notify" until a human adjusts the playbook.
    - If repeated `failed` outcomes occur for the same incident type:
      - Add a note into the incident report suggesting manual investigation and possible playbook update.
- Persist the derived knobs (effective cooldowns, enabled/disabled flags per incident type) in `policy_state.json` and/or `nucleus.yaml` overrides.

**Constraints:**
- No ML or opaque models in Phase F.
- All policy adjustments must be explainable by reading the code and `policy_state.json`.

**Exit check:**
- You can show a before/after where the controller:
  - Starts with conservative defaults.
  - Observes a series of successful dead-pipeline restarts.
  - Automatically tightens cooldowns for that incident type.
  - And, for a low success rate case, automatically disables an aggressive action.

---

## 4. Playbook Abstraction (Controller as Executor)

**Objective:** Turn the incident controller into a generic engine that executes per-incident playbooks instead of hardcoded if/else trees.

**Requirements:**
- Introduce a structured representation for playbooks (can start as Python dicts, later YAML), with fields like:
  - `name`
  - `incident_type`
  - `conditions` (PromQL queries + thresholds)
  - `actions` (ordered steps, each referencing an action primitive)
  - `retry` (max attempts, delay)
  - `cooldowns` (per-action)
  - `success_criteria` (how to decide resolution status)
- Refactor `incident-controller.py` so that:
  - Incident detection selects an appropriate playbook for the current incident type.
  - Execution is driven by this playbook structure and policy state, not scattered conditionals.
  - Adding or adjusting a playbook for an existing incident type does **not** require deep changes to the controller loop.

**Exit check:** You can define a new variant of an existing incident (e.g. a stricter `critical_error_rate_v2` playbook) by adding/modifying a playbook definition and see the controller honor it without touching core control flow.

---

## 5. Documentation and Guardrails

**Objective:** Make it clear that Phase F deepens autonomy while staying safe and explainable.

**Requirements:**
- Add `PHASE_F_SPEC` summary to:
  - `TELEMETRY_PIPELINE_README.md` (new subsection after Phase E).
  - `CURRENT_STATUS.md` (Phase F row with status and brief description).
- Document in `TELEMETRY_PIPELINE_README.md`:
  - How incident records and `policy_state.json` work.
  - Which knobs the controller is allowed to adjust automatically.
  - How to reset or override policy state if an operator wants to.
- Reiterate safety rails:
  - No auto-deletion of user data or configs.
  - Policy adaptation only changes thresholds, cooldowns, and action enable/disable flags, not what *kind* of destructive action is allowed.

**Exit criteria for Phase F:**
- For at least one incident type (e.g. `dead_pipeline`):
  - Incidents and actions are written using the new schema.
  - Resolution status is evaluated and stored automatically.
  - The controller adjusts its cooldowns or action flags based on recent outcomes.
  - The behavior change is visible and explainable via `policy_state.json` and docs.
- Phase E behaviors remain intact, now powered by a small autonomous policy engine instead of static config.
