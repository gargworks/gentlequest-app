### Phase I – Safe Rollouts and Automatic Rollbacks

**Goal:** Make configuration and runtime changes safe by default. When a new
version or config is applied, Nucleus should automatically validate it,
monitor its impact, and roll back to the last-known-good state if it
misbehaves—all without human intervention.

This phase is still infra-only: no pricing, billing, or GTM. It focuses on
change safety for a single-node deployment.

---

## 1. Versioned Runtime & Config Snapshots

**Objective:** Treat Nucleus runtime and config as versioned artifacts so the
system can roll back cleanly.

**Requirements:**
- Introduce a simple versioning mechanism for the local deployment, e.g.:
  - `deployments/`
    - `current/` → symlink or pointer to active version
    - `releases/<timestamp>-<label>/` → directories with config and optional
      runtime metadata.
- At minimum, track for each release:
  - A unique `release_id` (e.g. timestamp + hash or label).
  - Config files used (e.g. `nucleus.yaml`, tool configs, mounts).
  - Optional: a short human label/description.
- Provide helper commands/scripts (or documented procedures) to:
  - Create a new release snapshot from the current config.
  - Switch `current` to a chosen release (this will be used by the
    controller for rollback).

**Exit check:** You can create a new release snapshot, point `current` to it,
and, if needed, manually switch back to the previous release without
breaking Nucleus.

---

## 2. Health-Gated Rollout Procedure

**Objective:** Wrap changes in a standard procedure: apply → smoke test →
short metrics watch → accept or roll back.

**Requirements:**
- Define a rollout command/procedure, e.g.:
  - `npm run deploy:apply -- <release_id>` or a documented sequence.
- The rollout must:
  1. Point the system at the target release config.
  2. Restart or reload Nucleus as needed.
  3. Run startup smoke tests (`--smoke-test`) to ensure basic health.
  4. If smoke tests fail:
     - Immediately roll back to previous release.
     - Generate a `bad_rollout` incident with:
       - `release_id` and previous release.
       - Smoke test failures.
  5. If smoke tests pass:
     - Begin a short observation window (e.g. 5–10 minutes) where the
       controller:
       - Watches key metrics (error rate, crash-loop flags, component
         health).
       - Detects `rollout_regression` incidents if metrics exceed
         thresholds.

**Exit check:** A deliberately broken release (bad DB credentials, etc.) that
fails smoke tests is rolled back automatically and produces a
`bad_rollout` incident.

---

## 3. Automatic Rollback on Regression

**Objective:** If a rollout causes clear regressions after passing smoke
tests, the system should auto-rollback to the previous version.

**Requirements:**
- Define a `rollout_regression` incident type with playbook:
  - Conditions:
    - During the rollout observation window for `release_id`, any of:
      - Error rate exceeds critical threshold.
      - New crash-loop incidents for core components.
      - Core components marked unhealthy by Phase H checks.
  - Actions:
    - Generate `rollout_regression` incident with relevant metrics.
    - Automatically switch `current` back to previous release.
    - Restart or reload Nucleus to use previous release.
    - Generate follow-up incident noting rollback success/failure.
- Ensure rollback operations are:
  - Idempotent.
  - Recorded in incident JSON and `actions.log`.
  - Visible in the policy report with clear intent summaries.

**Exit check:** Introducing a release that passes smoke tests but triggers
critical error spikes in the observation window results in an automatic
rollback and a `rollout_regression` incident.

---

## 4. Integration with Policy Engine and Autonomy Modes

**Objective:** Make rollout and rollback behavior a controlled part of the
existing policy engine.

**Requirements:**
- Add configuration to `.brain/config/nucleus.yaml`, e.g. under
  `incident_response.policy.rollouts`:

  ```yaml
  policy:
    rollouts:
      observation_window_minutes: 10
      enable_auto_rollback: true
  ```

- Ensure that:
  - In `autonomy_mode: observe_only`, the system still detects rollout
    issues and creates incidents but does NOT auto-rollback.
  - In `infra_only` or `infra_and_app`, auto-rollback is allowed if
    `enable_auto_rollback: true`.
  - Hard limits can optionally include a guard like
    `allow_auto_rollback: true/false`.
- Reflect rollout-related capabilities and recent events in the
  `incident:policy` report and intent summaries.

**Exit check:** Changing `enable_auto_rollback` or autonomy mode in
`nucleus.yaml` visibly affects whether rollbacks happen automatically or
only incidents are generated.

---

## 5. Documentation and Operator Workflow

**Objective:** Make the safe rollout flow clear to humans, even though the
brain does most of the work.

**Requirements:**
- In `TELEMETRY_PIPELINE_README.md` (or a dedicated deployment doc):
  - Add a Phase I section describing:
    - How releases are snapshotted and versioned.
    - The recommended rollout command/sequence.
    - How the observation window and auto-rollback logic work.
    - How autonomy modes and `enable_auto_rollback` affect behavior.
- In `CURRENT_STATUS.md`:
  - Add a Phase I row summarizing "Safe Rollouts & Automatic Rollbacks".
  - Mark it in-progress/complete when implemented and tested.
- Provide a small checklist/smoke procedure, e.g.:
  - Create a good release → deploy → verify no rollback.
  - Create a bad release (broken config) → deploy → see automatic
    rollback and incidents.

**Exit criteria for Phase I:**
- On a standard single-node install:
  - You can apply a new release via the defined rollout flow.
  - Smoke tests and observation window are automatically applied.
  - Clearly broken releases are rolled back automatically with
    `bad_rollout` or `rollout_regression` incidents created.
  - Behavior is visible via incident JSON, policy reports, and docs, and
    respects autonomy modes + rollout config.
