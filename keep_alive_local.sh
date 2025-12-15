#!/bin/bash
# Local keep-alive script for GentleQuest
# Run this as a cron job every 10 minutes to prevent cold starts

URL="https://gentlequest.onrender.com/api/ping"
HEALTH_URL="https://gentlequest.onrender.com/api/health"

echo "[$(date)] Pinging GentleQuest..."

# Try ping endpoint first (lightweight)
if curl -fsSI --max-time 5 "$URL" > /dev/null 2>&1; then
    echo "[$(date)] ✅ Ping successful"
else
    # Fallback to health endpoint
    if curl -fsS --max-time 10 "$HEALTH_URL" > /dev/null 2>&1; then
        echo "[$(date)] ✅ Health check successful"
    else
        echo "[$(date)] ❌ Both endpoints failed!"
    fi
fi
