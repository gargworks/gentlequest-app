#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# Nucleus Telemetry: Start Everything (One Command)
#
# Architecture docs:
#   - WINDSURF_SUPER_PROMPT.md (Phase A4)
#   - TELEMETRY_QUICKSTART.md
#
# Usage:
#   npm run telemetry:all
#
# What it does:
#   1. Starts the OTel Collector container
#   2. Starts the Upstash drain in background
#   3. Checks tunnel status (informational)
#   4. Prints status summary
# ──────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="nucleus-otel-collector"

echo ""
echo "  ┌──────────────────────────────────────────┐"
echo "  │   Nucleus Telemetry — Starting All       │"
echo "  └──────────────────────────────────────────┘"
echo ""

# ── Step 1: Collector ──
echo "  [1/3] Starting OTel Collector..."
bash "$SCRIPT_DIR/telemetry.sh" up 2>&1 | sed 's/^/        /'

# ── Step 2: Check drain prerequisites ──
echo ""
echo "  [2/3] Checking drain prerequisites..."
if [ -z "${UPSTASH_REDIS_URL:-}" ] || [ -z "${UPSTASH_REDIS_TOKEN:-}" ]; then
  echo "        ⚠️  Upstash env vars not set. Drain will NOT start."
  echo "        Set these in your shell or .env:"
  echo "          export UPSTASH_REDIS_URL=\"rediss://...\""
  echo "          export UPSTASH_REDIS_TOKEN=\"...\""
  echo ""
  echo "        Collector is running, but spans from Upstash won't flow."
  DRAIN_STARTED=false
else
  echo "        ✅ Upstash credentials found."
  echo "        Starting drain in background..."
  
  # Start drain in background, log to a file
  DRAIN_LOG="/tmp/nucleus-drain.log"
  node "$SCRIPT_DIR/drain-upstash-spans.js" > "$DRAIN_LOG" 2>&1 &
  DRAIN_PID=$!
  echo "        Drain PID: $DRAIN_PID (log: $DRAIN_LOG)"
  DRAIN_STARTED=true
  
  # Give it a moment to start or fail
  sleep 2
  if kill -0 "$DRAIN_PID" 2>/dev/null; then
    echo "        ✅ Drain is running."
  else
    echo "        ❌ Drain exited immediately. Check: cat $DRAIN_LOG"
    DRAIN_STARTED=false
  fi
fi

# ── Step 3: Tunnel check ──
echo ""
echo "  [3/3] Checking Cloudflare tunnel..."
if command -v cloudflared &>/dev/null; then
  if pgrep -f "cloudflared.*tunnel" >/dev/null 2>&1; then
    echo "        ✅ Cloudflare tunnel process detected."
  else
    echo "        ⚠️  No cloudflared tunnel process found."
    echo "        Start it with: cloudflared tunnel run nucleus-telemetry"
  fi
else
  echo "        ℹ️  cloudflared not installed. Tunnel not available."
  echo "        Spans will still be buffered in Upstash."
fi

# ── Summary ──
echo ""
echo "  ┌──────────────────────────────────────────┐"
echo "  │   Status                                 │"
echo "  ├──────────────────────────────────────────┤"

# Collector
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"; then
  echo "  │ Collector:   ✅ Running                 │"
else
  echo "  │ Collector:   ❌ Not running              │"
fi

# Drain
if [ "${DRAIN_STARTED:-false}" = true ]; then
  echo "  │ Drain:       ✅ Running (PID: $DRAIN_PID)      │"
else
  echo "  │ Drain:       ❌ Not started              │"
fi

# Tunnel
if pgrep -f "cloudflared.*tunnel" >/dev/null 2>&1; then
  echo "  │ Tunnel:      ✅ Running                 │"
else
  echo "  │ Tunnel:      ⚠️  Not detected            │"
fi

echo "  └──────────────────────────────────────────┘"
echo ""
echo "  Next: Run Nucleus commands with telemetry:"
echo "    NUCLEUS_ANON_TELEMETRY=true nucleus morning-brief"
echo ""
echo "  Check telemetry:"
echo "    npm run telemetry:summary"
echo ""
