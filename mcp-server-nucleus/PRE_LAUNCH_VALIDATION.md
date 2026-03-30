# Pre-Launch Validation — Nucleus Incident Brain

**Purpose:** Systematically validate safety, stability, and developer ergonomics before publishing to PyPI/npm/GitHub.

**Status:** 🟡 IN PROGRESS

---

## 1. Safety: "It never makes things worse"

### 1.1 Autonomy Mode Constraints

**Objective:** Verify autonomy modes and hard limits correctly constrain actions.

#### Test 1.1.1: `observe_only` mode
- **Setup:** Set `policy.autonomy.autonomy_mode: observe_only` in `nucleus.yaml`
- **Trigger:** Induce critical error rate (>25%), collector down, component crash
- **Expected:**
  - ✅ Incidents detected and JSON files created
  - ✅ Reports generated in `incidents/`
  - ✅ Slack notifications sent (if configured)
  - ❌ NO restarts executed
  - ❌ NO rollbacks executed
  - ❌ NO command disables executed
- **Verification:**
  - Check `actions.log` — should only contain `generate_report`, `notify_slack`
  - Check `policy_state.json` — actions should show `effective_status: "OFF (observe_only)"`
  - Run `npm run incident:policy` — should show all actions marked OFF

**Status:** ⏳ PENDING

#### Test 1.1.2: `infra_only` mode
- **Setup:** Set `policy.autonomy.autonomy_mode: infra_only`
- **Trigger:** Collector down, component crash, critical error rate
- **Expected:**
  - ✅ Infra restarts allowed (`restart_collector`, `restart_component`)
  - ✅ Rollbacks allowed (if `enable_auto_rollback: true`)
  - ❌ NO command disables (app-level action)
- **Verification:**
  - Check `actions.log` — should contain restart actions
  - Check `policy_state.json` — `disable_command` should show OFF, restarts should show ON
  - Verify `disabled_commands.json` is NOT created/modified

**Status:** ⏳ PENDING

#### Test 1.1.3: Hard limits override everything
- **Setup:** Set `policy.autonomy.hard_limits.allow_disable_command: false`
- **Trigger:** High error rate for specific command
- **Expected:**
  - ❌ Command disable NEVER executes, even in `infra_and_app` mode
  - ✅ Incident detected, report generated
  - ✅ Policy report shows `disable_command: OFF (hard_limit)`
- **Verification:**
  - Check `disabled_commands.json` — should NOT exist or be empty
  - Check `actions.log` — should NOT contain `disable_command` actions
  - Run `npm run incident:policy` — should show hard limit enforcement

**Status:** ⏳ PENDING

#### Test 1.1.4: Hard limit `allow_auto_rollback: false`
- **Setup:** Set `policy.autonomy.hard_limits.allow_auto_rollback: false`
- **Trigger:** Bad rollout (smoke test failure)
- **Expected:**
  - ✅ Incident detected (`bad_rollout`)
  - ❌ NO automatic rollback executed
  - ✅ Report generated with rollback skipped
- **Verification:**
  - Check `actions.log` — should show `rollback_release: skipped (hard_limit)`
  - Verify release did NOT switch back

**Status:** ⏳ PENDING

### 1.2 Crash-Loop Defense and Backoff

**Objective:** Verify crash-loop detection prevents infinite restart storms.

#### Test 1.2.1: Bounded restarts
- **Setup:** Configure component with `max_restarts: 3`, `window_minutes: 5`
- **Trigger:** Make component crash immediately on restart (e.g., bad config)
- **Expected:**
  - ✅ Component restarted 3 times within 5 minutes
  - ✅ After 3rd restart, `crash_looping: true` set in `policy_state.json`
  - ✅ `core_crash_loop` incident generated
  - ❌ NO further restarts for `backoff_minutes` duration (default 15 min)
- **Verification:**
  - Check `policy_state.json` — component should have `crash_looping: true`, `backoff_until` timestamp
  - Check `actions.log` — should show exactly 3 restart attempts, then pause
  - Check `incidents/` — should have `core_crash_loop` incident JSON

**Status:** ⏳ PENDING

#### Test 1.2.2: Backoff expiration and reset
- **Setup:** After Test 1.2.1, wait for backoff period to expire
- **Trigger:** Fix component config, wait for backoff to expire
- **Expected:**
  - ✅ After backoff expires, component can be restarted again
  - ✅ If component is healthy, `crash_looping` flag clears
  - ✅ Restart counter resets
