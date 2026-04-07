/**
 * Cloudflare Worker: Nucleus Telemetry Ingestion Edge
 *
 * Architecture docs:
 *   - CLOUD_TELEMETRY_QUICKSTART.md (cloud-side flow)
 *   - TELEMETRY_PIPELINE_README.md  (end-to-end architecture)
 *   - WINDSURF_SUPER_PROMPT.md      (mission charter, Phase A)
 *
 * Flow:
 *   1. Accept POST with OTLP binary/JSON body from Nucleus clients.
 *   2. Try direct delivery to Mac via Cloudflare Tunnel (telemetry.nucleusos.dev).
 *   3. If direct fails or times out (2s), buffer to Upstash Redis queue.
 *   4. Drain script on Mac pulls from Upstash → local OTel Collector.
 *
 * Server-side enrichment:
 *   - Country code from Cloudflare edge (request.cf.country, ISO 3166-1 alpha-2)
 *   - No IP address is logged or stored
 *
 * Env vars (set in Cloudflare dashboard):
 *   - UPSTASH_REDIS_REST_URL   — e.g. https://moral-swine-69544.upstash.io
 *   - UPSTASH_REDIS_REST_TOKEN — Upstash REST auth token
 *
 * Queue key: "nucleus:spans" (Redis list, base64-encoded OTLP payloads)
 */

// Safe base64 encoding for large binary payloads.
// btoa(String.fromCharCode(...new Uint8Array(buf))) crashes with call stack
// overflow for payloads > ~64KB because of the spread operator.
// This chunked version handles arbitrarily large OTLP batches.
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
    // CORS preflight for browser-based clients
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    if (request.method !== "POST") {
      return new Response("Method Not Allowed. POST OTLP spans to this endpoint.", { status: 405 });
    }

    const spanBody = await request.arrayBuffer();
    const contentType = request.headers.get("Content-Type") || "application/octet-stream";

    if (spanBody.byteLength === 0) {
      return new Response("Empty body", { status: 400 });
    }

    // Server-side geo enrichment: country code from Cloudflare edge
    // No IP is logged — only the ISO 3166-1 alpha-2 country code
    const country = request.cf?.country || "XX";

    let directOk = false;

    // ── Step 1: Try direct delivery via Cloudflare Tunnel ──
    // Pass through the incoming request path so both /v1/traces and /v1/metrics
    // are correctly routed to the collector (HTTP OTLP port 4318).
    const incomingPath = new URL(request.url).pathname || "/v1/traces";
    const tunnelBase = "https://812b058f-3422-421c-ba1b-7a641c5b8bfe.cfargotunnel.com";

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 2000);

      const res = await fetch(`${tunnelBase}${incomingPath}`, {
        method: "POST",
        body: spanBody,
        headers: {
          "Content-Type": contentType,
          "X-Nucleus-Country": country,
        },
        signal: controller.signal,
      });

      clearTimeout(timeout);
      directOk = res.ok;

      if (directOk) {
        return new Response("ok", {
          status: 200,
          headers: { "Access-Control-Allow-Origin": "*" },
        });
      }
    } catch (err) {
      // Tunnel down or timeout — fall through to Upstash buffer
    }

    // ── Step 2: Buffer to Upstash Redis (always when direct fails) ──
    try {
      const url = env.UPSTASH_REDIS_REST_URL;
      const token = env.UPSTASH_REDIS_REST_TOKEN;

      if (!url || !token) {
        console.error("[nucleus-telemetry] Missing UPSTASH_REDIS_REST_URL or UPSTASH_REDIS_REST_TOKEN");
        return new Response("Upstash env vars not set", { status: 500 });
      }

      // Encode binary OTLP payload as base64 for Redis storage.
      // Uses chunked encoding to avoid call stack overflow on large batches.
      // The drain script (drain-upstash-spans.js) decodes with Buffer.from(val, 'base64').
      const base64Span = toBase64(spanBody);

      // Wrap span with server-side metadata (geo, timestamp).
      // Format v2: JSON envelope. Drain script detects by leading '{'.
      // Old format (raw base64) is still supported by drain for backwards compat.
      const entry = JSON.stringify({
        _v: 2,
        span: base64Span,
        country: country,
        ts: Date.now(),
      });

      // Upstash REST API: RPUSH to list key "nucleus:spans"
      const payload = ["RPUSH", "nucleus:spans", entry];

      const res = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errText = await res.text().catch(() => "unknown");
        console.error(`[nucleus-telemetry] Upstash RPUSH failed: ${res.status} ${errText}`);
        return new Response("failed to queue", { status: 500 });
      }

      return new Response("queued", {
        status: 202,
        headers: { "Access-Control-Allow-Origin": "*" },
      });
    } catch (err) {
      console.error(`[nucleus-telemetry] Upstash error: ${err.message || err}`);
      return new Response("failed to queue", { status: 500 });
    }
  },
};
