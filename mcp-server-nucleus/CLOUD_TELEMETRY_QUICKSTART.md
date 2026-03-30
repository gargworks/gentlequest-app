# CLOUD TELEMETRY QUICKSTART (WORKER + TUNNEL)

**Status:** ✅ Fully verified working as of 2026-03-14 (HTTP exporters, chunked base64, dynamic path routing)

This quickstart explains the **Cloudflare + Upstash + Tunnel** side of Nucleus telemetry so you (or any LLM) can reason about spans coming from the internet into your local collector.

For the local collector/drain side, see:
- `TELEMETRY_PIPELINE_README.md`
- `TELEMETRY_QUICKSTART.md`

Root local paths assumed:
- `/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus`
- `/Users/lokeshgarg/ai-mvp-backend`

---

## 1. High‑level flow (cloud side)

1. Nucleus client sends telemetry using **OTLP HTTP exporters** to `https://telemetry.nucleusos.dev` (Cloudflare Worker).
2. **Direct path (primary):** Worker → Cloudflare Tunnel → `localhost:4318` (HTTP OTLP) → OpenTelemetry Collector
3. **Fallback path (when tunnel down):** Worker → Upstash Redis (base64-encoded spans) → drain script → Collector
4. Your local **drain script** reads from Upstash and forwards spans to the local collector when needed.

**Key architecture (2026-03-14):** SDK uses HTTP exporters (`opentelemetry.exporter.otlp.proto.http`), NOT gRPC. Worker dynamically passes through `/v1/traces` and `/v1/metrics` paths. Base64 encoding uses chunked helper to avoid call stack overflow on large OTLP batches.

The Worker is the "cloud edge", Upstash is the persistence layer, and the Tunnel provides direct local access.

### Verified Configuration

- **Tunnel UUID:** `812b058f-3422-421c-ba1b-7a641c5b8bfe`
- **Custom Domain:** `telemetry.nucleusos.dev` → tunnel → `localhost:4318`
- **Worker URL:** `https://nucleus-telemetry.morning-lake-f944.workers.dev`
- **Upstash Region:** Mumbai (ap-south-1)
- **Queue Key:** `nucleus:spans`

---

## 2. Cloudflare Worker

### 2.1 Worker identity and environment

- Worker name (conceptual): `nucleus-telemetry`.
- Deployed in your Cloudflare account.
- Environment variables configured in Cloudflare dashboard:
  - `UPSTASH_REDIS_REST_URL` – e.g. `https://moral-swine-69544.upstash.io`.
  - `UPSTASH_REDIS_REST_TOKEN` – Upstash REST token.

The Worker should **not** have the raw Redis password; it only needs REST creds.

### 2.2 Actual Worker behavior (verified 2026-03-14)

The Worker implementation in `cloudflare/worker-telemetry.js`:

```js
// Chunked base64 helper (fixes call stack overflow on large OTLP batches)
function toBase64(arrayBuffer) {
  const bytes = new Uint8Array(arrayBuffer);
  let binary = "";
  const chunkSize = 8192;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    const chunk = bytes.subarray(i, i + chunkSize);
    binary += String.fromCharCode(...chunk);
  }
  return btoa(binary);
}

export default {
  async fetch(request, env, ctx) {
    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }

    const spanBody = await request.arrayBuffer();
    const contentType = request.headers.get("Content-Type") || "application/octet-stream";

    // Dynamic path passthrough (supports both /v1/traces and /v1/metrics)
    const incomingPath = new URL(request.url).pathname || "/v1/traces";
    const tunnelBase = "https://812b058f-3422-421c-ba1b-7a641c5b8bfe.cfargotunnel.com";

    let directOk = false;

    // Try direct delivery via Cloudflare Tunnel (2s timeout)
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 2000);

      const res = await fetch(`${tunnelBase}${incomingPath}`, {
        method: "POST",
        body: spanBody,
        headers: { "Content-Type": contentType },
        signal: controller.signal,
      });

      clearTimeout(timeout);
      directOk = res.ok;

      if (directOk) {
        return new Response("ok", { status: 200 });
      }
    } catch (err) {
      // Tunnel down or timeout — fall through to Upstash buffer
    }

    // Fallback: Buffer to Upstash Redis (only when direct fails)
    try {
      const base64Span = toBase64(spanBody); // Chunked encoding
      const payload = ["RPUSH", "nucleus:spans", base64Span];

      const res = await fetch(env.UPSTASH_REDIS_REST_URL, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.UPSTASH_REDIS_REST_TOKEN}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        return new Response("failed to queue", { status: 500 });
      }

      return new Response("queued", { status: 202 });
    } catch (err) {
      return new Response("failed to queue", { status: 500 });
    }
  },
};
```

