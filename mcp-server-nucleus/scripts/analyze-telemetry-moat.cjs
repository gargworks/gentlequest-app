#!/usr/bin/env node

/**
 * TELEMETRY DATA MOAT ANALYZER
 * 
 * Extracts competitive intelligence from collected OTLP spans to create
 * an undefeated data moat flywheel.
 * 
 * What this analyzes:
 * 1. Usage patterns - which tools/actions are most valuable
 * 2. Performance bottlenecks - where users wait
 * 3. Error patterns - what fails and why
 * 4. Feature adoption - what gets used vs ignored
 * 5. User journey - how users flow through the system
 * 6. Time-to-value - how fast users get results
 */

const fs = require('fs');
const path = require('path');

const TRACES_FILE = path.join(__dirname, '../.telemetry/traces.jsonl');
const OUTPUT_DIR = path.join(__dirname, '../.telemetry/insights');

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

function loadSpans() {
  if (!fs.existsSync(TRACES_FILE)) {
    console.log('[moat] No traces file found. Run the collector first.');
    return [];
  }

  const lines = fs.readFileSync(TRACES_FILE, 'utf8').split('\n').filter(Boolean);
  const spans = [];

  for (const line of lines) {
    try {
      const data = JSON.parse(line);
      if (data.resourceSpans) {
        for (const rs of data.resourceSpans) {
          for (const ss of rs.scopeSpans || []) {
            for (const span of ss.spans || []) {
              spans.push({
                name: span.name,
                traceId: span.traceId,
                spanId: span.spanId,
                parentSpanId: span.parentSpanId,
                startTime: parseInt(span.startTimeUnixNano) / 1e9,
                endTime: parseInt(span.endTimeUnixNano) / 1e9,
                duration: (parseInt(span.endTimeUnixNano) - parseInt(span.startTimeUnixNano)) / 1e6, // ms
                attributes: (span.attributes || []).reduce((acc, attr) => {
                  acc[attr.key] = attr.value.stringValue || attr.value.intValue || attr.value.boolValue;
                  return acc;
                }, {}),
                resource: (rs.resource?.attributes || []).reduce((acc, attr) => {
                  acc[attr.key] = attr.value.stringValue || attr.value.intValue || attr.value.boolValue;
                  return acc;
                }, {}),
              });
            }
          }
        }
      }
    } catch (e) {
      // Skip malformed lines
    }
  }

  return spans;
}

function analyzeUsagePatterns(spans) {
  const toolCounts = {};
  const actionCounts = {};
  const serviceCounts = {};

  for (const span of spans) {
    const tool = span.attributes['mcp.tool'] || span.name;
    const action = span.attributes['nucleus.action'];
    const service = span.resource['service.name'];

    toolCounts[tool] = (toolCounts[tool] || 0) + 1;
    if (action) actionCounts[action] = (actionCounts[action] || 0) + 1;
    if (service) serviceCounts[service] = (serviceCounts[service] || 0) + 1;
  }

  return {
    totalSpans: spans.length,
    uniqueTools: Object.keys(toolCounts).length,
    uniqueActions: Object.keys(actionCounts).length,
    topTools: Object.entries(toolCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([tool, count]) => ({ tool, count, percentage: (count / spans.length * 100).toFixed(1) })),
    topActions: Object.entries(actionCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([action, count]) => ({ action, count, percentage: (count / spans.length * 100).toFixed(1) })),
    services: serviceCounts,
  };
}

function analyzePerformance(spans) {
  const durations = spans.map(s => s.duration).filter(d => d > 0);
  durations.sort((a, b) => a - b);

  const p50 = durations[Math.floor(durations.length * 0.5)] || 0;
  const p95 = durations[Math.floor(durations.length * 0.95)] || 0;
  const p99 = durations[Math.floor(durations.length * 0.99)] || 0;

  const slowSpans = spans
    .filter(s => s.duration > p95)
    .sort((a, b) => b.duration - a.duration)
    .slice(0, 10)
    .map(s => ({
      name: s.name,
      duration: s.duration.toFixed(2) + 'ms',
      tool: s.attributes['mcp.tool'] || 'unknown',
    }));

  return {
    totalDuration: durations.reduce((a, b) => a + b, 0).toFixed(2) + 'ms',
    avgDuration: (durations.reduce((a, b) => a + b, 0) / durations.length).toFixed(2) + 'ms',
    p50: p50.toFixed(2) + 'ms',
    p95: p95.toFixed(2) + 'ms',
    p99: p99.toFixed(2) + 'ms',
    slowestSpans: slowSpans,
  };
}

