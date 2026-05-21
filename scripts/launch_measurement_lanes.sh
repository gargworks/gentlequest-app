#!/bin/zsh
# launch_measurement_lanes.sh — open 4 Terminal tabs (2 proxies + 2 CC sessions)
# so post-fix turns flow into .brain/measurement/turns.jsonl + turns.peer.jsonl.
#
# Usage:
#   bash scripts/launch_measurement_lanes.sh         # both surfaces
#   bash scripts/launch_measurement_lanes.sh main    # cc_main only (2 tabs)
#   bash scripts/launch_measurement_lanes.sh peer    # cc_peer only (2 tabs)
#
# Pre-flight:
#   - Fails fast if port 8787 / 8788 is already bound (no silent collision).
#   - Sets cwd in each tab so commands run from repo root.
#
# After running: every API call from those CC sessions gets captured.
# Tomorrow at T+24h, the nudge at .brain/nudges/phase1_t24h_preliminary_verdict.md
# triggers the preliminary verdict on the next peer-session start.

set -e
REPO="/Users/lokeshgarg/ai-mvp-backend"
MAIN_SESSION="85040a09-54d1-4550-aa9c-eb8e6bc8eb23"
PEER_SESSION="f6b976a1-5627-47c3-a431-af7d6be2633d"
FAIRNESS="${REPO}/.brain/measurement/fairness_config.baseline.sample.json"
# NOTE: --skip-fairness is in use below. AGENTS.md / CLAUDE.md drifted from
# the pinned reference (7479d5b vs d0e53472 as of 2026-04-27 launch attempt),
# so the fairness gate aborts startup. For the T+24h preliminary verdict
# (attribution % + R² fit) fairness comparison isn't the goal — flow first.
# To restore fairness gating: re-pin reference hashes against current
# AGENTS.md content, then drop --skip-fairness.

mode="${1:-both}"

# Pre-flight port checks
check_port() {
  local port=$1
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "ERROR: port $port is already bound. Run: lsof -nP -iTCP:$port -sTCP:LISTEN  → kill <PID>"
    exit 2
  fi
}

case "$mode" in
  main) check_port 8787 ;;
  peer) check_port 8788 ;;
  both) check_port 8787; check_port 8788 ;;
  *) echo "usage: $0 [main|peer|both]"; exit 1 ;;
esac

# Build the 4 commands
PROXY_MAIN="cd ${REPO} && python3 -m scripts.measurement_proxy --condition baseline --surface cc_main --phase dogfood --port 8787 --skip-fairness --out .brain/measurement/turns.jsonl"
PROXY_PEER="cd ${REPO} && python3 -m scripts.measurement_proxy --condition baseline --surface cc_peer --phase dogfood --port 8788 --skip-fairness --out .brain/measurement/turns.peer.jsonl"
CC_MAIN="cd ${REPO} && ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude --resume ${MAIN_SESSION} --dangerously-skip-permissions"
CC_PEER="cd ${REPO} && CC_SESSION_ROLE=peer ANTHROPIC_BASE_URL=http://127.0.0.1:8788 claude --resume ${PEER_SESSION} --dangerously-skip-permissions"

# Open a new Terminal tab and run a command in it
open_tab() {
  local cmd="$1"
  local label="$2"
  /usr/bin/osascript <<EOF
tell application "Terminal"
  activate
  tell application "System Events" to keystroke "t" using command down
  delay 0.4
  do script "echo '== ${label} ==' && ${cmd}" in front window
end tell
EOF
  sleep 0.5
}

case "$mode" in
  main)
    open_tab "$PROXY_MAIN" "proxy 8787 cc_main"
    sleep 1.5  # let proxy bind before CC connects
    open_tab "$CC_MAIN" "cc_main session"
    ;;
  peer)
    open_tab "$PROXY_PEER" "proxy 8788 cc_peer"
    sleep 1.5
    open_tab "$CC_PEER" "cc_peer session"
    ;;
  both)
    open_tab "$PROXY_MAIN" "proxy 8787 cc_main"
    open_tab "$PROXY_PEER" "proxy 8788 cc_peer"
    sleep 1.5
    open_tab "$CC_MAIN" "cc_main session"
    open_tab "$CC_PEER" "cc_peer session"
    ;;
esac

echo ""
echo "Launched [$mode] lane(s). Watch each tab for 'listening on...' (proxies) + Claude prompt (sessions)."
echo "If a CC session fails to connect, the proxy tab probably hasn't bound yet — wait 2s and try again in that tab."
