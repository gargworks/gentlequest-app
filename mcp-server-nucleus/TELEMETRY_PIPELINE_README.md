# Nucleus Telemetry Pipeline – Local + Cloudflare + Upstash

This document explains the telemetry setup for Nucleus MCP on Lokesh's Mac and in Cloudflare. It is written so that **any human or LLM** can understand the current state, where each piece lives, and how to extend it.

> Root paths used below:
> - Local telemetry repo: `/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus`
> - Main Nucleus repo (where `nucleus` CLI lives): `/Users/lokeshgarg/ai-mvp-backend`

---

## 1. High‑level architecture

Telemetry is designed to be **optional, buffered, and cheap**.

- The **Nucleus CLI / processes** emit telemetry spans using OTLP **HTTP** exporters.
- A **Cloudflare Worker** receives spans from the public internet at `https://telemetry.nucleusos.dev`.
- The Worker either:
  - Forwards spans directly to your Mac via **Cloudflare Tunnel** and OTLP HTTP (`:4318`), or
  - Base64-encodes and writes spans into an **Upstash Redis** queue (buffer) when your Mac is offline.
- A **drain script on your Mac** pulls spans from Upstash and forwards them to the local **OpenTelemetry Collector**.
- The **collector** is a Docker container (`nucleus-otel-collector`) that receives spans on HTTP port 4318 and writes them to `.telemetry/traces.jsonl` and `.telemetry/metrics.jsonl`.

**Key architectural decision (2026-03-14):** Switched from gRPC to HTTP exporters because Cloudflare Tunnel cannot route raw gRPC traffic. The SDK now uses `opentelemetry.exporter.otlp.proto.http` exporters with base endpoint `https://telemetry.nucleusos.dev` (no port). The HTTP exporter automatically appends `/v1/traces` and `/v1/metrics` paths.

Whenever Docker and the drain script are **not** running, spans are still accepted by the Worker and buffered in Upstash until you come back.

---

## 2. Components and file locations

### 2.1 Local telemetry control (this repo)

**Repo:** `/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus`

Key files that were created or edited:

- `package.json`
  - Provides friendly npm scripts:
    - `npm run telemetry:up` – start the collector container.
    - `npm run telemetry:down` – stop the collector container.
    - `npm run telemetry:drain` – run the Upstash → OTLP drain loop.
    - `npm run telemetry:summary` – summarize recent spans from collector logs.

- `scripts/telemetry.sh`
  - Wrapper used by `npm run telemetry:up` and `npm run telemetry:down`.
  - Treats the collector as an existing Docker container named `nucleus-otel-collector`.
  - Logic:
    - `up`:
      - Try `docker compose up -d nucleus-otel-collector` if a service exists.
      - Otherwise `docker start nucleus-otel-collector`.
    - `down`:
      - `docker stop nucleus-otel-collector`.

- `scripts/drain-upstash-spans.js`
  - Node.js script that connects to Upstash Redis and forwards spans to local collector.
  - Reads env vars from `process.env`:
    - `UPSTASH_REDIS_URL` – e.g. `rediss://moral-swine-69544.upstash.io:6379`.
    - `UPSTASH_REDIS_TOKEN` – Upstash Redis password/token.
    - Optional tuning:
      - `NUCLEUS_DRAIN_BATCH_SIZE` (default `50`).
      - `NUCLEUS_DRAIN_INTERVAL_MS` (default `1000`).
  - Behavior:
    - Connect to Upstash using `ioredis`.
    - In a loop, `LPOP` up to `BATCH_SIZE` entries from Redis list key `nucleus:spans`.
    - For each span:
      - HTTP `POST` to `http://localhost:4317` (OTLP collector, binary body).
      - If request fails or returns non‑2xx, push the span back onto Redis with `RPUSH` (basic retry).

- `scripts/telemetry-summary.sh`
  - Bash script to provide a **CLI telemetry summary** for humans and LLMs.
  - Called via: `npm run telemetry:summary`.
  - Behavior:
    - Expects collector container `nucleus-otel-collector` to be running.
    - Fetches the last N lines of logs (default `500`) via `docker logs`.
    - Computes:
      - `TOTAL_SPANS` – count of lines containing `Trace ID`.
      - `NUCLEUS_SPANS` – lines where `service.name: Str(nucleus` appears.
      - `LAST_TRACE` – last seen Trace ID.
      - `SERVICE_COUNTS` – a breakdown of spans by `service.name` using `grep/sed/sort/uniq`.
    - Prints a summary like:

      ```
      Recent telemetry summary
      ------------------------
      Total spans seen in last 500 lines             : 42
      Spans with service.name starting 'nucleus'     : 37
      Last Trace ID                                  : 0abc...

      Spans by service.name (approx, from logs):
           5 nucleus-cli
          12 nucleus-coordinator
          20 nucleus-server
           5 otelcol-contrib
      ```

### 2.2 Docker / OpenTelemetry collector

- Container name: `nucleus-otel-collector`.
- Runs via Docker Desktop.
- Exposes:
  - gRPC OTLP receiver on `:4317`.
  - HTTP OTLP receiver on `:4318`.
- Logs are accessed with:

  ```bash
  docker logs nucleus-otel-collector --tail 50
  ```

- Current configuration (inside the image) uses a **debug exporter**, so spans are printed to logs instead of being sent to Jaeger/Tempo/etc. This is intentional for now—easy to inspect and parse.

### 2.3 Upstash Redis

- Service: Upstash Redis (serverless Redis, free tier).
- Region: Mumbai (ap-south‑1).
- Database name: `nucleus-telemetry-redis`.
- Connection details (values are already configured in your environment; do NOT commit secrets):
  - REST:
    - `UPSTASH_REDIS_REST_URL="https://moral-swine-69544.upstash.io"`
    - `UPSTASH_REDIS_REST_TOKEN="<long token>"`
  - Redis (TCP):
    - URL example: `rediss://default:<password>@moral-swine-69544.upstash.io:6379`.
    - For the drain script we split this into:
      - `UPSTASH_REDIS_URL="rediss://moral-swine-69544.upstash.io:6379"`
      - `UPSTASH_REDIS_TOKEN="<password>` (same secret).

- Queue key used by the drain script (and expected from Worker):
  - `"nucleus:spans"` – spans as binary OTLP payloads, stored as list entries.

### 2.4 Cloudflare Worker (telemetry)

> Note: The Worker source file is not included in this document because it lives under Cloudflare’s UI / Git in `/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/cloudflare` (per earlier context). This section documents **what it is supposed to do**.

