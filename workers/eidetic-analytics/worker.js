// Eidetic conversion-funnel analytics — privacy-safe.
//
// Routes:
//   POST /event       — JSON body, CORS-enabled. Returns 204.
//   GET  /event?e=... — pixel-style tracking from <img> tag. Returns 1x1 GIF.
//   GET  /stats?days=N — admin-only (Bearer ADMIN_SECRET). Returns funnel JSON.
//   OPTIONS /event    — CORS preflight.
//
// Compliance with ADR-020 (local-first privacy posture):
//   - NO PII stored or logged (rejects email/ip/user_id/device_id keys → 400)
//   - NO IP / User-Agent ever written to Analytics Engine or console
//   - Only aggregate event counters with safe enum fields (event, surface, tier)
//
// Binding (wrangler.toml):
//   [[analytics_engine_datasets]]
//   binding = "ANALYTICS"
//   dataset = "eidetic_funnel"
//
// Secret:
//   ADMIN_SECRET — Bearer token guarding /stats. Set via `wrangler secret put`.

const ALLOWED_EVENTS  = new Set([
  // Product funnel events.
  "landing_view",
  "install_sh_fetch",
  "mcp_ping",
  "purchase",
  "dashboard_open",
  // Growth / distribution-automation events (growth-scheduler Worker).
  "growth_enqueue",
  "growth_posted",
  "growth_error",
  "growth_digest_error",
]);
const ALLOWED_SURFACE = new Set(["macos", "linux", "windows"]);
const ALLOWED_TIER    = new Set(["pro", "annual", "founder", "team"]);

// PII-flavoured keys — refuse any payload that includes these, even empty.
const FORBIDDEN_KEYS = ["email", "ip", "user_id", "device_id"];

// 1x1 transparent GIF (43 bytes).
const PIXEL_GIF = new Uint8Array([
  0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00, 0x80, 0x00,
  0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0x21, 0xf9, 0x04, 0x01, 0x00,
  0x00, 0x00, 0x00, 0x2c, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00,
  0x00, 0x02, 0x02, 0x44, 0x01, 0x00, 0x3b,
]);

const CORS_HEADERS = {
  "Access-Control-Allow-Origin":  "*",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Max-Age":       "86400",
};

function jsonResponse(obj, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", ...extraHeaders },
  });
}

function noContent(extraHeaders = {}) {
  return new Response(null, { status: 204, headers: extraHeaders });
}

function pixelResponse() {
  return new Response(PIXEL_GIF, {
    status: 200,
    headers: {
      "Content-Type":  "image/gif",
      "Content-Length": String(PIXEL_GIF.length),
      "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
      "Pragma":        "no-cache",
      ...CORS_HEADERS,
    },
  });
}

// Validate + strip an incoming payload. Returns {ok, value|error}.
// Only `event`, `surface`, `tier` are retained — every other key is dropped silently.
// Any FORBIDDEN_KEYS presence rejects the entire payload (400).
function sanitize(raw) {
  if (!raw || typeof raw !== "object") {
    return { ok: false, error: "payload must be an object" };
  }
  for (const k of FORBIDDEN_KEYS) {
    if (k in raw) {
      return { ok: false, error: `forbidden key: ${k}` };
    }
  }
  const event = typeof raw.event === "string" ? raw.event : null;
  if (!event || !ALLOWED_EVENTS.has(event)) {
    return { ok: false, error: "invalid event" };
  }
  const out = { event };
  if (typeof raw.surface === "string" && ALLOWED_SURFACE.has(raw.surface)) {
    out.surface = raw.surface;
  }
  if (typeof raw.tier === "string" && ALLOWED_TIER.has(raw.tier)) {
    out.tier = raw.tier;
  }
  return { ok: true, value: out };
}

// Write to Analytics Engine. NEVER includes IP / UA / cookies.
// Schema: blob1=event, blob2=surface, blob3=tier; double1=1 (count); index=event.
function writeEvent(env, payload) {
  if (!env.ANALYTICS || typeof env.ANALYTICS.writeDataPoint !== "function") {
    console.warn("ANALYTICS binding missing — event dropped:", payload.event);
    return;
  }
  try {
    env.ANALYTICS.writeDataPoint({
      blobs:   [payload.event, payload.surface || "", payload.tier || ""],
      doubles: [1],
      indexes: [payload.event],
    });
  } catch (err) {
    console.warn("writeDataPoint failed:", err && err.message);
  }
}

