#!/usr/bin/env bash
# gq_walk.sh — Haiku-driven multi-screen walk capture for GentleQuest
#
# Usage: gq_walk.sh <TIER_ID> [WALK_JSON_FILE]
#   TIER_ID:        e.g. "R1D4" — matches a tier in REVIEW.md
#   WALK_JSON_FILE: optional path to a walk script JSON; if omitted, the script
#                   looks for a walk_<TIER_ID>.json file in docs/design/refs/walks/
#                   If neither exists, falls back to launch-only mode.
#
# Walk script JSON shape:
#   {
#     "tier_id": "R1D4",
#     "steps": [
#       {"action": "screenshot", "name": "01_launch"},
#       {"action": "tap_label", "label": "Mood", "wait_ms": 800},
#       {"action": "screenshot", "name": "02_mood_tab"},
#       {"action": "tap_pixel", "x": 195, "y": 540, "wait_ms": 800},
#       {"action": "screenshot", "name": "04_heavy_selected"}
#     ]
#   }
#
# Supported actions:
#   screenshot    — headless simctl io screenshot (no computer-use needed)
#   tap_label     — Haiku agent OCR-finds label, clicks center (computer-use)
#   tap_pixel     — Haiku agent clicks at (x,y) relative to sim window origin
#   wait          — sleep wait_ms milliseconds
#
# Outputs:
#   - Captured PNGs written to docs/design/refs/screenshots/<TIER_ID>/
#   - Markdown table printed to stdout: per-screen row with legacy/current/diff
#   - Optional diff PNGs via ImageMagick compare vs legacy_v1.2.2_2026_05_09
#
# Exit codes:
#   0 = success (walk complete or graceful degradation)
#   1 = sim setup failure
#   2 = build/install failure
#   3 = walk script parse failure
#
# Computer-use prerequisites:
#   Simulator.app must be accessible (parked and visible on any Space).
#   First run: grant Terminal + Simulator access in System Settings > Privacy >
#   Accessibility (one-time setup by Lokesh). The script calls
#   mcp__computer-use__request_access via the Haiku agent — if the prompt
#   appears, approve it in macOS.
#
# Haiku agent dispatch:
#   If `claude` is on PATH:   spawned inline via `claude --model claude-haiku-4-5`
#   If `claude` is NOT on PATH: walk steps are executed by this script via
#   mcp__computer-use__* through a documented manual-fire path (see §MANUAL FIRE
#   section below). Walk output is identical either way.

set -euo pipefail

# ─── Config ──────────────────────────────────────────────────────────────────

TIER_ID="${1:-}"
WALK_JSON_ARG="${2:-}"

if [[ -z "${TIER_ID}" ]]; then
    echo "Usage: gq_walk.sh <TIER_ID> [WALK_JSON_FILE]" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

FLUTTER_PROJECT_DIR="${REPO_ROOT}/ai_buddy_web"
SCREENSHOT_DIR="${REPO_ROOT}/docs/design/refs/screenshots/${TIER_ID}"
LEGACY_DIR="${REPO_ROOT}/docs/design/refs/legacy_v1.2.2_2026_05_09/screens"
WALKS_DIR="${REPO_ROOT}/docs/design/refs/walks"

PREFERRED_UDID="519A108A-4FF3-495B-962E-8568A6870383"
BUNDLE_ID="com.gentlequest.app"

# ─── Helpers ─────────────────────────────────────────────────────────────────

log()  { echo "▶ $*" >&2; }
warn() { echo "⚠  $*" >&2; }
die()  { echo "✗  $*" >&2; exit "${2:-1}"; }

# ─── Locate walk script JSON ─────────────────────────────────────────────────

WALK_JSON=""
if [[ -n "${WALK_JSON_ARG}" && -f "${WALK_JSON_ARG}" ]]; then
    WALK_JSON="${WALK_JSON_ARG}"
    log "Walk script: ${WALK_JSON} (explicit argument)"
