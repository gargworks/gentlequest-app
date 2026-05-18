#!/usr/bin/env bash
# gq_comprehensive_walk.sh — JSON-driven comprehensive UI walk for GentleQuest
#
# Usage:
#   ./scripts/gq_comprehensive_walk.sh            # run all journeys J01-J08
#   ./scripts/gq_comprehensive_walk.sh J01 J04    # run specific journeys
#
# Prerequisites:
#   brew install facebook/fb/idb-companion
#   idb_companion must be in PATH
#   Flutter SDK at SSD path or in PATH
#
# Output:
#   Screenshots: docs/design/refs/screenshots/walks/<J##>/
#   Report:      docs/design/refs/walks/WALK_REPORT.md

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FLUTTER_PROJECT_DIR="${REPO_ROOT}/ai_buddy_web"
WALKS_DIR="${REPO_ROOT}/docs/design/refs/walks"
SCREENSHOTS_BASE="${REPO_ROOT}/docs/design/refs/screenshots/walks"
REPORT_FILE="${WALKS_DIR}/WALK_REPORT.md"
BUNDLE_ID="com.gentlequest.app"
PREFERRED_UDID="95843C74-7CB1-411B-965B-12CCB6F433AF"

# ─── Helpers ─────────────────────────────────────────────────────────────────
log()  { echo "[walk] $*" >&2; }
warn() { echo "[walk][WARN] $*" >&2; }
die()  { echo "[walk][ERROR] $*" >&2; exit "${2:-1}"; }

# ─── Flutter SDK ─────────────────────────────────────────────────────────────
SSD_FLUTTER="/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin/flutter"
if [[ -x "${SSD_FLUTTER}" ]]; then
    FLUTTER="${SSD_FLUTTER}"
else
    FLUTTER="${FLUTTER_BIN:-flutter}"
fi
command -v "${FLUTTER}" &>/dev/null || die "Flutter SDK not found. Set FLUTTER_BIN or add flutter to PATH."

# ─── idb_companion check ─────────────────────────────────────────────────────
ensure_idb_companion() {
    if ! command -v idb_companion &>/dev/null; then
        log "idb_companion not found — installing via brew..."
        brew install facebook/fb/idb-companion || die "brew install idb-companion failed"
    fi
    # Resolve Python idb client
    IDB_CMD=""
    for candidate in \
        "${HOME}/Library/Python/3.9/bin/idb" \
        "${HOME}/Library/Python/3.11/bin/idb" \
        "${HOME}/.local/bin/idb" \
        "idb"; do
        if command -v "${candidate}" &>/dev/null 2>&1; then
            IDB_CMD="${candidate}"
            break
        fi
    done
    [[ -n "${IDB_CMD}" ]] || die "idb Python client not found. Run: pip3 install fb-idb"
    log "idb client: ${IDB_CMD}"
}

# ─── UDID resolution ─────────────────────────────────────────────────────────
resolve_udid() {
    # Try preferred UDID first
    if xcrun simctl list devices available 2>/dev/null | grep -q "${PREFERRED_UDID}"; then
        echo "${PREFERRED_UDID}"
        return
    fi
    # Fall back to any iPhone 16/15/14 Pro
    local udid
    udid=$(xcrun simctl list devices available 2>/dev/null \
        | grep -E "iPhone 1[456] Pro" \
        | grep -v "iPhone 16 Pro Max\|iPhone 15 Pro Max\|iPhone 14 Pro Max" \
        | head -1 \
        | grep -oE '[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}')
    [[ -n "${udid}" ]] || die "No suitable iPhone Pro simulator found. Boot one in Simulator.app first."
    log "Using simulator UDID: ${udid}"
    echo "${udid}"
}

# ─── idb_companion daemon ─────────────────────────────────────────────────────
IDB_COMPANION_PID=""

start_idb_companion() {
    local udid="$1"
    pkill -f "idb_companion.*${udid}" 2>/dev/null || true
    idb_companion --udid "${udid}" &>/tmp/gq_idb_companion.log &
    IDB_COMPANION_PID=$!
    sleep 2
    if ! "${IDB_CMD}" list-targets 2>/dev/null | grep -q "${udid}"; then
        warn "idb companion may not be seeing UDID ${udid}. Continuing anyway."
    fi
    log "idb_companion started (PID ${IDB_COMPANION_PID})"
}