function analyzeErrors(spans) {
  const errors = spans.filter(s => 
    s.attributes['error'] === 'true' || 
    s.attributes['exception.type'] ||
    s.attributes['http.status_code'] >= 400
  );

  const errorTypes = {};
  for (const span of errors) {
    const type = span.attributes['exception.type'] || span.attributes['error.type'] || 'unknown';
    errorTypes[type] = (errorTypes[type] || 0) + 1;
  }

  return {
    totalErrors: errors.length,
    errorRate: ((errors.length / spans.length) * 100).toFixed(2) + '%',
    errorTypes: Object.entries(errorTypes)
      .sort((a, b) => b[1] - a[1])
      .map(([type, count]) => ({ type, count })),
    recentErrors: errors.slice(-5).map(s => ({
      name: s.name,
      type: s.attributes['exception.type'] || 'unknown',
      message: s.attributes['exception.message'] || 'no message',
    })),
  };
}

function analyzeUserJourneys(spans) {
  const traces = {};
  
  for (const span of spans) {
    if (!traces[span.traceId]) {
      traces[span.traceId] = [];
    }
    traces[span.traceId].push(span);
  }

  const journeys = Object.entries(traces).map(([traceId, spans]) => {
    spans.sort((a, b) => a.startTime - b.startTime);
    const duration = spans[spans.length - 1].endTime - spans[0].startTime;
    
    return {
      traceId: traceId.substring(0, 16),
      spanCount: spans.length,
      duration: (duration * 1000).toFixed(2) + 'ms',
      path: spans.map(s => s.name).join(' → '),
    };
  });

  journeys.sort((a, b) => b.spanCount - a.spanCount);

  return {
    totalTraces: Object.keys(traces).length,
    avgSpansPerTrace: (spans.length / Object.keys(traces).length).toFixed(1),
    topJourneys: journeys.slice(0, 5),
  };
}

function generateDataMoatInsights(analysis) {
  const insights = {
    timestamp: new Date().toISOString(),
    summary: {
      totalSpans: analysis.usage.totalSpans,
      totalTraces: analysis.journeys.totalTraces,
      errorRate: analysis.errors.errorRate,
      avgLatency: analysis.performance.avgDuration,
    },
    moatSignals: [],
  };

  // Signal 1: Feature adoption velocity
  if (analysis.usage.topTools.length > 0) {
    const topTool = analysis.usage.topTools[0];
    insights.moatSignals.push({
      signal: 'FEATURE_ADOPTION',
      strength: 'HIGH',
      finding: `${topTool.tool} is the killer feature (${topTool.percentage}% of usage)`,
      action: 'Double down on this tool. Build more features around it.',
    });
  }

  // Signal 2: Performance bottlenecks
  if (analysis.performance.slowestSpans.length > 0) {
    const slowest = analysis.performance.slowestSpans[0];
    insights.moatSignals.push({
      signal: 'PERFORMANCE_BOTTLENECK',
      strength: 'MEDIUM',
      finding: `${slowest.name} takes ${slowest.duration} (p95: ${analysis.performance.p95})`,
      action: 'Optimize this operation. Users are waiting here.',
    });
  }

  // Signal 3: Error patterns
  if (parseFloat(analysis.errors.errorRate) > 5) {
    insights.moatSignals.push({
      signal: 'RELIABILITY_ISSUE',
      strength: 'HIGH',
      finding: `Error rate is ${analysis.errors.errorRate} - above 5% threshold`,
      action: 'Fix top error types immediately. This is killing user trust.',
    });
  } else {
    insights.moatSignals.push({
      signal: 'RELIABILITY_STRENGTH',
      strength: 'HIGH',
      finding: `Error rate is ${analysis.errors.errorRate} - excellent reliability`,
      action: 'Maintain this quality. Reliability is your moat.',
    });
  }

  // Signal 4: User journey complexity
  const avgSpans = parseFloat(analysis.journeys.avgSpansPerTrace);
  if (avgSpans > 10) {
    insights.moatSignals.push({
      signal: 'JOURNEY_COMPLEXITY',
      strength: 'MEDIUM',
      finding: `Users take ${avgSpans} steps on average - complex workflows`,
      action: 'Consider simplifying common paths or adding shortcuts.',
    });
  }

  // Signal 5: Data moat growth
  insights.moatSignals.push({
    signal: 'DATA_MOAT_GROWTH',
    strength: 'COMPOUNDING',
    finding: `Collected ${analysis.usage.totalSpans} spans across ${analysis.usage.uniqueTools} tools`,
    action: 'Every span makes your AI smarter. This data is your unfair advantage.',
  });

  return insights;
}

