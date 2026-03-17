#!/bin/bash

# Nucleus Telemetry Status - One command to check everything
# Usage: ./scripts/telemetry-status.sh

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 NUCLEUS TELEMETRY STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check services
echo "📊 SERVICES"
echo "──────────────────────────────────────────────────────────────"

if docker ps | grep -q nucleus-otel-collector; then
    echo "✅ Collector: Running"
else
    echo "❌ Collector: Not running"
    echo "   Fix: docker start nucleus-otel-collector"
fi

if ps aux | grep -q "[c]loudflared tunnel run nucleus-telemetry"; then
    echo "✅ Tunnel: Running"
else
    echo "❌ Tunnel: Not running"
    echo "   Fix: cloudflared tunnel run nucleus-telemetry &"
fi

if launchctl list | grep -q com.nucleus.telemetry; then
    echo "✅ Auto-start: Configured"
else
    echo "⚠️  Auto-start: Not configured"
fi

echo ""

# Check data
echo "💾 DATA COLLECTED"
echo "──────────────────────────────────────────────────────────────"

if [ -f .telemetry/traces.jsonl ]; then
    TRACES=$(wc -l < .telemetry/traces.jsonl 2>/dev/null || echo "0")
    SIZE=$(du -h .telemetry/traces.jsonl 2>/dev/null | cut -f1 || echo "0B")
    echo "📈 Traces: $TRACES lines ($SIZE)"
else
    echo "📈 Traces: No data yet"
fi

if [ -f .telemetry/metrics.jsonl ]; then
    METRICS=$(wc -l < .telemetry/metrics.jsonl 2>/dev/null || echo "0")
    echo "📊 Metrics: $METRICS lines"
else
    echo "📊 Metrics: No data yet"
fi

echo ""

# Check Cloudflare
echo "🌐 CLOUDFLARE ROUTE"
echo "──────────────────────────────────────────────────────────────"

if curl -s -o /dev/null -w "%{http_code}" https://telemetry.nucleusos.dev/v1/traces 2>/dev/null | grep -q "200"; then
    echo "✅ telemetry.nucleusos.dev: Reachable (HTTP 200)"
else
    echo "⚠️  telemetry.nucleusos.dev: Not reachable"
fi

echo ""

# Quick actions
echo "🎯 QUICK ACTIONS"
echo "──────────────────────────────────────────────────────────────"
echo "View insights:  cat .telemetry/insights/moat-insights.json | jq ."
echo "Analyze data:   node scripts/analyze-telemetry-moat.cjs"
echo "View logs:      docker logs nucleus-otel-collector --tail 50"
echo "Test telemetry: NUCLEUS_ANON_TELEMETRY=true nucleus morning-brief"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Everything is zero-touch. Just use Nucleus normally."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
