#!/bin/zsh
# stop_sonnet_pair.sh — terminate the L3 Sonnet pair daemon for one lane.
#
# Usage:
#   bash scripts/stop_sonnet_pair.sh peer
#   bash scripts/stop_sonnet_pair.sh main
#
# Sends SIGTERM, waits up to 10s for graceful shutdown, escalates to SIGKILL.

set -e

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LANE="${1:-}"

if [[ -z "$LANE" || ! "$LANE" =~ ^(peer|main)$ ]]; then
  echo "usage: $0 <peer|main>" >&2
  exit 1
fi

PID_FILE="${REPO}/.brain/daemon/sonnet_pair_${LANE}.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "no pid file at $PID_FILE — daemon not running?"
  exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"
if [[ -z "$PID" ]]; then
  echo "empty pid file; removing"
  rm -f "$PID_FILE"
  exit 0
fi

if ! kill -0 "$PID" 2>/dev/null; then
  echo "pid $PID not running (stale pid file); removing"
  rm -f "$PID_FILE"
  exit 0
fi

echo "sending SIGTERM to sonnet_pair_${LANE} pid=$PID"
kill -TERM "$PID" 2>/dev/null || true

for i in 1 2 3 4 5 6 7 8 9 10; do
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "stopped after ${i}s"
    rm -f "$PID_FILE"
    exit 0
  fi
  sleep 1
done

echo "still alive after 10s; sending SIGKILL"
kill -KILL "$PID" 2>/dev/null || true
sleep 1
rm -f "$PID_FILE"
echo "killed sonnet_pair_${LANE}"