- Worker name: `nucleus-telemetry`.
- Environment variables configured in Cloudflare dashboard for this Worker:
  - `UPSTASH_REDIS_REST_URL` – Upstash REST URL.
  - `UPSTASH_REDIS_REST_TOKEN` – Upstash REST token.

- Intended responsibilities of the Worker:
  1. Accept incoming telemetry spans from Nucleus clients (likely as HTTP POST with OTLP binary body).
  2. When a Cloudflare Tunnel is up and the collector is reachable:
     - Forward the span directly to `https://telemetry.nucleus.sh` (which tunnels to `localhost:4317`).
  3. If direct forwarding fails (Mac offline, tunnel down) **or by design for buffering**:
     - Push the span into Upstash Redis using the REST API:
       - URL pattern: `${UPSTASH_REDIS_REST_URL}/lpush/nucleus:spans`.
       - Auth header: `Authorization: Bearer ${UPSTASH_REDIS_REST_TOKEN}`.
       - Body: base64 of OTLP payload or raw bytes (depending on Upstash client conventions).

This Worker ensures telemetry ingestion is **never lost** from the client’s perspective.

### 2.5 Cloudflare Tunnel

- Purpose: route `telemetry.nucleus.sh` from Cloudflare to your local collector.
- When running, the Worker can send OTLP directly to your Mac as if it were a public endpoint.
- When the tunnel is stopped, Worker falls back to Upstash buffering.

(Exact tunnel command and configuration are outside this document but live in your existing Cloudflare setup and shell history.)

---

## 3. Operational runbook

### 3.1 Everyday dev session (Lokesh’s workflow)

When you want telemetry **ON** and inspectable while working locally:

1. **Start the collector** (Terminal 1):

   ```bash
   cd ~/ai-mvp-backend/mcp-server-nucleus
   npm run telemetry:up
   ```

2. **Start the Upstash drain loop** (Terminal 2):

   ```bash
   cd ~/ai-mvp-backend/mcp-server-nucleus
   export UPSTASH_REDIS_URL="rediss://moral-swine-69544.upstash.io:6379"
   export UPSTASH_REDIS_TOKEN="<Upstash Redis password>"
   npm run telemetry:drain
   ```

   - This terminal will show: `Starting Upstash → OTLP drain loop...` and then stay mostly quiet.

3. **Ensure Cloudflare tunnel is running** (in another terminal or background):

   - Use your existing command to start the tunnel for `nucleus-telemetry` so that `telemetry.nucleus.sh` points to `localhost:4317`.

4. **Use Nucleus** (Terminal 3):

   ```bash
   cd ~/ai-mvp-backend
   NUCLEUS_ANON_TELEMETRY=true nucleus morning-brief
   ```

   - Any Nucleus command with `NUCLEUS_ANON_TELEMETRY=true` should emit spans.

5. **Inspect summary** (back in Terminal 1 or 2):

   ```bash
   cd ~/ai-mvp-backend/mcp-server-nucleus
   npm run telemetry:summary
   ```

   - You get counts and per‑`service.name` breakdown.
   - If the summary only prints the header line, it means no spans matching the patterns have yet hit the collector.

6. **Optional: raw logs**

   ```bash
   docker logs nucleus-otel-collector --tail 100
   ```


### 3.2 When you are offline / don’t care about analysis

- You can **stop Docker and the drain script**:

  ```bash
  cd ~/ai-mvp-backend/mcp-server-nucleus
  npm run telemetry:down
  # then Ctrl+C in the drain terminal
  ```

- Cloudflare Worker continues to accept spans from users and queue them in Upstash.
- When you next come back and start collector + drain, backlog in Redis will be replayed into the collector.


### 3.3 Quick sanity checks

- Collector running?

  ```bash
  docker ps --format '{{.Names}}' | grep nucleus-otel-collector
  ```

- Drain script running?

  - Look for a terminal with `Starting Upstash → OTLP drain loop...` at the top and no exit message.

- Logs show spans?

  ```bash
  docker logs nucleus-otel-collector --tail 40
  ```

  - You should see blocks containing `Trace ID` and `service.name` when telemetry is flowing.

- Summary works?

  ```bash
  cd ~/ai-mvp-backend/mcp-server-nucleus
  npm run telemetry:summary
  ```

  - If `TOTAL_SPANS` is `0`, it means collector logs don’t yet include span entries (telemetry path not fully wired).

---

## 4. Current gaps and next steps

This section is for future work by Lokesh or any collaborator.

### 4.1 Wire the Worker to Upstash

- Verify the Cloudflare Worker code:
  - Confirms it uses `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`.
  - Confirms it `LPUSH`es binary OTLP data into key `nucleus:spans`.
- If not yet wired, implement this behavior so that **any** telemetry POST is buffered.
- Add minimal logging in the Worker for debugging (e.g., count of enqueued spans per minute).

### 4.2 Ensure SDK emits OTLP spans

- Confirm Nucleus telemetry SDK is actually encoding spans as OTLP over HTTP/gRPC and sending them to the Worker endpoint.
- If it currently only logs or uses some custom shape, add an adapter that:
  - Converts internal span representation to OTLP protobuf.
  - Sends it to `https://<worker-endpoint>` with content type `application/x-protobuf` or similar.

### 4.3 Add real backend (Jaeger/Tempo/Grafana)

**Phase B is now implemented.** The full observability stack runs via Docker Compose:

```bash
npm run telemetry:dash          # Start full stack (collector + jaeger + prometheus + grafana)
npm run telemetry:dash:down     # Stop full stack
npm run telemetry:dash:logs     # Tail all container logs
npm run telemetry:open:jaeger   # Open Jaeger UI (http://localhost:16686)
npm run telemetry:open:grafana  # Open Grafana UI (http://localhost:3000, admin/nucleus)
npm run telemetry:open:prometheus # Open Prometheus UI (http://localhost:9090)
```

**Stack components** (`infra/telemetry/docker-compose.yaml`):

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `nucleus-otel-collector` | `otel/opentelemetry-collector-contrib:0.96.0` | 4317, 4318, 8889 | Receives OTLP, exports to Jaeger + Prometheus + file |
| `nucleus-jaeger` | `jaegertracing/all-in-one:1.53` | 16686 | Trace visualization |
| `nucleus-prometheus` | `prom/prometheus:v2.51.0` | 9090 | Metrics storage, scrapes collector |
| `nucleus-grafana` | `grafana/grafana:10.4.0` | 3000 | Dashboards (auto-provisioned with Prometheus + Jaeger datasources) |

