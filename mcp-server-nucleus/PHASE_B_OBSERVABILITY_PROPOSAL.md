# Phase B: Observability Dashboards – Jaeger + Grafana Integration

**Status:** Proposal (ready for implementation)  
**Prerequisites:** Phase A complete ✅ (HTTP exporters, Worker, Tunnel, Collector all verified working)  
**Estimated effort:** 2-3 hours  
**Value:** Visual trace exploration, performance analysis, error tracking

---

## 1. Objectives

Transform raw telemetry data into actionable insights through:

1. **Jaeger UI** - Visual trace exploration and dependency graphs
2. **Grafana dashboards** - Time-series metrics and alerting
3. **Prometheus** - Metrics storage and querying
4. **Zero-config setup** - Single command brings up full stack

---

## 2. Architecture

```
Nucleus CLI (OTLP HTTP)
    ↓
Cloudflare Worker → Tunnel → localhost:4318
    ↓
OpenTelemetry Collector
    ├─→ Jaeger (traces)
    ├─→ Prometheus (metrics)
    └─→ File exporters (backup)
         ↓
    Grafana (visualization)
```

**Key decision:** Keep existing file exporters as backup. Add Jaeger + Prometheus exporters in parallel.

---

## 3. Implementation Plan

### 3.1 Update OpenTelemetry Collector Config

**File:** `infra/telemetry/otel-collector-config.yaml`

Add exporters:

```yaml
exporters:
  # Existing file exporters (keep as backup)
  file/traces:
    path: /telemetry-data/traces.jsonl
    # ... existing config
  
  file/metrics:
    path: /telemetry-data/metrics.jsonl
    # ... existing config
  
  # NEW: Jaeger exporter for traces
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  
  # NEW: Prometheus exporter for metrics
  prometheus:
    endpoint: "0.0.0.0:8889"
    # Already configured, just verify it's enabled

  # Keep debug exporter for development
  debug:
    verbosity: detailed
    sampling_initial: 5
    sampling_thereafter: 200

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [file/traces, jaeger, debug]  # Add jaeger
    
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [file/metrics, prometheus, debug]  # Already has prometheus
```

### 3.2 Create Docker Compose Stack

**File:** `infra/telemetry/docker-compose.yml`

```yaml
version: '3.8'

services:
  # Existing collector (update to use this compose file)
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.147.0
    container_name: nucleus-otel-collector
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
      - ../../.telemetry:/telemetry-data
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8889:8889"   # Prometheus metrics
      - "13133:13133" # Health check
    networks:
      - telemetry
    restart: unless-stopped

  # Jaeger all-in-one (traces backend + UI)
  jaeger:
    image: jaegertracing/all-in-one:1.53
    container_name: nucleus-jaeger
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "16686:16686"  # Jaeger UI
      - "14250:14250"  # gRPC receiver (for collector)
    networks:
      - telemetry
    restart: unless-stopped

  # Prometheus (metrics backend)
  prometheus:
    image: prom/prometheus:v2.48.1
    container_name: nucleus-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"  # Prometheus UI
    networks:
      - telemetry
    restart: unless-stopped

  # Grafana (visualization)
  grafana:
    image: grafana/grafana:10.2.3
    container_name: nucleus-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=nucleus
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"  # Grafana UI
    networks:
      - telemetry
    depends_on:
      - prometheus
      - jaeger
    restart: unless-stopped

networks:
  telemetry:
    driver: bridge

volumes:
  prometheus-data:
  grafana-data:
```

### 3.3 Create Prometheus Config

**File:** `infra/telemetry/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Scrape metrics from OpenTelemetry Collector
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8889']
        labels:
          service: 'nucleus-collector'

  # Scrape Prometheus self-metrics
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

### 3.4 Create Grafana Provisioning

**File:** `infra/telemetry/grafana/provisioning/datasources/datasources.yml`

```yaml
apiVersion: 1

datasources:
  # Prometheus datasource
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  # Jaeger datasource
  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:16686
    editable: false
```

**File:** `infra/telemetry/grafana/provisioning/dashboards/dashboards.yml`

```yaml
apiVersion: 1

providers:
  - name: 'Nucleus Dashboards'
    orgId: 1
    folder: 'Nucleus'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