- **Verification:**
  - Check `policy_state.json` — `crash_looping: false`, `recent_restarts` pruned
  - Verify component can be restarted successfully

**Status:** ⏳ PENDING

### 1.3 Rollout Safety

**Objective:** Verify rollout safety mechanisms catch bad releases.

#### Test 1.3.1: Broken release (smoke test failure)
- **Setup:** Create release with invalid Prometheus URL
- **Trigger:** `npm run deploy:rollout -- <broken-release-id>`
- **Expected:**
  - ✅ Smoke tests fail immediately
  - ✅ `bad_rollout` incident generated
  - ✅ Automatic rollback to previous release
  - ✅ Rollback verified with smoke tests
  - ✅ System returns to working state
- **Verification:**
  - Check `deployments/current` — should point to previous release
  - Check `incidents/` — should have `bad_rollout` incident JSON
  - Check `actions.log` — should show rollback action
  - Run `npm run health:smoke-test` — should pass after rollback

**Status:** ⏳ PENDING

#### Test 1.3.2: Subtle bad release (regression detection)
- **Setup:** Create release that passes smoke tests but causes high error rate
- **Trigger:** `npm run deploy:rollout -- <regression-release-id>`
- **Expected:**
  - ✅ Smoke tests pass
  - ✅ Enters observation window (10 min)
  - ✅ During observation: error rate exceeds threshold
  - ✅ `rollout_regression` incident generated
  - ✅ Automatic rollback to previous release
  - ✅ Rollback verified
- **Verification:**
  - Check `policy_state.json` — should have `active_rollout` entry during observation
  - Check `incidents/` — should have `rollout_regression` incident JSON
  - Check `deployments/current` — should point to previous release after rollback
  - Verify error rate returns to normal after rollback

**Status:** ⏳ PENDING

---

## 2. Stability: "It behaves predictably over days"

### 2.1 Daemon Longevity

**Objective:** Verify daemon can run for extended periods without degradation.

#### Test 2.1.1: Long-running daemon (no incidents)
- **Setup:** Start `npm run incident:daemon` with healthy system
- **Duration:** 4+ hours
- **Expected:**
  - ✅ No memory leaks (RSS stays bounded)
  - ✅ No CPU spikes (stays <5% idle)
  - ✅ Logs show regular check cycles
  - ✅ No crashes or exceptions
- **Verification:**
  - Monitor with `ps aux | grep incident-controller` every 30 min
  - Check log file size growth is linear and bounded
  - Verify daemon can be stopped cleanly with Ctrl+C

**Status:** ⏳ PENDING

#### Test 2.1.2: Long-running daemon (intermittent incidents)
- **Setup:** Start daemon, induce incidents periodically (every 30 min)
- **Duration:** 4+ hours
- **Expected:**
  - ✅ Incidents detected and handled correctly
  - ✅ Memory usage stays bounded (no leak from incident objects)
  - ✅ Policy state grows but prunes old entries
  - ✅ No degradation in response time
- **Verification:**
  - Check `policy_state.json` size — should not grow unbounded
  - Verify old outcomes are pruned per rolling window config
  - Check incident JSON count — should match expected incident rate

**Status:** ⏳ PENDING

### 2.2 State Correctness

**Objective:** Verify state files remain consistent across operations.

#### Test 2.2.1: State consistency after many incidents
- **Setup:** Generate 20+ incidents of various types
- **Expected:**
  - ✅ `policy_state.json` remains valid JSON
  - ✅ All incident JSONs are valid and parseable
  - ✅ `actions.log` is append-only and consistent
  - ✅ No duplicate incident IDs
- **Verification:**
  - Parse all JSON files with `jq` — should not error
  - Verify incident IDs are unique
  - Check `actions.log` — should be chronological, no gaps

**Status:** ⏳ PENDING

#### Test 2.2.2: State recovery after controller restart
- **Setup:** Run incidents, stop controller, restart controller
- **Expected:**
  - ✅ Controller loads previous policy state correctly
  - ✅ Pending incidents are evaluated on restart
  - ✅ Cooldowns and backoffs are respected
  - ✅ No state corruption or loss
- **Verification:**
  - Check `policy_state.json` before/after restart — should be consistent
  - Verify controller doesn't re-trigger recently handled incidents
  - Check logs for successful state load messages

**Status:** ⏳ PENDING