**Key config files:**
- `infra/telemetry/otel-collector-config.yaml` — Collector pipelines (otlp/jaeger exporter for traces)
- `infra/telemetry/prometheus.yaml` — Prometheus scrape config
- `infra/telemetry/grafana/provisioning/datasources/prometheus.yaml` — Grafana datasources (Prometheus + Jaeger)
- `infra/telemetry/grafana/provisioning/dashboards/default.yaml` — Dashboard provisioning
- `infra/telemetry/grafana/dashboards/nucleus-usage.json` — Pre-built Nucleus dashboard (10 panels)

### 4.4 Phase C — Alerts and Daily Brief

**Phase C extends Phase B with automated monitoring and value extraction.**

#### Alerting

Grafana alert rules are auto-provisioned from `infra/telemetry/grafana/provisioning/alerting/nucleus-alerts.yaml`:

| Alert | Condition | Threshold | Duration |
|-------|-----------|-----------|----------|
| **High Error Rate** | `sum(rate(nucleus_nucleus_anon_commands_total{nucleus_error_type!=""}[5m])) / sum(rate(nucleus_nucleus_anon_commands_total[5m]))` | > 10% | 5 minutes |
| **Command Rate Drop** | `rate(nucleus_nucleus_anon_commands_total[5m])` | < 0.01/sec | 10 minutes |
| **No Commands in 24h** | `sum(increase(nucleus_nucleus_anon_commands_total[24h]))` | < 1 | 1 hour |

**View alerts:**
- Grafana UI: `http://localhost:3000/alerting/list`
- Alert rules are in folder "Nucleus Telemetry"

**Alert labels:**
- `severity: warning` — High error rate, no commands in 24h
- `severity: info` — Command rate drop
- `component: nucleus-telemetry` — All alerts

#### Daily Telemetry Brief

Run the daily brief to get a concise usage summary:

```bash
npm run telemetry:brief
```

**Output includes:**
- Total commands and commands/hour (last 24h)
- Top 10 commands by volume
- Error rate and top error types
- Latency percentiles (p50, p95, p99)
- Platform and Python version distribution
- Actionable insights based on metrics

**Customize time window:**
```bash
LOOKBACK_HOURS=12 npm run telemetry:brief  # Last 12 hours
LOOKBACK_HOURS=168 npm run telemetry:brief # Last 7 days
```

**Script location:** `scripts/telemetry-daily-brief.sh`

**Requirements:**
- Prometheus running at `http://localhost:9090`
- Phase B stack active (`npm run telemetry:dash`)
- Metrics accumulated over the lookback window

### 4.5 Phase D — Alert Delivery, Trends, and Anomaly Detection

**Phase D extends Phase C with alert delivery integrations, trend analysis, and statistical anomaly detection.**

#### Alert Delivery Integrations

Grafana alerts now route to Slack and email via auto-provisioned contact points.

**Configuration files:**
- `infra/telemetry/grafana/provisioning/alerting/contact-points.yaml` — Slack and email contact points
- `infra/telemetry/grafana/provisioning/alerting/notification-policies.yaml` — Routing policy