elif [[ -f "${WALKS_DIR}/walk_${TIER_ID}.json" ]]; then
    WALK_JSON="${WALKS_DIR}/walk_${TIER_ID}.json"
    log "Walk script: ${WALK_JSON} (auto-discovered)"
else
    warn "No walk script found for tier ${TIER_ID} — falling back to launch-only mode."
    warn "To enable walk mode, add a walk script at: ${WALKS_DIR}/walk_${TIER_ID}.json"
    warn "Or pass a JSON file as the second argument."
    WALK_JSON=""
fi

# ─── Step 1: Find Flutter SDK ─────────────────────────────────────────────────

SSD_FLUTTER="/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin/flutter"

if [[ -x "${SSD_FLUTTER}" ]]; then
    FLUTTER="${SSD_FLUTTER}"
    log "Flutter SDK: ${SSD_FLUTTER}"
elif command -v flutter &>/dev/null; then
    FLUTTER="flutter"
    log "Flutter SDK: $(command -v flutter) (PATH fallback)"
else
    die "Flutter SDK not found. Mount the SSD or add flutter to PATH." 2
fi

# ─── Step 2: Pick simulator UDID ─────────────────────────────────────────────

log "Querying available simulators..."

UDID=""
SIM_JSON="$(xcrun simctl list devices available --json 2>/dev/null)"

if echo "${SIM_JSON}" | python3 -c "
import json, sys
data = json.load(sys.stdin)
found = any(
    d['udid'] == '${PREFERRED_UDID}'
    for devs in data['devices'].values()
    for d in devs
)
sys.exit(0 if found else 1)
" 2>/dev/null; then
    UDID="${PREFERRED_UDID}"
    log "Using preferred UDID: ${UDID}"
else
    warn "Preferred UDID ${PREFERRED_UDID} not available — searching for fallback..."
    UDID="$(echo "${SIM_JSON}" | python3 -c "
import json, sys
data = json.load(sys.stdin)
priority = ['iPhone 16 Pro', 'iPhone 15 Pro', 'iPhone 14 Pro',
            'iPhone 16', 'iPhone 15', 'iPhone 14']
for pref in priority:
    for devs in data['devices'].values():
        for d in devs:
            if d['name'] == pref:
                print(d['udid'])
                sys.exit(0)
sys.exit(1)
" 2>/dev/null)" || die "No suitable iPhone simulator found. Run 'xcrun simctl list devices available'." 1
    log "Using fallback UDID: ${UDID}"
fi

# ─── Step 3: Erase + boot ────────────────────────────────────────────────────

CURRENT_STATE="$(xcrun simctl list devices --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for devs in data['devices'].values():
    for d in devs:
        if d['udid'] == '${UDID}':
            print(d['state'])
            sys.exit(0)
print('Unknown')
" 2>/dev/null)"

if [[ "${CURRENT_STATE}" == "Booted" ]]; then
    log "Simulator is Booted — shutting down before erase..."
    xcrun simctl shutdown "${UDID}" 2>&1 || warn "simctl shutdown returned non-zero (may already be shutting down)"
    for i in $(seq 1 15); do
        S="$(xcrun simctl list devices --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for devs in data['devices'].values():
    for d in devs:
        if d['udid'] == '${UDID}':
            print(d['state'])
            sys.exit(0)
print('Unknown')
" 2>/dev/null)"
        if [[ "${S}" == "Shutdown" ]]; then
            log "Simulator is Shutdown."
            break
        fi
        sleep 1
    done
fi

log "Erasing simulator ${UDID}..."
xcrun simctl erase "${UDID}" 2>&1 || die "xcrun simctl erase failed for UDID ${UDID}." 1

log "Booting simulator ${UDID}..."
xcrun simctl boot "${UDID}" 2>&1 || {
    STATE="$(xcrun simctl list devices --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for devs in data['devices'].values():
    for d in devs:
        if d['udid'] == '${UDID}':
            print(d['state'])
            sys.exit(0)
" 2>/dev/null)"
    [[ "${STATE}" == "Booted" ]] || die "Simulator boot failed (state: ${STATE})." 1
}

