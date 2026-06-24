#!/bin/bash
# Daily funnel snapshot — hits /api/metrics/funnel to persist a snapshot
# to the funnel_snapshots table. Runs via launchd daily at 08:00 UTC.
#
# Log: ~/.local/share/gentlequest/logs/funnel_snapshot.log

LOG_DIR="$HOME/.local/share/gentlequest/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/funnel_snapshot.log"

TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "[$TS] Hitting funnel endpoint..." >> "$LOG_FILE"

RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "User-Agent: launchd/funnel-snapshot" \
  --max-time 60 \
  "https://gentlequest.onrender.com/api/metrics/funnel" 2>&1)

BODY=$(echo "$RESPONSE" | sed '$d')
CODE=$(echo "$RESPONSE" | tail -1)

if [ "$CODE" = "200" ]; then
  CACHED=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cached','?'))" 2>/dev/null || echo "?")
  INSTALLS=$(echo "$BODY" | python3 -c "import sys,json; f=json.load(sys.stdin).get('funnel',{}); print(f.get('stage_2_installs',{}))" 2>/dev/null || echo "?")
  echo "[$TS] OK (200) | cached=$CACHED | installs=$INSTALLS" >> "$LOG_FILE"
else
  echo "[$TS] FAILED ($CODE)" >> "$LOG_FILE"
  echo "$BODY" >> "$LOG_FILE"
fi
