#!/bin/zsh
# start_sonnet_pair.sh — launch the L3 always-on Sonnet pair for one lane.
#
# Usage:
#   bash scripts/start_sonnet_pair.sh peer
#   bash scripts/start_sonnet_pair.sh main
#
# Backgrounds the daemon, writes PID to .brain/daemon/sonnet_pair_<lane>.pid,
# logs to .brain/daemon/sonnet_pair_<lane>.log. Idempotent: refuses to start
# if a live PID is already on file (clean up via stop_sonnet_pair.sh first).

set -e

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LANE="${1:-}"

if [[ -z "$LANE" || ! "$LANE" =~ ^(peer|main)$ ]]; then
  echo "usage: $0 <peer|main>" >&2
  exit 1
fi

DAEMON_DIR="${REPO}/.brain/daemon"
mkdir -p "$DAEMON_DIR"

PID_FILE="${DAEMON_DIR}/sonnet_pair_${LANE}.pid"
LOG_FILE="${DAEMON_DIR}/sonnet_pair_${LANE}.log"

if [[ -f "$PID_FILE" ]]; then
  EXISTING="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$EXISTING" ]] && kill -0 "$EXISTING" 2>/dev/null; then
    echo "ERROR: sonnet_pair_${LANE} already running (pid=$EXISTING). Stop it first: bash scripts/stop_sonnet_pair.sh ${LANE}" >&2
    exit 2
  else
    echo "stale pid file at $PID_FILE; removing"
    rm -f "$PID_FILE"
  fi
fi

cd "$REPO"

# Resolve interpreter — prefer the venv interpreter that has mcp_server_nucleus
# installed editable; fall back to system python3.
PY=""
for candidate in \
  "${REPO}/mcp-server-nucleus/.venv/bin/python" \
  "${REPO}/.venv/bin/python" \
  "$(command -v python3)"; do
  if [[ -x "$candidate" ]]; then
    if "$candidate" -c "import mcp_server_nucleus.runtime.sonnet_pair_daemon" 2>/dev/null; then
      PY="$candidate"
      break
    fi
  fi
done

if [[ -z "$PY" ]]; then
  echo "ERROR: could not find a Python with mcp_server_nucleus installed. Install editable: (cd mcp-server-nucleus && uv sync)" >&2
  exit 3
fi

echo "starting sonnet_pair_${LANE} with $PY"
echo "logs: $LOG_FILE"

nohup "$PY" -m mcp_server_nucleus.runtime.sonnet_pair_daemon "$LANE" \
  >> "$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

sleep 1
if kill -0 "$PID" 2>/dev/null; then
  echo "started sonnet_pair_${LANE} pid=$PID"
  echo "tail logs: tail -F $LOG_FILE"
else
  echo "ERROR: daemon exited within 1s. Check $LOG_FILE" >&2
  exit 4
fi
