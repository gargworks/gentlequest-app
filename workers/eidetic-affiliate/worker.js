// Eidetic affiliate tracking + Gumroad redirect.
//
// Vanity URLs (https://eidetic.works/ref/<code>) resolve here, get logged to KV,
// and 302 to the appropriate Gumroad product with `?wanted=true&affiliate=<code>`.
// Gumroad propagates the `affiliate` query param into its sale webhook, where
// gumroad-kit-sync can pick it up for the 20% recurring payout.
//
// Routes:
//   GET  /ref/<code>            → 302 Gumroad Pro     ($29/mo)         + click log
//   GET  /ref/<code>/team       → 302 Gumroad Team    ($99/mo)         + click log
//   GET  /ref/<code>/founder    → 302 Gumroad Founder ($499 lifetime)  + click log
//   GET  /ref/<code>/annual     → 302 Gumroad Annual  ($299/yr)        + click log
//   GET  /admin/codes           → list affiliate codes        (Bearer ADMIN_SECRET)
//   POST /admin/codes           → register affiliate code     (Bearer ADMIN_SECRET)
//   GET  /admin/clicks?code=…   → click stats for a code      (Bearer ADMIN_SECRET)
//
// KV (EIDETIC_AFFILIATES_KV):
//   code:<code>                      → {name,email,created_at,click_count,last_click_ts}
//   click:<code>:<unix_ts>:<hash6>   → {ip_hash,ua_hash,referrer}  (TTL 90 days)
//
// Privacy: IPs + UAs are SHA-256-hashed before storage. No PII in click rows.
// Admin auth: Bearer token in env.ADMIN_SECRET. If unset, /admin/* returns 503.

const GUMROAD_PRO     = "https://eideticworks.gumroad.com/l/eidetic-pro";
const GUMROAD_TEAM    = "https://eideticworks.gumroad.com/l/eidetic-team";
const GUMROAD_FOUNDER = "https://eideticworks.gumroad.com/l/eidetic-pro-founder";
const GUMROAD_ANNUAL  = "https://eideticworks.gumroad.com/l/eidetic-pro-annual";

const CLICK_TTL_SECS = 90 * 24 * 60 * 60; // 90 days
const CODE_RE = /^[a-zA-Z0-9_-]{2,32}$/;

