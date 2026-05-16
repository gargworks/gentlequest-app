#!/usr/bin/env bash
# launch_4lane.sh — Spin up 4-lane multi-agent capture in four Terminal windows:
#   Window 1: measurement_proxy --surface cc_main --port 8787 (foreground, Ctrl-C to stop)
#   Window 2: measurement_proxy --surface cc_peer --port 8788 (foreground, Ctrl-C to stop)
#   Window 3: claude (CC-main, ANTHROPIC_BASE_URL=http://127.0.0.1:8787, CC_SESSION_ROLE=main)
#   Window 4: claude (CC-peer, ANTHROPIC_BASE_URL=http://127.0.0.1:8788, CC_SESSION_ROLE=peer)
# Antigravity + Gemini CLI run separately in their own sessions (native Gemini, no proxy).
#
# Usage: bash scripts/launch_4lane.sh
#        (or alias n4lane='bash ~/ai-mvp-backend/scripts/launch_4lane.sh')

set -euo pipefail

REPO="${NUCLEUS_REPO:-$HOME/ai-mvp-backend}"
CONFIG_REL=".brain/measurement/fairness_config.baseline.sample.json"
TURNS_MAIN_REL=".brain/measurement/turns.jsonl"
TURNS_PEER_REL=".brain/measurement/turns.peer.jsonl"

if [ ! -d "$REPO" ]; then
  echo "ERROR: NUCLEUS_REPO not found at $REPO" >&2
  exit 1
fi

if [ ! -f "$REPO/$CONFIG_REL" ]; then
  echo "ERROR: fairness config missing at $REPO/$CONFIG_REL" >&2
  echo "Pin hashes (claudemd_ref_hash, cli_version, tool_set_hash, mcp_state_snapshot_hash) before running." >&2
  echo "Helper:   cd $REPO && shasum -a 256 AGENTS.md && claude --version" >&2
  exit 1
fi

for port in 8787 8788; do
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "WARN: port $port already bound. Kill existing listener first:" >&2
    echo "  kill \$(lsof -ti:$port)" >&2
    exit 2
  fi
done

launch_in_terminal() {
  local title="$1"
  local cmd="$2"
  osascript <<APPLESCRIPT
tell application "Terminal"
    activate
    do script "$cmd"
    delay 0.2
    try
        set custom title of front window to "$title"
    end try
end tell
APPLESCRIPT
}

PROXY_CMD_MAIN="cd '$REPO' && python3 -m scripts.measurement_proxy --condition baseline --surface cc_main --phase dogfood --port 8787 --fairness-config $CONFIG_REL --out $TURNS_MAIN_REL"
PROXY_CMD_PEER="cd '$REPO' && python3 -m scripts.measurement_proxy --condition baseline --surface cc_peer --phase dogfood --port 8788 --fairness-config $CONFIG_REL --out $TURNS_PEER_REL"
# Persistent CC session IDs (Lokesh-owned; update here if they rotate)
CC_MAIN_SESSION_ID="${CC_MAIN_SESSION_ID:-85040a09-54d1-4550-aa9c-eb8e6bc8eb23}"
CC_PEER_SESSION_ID="${CC_PEER_SESSION_ID:-f6b976a1-5627-47c3-a431-af7d6be2633d}"

CC_CMD_MAIN="cd '$REPO' && CC_SESSION_ROLE=main ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude --resume $CC_MAIN_SESSION_ID --dangerously-skip-permissions"
CC_CMD_PEER="cd '$REPO' && CC_SESSION_ROLE=peer ANTHROPIC_BASE_URL=http://127.0.0.1:8788 claude --resume $CC_PEER_SESSION_ID --dangerously-skip-permissions"

launch_in_terminal "proxy-cc_main-8787" "$PROXY_CMD_MAIN"
sleep 1
launch_in_terminal "proxy-cc_peer-8788" "$PROXY_CMD_PEER"
sleep 3
launch_in_terminal "CC-main-8787" "$CC_CMD_MAIN"
launch_in_terminal "CC-peer-8788" "$CC_CMD_PEER"

echo ""
echo "4-lane launch dispatched. Verify each Terminal shows expected startup:"
echo "  proxy windows: 'fairness gate PASSED (14 pins)' + 'listening on http://127.0.0.1:PORT'"
echo "  CC windows:    session startup + [DIRECTIVE-ON-WAKE] relay surface via plugin inbox monitor"
echo ""
echo "Antigravity + Gemini CLI continue in their own sessions (native Gemini, no proxy)."
echo "To stop: Ctrl-C each proxy window; each CC session is normal interactive claude."