function main() {
  console.log('[moat] 🔍 Analyzing telemetry data moat...\n');

  const spans = loadSpans();
  
  if (spans.length === 0) {
    console.log('[moat] ⚠️  No spans found. Start using Nucleus to collect data.\n');
    return;
  }

  console.log(`[moat] 📊 Loaded ${spans.length} spans\n`);

  const analysis = {
    usage: analyzeUsagePatterns(spans),
    performance: analyzePerformance(spans),
    errors: analyzeErrors(spans),
    journeys: analyzeUserJourneys(spans),
  };

  const insights = generateDataMoatInsights(analysis);

  // Save detailed analysis
  fs.writeFileSync(
    path.join(OUTPUT_DIR, 'full-analysis.json'),
    JSON.stringify(analysis, null, 2)
  );

  // Save insights
  fs.writeFileSync(
    path.join(OUTPUT_DIR, 'moat-insights.json'),
    JSON.stringify(insights, null, 2)
  );

  // Print summary
  console.log('═══════════════════════════════════════════════════════════');
  console.log('📈 TELEMETRY DATA MOAT ANALYSIS');
  console.log('═══════════════════════════════════════════════════════════\n');

  console.log('📊 USAGE PATTERNS');
  console.log('─────────────────────────────────────────────────────────');
  console.log(`Total spans:        ${analysis.usage.totalSpans}`);
  console.log(`Unique tools:       ${analysis.usage.uniqueTools}`);
  console.log(`Unique actions:     ${analysis.usage.uniqueActions}`);
  console.log(`\nTop tools:`);
  analysis.usage.topTools.forEach((t, i) => {
    console.log(`  ${i + 1}. ${t.tool.padEnd(40)} ${t.count.toString().padStart(5)} (${t.percentage}%)`);
  });

  console.log('\n⚡ PERFORMANCE');
  console.log('─────────────────────────────────────────────────────────');
  console.log(`Average latency:    ${analysis.performance.avgDuration}`);
  console.log(`P50:                ${analysis.performance.p50}`);
  console.log(`P95:                ${analysis.performance.p95}`);
  console.log(`P99:                ${analysis.performance.p99}`);

  console.log('\n🚨 ERRORS');
  console.log('─────────────────────────────────────────────────────────');
  console.log(`Total errors:       ${analysis.errors.totalErrors}`);
  console.log(`Error rate:         ${analysis.errors.errorRate}`);

  console.log('\n🗺️  USER JOURNEYS');
  console.log('─────────────────────────────────────────────────────────');
  console.log(`Total traces:       ${analysis.journeys.totalTraces}`);
  console.log(`Avg spans/trace:    ${analysis.journeys.avgSpansPerTrace}`);

  console.log('\n🏰 DATA MOAT SIGNALS');
  console.log('═══════════════════════════════════════════════════════════');
  insights.moatSignals.forEach((signal, i) => {
    console.log(`\n${i + 1}. ${signal.signal} [${signal.strength}]`);
    console.log(`   Finding: ${signal.finding}`);
    console.log(`   Action:  ${signal.action}`);
  });

  console.log('\n═══════════════════════════════════════════════════════════');
  console.log(`\n💾 Full analysis saved to:`);
  console.log(`   ${OUTPUT_DIR}/full-analysis.json`);
  console.log(`   ${OUTPUT_DIR}/moat-insights.json\n`);
}

main();