async function sha256Hex(input) {
  const data = new TextEncoder().encode(input || "");
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function redirect(target, code) {
  const url = new URL(target);
  url.searchParams.set("wanted", "true");
  url.searchParams.set("affiliate", code);
  return Response.redirect(url.toString(), 302);
}

function adminAuthGate(request, env) {
  if (!env.ADMIN_SECRET) {
    return json({ error: "admin not configured" }, 503);
  }
  const auth = request.headers.get("authorization") || "";
  const expected = `Bearer ${env.ADMIN_SECRET}`;
  if (auth !== expected) {
    return json({ error: "unauthorized" }, 401);
  }
  return null; // gate passed
}

async function logClick(env, code, request) {
  if (!env.EIDETIC_AFFILIATES_KV) return;

  const now = Math.floor(Date.now() / 1000);
  const ip = request.headers.get("cf-connecting-ip") || "";
  const ua = request.headers.get("user-agent") || "";
  const referrer = request.headers.get("referer") || "";

  const ipHash = await sha256Hex(ip);
  const uaHash = await sha256Hex(ua);
  const shortHash = ipHash.slice(0, 8);

  const clickKey = `click:${code}:${now}:${shortHash}`;
  const clickVal = JSON.stringify({
    ip_hash: ipHash,
    ua_hash: uaHash,
    referrer,
  });

  // Fire-and-forget KV writes; don't block the redirect on KV latency.
  env.EIDETIC_AFFILIATES_KV.put(clickKey, clickVal, {
    expirationTtl: CLICK_TTL_SECS,
  }).catch(() => {});

  // Update aggregate counter on the code row (best-effort, racy but fine for stats).
  const codeKey = `code:${code}`;
  env.EIDETIC_AFFILIATES_KV.get(codeKey)
    .then((existing) => {
      let rec;
      if (existing) {
        try {
          rec = JSON.parse(existing);
        } catch {
          rec = {};
        }
      } else {
        // Unknown code — record an anonymous shell so click stats still accumulate.
        rec = {
          name: null,
          email: null,
          created_at: null,
          click_count: 0,
          last_click_ts: 0,
          auto_created: true,
        };
      }
      rec.click_count = (rec.click_count || 0) + 1;
      rec.last_click_ts = now;
      return env.EIDETIC_AFFILIATES_KV.put(codeKey, JSON.stringify(rec));
    })
    .catch(() => {});
}

async function handleAdminClicks(request, env, url) {
  const code = url.searchParams.get("code");
  if (!code || !CODE_RE.test(code)) {
    return json({ error: "missing or invalid code" }, 400);
  }

  const codeRaw = await env.EIDETIC_AFFILIATES_KV.get(`code:${code}`);
  const codeRec = codeRaw ? JSON.parse(codeRaw) : null;

  // Walk click:<code>:* to compute distinct IP hashes.
  const distinct = new Set();
  let cursor;
  let total = 0;
  do {
    const listRes = await env.EIDETIC_AFFILIATES_KV.list({
      prefix: `click:${code}:`,
      cursor,
    });
    for (const k of listRes.keys) {
      total += 1;
      // The short hash is in the key; for distinct-IP, read the value's ip_hash.
      const raw = await env.EIDETIC_AFFILIATES_KV.get(k.name);
      if (raw) {
        try {
          const v = JSON.parse(raw);
          if (v.ip_hash) distinct.add(v.ip_hash);
        } catch {
          /* ignore */
        }
      }
    }
    cursor = listRes.list_complete ? undefined : listRes.cursor;
  } while (cursor);

  return json({
    code,
    registered: !!codeRec && !codeRec.auto_created,
    clicks: codeRec?.click_count ?? total,
    last_seen: codeRec?.last_click_ts ?? null,
    distinct_ip_count: distinct.size,
    raw_event_count: total,
  });
}

async function handleAdminCodesList(env) {
  const out = [];
  let cursor;
  do {
    const listRes = await env.EIDETIC_AFFILIATES_KV.list({
      prefix: "code:",
      cursor,
    });
    for (const k of listRes.keys) {
      const code = k.name.slice("code:".length);
      const raw = await env.EIDETIC_AFFILIATES_KV.get(k.name);
      let rec = {};
      if (raw) {
        try {
          rec = JSON.parse(raw);
        } catch {
          rec = {};
        }
      }
      out.push({
        code,
        name: rec.name ?? null,
        email: rec.email ?? null,
        created_at: rec.created_at ?? null,
        click_count: rec.click_count ?? 0,
        last_click_ts: rec.last_click_ts ?? null,
        auto_created: !!rec.auto_created,
      });
    }
    cursor = listRes.list_complete ? undefined : listRes.cursor;
  } while (cursor);

  return json({ count: out.length, codes: out });
}

async function handleAdminCodesPost(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid json body" }, 400);
  }
  const code = (body.code || "").trim();
  if (!CODE_RE.test(code)) {
    return json(
      { error: "code must match /^[a-zA-Z0-9_-]{2,32}$/" },
      400
    );
  }
  const name = (body.name || "").toString().slice(0, 200);
  const email = (body.email || "").toString().slice(0, 200);
  const created_at = body.created_at || new Date().toISOString();

  const codeKey = `code:${code}`;
  const existing = await env.EIDETIC_AFFILIATES_KV.get(codeKey);
  let rec;
  if (existing) {
    try {
      rec = JSON.parse(existing);
    } catch {
      rec = {};
    }
    // Promote auto-created shells; otherwise refuse to clobber a real registration.
    if (rec && !rec.auto_created) {
      return json({ error: "code already registered", code }, 409);
    }
  } else {
    rec = { click_count: 0, last_click_ts: null };
  }

  rec.name = name;
  rec.email = email;
  rec.created_at = created_at;
  rec.auto_created = false;

  await env.EIDETIC_AFFILIATES_KV.put(codeKey, JSON.stringify(rec));
  return json({ ok: true, code, registered: true }, 201);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const { pathname } = url;

    // -------- public redirect routes --------
    if (pathname.startsWith("/ref/")) {
      if (request.method !== "GET") {
        return new Response("method not allowed", { status: 405 });
      }
      const parts = pathname.slice("/ref/".length).split("/").filter(Boolean);
      const code = parts[0] || "";
      const variant = (parts[1] || "").toLowerCase();

      if (!CODE_RE.test(code)) {
        return new Response("invalid affiliate code", { status: 400 });
      }

      await logClick(env, code, request);

      switch (variant) {
        case "":
          return redirect(GUMROAD_PRO, code);
        case "team":
          return redirect(GUMROAD_TEAM, code);
        case "founder":
          return redirect(GUMROAD_FOUNDER, code);
        case "annual":
          return redirect(GUMROAD_ANNUAL, code);
        default:
          return new Response("unknown product variant", { status: 404 });
      }
    }

    // -------- admin routes --------
    if (pathname.startsWith("/admin/")) {
      const gate = adminAuthGate(request, env);
      if (gate) return gate;
      if (!env.EIDETIC_AFFILIATES_KV) {
        return json({ error: "KV namespace not bound" }, 503);
      }

      if (pathname === "/admin/clicks" && request.method === "GET") {
        return handleAdminClicks(request, env, url);
      }
      if (pathname === "/admin/codes" && request.method === "GET") {
        return handleAdminCodesList(env);
      }
      if (pathname === "/admin/codes" && request.method === "POST") {
        return handleAdminCodesPost(request, env);
      }
      return json({ error: "not found" }, 404);
    }

    // -------- misc --------
    if (pathname === "/ping") {
      return new Response(null, { status: 204 });
    }
    if (pathname === "/" || pathname === "") {
      return new Response("eidetic-affiliate: OK", { status: 200 });
    }
    return new Response("not found", { status: 404 });
  },
};