#### Test 2.2.3: State consistency across rollouts
- **Setup:** Perform 5+ rollouts (good and bad releases)
- **Expected:**
  - ✅ Release metadata remains consistent
  - ✅ `current` symlink always points to valid release
  - ✅ Policy state tracks active rollout correctly
  - ✅ No orphaned releases or broken symlinks
- **Verification:**
  - Check `deployments/releases/` — all releases have valid `release.json`
  - Verify `current` symlink is not broken
  - Check `policy_state.json` — `active_rollout` cleared after completion

**Status:** ⏳ PENDING

### 2.3 Partial Failure Handling

**Objective:** Verify graceful degradation when dependencies fail.

#### Test 2.3.1: Prometheus down
- **Setup:** Stop Prometheus, run incident check
- **Expected:**
  - ✅ Controller logs Prometheus unreachable
  - ✅ Skips metric-based detections gracefully
  - ✅ Does NOT crash or hang
  - ✅ Continues with non-metric checks (component health, etc.)
- **Verification:**
  - Check logs — should show clear "Prometheus unreachable" messages
  - Verify controller exits cleanly (exit code 0)
  - No stack traces or exceptions

**Status:** ⏳ PENDING

#### Test 2.3.2: Slack unreachable
- **Setup:** Set invalid Slack webhook URL, trigger incident
- **Expected:**
  - ✅ Incident detected and processed
  - ✅ Report generated
  - ✅ Slack notification fails gracefully
  - ✅ Failure logged but does NOT block other actions
- **Verification:**
  - Check `actions.log` — should show `notify_slack: failed`
  - Verify other actions (restart, report) still executed
  - No crashes or hangs

**Status:** ⏳ PENDING

#### Test 2.3.3: Docker errors
- **Setup:** Stop Docker daemon, trigger component restart
- **Expected:**
  - ✅ Restart action fails gracefully
  - ✅ Failure logged with clear error message
  - ✅ Controller does NOT crash
  - ✅ Incident marked as failed, not pending
- **Verification:**
  - Check `actions.log` — should show `restart_component: failed (docker error)`
  - Check logs — should have clear Docker error message
  - Verify controller continues running

**Status:** ⏳ PENDING

---

## 3. Developer Experience: "A new user can't shoot themselves immediately"

### 3.1 Fresh Install Path

**Objective:** Verify new user can get started without issues.

#### Test 3.1.1: Clean clone to working smoke test
- **Setup:** Fresh clone, no prior config
- **Steps:**
  ```bash
  git clone <repo>
  cd mcp-server-nucleus
  npm install
  # Minimal setup (if any)
  npm run health:smoke-test
  ```
- **Expected:**
  - ✅ Smoke test runs (pass or fail with clear message)
  - ✅ No stack traces or cryptic errors
  - ✅ Error messages point to docs or setup steps
- **Verification:**
  - Document exact steps required
  - Verify error messages are actionable
  - Check if defaults work for local dev

**Status:** ⏳ PENDING

#### Test 3.1.2: First incident check
- **Setup:** After 3.1.1, run incident check
- **Steps:**
  ```bash
  npm run incident:check
  npm run incident:policy
  ```
- **Expected:**
  - ✅ Commands run without crashes
  - ✅ If Prometheus missing, clear error message
  - ✅ If config missing, creates default or shows setup instructions
  - ✅ Policy report shows current state clearly
- **Verification:**
  - Document any required setup steps
  - Verify error messages are helpful
  - Check if defaults are safe for laptop

**Status:** ⏳ PENDING

### 3.2 Config Defaults Are Safe

**Objective:** Verify default config doesn't cause harm on dev machines.

#### Test 3.2.1: Default autonomy mode
- **Setup:** Fresh `nucleus.yaml` (or no config)
- **Expected:**
  - ✅ Default autonomy mode is `observe_only` or clearly documented
  - ✅ No destructive actions by default
  - ✅ User must explicitly opt-in to `infra_only` or `infra_and_app`
- **Verification:**
  - Check default `nucleus.yaml` — autonomy mode should be safe
  - Verify docs clearly explain how to enable autonomy
  - Test that default config doesn't restart services unexpectedly

**Status:** ⏳ PENDING

#### Test 3.2.2: Laptop vs server mode documentation
- **Setup:** Read docs as new user
- **Expected:**
  - ✅ Docs clearly distinguish "laptop/dev mode" vs "server/production mode"
  - ✅ Clear instructions for enabling daemon mode
  - ✅ Clear instructions for enabling autonomy
  - ✅ Warnings about destructive actions