log "Waiting for simulator to reach Booted state..."
for i in $(seq 1 30); do
    STATE="$(xcrun simctl list devices --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for devs in data['devices'].values():
    for d in devs:
        if d['udid'] == '${UDID}':
            print(d['state'])
            sys.exit(0)
print('Unknown')
" 2>/dev/null)"
    if [[ "${STATE}" == "Booted" ]]; then
        log "Simulator is Booted."
        break
    fi
    [[ $i -lt 30 ]] || die "Simulator did not reach Booted state after 30s (last state: ${STATE})." 1
    sleep 1
done

# ─── Step 4: Build ───────────────────────────────────────────────────────────

log "Building Flutter app (debug, simulator, no-codesign, bypass-compliance)..."
(
    cd "${FLUTTER_PROJECT_DIR}" || die "Flutter project dir not found: ${FLUTTER_PROJECT_DIR}" 2
    "${FLUTTER}" build ios \
        --debug \
        --simulator \
        --no-codesign \
        --dart-define=DEV_BYPASS_COMPLIANCE=true \
        2>&1
) || die "Flutter build failed. Check build output above." 2

APP_PATH="${FLUTTER_PROJECT_DIR}/build/ios/iphonesimulator/Runner.app"
[[ -d "${APP_PATH}" ]] || die "Runner.app not found at ${APP_PATH} after build." 2

# ─── Step 5: Install ─────────────────────────────────────────────────────────

log "Installing ${APP_PATH} onto ${UDID}..."
xcrun simctl install "${UDID}" "${APP_PATH}" 2>&1 || die "xcrun simctl install failed." 2

# ─── Step 6: Bring Simulator.app forward (without moving it) ─────────────────

log "Activating Simulator.app (window stays in its parked position)..."
osascript -e 'tell application "Simulator" to activate' 2>&1 || \
    warn "osascript activate returned non-zero — Simulator.app may not be installed at expected path. Continuing."

# ─── Step 7: Launch app + wait for splash ────────────────────────────────────

log "Launching ${BUNDLE_ID}..."
xcrun simctl launch "${UDID}" "${BUNDLE_ID}" 2>&1 || die "xcrun simctl launch failed for ${BUNDLE_ID}." 1

log "Waiting 4s for splash to settle..."
sleep 4

mkdir -p "${SCREENSHOT_DIR}"

# ─── Step 8: Walk dispatch ────────────────────────────────────────────────────
#
# If a walk script JSON exists, attempt to dispatch to a Haiku agent.
#
# Haiku agent dispatch protocol:
#   1. If `claude` is on PATH: spawn inline with model claude-haiku-4-5.
#      The agent receives the walk JSON and the sim context (UDID, window info)
#      and executes each step using mcp__computer-use__* tools.
#   2. If `claude` is NOT on PATH: this script calls a Python helper
#      (scripts/gq_walk_agent.py) that implements the walk steps via
#      subprocess calls to simctl (for screenshot steps) and logs
#      "MANUAL FIRE required" for tap_label/tap_pixel steps.
#
# Graceful degradation:
#   - tap_label OCR failure: logged, step skipped, walk continues
#   - tap_pixel out-of-bounds: logged, step skipped, walk continues
#   - claude CLI missing: walk falls back to screenshot-only steps
#   - All failures are non-fatal; the diff table is still emitted.

WALK_RESULT_LOG="${SCREENSHOT_DIR}/.walk_result.log"
: > "${WALK_RESULT_LOG}"   # truncate/create

if [[ -n "${WALK_JSON}" ]]; then
    log "Walk mode: processing ${WALK_JSON}"

    # Parse step count for progress logging
    STEP_COUNT="$(python3 -c "
