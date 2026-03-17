#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# Nucleus Daily Telemetry Brief — Phase C + D
#
# Queries Prometheus for anonymous telemetry metrics and generates
# a concise daily usage summary with:
#   - Period-over-period comparisons (Phase D)
#   - Statistical anomaly detection (Phase D)
#
# Usage:
#   npm run telemetry:brief
#   LOOKBACK_HOURS=12 npm run telemetry:brief  # Custom window
#
# Requires:
#   - Prometheus running at http://localhost:9090
#   - Phase B observability stack (npm run telemetry:dash)
# ──────────────────────────────────────────────────────────────

set -euo pipefail

PROM_URL="${PROMETHEUS_URL:-http://localhost:9090}"
LOOKBACK="${LOOKBACK_HOURS:-24}"

# ── Pre-flight checks ──
if ! curl -s "${PROM_URL}/-/healthy" >/dev/null 2>&1; then
  echo "❌ Prometheus not reachable at ${PROM_URL}" >&2
  echo "   Start the stack: npm run telemetry:dash" >&2
  exit 1
fi

echo "═══════════════════════════════════════════════════════════"
echo "  NUCLEUS DAILY TELEMETRY BRIEF"
echo "  $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ── Helper: Query Prometheus ──
query_prom() {
  local query="$1"
  curl -s "${PROM_URL}/api/v1/query" \
    --data-urlencode "query=${query}" \
    | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if d['status'] == 'success' and d['data']['result']:
        print(d['data']['result'][0]['value'][1])
    else:
        print('0')
except:
    print('0')
"
}

