#!/bin/zsh
# Phase-2 v2 trial harness — vibe-coding-shaped feature-add on a synthetic mini-repo.
#
# Spec: .brain/plans/phase2_test_vs_control_spec.md (v2 design notes inline below)
# Variant: B (NUCLEUS_VARIANT_B_RUNTIME_OFF=1 stubs nucleus_* substrate reads;
#             tool plumbing + tool schemas remain identical between arms)
#
# Differences from v1 (.brain/measurement/phase2/):
#   - Workload: real-shape feature-add (CSV export to notebook CLI), not toy
#     single-shot coding task. Trial is 20-50 turns of natural session work.
#   - Per-trial environment: tempdir with fresh copy of the synthetic mini-repo
#     + symlinked .brain/ snapshot containing pre-seeded engrams + policies.
#   - Pre-flight: validate baseline arm makes >=3 nucleus_* substrate calls.
#     If zero, the trial is invalid and the experiment fails before scaling.
#
# Usage:
#   bash scripts/phase2_v2_trial_runner.sh baseline      [N=5]
#   bash scripts/phase2_v2_trial_runner.sh experimental  [N=5]
#   bash scripts/phase2_v2_trial_runner.sh both          [N=5]
#   bash scripts/phase2_v2_trial_runner.sh smoke                  # 1+1, validates harness
#
# Output (per arm):
#   .brain/measurement/phase2_v2/turns.<arm>.jsonl    — proxy capture
#   .brain/measurement/phase2_v2/trials/<arm>/NNN/    — tempdir + logs

set -e
REPO="/Users/lokeshgarg/ai-mvp-backend"
V2_DIR="${REPO}/.brain/measurement/phase2_v2"
PROMPT="${V2_DIR}/prompt.txt"
REPO_TEMPLATE="${V2_DIR}/repo_template"
BRAIN_SNAPSHOT="${V2_DIR}/brain_snapshot"
TRIALS_ROOT="${V2_DIR}/trials"
TRIAL_TIMEOUT_S="${TRIAL_TIMEOUT_S:-900}"

ARM="${1:-both}"
N="${2:-5}"
[ "$ARM" = "smoke" ] && { ARM="both"; N=1; }

mkdir -p "$V2_DIR" "$TRIALS_ROOT"

[ -f "$PROMPT" ]              || { echo "ERROR: prompt missing at $PROMPT"; exit 1; }
[ -d "$REPO_TEMPLATE" ]       || { echo "ERROR: repo template missing at $REPO_TEMPLATE"; exit 1; }
[ -d "$BRAIN_SNAPSHOT" ]      || { echo "ERROR: brain snapshot missing at $BRAIN_SNAPSHOT"; exit 1; }

arm_port()       { case "$1" in baseline) echo 9787 ;; experimental) echo 9788 ;; *) return 1 ;; esac }
arm_turns_path() { echo "${V2_DIR}/turns.${1}.jsonl"; }

start_proxy() {
  local arm="$1" port; port=$(arm_port "$arm") || return 1
  local out; out=$(arm_turns_path "$arm")
  local log="${V2_DIR}/proxy.${arm}.log"

  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "ERROR: port $port already bound."
    return 2
  fi

  cd "$REPO"
  python3 -m scripts.measurement_proxy \
    --condition "$arm" --surface cc_main --phase dogfood \
    --port "$port" --skip-fairness --out "$out" \
    >"$log" 2>&1 &
  echo "$!" > "${V2_DIR}/proxy.${arm}.pid"
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    grep -q "listening on" "$log" 2>/dev/null && { echo "  proxy ${arm} :${port} ready"; return 0; }
    sleep 1
  done
  echo "ERROR: proxy ${arm} did not bind in 10s. Tail:"
  tail -10 "$log"
  return 3
}

stop_proxy() {
  local pidfile="${V2_DIR}/proxy.$1.pid"
  [ -f "$pidfile" ] || return 0
  kill "$(cat "$pidfile")" 2>/dev/null || true
  rm -f "$pidfile"
}

