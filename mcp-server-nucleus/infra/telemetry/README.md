# Nucleus Anonymous Telemetry — Server Setup

Production-ready OpenTelemetry collector stack for `telemetry.nucleusos.dev`.

## Architecture

```
Nucleus CLI / MCP Server
    │
    │  OTLP gRPC (port 4317)
    ▼
┌─────────────────────────────────┐
│  Caddy (TLS + Let's Encrypt)   │ ← telemetry.nucleusos.dev
└──────────┬──────────────────────┘
           │
┌──────────▼──────────────────────┐
│  OTel Collector                 │
│  - Receives OTLP gRPC/HTTP     │
│  - Exports → Prometheus         │
│  - Exports → File (backup)      │
└──────────┬──────────────────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
Prometheus    File Logs
    │         /var/log/nucleus-telemetry/
    ▼
 Grafana
 (dashboards)
```

## Prerequisites

- A VPS with Docker + Docker Compose (1 vCPU, 1GB RAM, 10GB disk is enough)
- Domain `telemetry.nucleusos.dev` pointing to the VPS IP
- Ports 80, 443, 4317 open in firewall

## Deployment Steps

### 1. DNS Setup

Add an A record in your DNS provider (wherever nucleusos.dev is managed):

```
telemetry.nucleusos.dev  →  A  →  <YOUR_VPS_IP>
```

### 2. Deploy the Stack

```bash
# SSH into your VPS
ssh root@<YOUR_VPS_IP>

# Clone or copy the infra/telemetry directory
mkdir -p /opt/nucleus-telemetry
cd /opt/nucleus-telemetry

# Copy all files from this directory, then:
docker compose up -d
```

### 3. Verify

```bash
# Health check
curl https://telemetry.nucleusos.dev/health

# Prometheus metrics
curl http://localhost:9090/api/v1/query?query=nucleus_nucleus_anon_commands_total

# Grafana (change password on first login!)
open https://telemetry.nucleusos.dev:3000
# Default: admin / admin
```

### 4. Test from a Nucleus Client

```bash
# On any machine with Nucleus installed:
nucleus morning-brief
# Check the collector logs:
docker logs nucleus-otel-collector --tail 20
```

## Files

| File | Purpose |
|------|---------|
| `docker-compose.yaml` | Full stack: OTel Collector + Prometheus + Grafana + Caddy |
| `otel-collector-config.yaml` | Collector receivers, processors, exporters |
| `prometheus.yaml` | Prometheus scrape config |
| `Caddyfile` | TLS reverse proxy with auto Let's Encrypt |
| `grafana/provisioning/` | Auto-provisioned Prometheus datasource |
| `grafana/dashboards/` | Pre-built Nucleus usage dashboard |

## Grafana Dashboards

The pre-built dashboard (`nucleus-usage.json`) includes:

- **Total Commands** — Aggregate count across all anonymous users
- **Commands per Hour** — Time series by command name
- **Top 10 Commands** — Most popular commands
- **Commands by Category** — CLI vs MCP facade breakdown
- **Error Rate** — % of commands that fail
- **P95 Command Duration** — Performance tracking
- **OS Distribution** — macOS vs Linux vs Windows
- **Python Version Distribution** — Which Python versions are in use
- **Nucleus Version Distribution** — Adoption of new releases
- **Top Error Types** — Most common error classes

## Security Notes

- **No PII is collected** — Only command names, durations, versions, OS platform
- **Grafana is internal** — Restrict port 3000 to your IP via firewall
- **Prometheus is internal** — Not exposed externally
- **Caddy handles TLS** — Auto-renewed Let's Encrypt certificates
- **File logs rotate** — 100MB max, 90 days retention

## Firewall Rules (Example: UFW)

```bash
# Allow OTLP gRPC ingest from anywhere (Nucleus clients)
ufw allow 4317/tcp

# Allow HTTP/HTTPS for Caddy (TLS termination)
ufw allow 80/tcp
ufw allow 443/tcp

# Restrict Grafana to your IP only
ufw allow from <YOUR_IP> to any port 3000

# Block direct access to Prometheus
ufw deny 9090/tcp
```

## Cost Estimate

A $5/mo VPS (Hetzner, DigitalOcean, Vultr) handles thousands of Nucleus installs:
- CPU: ~1% idle, spikes to 5% during batch exports
- RAM: ~300MB total for the full stack
- Disk: ~1GB/month of telemetry data at scale
- Bandwidth: Negligible (each command sends ~200 bytes)
