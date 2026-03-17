#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# Nucleus Telemetry Summary — Human + LLM readable
#
# Architecture docs:
#   - TELEMETRY_PIPELINE_README.md  (end-to-end)
#   - WINDSURF_SUPER_PROMPT.md      (Phase A3)
#
# Usage:
#   npm run telemetry:summary           # Default: last 500 lines
#   npm run telemetry:summary -- 1000   # Last 1000 lines
#   npm run telemetry:summary -- --json # JSON output for LLMs
# ──────────────────────────────────────────────────────────────

set -euo pipefail

CONTAINER_NAME="nucleus-otel-collector"
JSON_MODE=false

# Parse args
LINES=500
for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=true ;;
    [0-9]*) LINES="$arg" ;;
  esac
done

# ── Pre-flight: is collector running? ──
if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"; then
  if [ "$JSON_MODE" = true ]; then
    echo '{"error":"collector_not_running","hint":"npm run telemetry:up"}'
  else
    echo "[summary] ❌ Collector container '${CONTAINER_NAME}' is not running." >&2
    echo "[summary]    Start it with: npm run telemetry:up" >&2
    echo "[summary]    If Docker is not running, start Docker Desktop first." >&2
  fi
  exit 1
fi

echo "[summary] Inspecting last ${LINES} log lines from '${CONTAINER_NAME}'..." >&2

# Capture both stdout and stderr from docker logs (collector may log to either)
LOG_OUTPUT=$(docker logs "${CONTAINER_NAME}" --tail "${LINES}" 2>&1 || true)

if [ -z "$LOG_OUTPUT" ]; then
  if [ "$JSON_MODE" = true ]; then
    echo '{"error":"empty_logs","hint":"Collector may have just started. Wait 30s and retry."}'
  else
    echo "[summary] ⚠️  No logs from collector. It may have just restarted."
    echo "[summary]    Wait 30 seconds for spans to flow, then try again."
  fi
  exit 0
fi

# ── Count spans — handle both debug exporter and structured log formats ──
# Debug exporter format: "Trace ID       : <hex>"
# Structured log format: "traceID" or "trace_id"
TOTAL_SPANS=$(printf "%s" "$LOG_OUTPUT" | grep -ciE "Trace ID|traceID|trace_id" || true)
NUCLEUS_SPANS=$(printf "%s" "$LOG_OUTPUT" | grep -ciE "service\.name.*nucleus|nucleus.*service" || true)
LAST_TRACE=$(printf "%s" "$LOG_OUTPUT" | grep -ioE "(Trace ID\s*:\s*[0-9a-f]+|traceID\":\"[0-9a-f]+)" | tail -1 | grep -oE "[0-9a-f]{16,}" || true)

# Breakdown by service.name (debug exporter format)
SERVICE_COUNTS=$(printf "%s" "$LOG_OUTPUT" | \
  grep -oE "service\.name: Str\([^)]*\)" | \
  sed -E 's/service\.name: Str\(([^)]*)\)/\1/' | \
  sort | uniq -c | sort -rn || true)

# Also check for JSON-format service names
if [ -z "$SERVICE_COUNTS" ]; then
  SERVICE_COUNTS=$(printf "%s" "$LOG_OUTPUT" | \
    grep -oE '"service\.name":"[^"]*"' | \
    sed -E 's/"service\.name":"([^"]*)"/\1/' | \
    sort | uniq -c | sort -rn || true)
fi

# ── Output ──
if [ "$JSON_MODE" = true ]; then
  # Machine-readable JSON for LLMs
  cat <<JSONEOF
{
  "log_lines_inspected": ${LINES},
  "total_spans": ${TOTAL_SPANS},
  "nucleus_spans": ${NUCLEUS_SPANS},
  "last_trace_id": "${LAST_TRACE:-none}",
  "collector_running": true
}
JSONEOF
else
  cat <<EOF

  ┌────────────────────────────────────────────────────┐
  │         Nucleus Telemetry Summary                  │
  ├────────────────────────────────────────────────────┤
  │ Log lines inspected           : ${LINES}
  │ Total spans detected          : ${TOTAL_SPANS}
  │ Nucleus-specific spans        : ${NUCLEUS_SPANS}
  │ Last Trace ID                 : ${LAST_TRACE:-none}
  └────────────────────────────────────────────────────┘

EOF

  if [ "${TOTAL_SPANS}" = "0" ]; then
    echo "  ⚠️  No spans detected. Possible causes:"
    echo "     1. No Nucleus commands have been run with NUCLEUS_ANON_TELEMETRY=true"
    echo "     2. The drain script is not running (npm run telemetry:drain)"
    echo "     3. Collector was recently restarted and old logs were cleared"
    echo "     4. Spans are flowing but using a format this script doesn't recognize"
    echo ""
    echo "  Quick fix: Run a command and check again:"
    echo "     NUCLEUS_ANON_TELEMETRY=true nucleus morning-brief"
    echo "     npm run telemetry:summary"
    echo ""
  else
    echo "  Spans by service.name (top):"
    if [ -n "$SERVICE_COUNTS" ]; then
      echo "$SERVICE_COUNTS" | head -20 | sed 's/^/     /'
    else
      echo "     (could not parse service names from logs)"
    fi
    echo ""
  fi
fi