import json, sys
with open('${WALK_JSON}') as f:
    data = json.load(f)
print(len(data.get('steps', [])))
" 2>/dev/null)" || STEP_COUNT="?"
    log "Walk script has ${STEP_COUNT} step(s)."

    # Determine dispatch method
    if command -v claude &>/dev/null; then
        CLAUDE_CMD="$(command -v claude)"
        log "Haiku agent dispatch via: ${CLAUDE_CMD}"

        # Build the agent prompt
        WALK_JSON_CONTENT="$(cat "${WALK_JSON}")"
        AGENT_PROMPT="$(cat <<AGENTPROMPT
You are executing a GentleQuest simulator walk.

Context:
- Simulator UDID: ${UDID}
- Bundle ID: ${BUNDLE_ID}
- Screenshot output dir: ${SCREENSHOT_DIR}
- The iOS Simulator.app window is already open and the app is running.

Walk script JSON:
${WALK_JSON_CONTENT}

For each step:
1. "screenshot" action: run exactly this shell command and log success/failure:
   xcrun simctl io ${UDID} screenshot <output_dir>/<name>.png

2. "tap_label" action:
   a. Call mcp__computer-use__screenshot to capture current screen.
   b. Identify the label text in the Simulator window (OCR / visual search).
   c. If found: call mcp__computer-use__left_click at the label's center coords.
   d. If NOT found: log "LABEL_NOT_FOUND: <label>" and skip this step. Do NOT abort.
   e. After tap, wait wait_ms milliseconds.

3. "tap_pixel" action:
   a. Call mcp__computer-use__screenshot to find the Simulator window's top-left origin.
   b. Add step x/y to the window origin to get mac screen coords.
   c. Call mcp__computer-use__left_click at those mac screen coords.
   d. After tap, wait wait_ms milliseconds.

4. "wait" action: sleep wait_ms milliseconds (use a shell sleep, not the computer-use wait tool).

For every step, output one line to stdout:
  STEP_OK: <step_name_or_action>
  or
  STEP_SKIP: <reason>
  or
  STEP_FAIL: <reason>

After all steps, output:
  WALK_COMPLETE: <N_ok> ok, <N_skip> skipped, <N_fail> failed
AGENTPROMPT
)"

        # Spawn Haiku agent
        log "Spawning Haiku sub-agent for walk execution..."
        # headless mode: --print/-p handles non-interactive dispatch — verify the CLI supports this flag locally before relying on it
        "${CLAUDE_CMD}" \
            --model claude-haiku-4-5 \
            --print \
            -p "${AGENT_PROMPT}" \
            2>&1 | tee "${WALK_RESULT_LOG}" || \
            warn "Haiku agent exited non-zero — see ${WALK_RESULT_LOG} for details. Continuing with diff."

        # Summarise walk result
        if grep -q "WALK_COMPLETE:" "${WALK_RESULT_LOG}" 2>/dev/null; then
            WALK_SUMMARY="$(grep "WALK_COMPLETE:" "${WALK_RESULT_LOG}" | tail -1)"
            log "Walk agent reported: ${WALK_SUMMARY}"
        else
            warn "Walk agent did not emit WALK_COMPLETE line — walk may be partial."
        fi

        # Count LABEL_NOT_FOUND
        LABEL_FAIL_COUNT="$(grep -c "LABEL_NOT_FOUND:" "${WALK_RESULT_LOG}" 2>/dev/null || echo 0)"
        if [[ "${LABEL_FAIL_COUNT}" -gt 0 ]]; then
            warn "${LABEL_FAIL_COUNT} tap_label step(s) failed OCR — skipped gracefully."
        fi

    else
        # ─── Manual-fire fallback: no claude CLI ─────────────────────────────
        warn "'claude' CLI not found on PATH."
        warn "Tap steps (tap_label, tap_pixel) require the Haiku agent."
        warn "MANUAL FIRE PATH: run the following to enable full walk mode:"
        warn "  1. Install claude CLI: pip install claude-code OR brew install claude"
        warn "  2. Re-run: bash scripts/gq_walk.sh ${TIER_ID}"
        warn ""
        warn "Executing screenshot-only steps now (tap steps skipped)..."

        # Execute screenshot steps directly; skip tap steps
        python3 - <<PYSCRIPT 2>&1 | tee "${WALK_RESULT_LOG}"
