#!/usr/bin/env bash
# gq_screenshot_diff.sh — headless screenshot capture + markdown diff emitter
#
# Usage: gq_screenshot_diff.sh [TIER_NAME]
#   TIER_NAME: e.g. "tier-1.4-onboarding" — used in screenshot file names
#
# Outputs:
#   - Captured PNGs written to docs/design/refs/screenshots/<TIER_NAME>/
#   - Markdown block printed to stdout for paste into a PR body
#   - Optional side-by-side diff PNGs via ImageMagick compare (if installed)
#     compared against legacy_v1.2.2_2026_05_09 baseline
#
# Exit codes:
#   0 = success
#   1 = sim setup failure (UDID not found, erase/boot failed)
#   2 = build/install failure (Flutter SDK missing, build error, install error)
#
# Capture method: headless `simctl io screenshot` after fresh sim erase.
# Walk-mode: WALK_STEPS array is defined below but empty in v1.
#   Once idb_companion is installed, add entries like:
#     WALK_STEPS+=("tap:375:450:onboarding_welcome")
#   Each entry format: "<action>:<x>:<y>:<screen_name>"
#   The loop at the bottom of the capture section iterates these automatically.

set -euo pipefail

# ─── Config ─────────────────────────────────────────────────────────────────

TIER_NAME="${1:-tier-unnamed}"

# Resolve the repo root (script may be called from any CWD)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

FLUTTER_PROJECT_DIR="${REPO_ROOT}/ai_buddy_web"
SCREENSHOT_DIR="${REPO_ROOT}/docs/design/refs/screenshots/${TIER_NAME}"
LEGACY_DIR="${REPO_ROOT}/docs/design/refs/legacy_v1.2.2_2026_05_09/screens"

# Known target UDID (iPhone 16 Pro, iOS 18.5)
PREFERRED_UDID="519A108A-4FF3-495B-962E-8568A6870383"
BUNDLE_ID="com.gentlequest.app"

# ─── Walk steps (v1: empty — add idb taps here once idb_companion is installed)
# Format per entry: "<action>:<arg1>:<arg2>:<screen_name>"
# Example once idb lands:
#   WALK_STEPS+=("tap:375:450:02_onboarding_welcome")
#   WALK_STEPS+=("tap:375:700:03_onboarding_name")
# The capture loop below iterates this array automatically.
WALK_STEPS=()

# ─── Helpers ─────────────────────────────────────────────────────────────────

log()  { echo "▶ $*" >&2; }
warn() { echo "⚠ $*" >&2; }
die()  { echo "✗ $*" >&2; exit "${2:-1}"; }

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

# Try preferred UDID first, then fall back to any iPhone 16/15/14 Pro
UDID=""
SIM_JSON="$(xcrun simctl list devices available --json 2>/dev/null)"

# Check preferred UDID is listed as available
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
import json, sys, re
data = json.load(sys.stdin)
# Prefer iPhone 16/15/14 Pro models in that order
priority = ['iPhone 16 Pro', 'iPhone 15 Pro', 'iPhone 14 Pro',
            'iPhone 16', 'iPhone 15', 'iPhone 14']
for pref in priority:
    for devs in data['devices'].values():
        for d in devs:
            if d['name'] == pref:
                print(d['udid'])
                sys.exit(0)
sys.exit(1)
" 2>/dev/null)" || die "No suitable iPhone simulator found (16/15/14 Pro). Run 'xcrun simctl list devices available' to diagnose." 1
    log "Using fallback UDID: ${UDID}"
fi

# ─── Step 3: Erase + boot ────────────────────────────────────────────────────

# simctl erase requires the device to be shutdown first
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
    # Wait for shutdown
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

log "Erasing simulator ${UDID} (clears Springboard pending modals)..."
xcrun simctl erase "${UDID}" 2>&1 || die "xcrun simctl erase failed for UDID ${UDID}." 1