query_prom_vector() {
  local query="$1"
  curl -s "${PROM_URL}/api/v1/query" \
    --data-urlencode "query=${query}" \
    | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if d['status'] == 'success' and d['data']['result']:
        for r in d['data']['result'][:10]:
            labels = ', '.join(f\"{k}={v}\" for k,v in r['metric'].items() if k not in ['__name__', 'job', 'source'])
            print(f\"{r['value'][1]:>8}  {labels}\")
    else:
        print('No data')
except Exception as e:
    print(f'Error: {e}')
"
}

# ── 1. Total Commands ──
TOTAL_COMMANDS=$(query_prom "sum(increase(nucleus_nucleus_anon_commands_total[${LOOKBACK}h]))")
echo "📊 USAGE SUMMARY (Last ${LOOKBACK}h)"
echo "────────────────────────────────────────────────────────────"
printf "  Total commands: %s\n" "${TOTAL_COMMANDS}"

# ── 2. Commands per hour ──
COMMANDS_PER_HOUR=$(query_prom "sum(rate(nucleus_nucleus_anon_commands_total[${LOOKBACK}h])) * 3600")
printf "  Commands/hour:  %.2f\n" "${COMMANDS_PER_HOUR}"
echo ""

# ── 3. Top Commands ──
echo "🔝 TOP COMMANDS"
echo "────────────────────────────────────────────────────────────"
query_prom_vector "topk(10, sum by (nucleus_command) (increase(nucleus_nucleus_anon_commands_total[${LOOKBACK}h])))"
echo ""

# ── 4. Error Rate ──
TOTAL_WITH_ERRORS=$(query_prom "sum(increase(nucleus_nucleus_anon_commands_total{nucleus_error_type!=\"\"}[${LOOKBACK}h]))")
if [ "$(echo "$TOTAL_COMMANDS > 0" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
  ERROR_RATE=$(echo "scale=2; $TOTAL_WITH_ERRORS * 100 / $TOTAL_COMMANDS" | bc -l 2>/dev/null || echo "0")
else
  ERROR_RATE="0"
fi

echo "⚠️  ERROR ANALYSIS"
echo "────────────────────────────────────────────────────────────"
printf "  Commands with errors: %s\n" "${TOTAL_WITH_ERRORS}"
printf "  Error rate:           %s%%\n" "${ERROR_RATE}"

if [ "$(echo "$TOTAL_WITH_ERRORS > 0" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
  echo ""
  echo "  Top error types:"
  query_prom_vector "topk(5, sum by (nucleus_error_type) (increase(nucleus_nucleus_anon_commands_total{nucleus_error_type!=\"\"}[${LOOKBACK}h])))"
fi
echo ""

# ── 5. Latency Percentiles ──
echo "⏱️  LATENCY PERCENTILES (Last ${LOOKBACK}h)"
echo "────────────────────────────────────────────────────────────"
P50=$(query_prom "histogram_quantile(0.50, sum(rate(nucleus_nucleus_anon_command_duration_ms_bucket[${LOOKBACK}h])) by (le))")
P95=$(query_prom "histogram_quantile(0.95, sum(rate(nucleus_nucleus_anon_command_duration_ms_bucket[${LOOKBACK}h])) by (le))")
P99=$(query_prom "histogram_quantile(0.99, sum(rate(nucleus_nucleus_anon_command_duration_ms_bucket[${LOOKBACK}h])) by (le))")

printf "  p50: %.1fms\n" "${P50}"
printf "  p95: %.1fms\n" "${P95}"
printf "  p99: %.1fms\n" "${P99}"
echo ""

# ── 6. Platform Distribution ──
echo "💻 PLATFORM DISTRIBUTION"
echo "────────────────────────────────────────────────────────────"
query_prom_vector "sum by (os_platform) (increase(nucleus_nucleus_anon_commands_total[${LOOKBACK}h]))"
echo ""

# ── 7. Python Version Distribution ──
echo "🐍 PYTHON VERSION DISTRIBUTION"
echo "────────────────────────────────────────────────────────────"
query_prom_vector "sum by (python_version) (increase(nucleus_nucleus_anon_commands_total[${LOOKBACK}h]))"
echo ""

# ── 8. Period-over-Period Comparison (Phase D) ──
echo "📈 PERIOD-OVER-PERIOD COMPARISON"
echo "────────────────────────────────────────────────────────────"

# Compare current period vs previous period
PREV_PERIOD_COMMANDS=$(query_prom "sum(increase(nucleus_nucleus_anon_commands_total[${LOOKBACK}h] offset ${LOOKBACK}h))")
PREV_PERIOD_ERRORS=$(query_prom "sum(increase(nucleus_nucleus_anon_commands_total{nucleus_error_type!=\"\"}[${LOOKBACK}h] offset ${LOOKBACK}h))")

# Calculate percentage changes
if [ "$(echo "$PREV_PERIOD_COMMANDS > 0" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
  COMMAND_CHANGE=$(echo "scale=1; ($TOTAL_COMMANDS - $PREV_PERIOD_COMMANDS) * 100 / $PREV_PERIOD_COMMANDS" | bc -l 2>/dev/null || echo "0")
  PREV_ERROR_RATE=$(echo "scale=2; $PREV_PERIOD_ERRORS * 100 / $PREV_PERIOD_COMMANDS" | bc -l 2>/dev/null || echo "0")
  ERROR_RATE_CHANGE=$(echo "scale=1; $ERROR_RATE - $PREV_ERROR_RATE" | bc -l 2>/dev/null || echo "0")
  
  printf "  Commands:   %s → %s (" "$PREV_PERIOD_COMMANDS" "$TOTAL_COMMANDS"
  if [ "$(echo "$COMMAND_CHANGE >= 0" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
    printf "↑ +%s%%)\n" "$COMMAND_CHANGE"
  else
    printf "↓ %s%%)\n" "$COMMAND_CHANGE"
  fi
  
  printf "  Error rate: %s%% → %s%% (" "$PREV_ERROR_RATE" "$ERROR_RATE"
  if [ "$(echo "$ERROR_RATE_CHANGE >= 0" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
    printf "↑ +%s%%)\n" "$ERROR_RATE_CHANGE"
  else
    printf "↓ %s%%)\n" "$ERROR_RATE_CHANGE"
  fi
else
  echo "  Insufficient data for comparison (previous period: 0 commands)"
fi
echo ""

# ── 9. Anomaly Detection (Phase D) ──
echo "🔍 ANOMALY DETECTION"
echo "────────────────────────────────────────────────────────────"

# Calculate rolling mean and stddev over 24h windows for the last 7 days
# Using simple statistical approach: current rate vs historical mean ± 3σ
CURRENT_RATE=$(query_prom "sum(rate(nucleus_nucleus_anon_commands_total[1h]))")
HISTORICAL_MEAN=$(query_prom "avg_over_time((sum(rate(nucleus_nucleus_anon_commands_total[1h])))[7d:1h])")
HISTORICAL_STDDEV=$(query_prom "stddev_over_time((sum(rate(nucleus_nucleus_anon_commands_total[1h])))[7d:1h])")

ANOMALIES_DETECTED=0

if [ "$(echo "$HISTORICAL_STDDEV > 0" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
  # Calculate Z-score: (current - mean) / stddev
  Z_SCORE=$(echo "scale=2; ($CURRENT_RATE - $HISTORICAL_MEAN) / $HISTORICAL_STDDEV" | bc -l 2>/dev/null || echo "0")
  Z_SCORE_ABS=$(echo "$Z_SCORE" | tr -d '-')
  
  if [ "$(echo "$Z_SCORE_ABS > 3" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
    ANOMALIES_DETECTED=1
    printf "  ⚠️  Command rate anomaly detected!\n"
    printf "      Current rate:     %.4f commands/sec\n" "$CURRENT_RATE"
    printf "      Historical mean:  %.4f commands/sec\n" "$HISTORICAL_MEAN"
    printf "      Std deviation:    %.4f\n" "$HISTORICAL_STDDEV"
    printf "      Z-score:          %s (threshold: ±3σ)\n" "$Z_SCORE"
    if [ "$(echo "$Z_SCORE > 0" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
      echo "      → Unusually HIGH activity"
    else
      echo "      → Unusually LOW activity"
    fi
  fi
fi

# Check error rate anomaly
CURRENT_ERROR_RATE_DECIMAL=$(echo "scale=4; $ERROR_RATE / 100" | bc -l 2>/dev/null || echo "0")
HISTORICAL_ERROR_MEAN=$(query_prom "avg_over_time((sum(rate(nucleus_nucleus_anon_commands_total{nucleus_error_type!=\"\"}[1h])) / sum(rate(nucleus_nucleus_anon_commands_total[1h])))[7d:1h])")
HISTORICAL_ERROR_STDDEV=$(query_prom "stddev_over_time((sum(rate(nucleus_nucleus_anon_commands_total{nucleus_error_type!=\"\"}[1h])) / sum(rate(nucleus_nucleus_anon_commands_total[1h])))[7d:1h])")

if [ "$(echo "$HISTORICAL_ERROR_STDDEV > 0" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
  ERROR_Z_SCORE=$(echo "scale=2; ($CURRENT_ERROR_RATE_DECIMAL - $HISTORICAL_ERROR_MEAN) / $HISTORICAL_ERROR_STDDEV" | bc -l 2>/dev/null || echo "0")
  ERROR_Z_SCORE_ABS=$(echo "$ERROR_Z_SCORE" | tr -d '-')
  
  if [ "$(echo "$ERROR_Z_SCORE_ABS > 3" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
    ANOMALIES_DETECTED=1
    printf "  ⚠️  Error rate anomaly detected!\n"
    printf "      Current error rate:     %s%%\n" "$ERROR_RATE"
    printf "      Historical mean:        %.2f%%\n" "$(echo "$HISTORICAL_ERROR_MEAN * 100" | bc -l 2>/dev/null || echo "0")"
    printf "      Z-score:                %s (threshold: ±3σ)\n" "$ERROR_Z_SCORE"
    echo "      → Investigate recent error types above"
  fi
fi

if [ "$ANOMALIES_DETECTED" = "0" ]; then
  echo "  ✅ No statistical anomalies detected (3σ threshold)"
  printf "      Command rate Z-score: %s\n" "${Z_SCORE:-N/A}"
  printf "      Error rate Z-score:   %s\n" "${ERROR_Z_SCORE:-N/A}"
fi
echo ""

# ── 10. Insights ──
echo "💡 INSIGHTS"
echo "────────────────────────────────────────────────────────────"

if [ "$(echo "$TOTAL_COMMANDS == 0" | bc -l 2>/dev/null || echo 1)" = "1" ]; then
  echo "  ⚠️  No commands recorded in the last ${LOOKBACK}h"
  echo "      - Check if telemetry is enabled"
  echo "      - Verify collector is running: docker ps | grep nucleus-otel-collector"
  echo "      - Test: npm run telemetry:local:demo -- morning-brief"
elif [ "$(echo "$ERROR_RATE > 10" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
  echo "  🔴 High error rate detected (${ERROR_RATE}%)"
  echo "      - Review error types above"
  echo "      - Check Grafana alerts: http://localhost:3000/alerting/list"
  echo "      - Investigate with: npm run telemetry:summary"
elif [ "$(echo "$ERROR_RATE > 5" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
  echo "  🟡 Elevated error rate (${ERROR_RATE}%)"
  echo "      - Monitor for trends"
  echo "      - Review top error types"
else
  echo "  ✅ Telemetry pipeline healthy"
  echo "      - ${TOTAL_COMMANDS} commands processed"
  echo "      - Error rate: ${ERROR_RATE}%"
  echo "      - Median latency: ${P50}ms"
fi

echo ""

# ── 11. Recent Incidents (Phase E) ──
INCIDENTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/incidents"
ACTIONS_LOG="${INCIDENTS_DIR}/actions.log"

echo "🚨 RECENT INCIDENTS (Last ${LOOKBACK}h)"
echo "────────────────────────────────────────────────────────────"

INCIDENT_COUNT=0
if [ -d "$INCIDENTS_DIR" ]; then
  CUTOFF=$(date -v-${LOOKBACK}H +%Y-%m-%dT%H:%M:%S 2>/dev/null || date -d "${LOOKBACK} hours ago" +%Y-%m-%dT%H:%M:%S 2>/dev/null || echo "")
  
  # Find recent incident reports
  RECENT_REPORTS=$(find "$INCIDENTS_DIR" -name "INCIDENT-*.md" -mmin -$((LOOKBACK * 60)) 2>/dev/null | sort -r | head -10)
  if [ -n "$RECENT_REPORTS" ]; then
    while IFS= read -r report; do
      INCIDENT_COUNT=$((INCIDENT_COUNT + 1))
      BASENAME=$(basename "$report" .md)
      SEVERITY=$(grep -m1 "Severity" "$report" | sed 's/.*\*\*\(.*\)\*\*.*/\1/' 2>/dev/null || echo "unknown")
      SUMMARY=$(grep -m1 "Summary |" "$report" | sed 's/.*| //' 2>/dev/null || echo "")
      printf "  %s %s — %s\n" "$BASENAME" "$SEVERITY" "$SUMMARY"
    done <<< "$RECENT_REPORTS"
  fi
fi

# Count recent automated actions
if [ -f "$ACTIONS_LOG" ]; then
  ACTION_COUNT=$(tail -100 "$ACTIONS_LOG" | python3 -c "
import sys, json, datetime
cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=${LOOKBACK})
count = 0
for line in sys.stdin:
    try:
        e = json.loads(line.strip())
        t = datetime.datetime.fromisoformat(e['timestamp'].replace('Z',''))
        if t > cutoff:
            count += 1
    except: pass
print(count)
" 2>/dev/null || echo "0")
  
  if [ "$ACTION_COUNT" -gt 0 ]; then
    echo ""
    echo "  Automated actions in last ${LOOKBACK}h: ${ACTION_COUNT}"
    echo "  Recent actions:"
    tail -5 "$ACTIONS_LOG" | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line.strip())
        print(f\"    {e['timestamp'][:19]}  {e['action']} on {e['target']} → {e['result']}\")
    except: pass
" 2>/dev/null
  fi
fi

if [ "$INCIDENT_COUNT" = "0" ]; then
  echo "  ✅ No incidents in the last ${LOOKBACK}h"
fi
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "  Quick Actions:"
echo "    • Grafana dashboard: http://localhost:3000/d/nucleus-anon-usage"
echo "    • Grafana trends:    http://localhost:3000/d/nucleus-trends"
echo "    • Prometheus:        http://localhost:9090"
echo "    • Jaeger traces:     http://localhost:16686"
echo "    • Incident check:    npm run incident:check"
echo "═══════════════════════════════════════════════════════════"