stop_idb_companion() {
    [[ -n "${IDB_COMPANION_PID}" ]] && kill "${IDB_COMPANION_PID}" 2>/dev/null || true
    IDB_COMPANION_PID=""
}

# ─── Simulator boot ───────────────────────────────────────────────────────────
APP_PATH=""

boot_sim() {
    local udid="$1"
    local bypass="$2"

    log "Erasing simulator ${udid}..."
    xcrun simctl terminate "${udid}" "${BUNDLE_ID}" 2>/dev/null || true
    xcrun simctl shutdown "${udid}" 2>/dev/null || true
    sleep 1
    xcrun simctl erase "${udid}" || warn "Erase failed — continuing with current state"
    xcrun simctl boot "${udid}" || die "Failed to boot simulator ${udid}"

    log "Building Flutter app (bypass=${bypass})..."
    (
        cd "${FLUTTER_PROJECT_DIR}"
        "${FLUTTER}" build ios \
            --debug \
            --simulator \
            --no-codesign \
            "--dart-define=DEV_BYPASS_COMPLIANCE=${bypass}" \
            2>&1 | tail -5
    ) || die "Flutter build failed"

    APP_PATH="${FLUTTER_PROJECT_DIR}/build/ios/iphonesimulator/Runner.app"
    [[ -d "${APP_PATH}" ]] || die "Runner.app not found at ${APP_PATH}"

    log "Installing and launching..."
    # Xcode 26.5: simctl install <UDID> hangs; 'booted' works (script always boots exactly one sim)
    xcrun simctl install booted "${APP_PATH}"
    xcrun simctl launch booted "${BUNDLE_ID}"
    sleep 3
    log "App launched"
}

# ─── Action executor ──────────────────────────────────────────────────────────
SHOT_IDX=1

execute_action() {
    local udid="$1"
    local step_json="$2"
    local shot_dir="$3"

    local action
    action=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())['action'])" <<< "${step_json}")

    case "${action}" in
        screenshot)
            local screen_name
            screen_name=$(python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(d.get('screen_name','step'))" <<< "${step_json}")
            local shot_file="${shot_dir}/$(printf '%02d' ${SHOT_IDX})_${screen_name}.png"
            xcrun simctl io "${udid}" screenshot "${shot_file}" && log "Screenshot: ${shot_file}" || warn "Screenshot failed for ${screen_name}"
            (( SHOT_IDX++ ))
            ;;
        tap)
            local x y
            x=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())['x'])" <<< "${step_json}")
            y=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())['y'])" <<< "${step_json}")
            "${IDB_CMD}" ui tap "${x}" "${y}" --udid "${udid}" && sleep 0.3 || warn "Tap failed at ${x},${y}"
            ;;
        wait)
            local ms
            ms=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('duration_ms',500))" <<< "${step_json}")
            sleep "$(python3 -c "print(${ms}/1000.0)")"
            ;;
        type)
            local text
            text=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())['text'])" <<< "${step_json}")
            "${IDB_CMD}" ui text "${text}" --udid "${udid}" || warn "Type failed"
            ;;
        swipe)
            local x1 y1 x2 y2 dur
            x1=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())['x1'])" <<< "${step_json}")
            y1=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())['y1'])" <<< "${step_json}")
            x2=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())['x2'])" <<< "${step_json}")
            y2=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())['y2'])" <<< "${step_json}")
            dur=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('duration_ms',300)/1000.0)" <<< "${step_json}")
            "${IDB_CMD}" ui swipe "${x1}" "${y1}" "${x2}" "${y2}" --duration "${dur}" --udid "${udid}" && sleep 0.3 || warn "Swipe failed"
            ;;
        back)
            # iOS back: swipe from left edge
            "${IDB_CMD}" ui swipe 5 426 150 426 --duration 0.3 --udid "${udid}" && sleep 0.4 || warn "Back gesture failed"
            ;;
        *)
            warn "Unknown action '${action}' — skipping"
            ;;
    esac
}