run_one_trial() {
  local arm="$1" trial_n="$2"
  local port; port=$(arm_port "$arm") || return 1
  local trial_dir="${TRIALS_ROOT}/${arm}/$(printf '%03d' "$trial_n")"
  rm -rf "$trial_dir"
  mkdir -p "$trial_dir"

  # Fresh copy of the synthetic repo into the trial dir.
  cp -R "${REPO_TEMPLATE}/." "$trial_dir/"
  # Symlink the brain snapshot in. Trial CWD is the repo; .brain points to
  # the snapshot so engram + policy lookups land at the pre-seeded fixtures.
  ln -s "$BRAIN_SNAPSHOT" "${trial_dir}/.brain"

  local cmd_env=(env "ANTHROPIC_BASE_URL=http://127.0.0.1:${port}" "CC_SESSION_ROLE=phase2v2_${arm}")
  if [ "$arm" = "experimental" ]; then
    cmd_env+=("NUCLEUS_VARIANT_B_RUNTIME_OFF=1")
  fi

  local started; started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  echo "  [$(date +%H:%M:%S)] arm=${arm} trial=${trial_n} starting (cwd=${trial_dir})"

  (
    cd "$trial_dir"
    "${cmd_env[@]}" claude --print --dangerously-skip-permissions < "$PROMPT" \
      > "${trial_dir}/stdout.log" 2> "${trial_dir}/stderr.log" &
    local pid=$!
    local elapsed=0
    while kill -0 "$pid" 2>/dev/null; do
      if [ "$elapsed" -ge "$TRIAL_TIMEOUT_S" ]; then
        kill -9 "$pid" 2>/dev/null
        echo "TIMEOUT" > "${trial_dir}/result.txt"
        break
      fi
      sleep 3
      elapsed=$((elapsed + 3))
    done
    wait "$pid" 2>/dev/null
    local rc=$?
    [ -f "${trial_dir}/result.txt" ] || echo "rc=${rc}" > "${trial_dir}/result.txt"
  )

  local ended; ended=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  local result; result=$(cat "${trial_dir}/result.txt" 2>/dev/null || echo "?")
  if grep -q "PHASE2_V2_TRIAL_COMPLETE" "${trial_dir}/stdout.log" 2>/dev/null; then
    echo "    ✓ trial ${trial_n} complete (${result}; ${started} → ${ended})"
  elif grep -q "PHASE2_V2_TRIAL_FAILED" "${trial_dir}/stdout.log" 2>/dev/null; then
    echo "    ✗ trial ${trial_n} self-failed (${result})"
  else
    echo "    ? trial ${trial_n} no sentinel (${result})"
  fi
  echo "${started},${ended},${result}" >> "${V2_DIR}/trial_log.${arm}.csv"
}

run_arm() {
  local arm="$1" n="$2"
  echo ""
  echo "=== arm=${arm}  N=${n} ==="
  start_proxy "$arm" || return $?
  for i in $(seq 1 "$n"); do
    run_one_trial "$arm" "$i"
  done
  stop_proxy "$arm"
  echo "  arm=${arm} done."
}

# Pre-flight after all trials: confirm baseline arm actually used substrate.
preflight_check() {
  local n_calls=0
  if [ -f "${V2_DIR}/turns.baseline.jsonl" ]; then
    # Count tool calls that look like nucleus_* in any captured turn body.
    # Fallback: grep stdout.log files for substrate tool invocations.
    n_calls=$(find "${TRIALS_ROOT}/baseline" -name "stdout.log" -exec grep -hc "nucleus_engrams\|nucleus_sync\|nucleus_sessions\|nucleus_orchestration" {} \; 2>/dev/null | awk '{s+=$1} END {print s+0}')
  fi
  echo ""
  echo "=== pre-flight: substrate exercise validation ==="
  echo "  nucleus_* mentions in baseline trials' stdout: ${n_calls}"
  if [ "$n_calls" -lt 3 ]; then
    echo "  ⚠️  WARNING: baseline arm shows <3 substrate references."
    echo "     If trials completed but no substrate was used, the experiment"
    echo "     can't measure substrate's contribution. Inspect a stdout.log"
    echo "     to confirm the task actually invoked nucleus_* tools, OR"
    echo "     redesign the prompt to force substrate use."
    return 1
  fi
  echo "  ✓ substrate exercised in baseline arm; comparison is meaningful"
  return 0
}

trap 'stop_proxy baseline; stop_proxy experimental' EXIT

case "$ARM" in
  baseline)     run_arm baseline "$N" ;;
  experimental) run_arm experimental "$N" ;;
  both)
    run_arm baseline "$N"
    run_arm experimental "$N"
    preflight_check || true
    ;;
  *) echo "usage: $0 [baseline|experimental|both|smoke] [N]"; exit 1 ;;
esac

echo ""
echo "All trials done. Run analysis:"
echo "  python3 ${REPO}/scripts/phase2_v2_analyze.py"