log "Booting simulator ${UDID}..."
xcrun simctl boot "${UDID}" 2>&1 || {
    # Boot may error if already booting — check state
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

# ─── Step 6: Launch + wait ───────────────────────────────────────────────────

log "Launching ${BUNDLE_ID}..."
xcrun simctl launch "${UDID}" "${BUNDLE_ID}" 2>&1 || die "xcrun simctl launch failed for ${BUNDLE_ID}." 1

log "Waiting 4s for splash to settle..."
sleep 4

# ─── Step 7: Capture launch screen ───────────────────────────────────────────

mkdir -p "${SCREENSHOT_DIR}"
LAUNCH_SHOT="${SCREENSHOT_DIR}/01_launch.png"
log "Capturing launch screenshot -> ${LAUNCH_SHOT}"
xcrun simctl io "${UDID}" screenshot "${LAUNCH_SHOT}" 2>&1 || die "Screenshot capture failed." 1
log "Captured: ${LAUNCH_SHOT} ($(wc -c < "${LAUNCH_SHOT}" | tr -d ' ') bytes)"

# ─── Step 8: Walk steps (modular hook — idb taps go here) ────────────────────
# WALK_STEPS array is empty in v1; this loop is a no-op until entries are added.
# Each entry format: "tap:<x>:<y>:<screen_name>"
# Once idb_companion is installed, add entries to WALK_STEPS above and they
# will be executed in sequence. Example:
#   WALK_STEPS+=("tap:375:450:02_onboarding_welcome")
# which would do: idb ui tap --x 375 --y 450 --udid $UDID; sleep 1; screenshot

STEP_IDX=2
for step in ${WALK_STEPS[@]+"${WALK_STEPS[@]}"}; do
    IFS=':' read -r action arg1 arg2 screen_name <<< "${step}"
    case "${action}" in
        tap)
            log "Walk step: tap ${arg1},${arg2} -> ${screen_name}"
            # idb ui tap --x "${arg1}" --y "${arg2}" --udid "${UDID}"
            # (uncomment above once idb_companion is installed)
            warn "WALK_STEPS tap skipped — idb_companion not yet installed."
            ;;
        *)
            warn "Unknown walk action '${action}' in step '${step}' — skipping."
            ;;
    esac
    sleep 1
    SHOT_FILE="${SCREENSHOT_DIR}/$(printf '%02d' ${STEP_IDX})_${screen_name}.png"
    xcrun simctl io "${UDID}" screenshot "${SHOT_FILE}" 2>&1 || warn "Screenshot for step ${screen_name} failed."
    log "Captured walk step: ${SHOT_FILE}"
    (( STEP_IDX++ )) || true
done

# ─── Step 9: Diff vs legacy baseline ─────────────────────────────────────────

HAS_COMPARE=false
if command -v compare &>/dev/null; then
    HAS_COMPARE=true
    log "ImageMagick 'compare' found — will generate diff PNGs where baseline exists."
else
    warn "ImageMagick not installed — skipping diff PNGs (inline only)."
fi

# Gather captured screenshots (bash 3-compatible: use find + while loop, no mapfile)
# Diff map: track which screen names have a diff PNG by creating sentinel files
DIFF_SENTINEL_DIR="${SCREENSHOT_DIR}/.diff_sentinels"
mkdir -p "${DIFF_SENTINEL_DIR}"

while IFS= read -r shot; do
    [[ -z "${shot}" ]] && continue
    screen_name="$(basename "${shot}" .png)"
    legacy_path="${LEGACY_DIR}/${screen_name}.png"
    diff_path="${SCREENSHOT_DIR}/${screen_name}_diff.png"

    if [[ -f "${legacy_path}" ]] && ${HAS_COMPARE}; then
        log "Generating diff: ${screen_name}"
        # compare returns exit 1 if images differ (expected) — suppress set -e
        compare "${legacy_path}" "${shot}" "${diff_path}" 2>&1 || true
        if [[ -f "${diff_path}" ]]; then
            touch "${DIFF_SENTINEL_DIR}/${screen_name}"
            log "Diff PNG: ${diff_path}"
        fi
    fi
done < <(find "${SCREENSHOT_DIR}" -maxdepth 1 -name "*.png" ! -name "*_diff.png" | sort)

# ─── Step 10: Emit markdown to stdout ────────────────────────────────────────

# Paths in the markdown are relative to repo root (for GitHub rendering)
rel_screenshot_dir="docs/design/refs/screenshots/${TIER_NAME}"
rel_legacy_dir="docs/design/refs/legacy_v1.2.2_2026_05_09/screens"

echo ""
echo "### Visual diff — ${TIER_NAME}"
echo ""

# Build table header
if ${HAS_COMPARE}; then
    echo "| Screen | Legacy v1.2.2 | This PR | Pixel Diff |"
    echo "|---|---|---|---|"
else
    echo "| Screen | Legacy v1.2.2 | This PR |"
    echo "|---|---|---|"
fi

while IFS= read -r shot; do
    [[ -z "${shot}" ]] && continue
    screen_name="$(basename "${shot}" .png)"
    this_pr_img="![${screen_name}](${rel_screenshot_dir}/${screen_name}.png)"

    legacy_img="—"
    legacy_path="${LEGACY_DIR}/${screen_name}.png"
    if [[ -f "${legacy_path}" ]]; then
        legacy_img="![legacy ${screen_name}](${rel_legacy_dir}/${screen_name}.png)"
    fi

    if ${HAS_COMPARE} && [[ -f "${DIFF_SENTINEL_DIR}/${screen_name}" ]]; then
        diff_img="![diff ${screen_name}](${rel_screenshot_dir}/${screen_name}_diff.png)"
        echo "| ${screen_name} | ${legacy_img} | ${this_pr_img} | ${diff_img} |"
    else
        echo "| ${screen_name} | ${legacy_img} | ${this_pr_img} |"
    fi
done < <(find "${SCREENSHOT_DIR}" -maxdepth 1 -name "*.png" ! -name "*_diff.png" | sort)

# Clean up sentinel dir
rm -rf "${DIFF_SENTINEL_DIR}"

echo ""
echo "_Capture method: headless \`simctl io screenshot\` after fresh sim erase + \`DEV_BYPASS_COMPLIANCE=true\` build. Walk-mode pending \`idb_companion\` install._"
echo ""

log "Done. Screenshots in ${SCREENSHOT_DIR}"
