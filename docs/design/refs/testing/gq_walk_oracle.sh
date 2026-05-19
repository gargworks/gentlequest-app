#!/usr/bin/env bash
# gq_walk_oracle.sh — instrumented walk with no-op detection + oracle validation
#
# After each tap, asserts the screenshot changed (detects silent no-ops).
# After the full walk, runs validate_walk.py against gq_oracle.json.
#
# Usage:
#   bash gq_walk_oracle.sh              # full walk + validate
#   bash gq_walk_oracle.sh --validate-only  # validate existing screenshots only

UDID="95843C74-7CB1-411B-965B-12CCB6F433AF"
BUNDLE="com.gentlequest.app"
OUT="/Users/lokeshgarg/ai-mvp-backend/docs/design/refs/screenshots/oracle-run-$(date +%Y-%m-%d)"
TESTING_DIR="/Users/lokeshgarg/ai-mvp-backend/docs/design/refs/testing"
ORACLE="$TESTING_DIR/gq_oracle.json"

NOOP_LOG="$TESTING_DIR/noop_suspects.txt"
PASS=0; FAIL=0; NOOP=0

mkdir -p "$OUT"
> "$NOOP_LOG"

# ── helpers ──────────────────────────────────────────────────────────────────

snap() {
  local name="$1" delay="${2:-1.2}"
  sleep "$delay"
  xcrun simctl io "$UDID" screenshot "$OUT/${name}.png" 2>/dev/null && echo "✓ $name"
}

tap() {
  local x=$1 y=$2
  # Hash screen before tap
  local before
  before=$(xcrun simctl io "$UDID" screenshot /tmp/gq_before.png 2>/dev/null && md5 -q /tmp/gq_before.png)
  idb ui tap --udid "$UDID" "$x" "$y" 2>/dev/null
  sleep 0.6
  # Hash screen after tap
  local after
  after=$(xcrun simctl io "$UDID" screenshot /tmp/gq_after.png 2>/dev/null && md5 -q /tmp/gq_after.png)
  if [ "$before" = "$after" ]; then
    echo "  ⚠ NO-OP detected at tap($x,$y)"
    echo "tap($x,$y)" >> "$NOOP_LOG"
    NOOP=$((NOOP+1))
  fi
}

back() { idb ui tap --udid "$UDID" 29 83 2>/dev/null; sleep 0.8; }
swipe_up() { idb ui swipe --udid "$UDID" 196 650 196 250 2>/dev/null; sleep 0.6; }

foreground() {
  xcrun simctl launch "$UDID" "$BUNDLE" > /dev/null 2>&1 || true
  sleep 1.5
}

# ── validate-only shortcut ────────────────────────────────────────────────────

if [ "${1:-}" = "--validate-only" ]; then
  LATEST=$(ls -dt /Users/lokeshgarg/ai-mvp-backend/docs/design/refs/screenshots/oracle-run-* 2>/dev/null | head -1)
  if [ -z "$LATEST" ]; then
    # Fall back to the existing walk dir
    LATEST="/Users/lokeshgarg/ai-mvp-backend/docs/design/refs/screenshots/walk-2026-05-19"
  fi
  echo "Validating $LATEST against $ORACLE"
  python3 "$TESTING_DIR/validate_walk.py" --walk "$LATEST" --oracle "$ORACLE"
  exit $?
fi

# ── walk ─────────────────────────────────────────────────────────────────────

echo "=== GentleQuest Oracle Walk ==="
echo "Output: $OUT"

# Make sure app is up
foreground
snap "I1_chat_home" 3.0

# Nav sheet
tap 328 88; snap "I5_nav_sheet" 1.2

# Settings via sheet
tap 196 682; snap "S1_settings_top" 2.0
swipe_up;    snap "S1b_settings_scrolled" 0.6
back

# Profile via sheet
tap 328 88; sleep 1.0
tap 196 622; snap "P1_profile_top" 2.0
swipe_up;   snap "P1b_about_you" 0.6
swipe_up;   snap "P2_voice_section" 0.6
swipe_up;   snap "P3_safety_plan_card" 0.6
back

# Overflow → safety sheet
tap 360 88; snap "I7_overflow_open" 0.8
tap 196 180; snap "I7b_safety_legal_sheet" 1.2
tap 196 100; sleep 0.5

# Mood tab
tap 155 800; snap "M1_mood_tab" 2.0
tap 196 200; snap "M2_mood_sheet" 1.2
tap 80 474;  snap "M2b_emoji_selected" 0.8
tap 196 580; snap "M2c_mood_submitted" 2.5

# Quest tab
tap 238 800; snap "Q1_quest_tab" 2.0
swipe_up;    snap "Q1b_scrolled" 0.8
tap 196 400; snap "Q2_quest_preview" 1.5
back

# Community
tap 322 800; snap "X_community_tab" 2.0

# Journal via nav sheet
tap 71 800; sleep 0.5
tap 328 88; sleep 1.0
tap 196 742; snap "J1_journal_empty" 2.0
back

# Library via nav sheet
tap 328 88; sleep 1.0
tap 196 802; snap "RL1_library_all" 2.0
tap 100 300; snap "RL2_breathing" 1.0
back

# Tab cycler
tap 71 800;  snap "X1_talk"      0.8
tap 155 800; snap "X1b_mood"     0.8
tap 238 800; snap "X1c_quest"    0.8
tap 322 800; snap "X1d_community" 0.8

# ── validate ─────────────────────────────────────────────────────────────────

echo ""
echo "=== Validating against oracle ==="

if [ ! -f "$ORACLE" ]; then
  echo "Oracle not found — building from walk-2026-05-19 golden screenshots first..."
  python3 "$TESTING_DIR/build_oracle.py" \
    --golden "/Users/lokeshgarg/ai-mvp-backend/docs/design/refs/screenshots/walk-2026-05-19" \
    --out "$ORACLE"
fi

python3 "$TESTING_DIR/validate_walk.py" --walk "$OUT" --oracle "$ORACLE"
VALIDATE_EXIT=$?

echo ""
if [ $NOOP -gt 0 ]; then
  echo "⚠  $NOOP no-op tap(s) detected — see $NOOP_LOG"
fi

exit $VALIDATE_EXIT
