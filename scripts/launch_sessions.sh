#!/usr/bin/env bash
# launch_sessions.sh — Multi-lane CC launcher (tabs in CURRENT Terminal window, resumes session IDs)
#
# Adds new TABS to the front Terminal window (does NOT open a new window).
# Resumes canonical session IDs from Apple Notes "Claude Thread Resume".
# All CC sessions launched with --dangerously-skip-permissions.
# Note: op-assistant is YOUR current session — do not pass `op` to this launcher.
#
# Roles + session IDs:
#   main → 85040a09-54d1-4550-aa9c-eb8e6bc8eb23  CC_SESSION_ROLE=main, proxy :8787
#   peer → f6b976a1-5627-47c3-a431-af7d6be2633d  CC_SESSION_ROLE=peer, proxy :8788
#   tb   → 27343e78-dec3-42b7-bdd0-f1785d4d4fd7  CC_SESSION_ROLE=tb
#   gq   → 442b30af-5a56-45fc-9269-3c5dc81eb2b7  CC_SESSION_ROLE=cc_gq, CWD=ai_buddy_web/
#   ant  → opens Antigravity.app (separate window, not a tab)
#
# Usage:
#   bash scripts/launch_sessions.sh                 # default: main,peer,tb,gq (4 CC tabs + 2 proxy tabs)
#   bash scripts/launch_sessions.sh main,peer       # measurement spike only (2 CC + 2 proxy)
#   bash scripts/launch_sessions.sh tb              # one CC tab, no proxy
#   bash scripts/launch_sessions.sh main,peer,tb,gq,ant
#
# Optional env override:
#   EFFORT=max bash scripts/launch_sessions.sh ...  # adds --effort max to all CC commands
#                                                   # (default = no --effort flag; CC uses its own default)

set -euo pipefail

REPO="${NUCLEUS_REPO:-$HOME/ai-mvp-backend}"
CONFIG_REL=".brain/measurement/fairness_config.baseline.sample.json"
TURNS_MAIN_REL=".brain/measurement/turns.jsonl"
TURNS_PEER_REL=".brain/measurement/turns.peer.jsonl"
SESSIONS="${1:-main,peer,tb,op,gq}"

SID_main="85040a09-54d1-4550-aa9c-eb8e6bc8eb23"
SID_peer="f6b976a1-5627-47c3-a431-af7d6be2633d"
SID_tb="27343e78-dec3-42b7-bdd0-f1785d4d4fd7"
SID_gq="442b30af-5a56-45fc-9269-3c5dc81eb2b7"
# op resumes the current op-assistant session (named "main-operator-assistant" by Lokesh).
# Will fail with "session already in use" if you're already in this session — exit that tab first.
SID_op="6a70c39b-ea6b-46df-92b7-97f66d26fc1a"

# Optional --effort flag (default: omitted; lets CC choose)
EFFORT_FLAG=""
[ -n "${EFFORT:-}" ] && EFFORT_FLAG=" --effort $EFFORT"

# Fairness gate handling — mutually exclusive with --fairness-config in the proxy.
# Default: skip mode (so casual launches don't fail on AGENTS.md hash drift).
# Set FAIRNESS=1 to enforce baseline pins (required for real measurement-spike runs).
FAIRNESS_ARGS=" --skip-fairness"
[ "${FAIRNESS:-}" = "1" ] && FAIRNESS_ARGS=" --fairness-config $CONFIG_REL"

if [ ! -d "$REPO" ]; then
  echo "ERROR: NUCLEUS_REPO not found at $REPO" >&2
  exit 1
fi

IFS=',' read -r -a REQUESTED <<<"$SESSIONS"

# Warn if op spawn requested while caller is already in an op session
for role in "${REQUESTED[@]}"; do
  if [ "$role" = "op" ] || [ "$role" = "operator_assistant" ]; then
    if [ "${CC_SESSION_ROLE:-}" = "operator_assistant" ]; then
      echo "NOTE: spawning a cold op-assistant tab — you appear to already be in one (CC_SESSION_ROLE=operator_assistant). Two op tabs will coexist." >&2
    fi
  fi
done

NEED_MAIN_PROXY=0
NEED_PEER_PROXY=0
for s in "${REQUESTED[@]}"; do
  [ "$s" = "main" ] && NEED_MAIN_PROXY=1
  [ "$s" = "peer" ] && NEED_PEER_PROXY=1
done

# Preflight (only when measured sessions requested)
if [ $NEED_MAIN_PROXY -eq 1 ] || [ $NEED_PEER_PROXY -eq 1 ]; then
  if [ ! -f "$REPO/$CONFIG_REL" ]; then
    echo "ERROR: fairness config missing at $REPO/$CONFIG_REL" >&2
    exit 1
  fi
  ports=()
  [ $NEED_MAIN_PROXY -eq 1 ] && ports+=(8787)
  [ $NEED_PEER_PROXY -eq 1 ] && ports+=(8788)
  for port in "${ports[@]}"; do
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "WARN: port $port already bound. Kill listener: kill \$(lsof -ti:$port)" >&2
      exit 2
    fi
  done