// GET /event?e=landing_view&s=macos&t=pro — pixel tracking from <img>.
function handlePixelEvent(url, env) {
  const event   = url.searchParams.get("e");
  const surface = url.searchParams.get("s");
  const tier    = url.searchParams.get("t");
  const raw = { event };
  if (surface) raw.surface = surface;
  if (tier)    raw.tier    = tier;
  const v = sanitize(raw);
  if (v.ok) {
    writeEvent(env, v.value);
  }
  // Always return the pixel — never reveal validation outcome to a browser <img>.
  return pixelResponse();
}

// POST /event — JSON body. CORS-enabled.
async function handlePostEvent(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return jsonResponse({ error: "invalid json" }, 400, CORS_HEADERS);
  }
  const v = sanitize(body);
  if (!v.ok) {
    return jsonResponse({ error: v.error }, 400, CORS_HEADERS);
  }
  writeEvent(env, v.value);
  return noContent(CORS_HEADERS);
}

// GET /stats?days=7 — admin-only Bearer auth.
async function handleStats(request, env, url) {
  const auth = request.headers.get("authorization") || "";
  const expected = env.ADMIN_SECRET ? `Bearer ${env.ADMIN_SECRET}` : null;
  if (!expected || auth !== expected) {
    return jsonResponse({ error: "unauthorized" }, 401);
  }
  if (!env.ANALYTICS_ACCOUNT_ID || !env.ANALYTICS_API_TOKEN) {
    return jsonResponse(
      { error: "analytics not yet provisioned",
        hint:  "set ANALYTICS_ACCOUNT_ID + ANALYTICS_API_TOKEN secrets and bind ANALYTICS dataset" },
      503,
    );
  }
  if (!env.ANALYTICS) {
    return jsonResponse({ error: "analytics not yet provisioned" }, 503);
  }

  const daysParam = parseInt(url.searchParams.get("days") || "7", 10);
  const days = Number.isFinite(daysParam) && daysParam > 0 && daysParam <= 90 ? daysParam : 7;

  // Analytics Engine SQL API. Counts events grouped by event name.
  const dataset = env.ANALYTICS_DATASET || "eidetic_funnel";
  const sql =
    `SELECT blob1 AS event, SUM(_sample_interval) AS count ` +
    `FROM ${dataset} ` +
    `WHERE timestamp > NOW() - INTERVAL '${days}' DAY ` +
    `GROUP BY event ` +
    `FORMAT JSON`;

  let counts = {};
  try {
    const res = await fetch(
      `https://api.cloudflare.com/client/v4/accounts/${env.ANALYTICS_ACCOUNT_ID}/analytics_engine/sql`,
      {
        method:  "POST",
        headers: {
          "Authorization": `Bearer ${env.ANALYTICS_API_TOKEN}`,
          "Content-Type":  "text/plain",
        },
        body: sql,
      },
    );
    if (!res.ok) {
      return jsonResponse(
        { error: "analytics query failed", status: res.status },
        502,
      );
    }
    const json = await res.json();
    for (const row of (json.data || [])) {
      counts[row.event] = Number(row.count) || 0;
    }
  } catch (err) {
    return jsonResponse({ error: "analytics query error", detail: err && err.message }, 502);
  }

  const landing_views   = counts.landing_view     || 0;
  const install_fetches = counts.install_sh_fetch || 0;
  const pings           = counts.mcp_ping         || 0;
  const purchases       = counts.purchase         || 0;
  const dashboard_opens = counts.dashboard_open   || 0;
  const conv_rate = landing_views > 0
    ? Number((purchases / landing_views).toFixed(4))
    : 0;

  return jsonResponse({
    days,
    landing_views,
    install_fetches,
    pings,
    purchases,
    dashboard_opens,
    conv_rate,
  });
}

