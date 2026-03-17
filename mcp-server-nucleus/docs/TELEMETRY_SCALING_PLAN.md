# Nucleus Telemetry Scaling Plan

## 0. Current State (March 2026)
- Single-node telemetry stack running via Docker Compose.
- Components: OTel Collector, Prometheus, Grafana, Caddy TLS.
- Ingest endpoint: `https://telemetry.nucleusos.dev/v1/traces` (HTTP) and `:4317` (gRPC).
- Storage: local Docker volumes on a single VM (Oracle Always Free or similar).
- Assumed baseline: up to ~1k active Nucleus installs, low QPS, spans retained 30–90 days.

---

## 1. Scale-Up Path (Vertical) — 0 → 10k Active Installs

Goal: Max out a single inexpensive VM before adding complexity.

### 1.1. VM Sizing
- Start: 1 vCPU, 1–2GB RAM, 20–40GB disk.
- Target: 4 vCPU, 8GB RAM, 200GB disk before moving to multi-node.
- Use managed block storage with snapshot support (e.g., OCI Block Volume, DO Volumes).

### 1.2. OTel Collector Tuning
- Increase concurrency:
  - `processors.batch` — raise `send_batch_size` and `timeout` for throughput.
  - Enable `memory_limiter` to prevent OOM.
- Export strategy:
  - Keep **Prometheus metrics** and **file exporter for traces** for now.
  - When disk usage approaches 70%, start pruning old trace files (see 3.2).

### 1.3. Prometheus & Grafana
- Prometheus retention:
  - Start with `--storage.tsdb.retention.time=90d` and `--storage.tsdb.retention.size=5GB`.
  - For higher volume, reduce to 30 days and/or 2–3GB.
- Grafana:
  - Single instance is fine up to 10k active installs.
  - Enable admin audit logging and backup `/var/lib/grafana` weekly.

### 1.4. Reliability Basics
- Use a **managed DNS health check** (Cloudflare/OCI) on `telemetry.nucleusos.dev`.
- Configure systemd or Docker restart policies (already `unless-stopped`).
- Nightly cron health check:
  - Hit `/health` and send alert to email/Slack if failing for >5 minutes.

---

## 2. Scale-Out Path (Horizontal) — 10k → 100k Active Installs

At this point, single-node starts to hurt (CPU, disk IO, backups). Strategy: keep **Prometheus + Grafana** mostly single-node, but fan out **OTel Collectors**.

### 2.1. Front Door & Routing
- Move DNS to point at a load-balancer instead of a single VM.
- Options:
  - Cloud provider LB (OCI, DO, GCP) terminating TLS.
  - Or keep Caddy per-node and use DNS round-robin (simpler but less precise).
- Maintain a simple contract: `telemetry.nucleusos.dev` always accepts OTLP HTTP/gRPC.

### 2.2. Collector Pool
- Run multiple OTel Collector instances behind the LB.
- Modes:
  - **Stateless ingestion layer** with exporters → central metrics backend.
  - Use `routing` processor to shunt traffic by tenant or region if needed later.
- For traces, options:
  - Continue file-based export per-node + S3/OCI Object Storage sync.
  - Or introduce a trace backend (Tempo/Jaeger/ClickHouse) in phase 3.

### 2.3. Metrics Backend
- Keep Prometheus as **metrics aggregator**, but avoid scraping every collector directly.
- Use `prometheusremotewrite` exporter in collectors → single Prometheus or Cortex/Thanos.
- If Prometheus load or retention becomes an issue, plan migration to a long-term metrics store:
  - Thanos/Cortex (object-storage backed, horizontally scalable).

### 2.4. Multi-Region Considerations
- Keep v1 simple: single region for telemetry.
- When needed:
  - Deploy per-region collector pools.
  - Export anonymized aggregates to a central metrics cluster.

---

## 3. Data Retention, Privacy, and Cost Controls

### 3.1. Data Model & PII
- Strictly enforce **no PII** in spans by SDK design (span attributes are whitelisted).
- Provide clear docs and `TELEMETRY.md` explaining exactly what is collected.
- Ensure opt-out remains easy: `nucleus config --no-telemetry` and env flag.

### 3.2. Trace Retention Strategy
- Traces are diagnostic, not product analytics; keep them short-lived.
- Phases:
  1. MVP: file exporter, 30–90 days, rotate with `logrotate` or custom cron.
  2. Scale: export to object storage (OCI/GCS/S3) and delete local after N days.
  3. Advanced: optional trace backend (Tempo/Jaeger) for deep dives.

### 3.3. Metrics Retention & Downsampling
- For long-term product analytics, only metrics need to live >90 days.
- Strategy:
  - Prometheus short retention (15–30 days).
  - Periodic batch jobs that aggregate into long-term store (e.g., BigQuery/ClickHouse).

### 3.4. Cost Guardrails
- Always-on alerts for:
  - Disk usage >80% on telemetry volumes.
  - Prometheus WAL growth spikes.
  - Collector CPU >80% for sustained periods.
- Add a one-click script (`scripts/telemetry_prune.sh`) to prune old traces/metrics.

---

## 4. SLOs and Alerting

### 4.1. Ingest SLOs
- Target availability for ingest endpoint: **99.9%**.
- Define SLOs in terms of:
  - Median and p95 ingest latency.
  - Error rate for OTLP requests.

### 4.2. Alerts (Grafana)
- Alert classes:
  - **Critical**: ingest endpoint down, 5xx error rate >5% for 5 minutes.
  - **Warning**: CPU or memory >80% for 10 minutes, disk >75%.
  - **Info**: ingestion QPS sudden drop to near-zero (possible client-wide issue).

### 4.3. Dashboards
- Core panels:
  - Commands per minute/hour (by command type).
  - Active installs (unique anonymous IDs) over time.
  - Error breakdown by command and version.
  - Resource usage (CPU/mem/disk) of telemetry stack itself.

---

## 5. Operational Playbooks

### 5.1. Scaling Up
- When you approach 70% CPU or 70% disk on current VM:
  1. Resize VM (CPU/RAM) or attach new volume.
  2. Adjust Prometheus retention settings.
  3. Schedule a short maintenance window if needed.

### 5.2. Scaling Out
- When a single node cannot handle load even after vertical scaling:
  1. Introduce load balancer and additional collector nodes.
  2. Configure `prometheusremotewrite` to central metrics store.
  3. Use Terraform or Ansible to standardize node provisioning.

### 5.3. Disaster Recovery
- Nightly backups:
  - Prometheus data directory.
  - Grafana config + dashboards.
  - OTel config + deployment scripts.
- Recovery steps:
  1. Provision new VM.
  2. Restore volumes/config from backup.
  3. Point `telemetry.nucleusos.dev` DNS at new IP.

---

## 6. Future Enhancements (Post-Product-Market-Fit)

- Multi-tenant usage dashboards per enterprise customer.
- Per-workspace billing metrics derived from telemetry.
- Optional self-hosted telemetry bundle for on-prem customers.
- Pluggable exporters (e.g., send anonymized aggregates to customer-owned stacks).

This plan is intentionally conservative: maximize the value of a single cheap VM, then introduce horizontal scaling only when real usage justifies the added complexity.