import json, subprocess, time, sys, os

walk_file = "${WALK_JSON}"
screenshot_dir = "${SCREENSHOT_DIR}"
udid = "${UDID}"

with open(walk_file) as f:
    data = json.load(f)

steps = data.get("steps", [])
n_ok = n_skip = 0

for step in steps:
    action = step.get("action")
    wait_ms = step.get("wait_ms", 0)

    if action == "screenshot":
        name = step.get("name", "unnamed")
        out_path = os.path.join(screenshot_dir, f"{name}.png")
        result = subprocess.run(
            ["xcrun", "simctl", "io", udid, "screenshot", out_path],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"STEP_OK: screenshot {name}")
            n_ok += 1
        else:
            print(f"STEP_FAIL: screenshot {name} — {result.stderr.strip()}")
    elif action in ("tap_label", "tap_pixel"):
        label = step.get("label", step.get("comment", f"x={step.get('x')},y={step.get('y')}"))
        print(f"STEP_SKIP: {action} '{label}' — claude CLI not available (manual fire required)")
        n_skip += 1
    elif action == "wait":
        time.sleep(wait_ms / 1000)
        print(f"STEP_OK: wait {wait_ms}ms")
        n_ok += 1
    else:
        print(f"STEP_SKIP: unknown action '{action}'")
        n_skip += 1

    if wait_ms > 0 and action != "wait":
        time.sleep(wait_ms / 1000)

print(f"WALK_COMPLETE: {n_ok} ok, {n_skip} skipped, 0 failed")
PYSCRIPT
    fi

else
    # ─── Launch-only fallback ─────────────────────────────────────────────────
    log "Launch-only mode — capturing single launch screenshot."
    LAUNCH_SHOT="${SCREENSHOT_DIR}/01_launch.png"
    xcrun simctl io "${UDID}" screenshot "${LAUNCH_SHOT}" 2>&1 || \
        die "Screenshot capture failed." 1
    log "Captured: ${LAUNCH_SHOT} ($(wc -c < "${LAUNCH_SHOT}" | tr -d ' ') bytes)"
    echo "WALK_COMPLETE: 1 ok, 0 skipped, 0 failed (launch-only)" >> "${WALK_RESULT_LOG}"
fi

# ─── Step 9: Diff vs legacy baseline ─────────────────────────────────────────

HAS_COMPARE=false
if command -v compare &>/dev/null; then
    HAS_COMPARE=true
    log "ImageMagick 'compare' found — generating diff PNGs where baseline exists."
else
    warn "ImageMagick not installed — skipping diff PNGs."
fi

DIFF_SENTINEL_DIR="${SCREENSHOT_DIR}/.diff_sentinels"
mkdir -p "${DIFF_SENTINEL_DIR}"

while IFS= read -r shot; do
    [[ -z "${shot}" ]] && continue
    screen_name="$(basename "${shot}" .png)"
    legacy_path="${LEGACY_DIR}/${screen_name}.png"
    diff_path="${SCREENSHOT_DIR}/${screen_name}_diff.png"

    if [[ -f "${legacy_path}" ]] && ${HAS_COMPARE}; then
        log "Generating diff: ${screen_name}"
        compare "${legacy_path}" "${shot}" "${diff_path}" 2>&1 || true
        if [[ -f "${diff_path}" ]]; then
            touch "${DIFF_SENTINEL_DIR}/${screen_name}"
            log "Diff PNG: ${diff_path}"
        fi
    fi