// GET /funnel?days=N — admin-only Bearer auth. Returns stage-by-stage
// conversion drop-off: each step's count + the ratio to the previous step.
// Also includes growth-channel events (enqueued / posted / errors) so the
// publisher health is visible alongside conversion health in one query.
async function handleFunnel(request, env, url) {
  const auth = request.headers.get("authorization") || "";
  const expected = env.ADMIN_SECRET ? `Bearer ${env.ADMIN_SECRET}` : null;
  if (!expected || auth !== expected) {
    return jsonResponse({ error: "unauthorized" }, 401);
  }
  if (!env.ANALYTICS_ACCOUNT_ID || !env.ANALYTICS_API_TOKEN || !env.ANALYTICS) {
    return jsonResponse({ error: "analytics not yet provisioned" }, 503);
  }

  const daysParam = parseInt(url.searchParams.get("days") || "7", 10);
  const days = Number.isFinite(daysParam) && daysParam > 0 && daysParam <= 90 ? daysParam : 7;

  const dataset = env.ANALYTICS_DATASET || "eidetic_funnel";
  const sql =
    `SELECT blob1 AS event, SUM(_sample_interval) AS count ` +
    `FROM ${dataset} ` +
    `WHERE timestamp > NOW() - INTERVAL '${days}' DAY ` +
    `GROUP BY event ` +
    `FORMAT JSON`;

  let counts = {};
  try {
    const res = await fetch(
      `https://api.cloudflare.com/client/v4/accounts/${env.ANALYTICS_ACCOUNT_ID}/analytics_engine/sql`,
      {
        method:  "POST",
        headers: {
          "Authorization": `Bearer ${env.ANALYTICS_API_TOKEN}`,
          "Content-Type":  "text/plain",
        },
        body: sql,
      },
    );
    if (!res.ok) {
      return jsonResponse({ error: "analytics query failed", status: res.status }, 502);
    }
    const json = await res.json();
    for (const row of (json.data || [])) {
      counts[row.event] = Number(row.count) || 0;
    }
  } catch (err) {
    return jsonResponse({ error: "analytics query error", detail: err && err.message }, 502);
  }

  // Funnel stages in declared order. ratio_from_prev shows how many of the
  // previous stage's visitors made it to this one (0..1 or null when prev=0).
  const stages = [
    { name: "landing_view",     count: counts.landing_view     || 0 },
    { name: "install_sh_fetch", count: counts.install_sh_fetch || 0 },
    { name: "mcp_ping",         count: counts.mcp_ping         || 0 },
    { name: "dashboard_open",   count: counts.dashboard_open   || 0 },
    { name: "purchase",         count: counts.purchase         || 0 },
  ];
  for (let i = 0; i < stages.length; i++) {
    if (i === 0) {
      stages[i].ratio_from_prev = null;
      stages[i].ratio_from_top = 1;
    } else {
      const prev = stages[i - 1].count;
      const top  = stages[0].count;
      stages[i].ratio_from_prev = prev > 0 ? Number((stages[i].count / prev).toFixed(4)) : null;
      stages[i].ratio_from_top  = top  > 0 ? Number((stages[i].count / top ).toFixed(4)) : null;
    }
  }

  // Growth-channel side metrics for distribution publisher visibility.
  const growth = {
    enqueued:     counts.growth_enqueue       || 0,
    posted:       counts.growth_posted        || 0,
    errors:       counts.growth_error         || 0,
    digest_error: counts.growth_digest_error  || 0,
    publish_success_ratio:
      ((counts.growth_posted || 0) + (counts.growth_error || 0)) > 0
        ? Number(((counts.growth_posted || 0) / ((counts.growth_posted || 0) + (counts.growth_error || 0))).toFixed(4))
        : null,
  };

  return jsonResponse({
    days,
    stages,
    growth,
    raw_counts: counts,
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/event") {
      if (request.method === "OPTIONS") {
        return new Response(null, { status: 204, headers: CORS_HEADERS });
      }
      if (request.method === "GET") {
        return handlePixelEvent(url, env);
      }
      if (request.method === "POST") {
        return handlePostEvent(request, env);
      }
      return new Response("method not allowed", { status: 405, headers: CORS_HEADERS });
    }

    if (url.pathname === "/stats" && request.method === "GET") {
      return handleStats(request, env, url);
    }

    if (url.pathname === "/funnel" && request.method === "GET") {
      return handleFunnel(request, env, url);
    }

    if (url.pathname === "/" || url.pathname === "/health") {
      return jsonResponse({ ok: true, service: "eidetic-analytics" });
    }

    return new Response("not found", { status: 404 });
  },
};