Key points:
- **Dynamic path routing**: Uses `new URL(request.url).pathname` to support both `/v1/traces` and `/v1/metrics`
- **Chunked base64**: Uses `toBase64()` helper with 8KB chunks to avoid call stack overflow
- **Direct-first strategy**: Tries tunnel delivery first (2s timeout), only buffers to Upstash on failure
- **Tunnel URL**: Uses tunnel UUID directly (`812b058f-3422-421c-ba1b-7a641c5b8bfe.cfargotunnel.com`)
- **Upstash REST API**: Uses `RPUSH` command via REST endpoint

### 2.3 How to update the Worker (summary)

1. Open Cloudflare dashboard → Workers & Pages → your telemetry Worker.
2. Edit the script to align with the pseudocode above.
3. Ensure `env.UPSTASH_REDIS_REST_URL` and `env.UPSTASH_REDIS_REST_TOKEN` are referenced exactly.
4. Deploy and test with a simple curl:

```bash
curl -X POST \
  -H "Content-Type: application/x-protobuf" \
  --data-binary @dummy-span.bin \
  'https://<your-worker-route>/v1/traces'
```

Then watch Redis and local collector logs once drain is running.

---

## 3. Upstash Redis (cloud view)

- Service: Upstash Redis, region Mumbai (ap-south-1).
- REST credentials are stored in Worker env vars.
- Redis queue key: `nucleus:spans`.
- Values: base64‑encoded OTLP payloads (each entry equals one HTTP POST’s worth of spans, or one span batch).

You can inspect the queue from a dev machine (not from the Worker) via REST:

```bash
curl "${UPSTASH_REDIS_REST_URL}/lrange/nucleus:spans/0/10" \
  -H "Authorization: Bearer ${UPSTASH_REDIS_REST_TOKEN}"
```

This is useful to confirm that the Worker is actually writing entries.

---

## 4. Cloudflare Tunnel

The tunnel connects a public hostname (e.g. `telemetry.nucleus.sh`) to your local collector.

### 4.1 Conceptual config

- Public hostname: `telemetry.nucleus.sh`.
- Origin: `http://localhost:4318` or `http://localhost:4317` depending on whether you use HTTP or gRPC OTLP.
- Tunnel name: something like `nucleus-telemetry`.

The Worker’s `directUrl` should match the hostname and OTLP path you expose via the tunnel, for example:

- `https://telemetry.nucleus.sh/v1/traces` → forwarded to `http://localhost:4318/v1/traces` (HTTP OTLP).

### 4.2 Typical tunnel command

On your Mac (one-time per session):

```bash
cloudflared tunnel run nucleus-telemetry
```

Or using the `cloudflared` config file in `~/.cloudflared/config.yml` if you defined one.

When this is running, `telemetry.nucleus.sh` becomes reachable from the Worker.

---

## 5. End‑to‑end sanity test (cloud → local)

Once you have:
- Collector running (`npm run telemetry:up`).
- Drain running (`npm run telemetry:drain`).
- Cloudflare tunnel running (`cloudflared tunnel run nucleus-telemetry`).
- Worker deployed as described.

Do this:

1. **Send a test span from any machine** (even remote) to the Worker URL:

   ```bash
   curl -X POST \
     -H "Content-Type: application/x-protobuf" \
     --data-binary @dummy-span.bin \
     'https://<your-worker-route>/v1/traces'
   ```

   - `dummy-span.bin` can be any small OTLP batch generated by your SDK.

2. **Check Upstash** to ensure at least one new entry is in `nucleus:spans` (if you always enqueue).

3. **Wait a few seconds** for drain to forward spans to collector.

4. **Run summary locally**:

   ```bash
   cd ~/ai-mvp-backend/mcp-server-nucleus
   npm run telemetry:summary
   ```

   - If wiring is correct, you should see non‑zero span counts.

5. **Inspect raw logs** if needed:

   ```bash
   docker logs nucleus-otel-collector --tail 60
   ```

---

## 6. What to adjust next

If spans are still not visible locally:

- Confirm Worker logs (in Cloudflare dashboard) show successful Upstash writes or direct sends.
- Confirm Upstash queue size > 0 using REST.
- Confirm drain script is **decoding** base64 payloads consistently with how Worker encodes them.
- Confirm collector is listening on the same OTLP path you used in `directUrl`.

Any future changes you make to the Worker, Upstash schema, or tunnel hostname should be reflected in this file so LLMs and contributors stay in sync.