- **Verification:**
  - Review `TELEMETRY_PIPELINE_README.md` — should have clear mode sections
  - Check for "Quick Start" section with safe defaults
  - Verify "Production Deployment" section with systemd instructions

**Status:** ⏳ PENDING

### 3.3 Error Messages Are Clear

**Objective:** Verify common misconfigurations produce helpful errors.

#### Test 3.3.1: Prometheus not running
- **Setup:** Stop Prometheus, run incident check
- **Expected:**
  - ✅ Clear error: "Prometheus unreachable at http://localhost:9090"
  - ✅ Suggestion: "Start Prometheus with: npm run telemetry:dash"
  - ✅ Link to docs section
  - ❌ NO stack trace or cryptic connection errors
- **Verification:**
  - Check error message format
  - Verify docs link is correct
  - Test that suggestion actually works

**Status:** ⏳ PENDING

#### Test 3.3.2: Missing environment variables
- **Setup:** Unset `NUCLEUS_SLACK_WEBHOOK_URL`, trigger incident
- **Expected:**
  - ✅ Clear message: "Slack webhook not configured (NUCLEUS_SLACK_WEBHOOK_URL)"
  - ✅ Slack notification skipped gracefully
  - ✅ Other actions continue
  - ❌ NO crash or exception
- **Verification:**
  - Check logs for clear message
  - Verify incident still processed
  - Check docs mention optional env vars

**Status:** ⏳ PENDING

#### Test 3.3.3: Docker not running
- **Setup:** Stop Docker, trigger component health check
- **Expected:**
  - ✅ Clear error: "Docker daemon not running or not accessible"
  - ✅ Suggestion: "Start Docker Desktop or check Docker service"
  - ✅ Component marked as unhealthy, not crashed
  - ❌ NO stack trace
- **Verification:**
  - Check error message clarity
  - Verify controller doesn't crash
  - Check docs mention Docker requirement

**Status:** ⏳ PENDING

---

## 4. Validation Execution Plan

### 4.1 Automated Tests (Priority 1)

Create `tests/test_pre_launch_validation.py` with:
- Autonomy mode constraint tests (1.1.1 - 1.1.4)
- Crash-loop defense tests (1.2.1 - 1.2.2)
- State consistency tests (2.2.1 - 2.2.2)
- Partial failure tests (2.3.1 - 2.3.3)
- Error message tests (3.3.1 - 3.3.3)

**Run with:** `pytest tests/test_pre_launch_validation.py -v`

### 4.2 Manual Smoke Procedures (Priority 2)

Document in `TELEMETRY_PIPELINE_README.md` Section 6:
- Rollout safety tests (1.3.1 - 1.3.2)
- Daemon longevity tests (2.1.1 - 2.1.2)
- Fresh install path (3.1.1 - 3.1.2)
- Config defaults verification (3.2.1 - 3.2.2)

**Run before each release.**

### 4.3 Continuous Monitoring (Priority 3)

Set up for production deployments:
- Memory/CPU monitoring dashboard
- State file size alerts
- Incident rate tracking
- Error log aggregation

---

## 5. Sign-Off Checklist

Before publishing to PyPI/npm/GitHub:

- [ ] All automated tests pass (Section 4.1)
- [ ] Manual smoke procedures documented and verified (Section 4.2)
- [ ] Default config is safe for dev machines (Section 3.2)
- [ ] Error messages are clear and actionable (Section 3.3)
- [ ] Docs clearly distinguish laptop vs server mode
- [ ] Autonomy modes correctly constrain actions (Section 1.1)
- [ ] Crash-loop defense prevents infinite restarts (Section 1.2)
- [ ] Rollout safety catches bad releases (Section 1.3)
- [ ] Daemon can run for 4+ hours without issues (Section 2.1)
- [ ] State files remain consistent across operations (Section 2.2)

**Signed off by:** _________________  
**Date:** _________________

---

## 6. Next Steps

1. **Implement automated test suite** (`tests/test_pre_launch_validation.py`)
2. **Run all automated tests** and fix any failures
3. **Execute manual smoke procedures** and document results
4. **Update docs** with clear laptop/server mode instructions
5. **Review error messages** and improve clarity where needed
6. **Final sign-off** by reviewing this checklist
7. **Publish** to PyPI/npm/GitHub

**Estimated time:** 2-3 days for full validation cycle.