**Environment variables** (set in `infra/telemetry/docker-compose.yaml`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `NUCLEUS_SLACK_WEBHOOK_URL` | `https://hooks.slack.com/services/PLACEHOLDER` | Slack incoming webhook URL |
| `NUCLEUS_ALERT_EMAIL` | `alerts@example.com` | Email address for alerts |
| `GF_SMTP_ENABLED` | `false` | Enable SMTP for email delivery |
| `GF_SMTP_HOST` | `smtp.gmail.com:587` | SMTP server and port |
| `GF_SMTP_USER` | (empty) | SMTP username |
| `GF_SMTP_PASSWORD` | (empty) | SMTP password |
| `GF_SMTP_FROM_ADDRESS` | `grafana@nucleusos.dev` | From address for alert emails |

**Setup for Slack alerts:**
1. Create a Slack incoming webhook at https://api.slack.com/messaging/webhooks
2. Set the webhook URL:
   ```bash
   export NUCLEUS_SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   ```
3. Restart Grafana:
   ```bash
   npm run telemetry:dash:down
   npm run telemetry:dash
   ```

**Setup for email alerts:**
1. Configure SMTP settings in `.env` or export as environment variables
2. Enable SMTP: `export GF_SMTP_ENABLED=true`
3. Restart Grafana

**Notification policy:**
- All alerts with `component=nucleus-telemetry` route to Slack
- Alerts with `severity=warning` also route to email
- Alerts grouped by `alertname` and `severity`
- Repeat interval: 4 hours

**Alert rules** (4 total):

| Alert | Severity | Condition | Duration |
|-------|----------|-----------|----------|
| High Error Rate | warning | Error rate > 10% | 5 min |
| Command Rate Drop | info | Rate < 0.01/sec | 10 min |
| No Commands in 24h | warning | Zero commands | 1 hour |
| **Command Rate Anomaly** | critical | Z-score > 3σ | 15 min |

#### Trend Analysis Dashboard

**Dashboard:** "Nucleus Telemetry Trends" (UID: `nucleus-trends`)

**Panels:**
- Commands per hour (7-day view)
- Error rate trend (7-day view)
- Latency percentiles trend (p50, p95 over 7 days)
- Commands per day (30-day view)
- Error rate trend (30-day view)

**Access:** `http://localhost:3000/d/nucleus-trends`

#### Enhanced Daily Brief

The daily brief now includes:

**Period-over-period comparison:**
- Current period vs previous period (same duration)
- Percentage change in total commands
- Percentage change in error rate
- Visual indicators (↑/↓) for trends

**Statistical anomaly detection:**
- Command rate anomaly detection using 3σ threshold
- Error rate anomaly detection using 3σ threshold
- Z-score calculation: `(current - historical_mean) / historical_stddev`
- Historical baseline: 7-day rolling window

**Algorithm:**
```
Z-score = (current_rate - avg_over_time(rate[7d])) / stddev_over_time(rate[7d])
Anomaly if |Z-score| > 3
```

**Example output:**
```
📈 PERIOD-OVER-PERIOD COMPARISON
  Commands:   45 → 67 (↑ +48.9%)
  Error rate: 2.2% → 1.5% (↓ -0.7%)

🔍 ANOMALY DETECTION
  ✅ No statistical anomalies detected (3σ threshold)
      Command rate Z-score: 1.23
      Error rate Z-score:   -0.45
```

**Assumptions:**
- Normal distribution of command rates over time
- 7-day historical window provides stable baseline
- 3σ threshold balances sensitivity vs false positives
- Requires at least 7 days of data for accurate detection

### 4.6 Phase D Smoke Test

**Test alert delivery without waiting for real anomalies:**

1. **Temporarily lower alert thresholds:**
   Edit `infra/telemetry/grafana/provisioning/alerting/nucleus-alerts.yaml`:
   ```yaml
   # Change High Error Rate threshold from 0.1 to 0.01 (1%)
   # Change Command Rate Drop threshold from 0.01 to 100 (impossible rate)
   ```

2. **Restart Grafana to apply changes:**
   ```bash
   npm run telemetry:dash:down
   npm run telemetry:dash
   ```

3. **Trigger alerts by running commands:**
   ```bash
   npm run telemetry:local:demo -- morning-brief
   # Wait 5-10 minutes for alert evaluation
   ```

4. **Verify alert delivery:**
   - Check Grafana: `http://localhost:3000/alerting/list`
   - Check Slack channel for alert message
   - Check email inbox for alert notification

5. **Restore original thresholds and restart Grafana**

### 4.7 Phase E — Automated Incident Response ("Nucleus auto-heals itself so Lokesh can sleep")

**Phase E adds a self-healing incident controller that detects anomalies, executes automated responses, generates incident reports, and notifies via Slack — all without human intervention.**

#### Architecture

```
Prometheus metrics
       │
       ▼
┌──────────────────────┐
│  Incident Controller │  (scripts/incident-controller.py)
│                      │
│  1. Poll metrics     │
│  2. Detect incidents │
│  3. Execute actions  │───► Docker restart, disable commands
│  4. Generate report  │───► incidents/YYYY-MM/INCIDENT-*.md
│  5. Notify Slack     │───► Slack webhook
│  6. Log all actions  │───► incidents/actions.log
└──────────────────────┘
```

No new services required — the controller is a script run via cron or as a daemon.

#### Running the Incident Controller

```bash
# Single check (cron-friendly, exits with code 1 if critical incident)
npm run incident:check

# Daemon mode (polls every 60s, Ctrl+C to stop)
npm run incident:daemon

# Preview what would happen without taking action
npm run incident:dry-run
```

**Cron setup (recommended for production):**
```bash
# Run every 5 minutes
*/5 * * * * cd /path/to/mcp-server-nucleus && python3 scripts/incident-controller.py >> /tmp/nucleus-incident.log 2>&1
```

#### Configuration

All behavior is controlled via `.brain/config/nucleus.yaml`:

```yaml
incident_response:
  enabled: true                    # Master switch
  prometheus_url: "http://localhost:9090"
  poll_interval_seconds: 60        # Daemon polling interval
  action_cooldown_minutes: 30      # Prevents action flapping
  
  thresholds:
    error_rate_warning: 0.10       # 10% — report + notify
    error_rate_critical: 0.25      # 25% — restart + disable
    anomaly_zscore: 3.0            # Statistical anomaly threshold
    min_commands_for_action: 5     # Minimum traffic for error rate checks
    dead_pipeline_hours: 6         # No commands triggers dead pipeline
  
  actions:
    restart_collector:
      enabled: true
      max_restarts_per_hour: 2
    disable_command:
      enabled: false               # Opt-in only
      auto_reenable_minutes: 60    # Commands auto-re-enable
    generate_report:
      enabled: true
    notify_slack:
      enabled: true                # Requires NUCLEUS_SLACK_WEBHOOK_URL
    restart_metrics_pipeline:
      enabled: true
      max_restarts_per_hour: 1
```

#### Incident Types and Automated Actions

| Incident | Severity | Detection | Actions |
|----------|----------|-----------|---------|
| Dead Pipeline | warning | 0 commands in 6h | Restart collector, restart pipeline, report, Slack |
| High Error Rate | warning | Error rate > 10% | Report, Slack |
| Critical Error Rate | critical | Error rate > 25% | Restart collector, optionally disable command, report, Slack |
| Command Rate Anomaly | critical | Z-score > 3σ | Report, Slack |
| Collector Unhealthy | critical | `up{job="nucleus-otel-collector"} < 1` | Restart collector, report, Slack |

#### Safety Guarantees

- **Idempotent:** Every action is safe to run multiple times
- **Rate-limited:** Max restarts per hour, cooldown between duplicate actions
- **Append-only logging:** All actions logged to `incidents/actions.log` (JSONL)
- **No data deletion:** Never deletes user data or configs
- **Opt-in escalation:** Command disabling is disabled by default
- **Auto-recovery:** Disabled commands auto-re-enable after configurable timeout
- **Graceful degradation:** If Prometheus is unreachable, controller skips (no crash)

#### Incident Reports

Auto-generated at `incidents/YYYY-MM/INCIDENT-<timestamp>.md`, each report contains:
- Summary table (ID, type, severity, timestamp)
- Key metrics at time of detection
- Actions taken (with results)
- Links to Grafana, Prometheus, Jaeger
- Recommended PromQL queries for investigation
- Next-steps checklist

#### Action Log

All automated actions are appended to `incidents/actions.log` as JSONL:
```json
{"timestamp":"2026-03-14T05:03:37Z","incident_id":"INC-20260314T050336-DEAD_PIP","action":"restart_collector","target":"nucleus-otel-collector","result":"success","details":""}
```

#### Daily Brief Integration

The daily brief (`npm run telemetry:brief`) now includes:
- Recent incidents in the lookback window
- Count of automated actions taken
- Last 5 action log entries

### 4.8 Phase E Smoke Test

**Test the full self-healing loop:**

1. **Dry run first:**
   ```bash
   npm run incident:dry-run
   ```
   Verify it detects the current state without taking action.

2. **Live check:**
   ```bash
   npm run incident:check
   ```
   Verify:
   - Incident report generated in `incidents/YYYY-MM/`
   - Action log entry appended to `incidents/actions.log`
   - Container restarted (if applicable): `docker ps | grep nucleus-otel-collector`

3. **Verify in daily brief:**
   ```bash
   npm run telemetry:brief
   ```
   Confirm the "Recent Incidents" section shows the incident.

4. **Test Slack notifications (if configured):**
   ```bash
   export NUCLEUS_SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   npm run incident:check
   ```
   Verify Slack channel receives structured incident message.

5. **Test daemon mode (brief):**
   ```bash
   npm run incident:daemon
   # Let it run for 2-3 cycles, then Ctrl+C
   ```

### 4.9 Phase F — Autonomous Policy Engine

Phase F upgrades the incident controller from a stateless fire-and-forget system
to a **playbook-driven, outcome-aware policy engine** that adapts its behavior
based on historical resolution success rates.

**Key Principles:**
- **Deterministic** — all adaptation rules are threshold-based, no ML
- **Explainable** — every policy change is logged with reasoning
- **Safe** — all Phase E safety rails preserved (rate limits, cooldowns, HITL for critical)

#### 4.9.1 Architecture

```
┌───────────────┐     ┌──────────────┐     ┌────────────────┐
│   PLAYBOOKS   │────▶│   ENGINE     │────▶│  INCIDENT JSON │
│ (detect+act)  │     │ (executor)   │     │  + MD Report   │
└───────────────┘     └──────┬───────┘     └────────┬───────┘
                             │                      │
                      ┌──────▼───────┐       ┌──────▼───────┐
                      │ POLICY STATE │◀──────│  OUTCOME     │
                      │ (adaptive)   │       │  EVALUATION  │
                      └──────────────┘       └──────────────┘
```

1. **Playbooks** define incident types with detection conditions, ordered actions, and success criteria
2. **Engine** iterates playbooks, detects incidents, executes actions per policy
3. **Incident JSON** written alongside MD reports for machine processing
4. **Outcome Evaluation** re-queries Prometheus after a delay to grade resolution
5. **Policy State** tracks rolling success rates and adapts cooldowns/action flags

#### 4.9.2 Playbook Structure

Each playbook defines:

| Field | Description |
|-------|-------------|
| `name` | Matches incident type (e.g. `dead_pipeline`) |
| `severity` | From `severity_map` in config |
| `detect` | Detection function returning `(bool, summary, metrics)` |
| `actions` | Ordered list of action primitives to execute |
| `eval_delay_seconds` | Wait time before outcome evaluation |
| `success_query` | PromQL query to check if the issue resolved |
| `success_comparator` | `"gt"` or `"lt"` — how to interpret the query result |
| `success_threshold` | Numeric threshold for success criteria |

Built-in playbooks: `dead_pipeline`, `collector_unhealthy`, `critical_error_rate`,
`high_error_rate`, `command_rate_anomaly`.

#### 4.9.3 Incident JSON Schema

Every incident now produces **both** a Markdown report and a machine-readable JSON file:

```
incidents/
├── SCHEMA.md                        # Canonical schema documentation
├── policy_state.json                # Rolling success rates & adaptive config
├── actions.log                      # Append-only JSONL action log
└── 2026-03/
    ├── INC-20260314T050336-DEAD_PIP.json   # Machine-readable
    └── INC-20260314T050336-DEAD_PIP.md     # Human-readable
```

See `incidents/SCHEMA.md` for the full JSON schema reference.

#### 4.9.4 Outcome Evaluation

After an incident's `eval_delay_seconds` has elapsed, the controller:

1. Re-queries the playbook's `success_query` against Prometheus
2. Compares the result using `success_comparator` and `success_threshold`
3. Grades the incident as `success`, `partial`, `failed`, or `unknown`
4. Updates the incident JSON with evaluation data
5. Records the outcome in `policy_state.json`

**Resolution statuses:**

| Status | Meaning |
|--------|---------|
| `pending` | Actions taken, awaiting evaluation |
| `success` | Metrics recovered after actions |
| `partial` | Some actions succeeded but criteria not fully met |
| `failed` | Metrics did not improve |
| `unknown` | Could not determine (e.g. Prometheus unreachable) |

#### 4.9.5 Policy Feedback Loop

The policy state file (`incidents/policy_state.json`) tracks per-incident-type:

- **Rolling outcomes** — last N resolution statuses (configurable, default 10)
- **Success rate** — fraction of outcomes that were `"success"`
- **Cooldown multiplier** — dynamically adjusts action cooldowns
- **Action overrides** — can disable specific actions for specific incident types

**Adaptation rules (deterministic, no ML):**

| Condition | Effect |
|-----------|--------|
| `success_rate >= 0.8` | Reduce cooldown multiplier (min 0.5x), re-enable all actions |
| `success_rate <= 0.3` | Increase cooldown multiplier (max 3.0x), disable restart actions |
| `0.3 < success_rate < 0.8` | Drift multiplier back toward 1.0x |

**Example:** If `dead_pipeline` restarts keep failing (success_rate drops to 20%),
the policy engine will automatically disable restart actions for that type and
lengthen cooldowns — falling back to report+notify only. Once manually fixed and
success rate recovers, restarts are re-enabled automatically.

#### 4.9.6 Configuration

Policy settings in `.brain/config/nucleus.yaml`:

```yaml
policy:
  rolling_window: 10              # Outcomes to track
  high_success_threshold: 0.8     # Reward threshold
  low_success_threshold: 0.3      # Penalize threshold
  min_cooldown_minutes: 10        # Floor after multiplier
  max_cooldown_minutes: 120       # Ceiling after multiplier
```

#### 4.9.7 New Commands

```bash
# Evaluate pending incidents (check outcomes)
npm run incident:evaluate

# View current policy state
npm run incident:policy

# Standard commands still work
npm run incident:check
npm run incident:daemon
npm run incident:dry-run
```

#### 4.9.8 Phase F Smoke Test

1. **Dry-run check (generates incident JSON + MD):**
   ```bash
   npm run incident:dry-run
   # Verify: incident detected, playbook name shown, actions listed
   ```

2. **View policy state:**
   ```bash
   npm run incident:policy
   # Expected: Empty state on first run, or per-type stats after incidents
   ```

3. **Evaluate pending incidents:**
   ```bash
   npm run incident:evaluate
   # Expected: Evaluates any incidents whose delay has elapsed
   ```

4. **Verify JSON output:**
   ```bash
   ls incidents/2026-*/INC-*.json
   cat incidents/2026-*/INC-*.json | python3 -m json.tool
   # Expected: Valid JSON matching schema in incidents/SCHEMA.md
   ```

5. **Verify policy adaptation (after multiple incidents):**
   ```bash
   npm run incident:policy
   # Expected: success_rate, cooldown_multiplier, action_overrides per type
   ```

### 4.10 Phase G — Reliability Policy Surface

Phase G adds a visibility and control layer on top of the Phase F policy engine,
providing operators with clear insight into what the system will do and explicit
controls over autonomy boundaries.

#### 4.10.1 Enhanced Policy Report

The `--policy-report` command now provides comprehensive visibility:

```bash
npm run incident:policy
```

**Report includes:**
- **Autonomy mode** — current operational mode (observe_only, infra_only, infra_and_app)
- **Hard limits** — absolute constraints on actions
- **Per-incident-type stats:**
  - Total incidents
  - Outcome breakdown (success/partial/failed/unknown/pending counts)
  - Success rate
  - Effective cooldown (base × policy multiplier)
  - Action status (ON/OFF with reason: observe_only, hard_limit, policy, config)
  - **Intent summary** — plain-language description of what the system will do

**Example output:**
```
═══ NUCLEUS POLICY ENGINE — STATUS REPORT ═══
Updated: 2026-03-14T06:16:39Z
Autonomy Mode: INFRA_AND_APP
Hard Limits: allow_restart_collector=True, allow_disable_command=False

┌─ [dead_pipeline] ────────────────────────────────────────
│ Total incidents: 5
│ Outcomes (last 5): success=4, partial=0, failed=1, unknown=0, pending=0
│ Success rate: 80%
│ Cooldown: 27min (base=30min × 0.9x)
│ Actions: restart_collector=ON, restart_metrics_pipeline=ON,
│          generate_report=ON, notify_slack=ON
│
│ Intent: If commands drop to zero for 6h, I will restart the
│         collector, restart metrics pipeline, generate an incident
│         report, post to Slack (cooldown 27m).
└──────────────────────────────────────────────────────────
```

#### 4.10.2 Autonomy Modes

Configure in `.brain/config/nucleus.yaml` under `policy.autonomy.autonomy_mode`:

| Mode | Behavior |
|------|----------|
| `observe_only` | Detect and report only. No automated actions except generate_report and notify_slack. |
| `infra_only` | Allow infrastructure restarts (collector, metrics pipeline) but no application-level changes (e.g., disable_command). |
| `infra_and_app` | Full autonomy subject to hard limits and Phase F safety rails. |

**Use cases:**
- **observe_only** — Initial deployment, debugging, or during major incidents when you want full manual control
- **infra_only** — Production default for most teams (safe restarts, no app changes)
- **infra_and_app** — High-trust environments with mature playbooks

#### 4.10.3 Hard Limits

Hard limits are **absolute constraints** that override all other settings, including
Phase F policy adaptation. Configure in `.brain/config/nucleus.yaml` under
`policy.autonomy.hard_limits`:

```yaml
policy:
  autonomy:
    autonomy_mode: "infra_and_app"
    hard_limits:
      allow_restart_collector: true
      allow_restart_metrics_pipeline: true
      allow_disable_command: false  # Requires explicit opt-in
```

**Precedence order (highest to lowest):**
1. Hard limits (absolute)
2. Autonomy mode (observe_only, infra_only, infra_and_app)
3. Phase F policy overrides (learned from outcomes)
4. Config-level action.enabled flags

#### 4.10.4 Intent Summaries

Each incident type in the policy report includes a plain-language intent summary
that reflects:
- Detection conditions (thresholds from config)
- Actions that will be taken (considering autonomy mode, hard limits, policy state)
- Current cooldown settings

**Examples:**

```
dead_pipeline:
  Intent: If commands drop to zero for 6h, I will restart the collector,
          restart metrics pipeline, generate an incident report, post to
          Slack (cooldown 30m).

critical_error_rate (after policy learns restarts fail):
  Intent: If error rate >25%, I will generate an incident report, post to
          Slack; restart the collector [DISABLED] (cooldown 90m).

high_error_rate (observe_only mode):
  Intent: If error rate >10%, I will detect and report only (observe_only mode).
```

Intent summaries update automatically when you change config, autonomy mode, or
when Phase F policy adaptation disables actions.

#### 4.10.5 Phase G Smoke Test

1. **View policy report with full autonomy:**
   ```bash
   npm run incident:policy
   # Expected: autonomy_mode=INFRA_AND_APP, actions show ON status
   ```

2. **Change to observe_only mode:**
   ```bash
   # Edit .brain/config/nucleus.yaml:
   #   policy.autonomy.autonomy_mode: "observe_only"
   
   npm run incident:policy
   # Expected: autonomy_mode=OBSERVE_ONLY, restart actions show OFF (observe_only)
   ```

3. **Test observe_only enforcement:**
   ```bash
   npm run incident:dry-run
   # Expected: Detects incidents, skips restart actions with reason "autonomy_mode=observe_only"
   ```

4. **Test hard limit:**
   ```bash
   # Edit .brain/config/nucleus.yaml:
   #   policy.autonomy.hard_limits.allow_restart_collector: false
   
   npm run incident:policy
   # Expected: restart_collector shows OFF (hard_limit)
   ```

5. **Restore defaults:**
   ```bash
   # Edit .brain/config/nucleus.yaml:
   #   policy.autonomy.autonomy_mode: "infra_and_app"
   #   policy.autonomy.hard_limits.allow_restart_collector: true
   ```

### 4.11 Phase H — Full Stack Health & Crash-Loop Defense

Phase H extends monitoring from telemetry components to the full Nucleus runtime
stack, adding crash-loop detection with backoff and startup smoke tests for
single-node deployments.

#### 4.11.1 Core Stack Monitoring

The incident controller now monitors all critical components defined in
`.brain/config/nucleus.yaml` under `core_stack.components`:

```yaml
core_stack:
  enabled: true
  components:
    - name: "nucleus-otel-collector"
      type: "docker"
      container: "nucleus-otel-collector"
      health_check: "docker"
      critical: true
    
    - name: "prometheus"
      type: "docker"
      container: "prometheus"
      health_check: "http"
      health_url: "http://localhost:9090/-/healthy"
      critical: true
```

**Health check types:**
- `docker` — Checks if container is running via `docker ps`
- `http` — Checks if HTTP endpoint returns 2xx/3xx
- `process` — Checks if PID file exists and process is running

**Component incidents:**
- `component_down_<name>` — Detected when health check fails
- Actions: `restart_component`, `generate_report`, `notify_slack`
- Respects autonomy modes and hard limits

#### 4.11.2 Crash-Loop Detection and Backoff

Prevents infinite restart storms when a component is fundamentally broken:

**Configuration:**
```yaml
core_stack:
  crash_loop:
    max_restarts: 3  # Max restarts within window
    window_minutes: 5  # Time window for counting
    backoff_minutes: 15  # Pause duration after crash loop detected
```

**Behavior:**
1. Controller tracks recent restarts per component in `policy_state.json`
2. If `max_restarts` exceeded within `window_minutes`:
   - Mark component as `crash_looping`
   - Stop auto-restarts for `backoff_minutes`
   - Generate `core_crash_loop` incident with restart history
3. After backoff expires, reset state and allow restarts again

**Example crash-loop incident:**
```json
{
  "type": "core_crash_loop",
  "severity": "critical",
  "summary": "Component prometheus is crash-looping: 3 restarts in 5 minutes",
  "metrics_snapshot": {
    "component": "prometheus",
    "restart_count": 3,
    "recent_restarts": ["2026-03-14T...", "2026-03-14T...", "2026-03-14T..."],
    "backoff_until": "2026-03-14T13:30:00Z"
  }
}
```

#### 4.11.3 Startup Smoke Tests

Verify core dependencies before marking system as healthy:

**Configuration:**
```yaml
core_stack:
  smoke_tests:
    enabled: true
    timeout_seconds: 30
    required_checks:
      - prometheus_reachable
      - otel_collector_listening
      # Future: db_reachable, queue_reachable, core_health_endpoint
```

**Run smoke tests:**
```bash
npm run health:smoke-test
# or
python3 scripts/incident-controller.py --smoke-test
```

**Output:**
```
═══════════════════════════════════════════════════════════
  NUCLEUS STARTUP SMOKE TESTS — Phase H
  2026-03-14 13:45:00 
═══════════════════════════════════════════════════════════

✅ PASS prometheus_reachable: http://localhost:9090
✅ PASS otel_collector_listening: nucleus-otel-collector

✅ All smoke tests passed — system ready
```

**On failure:**
- Smoke test returns exit code 1
- `bad_boot` incident generated with failed check details
- System should refuse to advertise as healthy/ready
- Future: Auto-rollback to last-known-good config (Phase I)

#### 4.11.4 Integration with Policy Engine

All Phase H incidents are first-class citizens:

**New incident types:**
- `component_down_<name>` — Component health check failed
- `core_crash_loop` — Component crash-looping
- `bad_boot` — Startup smoke tests failed

**Policy integration:**
- Produce JSON incidents using Phase F schema
- Participate in outcome evaluation (did restart fix the issue?)
- Show in `npm run incident:policy` with stats and intent summaries
- Respect autonomy modes:
  - `observe_only` — Detect and report, no restarts
  - `infra_only` — Allow component restarts
  - `infra_and_app` — Full autonomy (default)

**New hard limits:**
```yaml
policy:
  autonomy:
    hard_limits:
      allow_restart_core_process: true
      allow_restart_db: true
      allow_restart_queue: true
```

#### 4.11.5 Phase H Smoke Test

1. **Kill a critical component:**
   ```bash
   docker stop prometheus
   
   # Wait 60s, then check
   npm run incident:check
   # Expected: component_down_prometheus incident, auto-restart attempted
   
   ls incidents/2026-*/INC-*prometheus*.json
   # Expected: JSON incident file exists
   ```

2. **Trigger crash loop:**
   ```bash
   # Introduce bad config that causes immediate crash
   # (e.g., wrong port binding in prometheus.yml)
   
   # Restart 3+ times quickly
   docker restart prometheus
   docker restart prometheus
   docker restart prometheus
   
   npm run incident:check
   # Expected: core_crash_loop incident, restarts paused for 15min
   
   npm run incident:policy
   # Expected: Shows prometheus in crash_looping state with backoff_until
   ```

3. **Test smoke tests:**
   ```bash
   docker stop prometheus
   
   npm run health:smoke-test
   # Expected: ❌ FAIL prometheus_reachable, exit code 1
   
   docker start prometheus
   npm run health:smoke-test
   # Expected: ✅ All tests pass, exit code 0
   ```

4. **Verify autonomy modes:**
   ```bash
   # Edit .brain/config/nucleus.yaml:
   #   policy.autonomy.autonomy_mode: "observe_only"
   
   docker stop grafana
   npm run incident:check
   # Expected: Detects component_down_grafana but skips restart (observe_only)
   
   npm run incident:policy
   # Expected: Shows restart_component=OFF (observe_only)
   ```

### 4.12 Phase I — Safe Rollouts and Automatic Rollbacks

Phase I adds versioned releases with health-gated rollout procedures and automatic
rollback on smoke test failures or runtime regressions for single-node deployments.

#### 4.12.1 Versioned Releases

All configuration changes are tracked as versioned releases in `deployments/`:

```
deployments/
  current -> releases/20260314-111111-baseline/
  releases/
    20260314-111111-baseline/
      nucleus.yaml
      release.json
    20260314-120000-feature-x/
      nucleus.yaml
      release.json
```

**Release metadata** (`release.json`):
```json
{
  "release_id": "20260314-111111-baseline",
  "timestamp": "20260314-111111",
  "label": "baseline",
  "description": "Initial baseline release",
  "previous_release": null,
  "created_at": "2026-03-14T11:11:11Z",
  "status": "created"
}
```

**Create a release snapshot:**
```bash
npm run deploy:snapshot -- baseline --description "Baseline config"
# or
python3 scripts/incident-controller.py --create-release baseline --description "Baseline config"
```

**List all releases:**
```bash
npm run deploy:list
# Shows all releases with current marker (→)
```

#### 4.12.2 Health-Gated Rollout Procedure

Rollouts follow a strict safety procedure:

1. **Switch to target release** — Update `current` symlink
2. **Run smoke tests** — Verify basic health (Prometheus, collector, etc.)
3. **If smoke tests fail:**
   - Generate `bad_rollout` incident
   - Automatically rollback to previous release
   - Verify rollback with smoke tests
4. **If smoke tests pass:**
   - Enter observation window (default: 10 minutes)
   - Monitor for regressions (error rate, crash loops, component health)
   - If regression detected → automatic rollback
   - If window expires without issues → mark release as stable

**Execute a rollout:**
```bash
npm run deploy:rollout -- 20260314-120000-feature-x
# or
python3 scripts/incident-controller.py --rollout 20260314-120000-feature-x
```

**Output:**
```
═══════════════════════════════════════════════════════════
  NUCLEUS ROLLOUT — Phase I
  2026-03-14 12:00:00 
═══════════════════════════════════════════════════════════

Rollout status: OBSERVING
✅ Smoke tests passed
⏳ Observation window: 2026-03-14T12:10:00Z
   Monitoring for regressions...
```

#### 4.12.3 Automatic Rollback on Regression

During the observation window, the incident controller monitors for:

**Regression conditions:**
- Error rate exceeds threshold (default: 30%, higher than critical 25%)
- Any component enters crash-loop state
- Critical components go down

**On regression detected:**
1. Generate `rollout_regression` incident with metrics
2. Execute `rollback_release` action
3. Switch back to previous release
4. Verify rollback with smoke tests
5. Clear active rollout state

**Configuration** (`.brain/config/nucleus.yaml`):
```yaml
policy:
  rollouts:
    observation_window_minutes: 10
    enable_auto_rollback: true
    
    regression_thresholds:
      max_error_rate: 0.30
      allow_crash_loops: false
      allow_component_down: false
```

**Manual rollback:**
```bash
npm run deploy:rollback
# or
python3 scripts/incident-controller.py --rollback
```

#### 4.12.4 Integration with Policy Engine

**New incident types:**
- `bad_rollout` — Rollout failed smoke tests
- `rollout_regression` — Rollout passed smoke tests but caused regressions

**Policy integration:**
- Produce JSON incidents using Phase F schema
- Participate in outcome evaluation
- Show in `npm run incident:policy` with stats
- Respect autonomy modes:
  - `observe_only` — Detect rollout issues, create incidents, NO auto-rollback
  - `infra_only` — Auto-rollback allowed if `enable_auto_rollback: true`
  - `infra_and_app` — Full auto-rollback capability (default)

**New hard limit:**
```yaml
policy:
  autonomy:
    hard_limits:
      allow_auto_rollback: true  # Override all rollback behavior
```

**Observation window tracking:**

Active rollouts are tracked in `policy_state.json`:
```json
{
  "active_rollout": {
    "release_id": "20260314-120000-feature-x",
    "previous_release": "20260314-111111-baseline",
    "started_at": "2026-03-14T12:00:00Z",
    "observation_until": "2026-03-14T12:10:00Z",
    "status": "observing"
  }
}
```

#### 4.12.5 Phase I Smoke Test

1. **Create baseline and good release:**
   ```bash
   npm run deploy:snapshot -- baseline --description "Working config"
   
   # Make a safe config change (e.g., increase observation window)
   # Edit .brain/config/nucleus.yaml: observation_window_minutes: 15
   
   npm run deploy:snapshot -- feature-safe --description "Increased observation window"
   npm run deploy:rollout -- <release-id>
   # Expected: Smoke tests pass, enters observation window, becomes stable
   ```

2. **Test bad rollout (smoke test failure):**
   ```bash
   # Break config (e.g., invalid Prometheus URL)
   # Edit .brain/config/nucleus.yaml: prometheus_url: "http://invalid:9999"
   
   npm run deploy:snapshot -- broken-config --description "Bad Prometheus URL"
   npm run deploy:rollout -- <broken-release-id>
   # Expected: Smoke tests fail, auto-rollback to previous, bad_rollout incident
   
   ls incidents/2026-*/INC-*bad_rollout*.json
   # Expected: JSON incident file exists
   ```

3. **Test rollout regression (passes smoke, fails metrics):**
   ```bash
   # This would require introducing a config that passes smoke tests
   # but causes high error rates during observation window
   # (e.g., aggressive rate limits, broken integrations)
   
   # Expected: Rollout passes smoke tests, enters observation
   # During observation: error rate spikes → rollout_regression incident
   # Auto-rollback to previous release
   ```

4. **Verify autonomy modes:**
   ```bash
   # Edit .brain/config/nucleus.yaml:
   #   policy.autonomy.autonomy_mode: "observe_only"
   
   # Try rollout with broken config
   npm run deploy:rollout -- <broken-release-id>
   # Expected: Detects failure but does NOT auto-rollback (observe_only)
   
   npm run incident:policy
   # Expected: Shows rollback_release=OFF (observe_only)
   ```

5. **Verify hard limits:**
   ```bash
   # Edit .brain/config/nucleus.yaml:
   #   policy.autonomy.hard_limits.allow_auto_rollback: false
   
   # Try rollout with broken config
   npm run deploy:rollout -- <broken-release-id>
   # Expected: Detects failure but does NOT auto-rollback (hard_limit)
   ```

### 4.13 Harden secrets and config

- Move hard‑coded tokens out of shell history into:
  - `~/.zshrc` exports (for local dev only), or
  - A `.env.local` loaded by scripts.
- In docs and Git, always redact the actual Upstash token and Redis password.

---

## 5. Telemetry Verification (Self-Check Commands)

**Use these commands to verify telemetry is working correctly.** Run them after any changes to telemetry code or infrastructure.

### 5.1 Quick verification checklist

```bash
# 1. Confirm Cloudflare Tunnel is running
pgrep -a cloudflared | head -5
# Expected: Should show process running 'nucleus-telemetry' tunnel

# 2. Confirm OpenTelemetry Collector is running
docker ps --filter name=nucleus-otel-collector
# Expected: Container status 'Up' with ports 4317-4318 exposed

# 3. Send test telemetry (must complete with NO opentelemetry errors)
NUCLEUS_ANON_TELEMETRY=true nucleus morning-brief
# Expected: Clean execution, no DEADLINE_EXCEEDED or export errors

# 4. Verify spans were written to local files
tail -3 .telemetry/traces.jsonl
# Expected: JSON with service.name="nucleus-anon-telemetry" and nucleus.command="morning-brief"

# 5. Verify collector received spans
npm run telemetry:summary
# Expected: Non-zero span count for 'nucleus-anon-telemetry'
```

### 5.2 Interpreting results

| Command | Success Indicator | Failure Indicator |
|---------|------------------|-------------------|
| `pgrep cloudflared` | Shows PID and `nucleus-telemetry` | No output or different tunnel name |
| `docker ps` | Status `Up`, ports `4317-4318` | Container not found or exited |
| `nucleus morning-brief` | No `opentelemetry` errors in output | `DEADLINE_EXCEEDED`, `Failed to export`, `Internal Server Error` |
| `tail traces.jsonl` | Valid JSON with `nucleus-anon-telemetry` | Empty file or missing service.name |
| `npm run telemetry:summary` | Shows `2+ nucleus-anon-telemetry` | Zero spans or service not listed |

**If any check fails:** Diagnose and repair telemetry before doing new feature work. See section 4 (Debugging) for troubleshooting steps.

### 5.3 Critical invariants (never regress these)

After the 2026-03-14 fixes, these must always be true:

1. **HTTP exporters only** - `anon_telemetry.py` uses `opentelemetry.exporter.otlp.proto.http` (NOT `proto.grpc`)
2. **Base endpoint without port** - Default endpoint is `https://telemetry.nucleusos.dev` (no `:4317` or `:4318`)
3. **Dynamic path passthrough** - Worker uses `new URL(request.url).pathname` (NOT hardcoded `/v1/traces`)
4. **Chunked base64 encoding** - Worker uses `toBase64(arrayBuffer)` helper with 8KB chunks (NOT `btoa(String.fromCharCode(...spread))`)

---

## 6. Minimal checklist for a new contributor or LLM

If you are **not Lokesh** and want to understand or extend this telemetry system, follow this checklist:

1. Read this file fully to understand the architecture.
2. Inspect these local files:
   - `scripts/drain-upstash-spans.js`
   - `scripts/telemetry.sh`
   - `scripts/telemetry-summary.sh`
   - `package.json`
3. Confirm Docker container `nucleus-otel-collector` exists in Docker Desktop.
4. Start collector and drain using the commands in section 3.1.
5. Run Nucleus commands with `NUCLEUS_ANON_TELEMETRY=true`.
6. Use `npm run telemetry:summary` and `docker logs nucleus-otel-collector` to validate spans.
7. If there are no spans, debug from the producer side (Cloudflare Worker and Nucleus SDK) using section 4 as a guide.

This document should be kept in sync with any future changes to the telemetry pipeline so that both humans and LLMs can orient quickly and make safe modifications.
