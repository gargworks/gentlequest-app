#!/bin/zsh
# Phase-2 (test vs control) trial harness for the Nucleus measurement experiment.
#
# Spec: .brain/plans/phase2_test_vs_control_spec.md
# Variant: B (NUCLEUS_VARIANT_B_RUNTIME_OFF=1 disables substrate reads while
#             keeping tool plumbing identical between arms)
# Workload: pre-registered coding task at .brain/measurement/phase2_prompt.txt
# Cadence: back-to-back batch (one arm fully run, then the other)
# Runner: scripted (this file)
#
# Usage:
#   bash scripts/phase2_trial_runner.sh baseline      [N=10]   # control arm
#   bash scripts/phase2_trial_runner.sh experimental  [N=10]   # Variant B arm
#   bash scripts/phase2_trial_runner.sh both          [N=10]   # all baseline then all experimental
#
# Outputs (per arm):
#   .brain/measurement/phase2/turns.<arm>.jsonl         — proxy capture
#   .brain/measurement/phase2/trials/<arm>/<N>/         — tempdir + stdout/stderr per trial
#
# Each trial:
#   1. Spin up a fresh proxy on a phase-2-only port (9787 baseline / 9788 experimental).
#   2. Create a clean tempdir for CC to work in.
#   3. Run `claude --print --dangerously-skip-permissions` with the frozen prompt.
#   4. Wait for completion sentinel ("PHASE2_TRIAL_COMPLETE" or "PHASE2_TRIAL_FAILED")
#      OR a hard wall timeout (default 300s).
#   5. Tear down proxy. Move to next trial.
#
# This keeps the same `--condition` / `--phase` semantics as the existing
# 8787/8788 proxies but tags trials separately so they don't pollute the
# Phase-1 capture.

set -e
REPO="/Users/lokeshgarg/ai-mvp-backend"
PROMPT="${REPO}/.brain/measurement/phase2_prompt.txt"
OUT_ROOT="${REPO}/.brain/measurement/phase2"
TRIALS_ROOT="${OUT_ROOT}/trials"
TRIAL_TIMEOUT_S="${TRIAL_TIMEOUT_S:-300}"

ARM="${1:-both}"
N="${2:-10}"

mkdir -p "$OUT_ROOT" "$TRIALS_ROOT"

if [ ! -f "$PROMPT" ]; then
  echo "ERROR: pre-registered prompt missing at $PROMPT"
  exit 1
fi

# ── Per-arm config ───────────────────────────────────────────────────────
arm_port() {
  case "$1" in
    baseline)     echo 9787 ;;
    experimental) echo 9788 ;;
    *) echo "unknown arm: $1" >&2; return 1 ;;
  esac
}
arm_turns_path() { echo "${OUT_ROOT}/turns.${1}.jsonl"; }

# ── Proxy lifecycle ──────────────────────────────────────────────────────
start_proxy() {
  local arm="$1"; local port; port=$(arm_port "$arm") || return 1
  local out; out=$(arm_turns_path "$arm")

  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "ERROR: port $port already bound. lsof -nP -iTCP:$port -sTCP:LISTEN to find PID."
    return 2
  fi

  cd "$REPO"
  local log="${OUT_ROOT}/proxy.${arm}.log"
  python3 -m scripts.measurement_proxy \
    --condition "$arm" \
    --surface cc_main \
    --phase dogfood \
    --port "$port" \
    --skip-fairness \
    --out "$out" \
    >"$log" 2>&1 &
  local pid=$!
  echo "$pid" > "${OUT_ROOT}/proxy.${arm}.pid"

  # Wait up to 10s for "listening on" line
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if grep -q "listening on" "$log" 2>/dev/null; then
      echo "  proxy ${arm} :${port} ready (pid=$pid)"
      return 0
    fi
    sleep 1
  done
  echo "ERROR: proxy ${arm} did not bind in 10s. Tail of log:"
  tail -20 "$log"
  return 3
}

stop_proxy() {
  local arm="$1"
  local pidfile="${OUT_ROOT}/proxy.${arm}.pid"
  [ -f "$pidfile" ] || return 0
  local pid; pid=$(cat "$pidfile")
  kill "$pid" 2>/dev/null || true
  rm -f "$pidfile"
}

# ── Single trial ─────────────────────────────────────────────────────────
run_one_trial() {
  local arm="$1"; local trial_n="$2"
  local port; port=$(arm_port "$arm") || return 1
  local trial_dir="${TRIALS_ROOT}/${arm}/$(printf '%03d' "$trial_n")"
  mkdir -p "$trial_dir"

  local cmd_env=(env "ANTHROPIC_BASE_URL=http://127.0.0.1:${port}" "CC_SESSION_ROLE=phase2_${arm}")
  if [ "$arm" = "experimental" ]; then
    cmd_env+=("NUCLEUS_VARIANT_B_RUNTIME_OFF=1")
  fi

  local started; started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  echo "  [$(date +%H:%M:%S)] arm=${arm} trial=${trial_n} starting (cwd=${trial_dir})"

  # Run claude --print in the trial dir, with the prompt on stdin.
  # Wall timeout via background-and-wait pattern (BSD doesn't have `timeout`).
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
        return 124
      fi
      sleep 2
      elapsed=$((elapsed + 2))
    done
    wait "$pid"
    local rc=$?
    echo "rc=${rc}" > "${trial_dir}/result.txt"
  )

  local ended; ended=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  local result; result=$(cat "${trial_dir}/result.txt" 2>/dev/null || echo "?")
  if grep -q "PHASE2_TRIAL_COMPLETE" "${trial_dir}/stdout.log" 2>/dev/null; then
    echo "    ✓ trial ${trial_n} complete (${result}; ${started} → ${ended})"
  elif grep -q "PHASE2_TRIAL_FAILED" "${trial_dir}/stdout.log" 2>/dev/null; then
    echo "    ✗ trial ${trial_n} self-failed (${result})"
  else
    echo "    ? trial ${trial_n} no sentinel (${result}) — see stdout.log"
  fi
  echo "${started},${ended},${result}" >> "${OUT_ROOT}/trial_log.${arm}.csv"
}

# ── Per-arm batch ────────────────────────────────────────────────────────
run_arm() {
  local arm="$1"; local n="$2"
  echo ""
  echo "=== arm=${arm}  N=${n} ==="
  start_proxy "$arm" || return $?
  local i
  for i in $(seq 1 "$n"); do
    run_one_trial "$arm" "$i"
  done
  stop_proxy "$arm"
  echo "  arm=${arm} done. proxy stopped."
}

# ── Top-level dispatch ───────────────────────────────────────────────────
trap 'stop_proxy baseline; stop_proxy experimental' EXIT

case "$ARM" in
  baseline)     run_arm baseline "$N" ;;
  experimental) run_arm experimental "$N" ;;
  both)
    run_arm baseline "$N"
    run_arm experimental "$N"
    ;;
  *) echo "usage: $0 [baseline|experimental|both] [N]"; exit 1 ;;
esac

echo ""
echo "All trials done. Run analysis with:"
echo "  python3 ${REPO}/scripts/phase2_analyze.py"