fi

# Build ordered command + title list (proxies first so CC sessions can connect)
declare -a CMDS
declare -a TITLES

if [ $NEED_MAIN_PROXY -eq 1 ]; then
  CMDS+=("cd '$REPO' && python3 -m scripts.measurement_proxy --condition baseline --surface cc_main --phase dogfood --port 8787 $FAIRNESS_ARGS --out $TURNS_MAIN_REL")
  TITLES+=("proxy: cc_main :8787")
fi
if [ $NEED_PEER_PROXY -eq 1 ]; then
  CMDS+=("cd '$REPO' && python3 -m scripts.measurement_proxy --condition baseline --surface cc_peer --phase dogfood --port 8788 $FAIRNESS_ARGS --out $TURNS_PEER_REL")
  TITLES+=("proxy: cc_peer :8788")
fi

ANT_REQUESTED=0
for role in "${REQUESTED[@]}"; do
  case "$role" in
    main)
      CMDS+=("cd '$REPO' && CC_SESSION_ROLE=main ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude --resume $SID_main --dangerously-skip-permissions$EFFORT_FLAG")
      TITLES+=("CC main (resumed, :8787)")
      ;;
    peer)
      CMDS+=("cd '$REPO' && CC_SESSION_ROLE=peer ANTHROPIC_BASE_URL=http://127.0.0.1:8788 claude --resume $SID_peer --dangerously-skip-permissions$EFFORT_FLAG")
      TITLES+=("CC peer (resumed, :8788)")
      ;;
    tb)
      CMDS+=("cd '$REPO' && CC_SESSION_ROLE=tb claude --resume $SID_tb --dangerously-skip-permissions$EFFORT_FLAG")
      TITLES+=("CC tb (resumed)")
      ;;
    gq)
      # gq session was created from repo root (verified — jsonl at -Users-lokeshgarg-ai-mvp-backend/),
      # NOT from ai_buddy_web subdirectory. Stay at repo root to resolve session ID.
      CMDS+=("cd '$REPO' && CC_SESSION_ROLE=cc_gq claude --resume $SID_gq --dangerously-skip-permissions$EFFORT_FLAG")
      TITLES+=("CC gq (resumed)")
      ;;
    op|operator_assistant)
      # Resume the canonical op session (no --model flag — uses session's existing model)
      CMDS+=("cd '$REPO' && CC_SESSION_ROLE=operator_assistant claude --resume $SID_op --dangerously-skip-permissions$EFFORT_FLAG")
      TITLES+=("CC op (resumed)")
      ;;
    ant)
      ANT_REQUESTED=1
      ;;
    *)
      echo "WARN: unknown session '$role' — skipping" >&2
      ;;
  esac
done

NUM_TABS=${#CMDS[@]}
if [ $NUM_TABS -eq 0 ] && [ $ANT_REQUESTED -eq 0 ]; then
  echo "ERROR: no sessions to launch" >&2
  exit 1
fi

# Build AppleScript: add N tabs to the FRONT Terminal window (don't create new window).
# Pattern per tab: cmd+t (opens new tab in front window) → do script in front window → set title.
if [ $NUM_TABS -gt 0 ]; then
  APPLESCRIPT='tell application "Terminal"
    activate'
  for ((i=0; i<NUM_TABS; i++)); do
    cmd_escaped="${CMDS[$i]//\\/\\\\}"
    cmd_escaped="${cmd_escaped//\"/\\\"}"
    title_escaped="${TITLES[$i]//\"/\\\"}"
    APPLESCRIPT+="
    tell application \"System Events\" to keystroke \"t\" using command down
    delay 0.4
    do script \"$cmd_escaped\" in front window
    delay 0.3
    try
        set custom title of selected tab of front window to \"$title_escaped\"
    end try"
  done
  APPLESCRIPT+='
end tell'

  osascript -e "$APPLESCRIPT"
fi

if [ $ANT_REQUESTED -eq 1 ]; then
  osascript -e 'tell application "Antigravity" to activate' 2>/dev/null \
    || open -a "Antigravity" 2>/dev/null \
    || echo "WARN: Antigravity.app not found; skipping" >&2
fi

echo ""
echo "Added $NUM_TABS tab(s) to current Terminal window: $SESSIONS"
[ $ANT_REQUESTED -eq 1 ] && echo "Antigravity activated."
echo ""
echo "Session IDs (from Apple Notes 'Claude Thread Resume'):"
[ $NEED_MAIN_PROXY -eq 1 ] && echo "  main: $SID_main"
[ $NEED_PEER_PROXY -eq 1 ] && echo "  peer: $SID_peer"
for r in "${REQUESTED[@]}"; do
  [ "$r" = "tb" ] && echo "  tb:   $SID_tb"
  [ "$r" = "gq" ] && echo "  gq:   $SID_gq"
done
echo ""
echo "Stop a proxy: Ctrl-C in its tab OR  kill \$(lsof -ti:8787,8788)"