```

### 3.5 Create Nucleus Dashboard

**File:** `infra/telemetry/grafana/dashboards/nucleus-overview.json`

```json
{
  "dashboard": {
    "title": "Nucleus Telemetry Overview",
    "panels": [
      {
        "title": "Spans per Service",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(nucleus_anon_commands_total[5m])",
            "legendFormat": "{{nucleus_command}}"
          }
        ]
      },
      {
        "title": "Command Duration (p95)",
        "type": "timeseries",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(nucleus_anon_command_duration_ms_bucket[5m]))",
            "legendFormat": "{{nucleus_command}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(nucleus_anon_commands_total{nucleus_error_type!=\"\"}[5m])",
            "legendFormat": "{{nucleus_error_type}}"
          }
        ]
      }
    ]
  }
}
```

### 3.6 Update Scripts

**File:** `package.json` (add new scripts)

```json
{
  "scripts": {
    "telemetry:up": "bash scripts/telemetry.sh up",
    "telemetry:down": "bash scripts/telemetry.sh down",
    "telemetry:dash": "cd infra/telemetry && docker compose up -d",
    "telemetry:dash:down": "cd infra/telemetry && docker compose down",
    "telemetry:dash:logs": "cd infra/telemetry && docker compose logs -f",
    "telemetry:open:jaeger": "open http://localhost:16686",
    "telemetry:open:grafana": "open http://localhost:3000",
    "telemetry:open:prometheus": "open http://localhost:9090"
  }
}
```

**Update:** `scripts/telemetry.sh`

```bash
#!/bin/bash
set -e

case "$1" in
  up)
    echo "Starting full observability stack..."
    cd infra/telemetry && docker compose up -d
    echo "✅ Stack started:"
    echo "   Jaeger UI:     http://localhost:16686"
    echo "   Grafana:       http://localhost:3000 (admin/nucleus)"
    echo "   Prometheus:    http://localhost:9090"
    echo "   Collector:     localhost:4318 (HTTP OTLP)"
    ;;
  down)
    echo "Stopping observability stack..."
    cd infra/telemetry && docker compose down
    ;;
  *)
    echo "Usage: $0 {up|down}"
    exit 1
    ;;
esac
```

---

## 4. Usage

### 4.1 Start Full Stack

```bash
npm run telemetry:dash
```

This brings up:
- OpenTelemetry Collector (ports 4317, 4318, 8889)
- Jaeger UI (http://localhost:16686)
- Grafana (http://localhost:3000, admin/nucleus)
- Prometheus (http://localhost:9090)

### 4.2 Send Test Telemetry

```bash
NUCLEUS_ANON_TELEMETRY=true nucleus morning-brief
```

### 4.3 View Traces in Jaeger

```bash
npm run telemetry:open:jaeger
```

- Search for service: `nucleus-anon-telemetry`
- View trace timeline and spans
- Analyze dependencies and latencies

### 4.4 View Metrics in Grafana

```bash
npm run telemetry:open:grafana
```

- Login: admin / nucleus
- Navigate to "Nucleus" folder
- Open "Nucleus Telemetry Overview" dashboard
- View command rates, durations, errors

---

## 5. Verification Checklist

After implementation, verify:

```bash
# 1. All containers running
docker ps | grep nucleus

# 2. Collector exporting to Jaeger
curl http://localhost:16686/api/services
# Should show: ["nucleus-anon-telemetry"]

# 3. Prometheus scraping metrics
curl http://localhost:9090/api/v1/targets
# Should show otel-collector target as UP

# 4. Grafana datasources configured
curl -u admin:nucleus http://localhost:3000/api/datasources
# Should show Prometheus and Jaeger

# 5. Send test telemetry and verify in Jaeger
NUCLEUS_ANON_TELEMETRY=true nucleus morning-brief
# Wait 5s, then check Jaeger UI for new traces
```

---

## 6. Documentation Updates Required

After implementation, update these files:

1. **TELEMETRY_PIPELINE_README.md**
   - Add section 2.3: "Observability Stack (Jaeger + Grafana)"
   - Update architecture diagram
   - Add verification commands for dashboards

2. **TELEMETRY_QUICKSTART.md**
   - Add "Quick Start with Dashboards" section
   - Document `npm run telemetry:dash` command
   - Add screenshots of Jaeger and Grafana

3. **CURRENT_STATUS.md**
   - Mark Phase B as complete
   - Add dashboard URLs to environment facts

4. **README_TELEMETRY.md**
   - Add "View insights" commands for Jaeger/Grafana

---

## 7. Benefits

**For Developers:**
- Visual trace exploration (no more grepping logs)
- Performance bottleneck identification
- Error tracking and debugging

**For LLMs:**
- Structured query interface (Prometheus PromQL)
- JSON API access to traces (Jaeger API)
- Dashboard-as-code (Grafana JSON)

**For Product:**
- Real-time usage analytics
- Performance regression detection
- User journey visualization

---

## 8. Next Steps (Phase C)

After Phase B is complete:

1. **Automated alerts** - Grafana alerts for error spikes, latency regressions
2. **Daily telemetry brief** - Script that queries Jaeger/Prometheus and generates summary
3. **Embedding/search** - Index interesting traces for LLM memory
4. **Guided debugging** - Playbooks linking dashboard patterns to fixes

---

**Ready to implement:** All prerequisites met, architecture validated, no blockers.
