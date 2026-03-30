# Nucleus Observability Portal

Quick reference for all telemetry and observability endpoints.

> Architecture docs: `WINDSURF_SUPER_PROMPT.md` (Phase B3)

## Local Development (Lokesh's Mac)

| Service | URL | Notes |
|---------|-----|-------|
| OTel Collector (gRPC) | `localhost:4317` | OTLP gRPC ingest |
| OTel Collector (HTTP) | `localhost:4318` | OTLP HTTP ingest |
| Collector Health | `localhost:13133` | Health check |
| Jaeger UI | `http://localhost:16686` | Trace viewer (when `telemetry:dash` is running) |
| Prometheus | `http://localhost:9090` | Metrics (when `telemetry:dash` is running) |
| Grafana | `http://localhost:3000` | Dashboards (admin/admin) |

## Production (telemetry.nucleusos.dev)

| Service | URL | Notes |
|---------|-----|-------|
| OTLP gRPC Ingest | `telemetry.nucleusos.dev:4317` | TLS via Caddy |
| OTLP HTTP Ingest | `https://telemetry.nucleusos.dev/v1/traces` | TLS via Caddy |
| Health Check | `https://telemetry.nucleusos.dev/health` | Public |
| Grafana | `https://telemetry.nucleusos.dev:3000` | Restrict via firewall |

## Cloudflare (Edge)

| Service | URL | Notes |
|---------|-----|-------|
| Worker Ingest | `https://nucleus-telemetry.<account>.workers.dev/v1/traces` | POST OTLP spans |
| Upstash Redis REST | `https://moral-swine-69544.upstash.io` | Queue inspection |
| Upstash Queue Key | `nucleus:spans` | LRANGE to inspect |

## Quick Commands

```bash
# Start full local stack
npm run telemetry:all

# Start with Jaeger + Grafana
npm run telemetry:dash

# Check everything is wired
npm run telemetry:audit

# Daily brief
npm run telemetry:brief

# Quick summary
npm run telemetry:summary

# Stop everything
npm run telemetry:down
```

## Default Credentials

| Service | Username | Password | Notes |
|---------|----------|----------|-------|
| Grafana (local) | admin | admin | Change on first login |
| Grafana (prod) | admin | admin | **CHANGE IMMEDIATELY** |
| Prometheus | n/a | n/a | No auth (internal only) |
| Jaeger | n/a | n/a | No auth (local only) |

## Grafana Dashboards

| Dashboard | UID | Description |
|-----------|-----|-------------|
| Nucleus Anonymous Usage | `nucleus-anon-usage` | 10-panel overview: commands, errors, versions, OS |

## Architecture Diagram

```
Nucleus CLI / MCP Server
    │
    │  OTLP gRPC/HTTP
    ▼
┌──────────────────────────┐     ┌─────────────────┐
│  Cloudflare Worker       │────▶│  Upstash Redis   │
│  (edge ingest)           │     │  (buffer queue)  │
└──────────┬───────────────┘     └────────┬─────────┘
           │ direct (tunnel)              │ drain script
           ▼                              ▼
┌──────────────────────────────────────────────────┐
│  OTel Collector (nucleus-otel-collector)          │
│  - Debug exporter (logs)                          │
│  - Prometheus exporter (:8889)                    │
│  - File exporter (/var/log/nucleus-telemetry/)    │
└──────────┬──────────────┬────────────────────────┘
           │              │
           ▼              ▼
      Prometheus      Jaeger/Tempo
           │
           ▼
        Grafana
```

---

*Keep this file in sync with any endpoint or credential changes.*
