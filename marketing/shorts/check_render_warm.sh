#!/bin/bash
# Random Render warm-check — logs response time for GQ backend
# Runs via launchd at random intervals for a few days
LOG="$HOME/gentlequest/marketing/shorts/logs/render_warm_check.log"
mkdir -p "$(dirname "$LOG")"

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
RESP1=$(curl -s -o /dev/null -w "%{http_code}|%{time_total}" --max-time 60 https://gentlequest.onrender.com/api/health 2>&1)
RESP2=$(curl -s -o /dev/null -w "%{http_code}|%{time_total}" --max-time 60 https://app.gentlequest.app/api/health 2>&1)

echo "$TS | onrender: $RESP1 | app.gq: $RESP2" >> "$LOG"

# Flag if cold start detected (>5s = likely was sleeping)
CODE1=$(echo "$RESP1" | cut -d'|' -f1)
TIME1=$(echo "$RESP1" | cut -d'|' -f2)
if (( $(echo "$TIME1 > 5.0" | bc -l 2>/dev/null || echo 0) )); then
    echo "$TS | ⚠️  COLD START DETECTED: ${TIME1}s on gentlequest.onrender.com" >> "$LOG"
fi