# ─── Journey runner ───────────────────────────────────────────────────────────
COMPLETED_JOURNEYS=()

run_journey() {
    local journey_id="$1"
    local walk_file="${WALKS_DIR}/walk_${journey_id}.json"
    [[ -f "${walk_file}" ]] || { warn "Walk file not found: ${walk_file}"; return 1; }

    local bypass description
    bypass=$(python3 -c "import json; d=json.load(open('${walk_file}')); print(str(d.get('bypass_compliance',True)).lower())")
    description=$(python3 -c "import json; d=json.load(open('${walk_file}')); print(d.get('description',''))")

    local shot_dir="${SCREENSHOTS_BASE}/${journey_id}"
    mkdir -p "${shot_dir}"
    SHOT_IDX=1

    log "=== Journey ${journey_id}: ${description} ==="

    # Check for pre_run_note
    local pre_note
    pre_note=$(python3 -c "import json; d=json.load(open('${walk_file}')); print(d.get('pre_run_note',''))")
    [[ -n "${pre_note}" ]] && log "PRE-RUN: ${pre_note}"

    local UDID
    UDID=$(resolve_udid)
    boot_sim "${UDID}" "${bypass}"
    start_idb_companion "${UDID}"

    local total_steps
    total_steps=$(python3 -c "import json; d=json.load(open('${walk_file}')); print(len(d['steps']))")

    local step_num=0
    for idx in $(seq 0 $((total_steps - 1))); do
        local step_json
        step_json=$(python3 -c "import json; d=json.load(open('${walk_file}')); print(json.dumps(d['steps'][${idx}]))")
        execute_action "${UDID}" "${step_json}" "${shot_dir}" || warn "Step ${idx} failed"
        (( step_num++ ))
    done

    stop_idb_companion

    log "Journey ${journey_id} complete: ${step_num} steps, $(ls "${shot_dir}"/*.png 2>/dev/null | wc -l | tr -d ' ') screenshots"
    COMPLETED_JOURNEYS+=("${journey_id}")
}

# ─── Report generator ─────────────────────────────────────────────────────────
generate_report() {
    log "Generating WALK_REPORT.md..."
    python3 - "${WALKS_DIR}" "${SCREENSHOTS_BASE}" "${REPORT_FILE}" "${REPO_ROOT}" \
        "${COMPLETED_JOURNEYS[@]}" << 'PYEOF'
import os, sys, json, glob
from datetime import datetime

walks_dir, shots_base, report_path, repo_root = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
completed = sys.argv[5:]

lines = [
    f"# GentleQuest Comprehensive Walk Report\n\n",
    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n",
    f"Journeys run: {', '.join(completed)}\n\n",
]

for jid in sorted(set(completed)):
    walk_file = os.path.join(walks_dir, f"walk_{jid}.json")
    if not os.path.exists(walk_file):
        continue
    d = json.load(open(walk_file))
    lines.append(f"## {jid} — {d['description']}\n\n")
    shot_dir = os.path.join(shots_base, jid)
    shots = sorted(glob.glob(os.path.join(shot_dir, "*.png")))
    if shots:
        lines.append("| # | Screen | Screenshot |\n|---|---|---|\n")
        for i, s in enumerate(shots, 1):
            name = os.path.basename(s).replace(".png", "")
            rel = os.path.relpath(s, repo_root)
            lines.append(f"| {i} | {name} | ![]({rel}) |\n")
    else:
        lines.append("_No screenshots captured for this journey._\n")
    lines.append("\n")

open(report_path, "w").writelines(lines)
print(f"Report written: {report_path}")
PYEOF
}

# ─── Main ─────────────────────────────────────────────────────────────────────
ensure_idb_companion

# Journeys to run: args or default all
if [[ $# -gt 0 ]]; then
    JOURNEYS=("$@")
else
    JOURNEYS=(J01 J02 J03 J04 J05 J06 J07 J08)
fi

for journey in "${JOURNEYS[@]}"; do
    run_journey "${journey}" || warn "Journey ${journey} failed — continuing"
done

generate_report
log "All done. Report: ${REPORT_FILE}"
log "Screenshots: find ${SCREENSHOTS_BASE} -name '*.png' | wc -l"