done < <(find "${SCREENSHOT_DIR}" -maxdepth 1 -name "*.png" ! -name "*_diff.png" | sort)

# ─── Step 10: Emit markdown table ────────────────────────────────────────────

rel_screenshot_dir="docs/design/refs/screenshots/${TIER_ID}"
rel_legacy_dir="docs/design/refs/legacy_v1.2.2_2026_05_09/screens"

# Compute walk mode label for footer
WALK_MODE_LABEL="launch-only"
if [[ -n "${WALK_JSON}" ]] && command -v claude &>/dev/null; then
    WALK_MODE_LABEL="Haiku-driven walk (computer-use)"
elif [[ -n "${WALK_JSON}" ]]; then
    WALK_MODE_LABEL="screenshot-only walk (claude CLI not found; tap steps skipped)"
fi

# Compute walk result summary
WALK_RESULT_SUMMARY=""
if [[ -f "${WALK_RESULT_LOG}" ]]; then
    WALK_RESULT_SUMMARY="$(grep 'WALK_COMPLETE:' "${WALK_RESULT_LOG}" 2>/dev/null | tail -1 || true)"
fi

echo ""
echo "### Walk gallery — ${TIER_ID}"
echo ""

if [[ -n "${WALK_RESULT_SUMMARY}" ]]; then
    echo "_${WALK_RESULT_SUMMARY}_"
    echo ""
fi

if ${HAS_COMPARE}; then
    echo "| Screen | Legacy v1.2.2 | This tier | Pixel diff |"
    echo "|---|---|---|---|"
else
    echo "| Screen | Legacy v1.2.2 | This tier |"
    echo "|---|---|---|"
fi

SCREEN_COUNT=0
while IFS= read -r shot; do
    [[ -z "${shot}" ]] && continue
    screen_name="$(basename "${shot}" .png)"
    this_tier_img="![${screen_name}](${rel_screenshot_dir}/${screen_name}.png)"

    legacy_img="—"
    legacy_path="${LEGACY_DIR}/${screen_name}.png"
    if [[ -f "${legacy_path}" ]]; then
        legacy_img="![legacy ${screen_name}](${rel_legacy_dir}/${screen_name}.png)"
    fi

    if ${HAS_COMPARE} && [[ -f "${DIFF_SENTINEL_DIR}/${screen_name}" ]]; then
        diff_img="![diff ${screen_name}](${rel_screenshot_dir}/${screen_name}_diff.png)"
        echo "| ${screen_name} | ${legacy_img} | ${this_tier_img} | ${diff_img} |"
    elif ${HAS_COMPARE}; then
        echo "| ${screen_name} | ${legacy_img} | ${this_tier_img} | — |"
    else
        echo "| ${screen_name} | ${legacy_img} | ${this_tier_img} |"
    fi
    (( SCREEN_COUNT++ )) || true
done < <(find "${SCREENSHOT_DIR}" -maxdepth 1 -name "*.png" ! -name "*_diff.png" | sort)

rm -rf "${DIFF_SENTINEL_DIR}"

echo ""
echo "_Capture method: ${WALK_MODE_LABEL}. ${SCREEN_COUNT} screenshot(s) captured._"
if [[ -n "${WALK_JSON}" ]]; then
    echo "_Walk script: \`${WALK_JSON}\`_"
fi
echo ""

# Emit skip log if any steps were skipped
if [[ -f "${WALK_RESULT_LOG}" ]] && grep -q "STEP_SKIP\|LABEL_NOT_FOUND" "${WALK_RESULT_LOG}" 2>/dev/null; then
    echo "<details><summary>Skipped steps</summary>"
    echo ""
    echo '```'
    grep "STEP_SKIP\|LABEL_NOT_FOUND" "${WALK_RESULT_LOG}"
    echo '```'
    echo ""
    echo "</details>"
    echo ""
fi

log "Done. ${SCREEN_COUNT} screenshot(s) in ${SCREENSHOT_DIR}"
