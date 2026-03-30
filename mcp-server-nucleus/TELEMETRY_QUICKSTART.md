# TELEMETRY QUICKSTART

This is a **short, operational cheat sheet** for Nucleus telemetry on Lokesh's Mac. Use this when you just want telemetry to work without re-reading the long README.

For deeper details, see `TELEMETRY_PIPELINE_README.md` in the same directory.

---

## 1. Paths and prerequisites

- Repo for telemetry scripts:
  - `/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus`
- Main Nucleus repo (where you run `nucleus` commands):
  - `/Users/lokeshgarg/ai-mvp-backend`
- Docker Desktop should be running.
- Cloudflare Worker + Upstash Redis are already configured.

Export your Upstash Redis credentials once per shell (or put them in your shell profile):

```bash
export UPSTASH_REDIS_URL="rediss://moral-swine-69544.upstash.io:6379"
export UPSTASH_REDIS_TOKEN="<Upstash Redis password/token>"
```

---

## 2. Start telemetry (collector + drain)

You typically need **two terminals** dedicated to telemetry.

### Terminal 1 – Collector

```bash
cd ~/ai-mvp-backend/mcp-server-nucleus
npm run telemetry:up
```

- Starts the `nucleus-otel-collector` Docker container.
- If it is already running, this is a no-op.

### Terminal 2 – Upstash drain

```bash
cd ~/ai-mvp-backend/mcp-server-nucleus
npm run telemetry:drain
```

- Starts the Upstash → OTLP drain loop.
- This terminal should stay open while you want telemetry flowing into your local collector.

### Optional – Cloudflare tunnel

If you want **live** telemetry from remote clients or from the public internet:

- Start your Cloudflare tunnel for `telemetry.nucleus.sh` (same way you used before) so that the Worker can reach `localhost:4317`.

---

## 3. Use Nucleus with telemetry enabled

In a **separate terminal** where you do your normal work:

```bash
cd ~/ai-mvp-backend
NUCLEUS_ANON_TELEMETRY=true nucleus morning-brief
```

- Any Nucleus command with `NUCLEUS_ANON_TELEMETRY=true` will emit telemetry spans.

You can alias this if you want:

```bash
alias ntelemetry='cd ~/ai-mvp-backend && NUCLEUS_ANON_TELEMETRY=true nucleus'

# Example usage:
ntelemetry morning-brief
```

---

## 4. Inspect telemetry

### 4.1 Quick numeric summary

From `mcp-server-nucleus` repo:

```bash
cd ~/ai-mvp-backend/mcp-server-nucleus
npm run telemetry:summary
```

- Shows:
  - Total spans seen in the last 500 collector log lines.
  - Spans where `service.name` starts with `nucleus`.
  - Last Trace ID.
  - Approximate per-service counts.

If you only see:

```text
[summary] Inspecting last 500 log lines from 'nucleus-otel-collector'...
```

and nothing else, it means the collector log currently has no matching span entries (telemetry path not fully wired or too quiet).

### 4.2 Raw logs

For deeper inspection:

```bash
docker logs nucleus-otel-collector --tail 100
```

You should see entries with `Trace ID` and `service.name` when spans are flowing.

---

## 5. Stop telemetry when done

When you want to stop all telemetry infra:

1. **Stop drain loop** – press `Ctrl+C` in the Terminal 2 window running `npm run telemetry:drain`.

2. **Stop collector**:

   ```bash
   cd ~/ai-mvp-backend/mcp-server-nucleus
   npm run telemetry:down
   ```

This stops the `nucleus-otel-collector` container.

---

## 6. If something looks wrong

Use this sequence:

1. Check collector is running:

   ```bash
   docker ps --format '{{.Names}}' | grep nucleus-otel-collector
   ```

2. Check collector logs:

   ```bash
   docker logs nucleus-otel-collector --tail 40
   ```

3. Run summary again:

   ```bash
   cd ~/ai-mvp-backend/mcp-server-nucleus
   npm run telemetry:summary
   ```

4. Make sure you ran a Nucleus command **with** `NUCLEUS_ANON_TELEMETRY=true`.

If those are all correct and you still see no spans, the issue is likely on the Cloudflare Worker or SDK production side. In that case, read `TELEMETRY_PIPELINE_README.md` for a full deep-dive and debugging steps.
