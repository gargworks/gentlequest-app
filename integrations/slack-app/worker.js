// Eidetic — Slack App Worker
//
// Lets any Slack user run `/eidetic <question>` in their workspace and have it
// answered by THEIR own eideticd daemon (exposed via Cloudflare tunnel). The
// Worker is a thin HMAC-verifying relay; no engram content is ever stored
// here. The user's bridge URL + bearer token live in Workers KV, keyed by
// team_id + user_id (see ADR-020 — no PII beyond Slack IDs).
//
// Routes:
//   GET  /slack-setup       — HTML form: user pastes bridge URL + token.
//   POST /slack-setup       — Form submit handler; writes config to KV.
//   POST /slack/command     — Slack slash-command receiver (HMAC-verified).
//   POST /slack/oauth       — OAuth install callback (token exchange).
//   GET  /healthz           — Worker liveness probe.
//
// Secrets (wrangler secret put):
//   SLACK_SIGNING_SECRET    — used for HMAC verification on /slack/command.
//   SLACK_CLIENT_ID         — Slack app client id (OAuth).
//   SLACK_CLIENT_SECRET     — Slack app client secret (OAuth).
//
// KV bindings:
//   EIDETIC_SLACK_KV        — namespace storing team:<team>:user:<user>
//                             values: JSON {bridge_url, token, updated_at}
//
// Trust boundary (per ADR-020):
//   - Bridge URL + bearer token ARE customer-provided sensitive data.
//   - Stored in Workers KV (encryption-at-rest = Cloudflare-managed key,
//     not customer-managed). Documented in README §Privacy.
//   - Only team_id + user_id from Slack are retained as keys. No channel
//     contents, no user names, no email — purely opaque IDs.
//   - Token is only ever read on the synchronous /slack/command path and
//     forwarded to the user's own bridge URL over HTTPS. Never logged.

const MAX_TIMESTAMP_SKEW_SEC = 60 * 5;        // Slack replay window: 5 min.
const BRIDGE_FETCH_TIMEOUT_MS = 12_000;        // Slack response budget = 3s for
                                               // ack + 30s for response_url.
const TOP_ENGRAMS = 3;
const ENGRAM_SNIPPET_CHARS = 240;

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === "/healthz") {
      return json({ ok: true, service: "eidetic-slack" });
    }

    if (url.pathname === "/slack-setup") {
      if (request.method === "GET")  return renderSetupPage(url);
      if (request.method === "POST") return handleSetupSubmit(request, env);
      return new Response("method not allowed", { status: 405 });
    }

    if (url.pathname === "/slack/command") {
      if (request.method !== "POST") return new Response("method not allowed", { status: 405 });
      return handleSlashCommand(request, env, ctx);
    }

    if (url.pathname === "/slack/oauth") {
      if (request.method !== "POST" && request.method !== "GET") {
        return new Response("method not allowed", { status: 405 });
      }
      return handleOauth(request, env);
    }

    return new Response("not found", { status: 404 });
  },
};

// ---------------------------------------------------------------------------
// /slack/command — HMAC-verified slash-command handler
// ---------------------------------------------------------------------------

async function handleSlashCommand(request, env, ctx) {
  // Slack signs the raw request body, so we must read it as text before
  // running formData() (which consumes the body).
  const rawBody = await request.text();

  const sig       = request.headers.get("x-slack-signature") || "";
  const timestamp = request.headers.get("x-slack-request-timestamp") || "";

  const verified = await verifySlackSignature({
    signingSecret: env.SLACK_SIGNING_SECRET,
    signature: sig,
    timestamp,
    rawBody,
  });
  if (!verified) {
    return new Response("invalid signature", { status: 401 });
  }

  const form = parseFormUrlEncoded(rawBody);
  const text     = (form.text     || "").trim();
  const userId   = form.user_id   || "";
  const teamId   = form.team_id   || "";
  const responseUrl = form.response_url || "";

  if (!teamId || !userId) {
    return ephemeral("Missing team_id / user_id from Slack payload.");
  }
  if (!text) {
    return ephemeral("Usage: `/eidetic <your question>`");
  }

  const config = await loadUserConfig(env, teamId, userId);
  if (!config) {
    const setupUrl = setupUrlFor(request);
    return ephemeral(
      `Hi! Configure your bridge URL + token at ${setupUrl} (one time).`
    );
  }

  // Fire-and-forget the daemon call so Slack gets <3s ack. Real result is
  // delivered via response_url (ephemeral) once the bridge replies.
  const asyncWork = answerAndDeliver({
    bridgeUrl: config.bridge_url,
    token: config.token,
    question: text,
    responseUrl,
  });
  // ctx.waitUntil keeps the Worker alive past the response.
  ctx.waitUntil(asyncWork);

  return ephemeral(`Asking your eidetic-daemon: _${escapeMd(text)}_ …`);
}

async function answerAndDeliver({ bridgeUrl, token, question, responseUrl }) {
  try {
    const data = await askBridge(bridgeUrl, token, question);
    const blocks = renderAnswerBlocks(question, data);
    await postToResponseUrl(responseUrl, {
      response_type: "ephemeral",
      blocks,
    });
  } catch (err) {
    await postToResponseUrl(responseUrl, {
      response_type: "ephemeral",
      text: `Bridge call failed: ${truncate(String(err.message || err), 200)}`,
    });
  }
}

async function askBridge(bridgeUrl, token, question) {
  const url = `${bridgeUrl.replace(/\/+$/, "")}/ask?question=${encodeURIComponent(question)}`;
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), BRIDGE_FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    });
    if (!res.ok) {
      throw new Error(`bridge HTTP ${res.status}`);
    }
    return await res.json();
  } finally {
    clearTimeout(t);
  }
}

async function postToResponseUrl(responseUrl, payload) {
  if (!responseUrl) return;
  await fetch(responseUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// Slack Block Kit rendering
// ---------------------------------------------------------------------------

function renderAnswerBlocks(question, data) {
  const answer = data.answer || data.instructions || data.response || "";
  const items  = data.results || data.engrams || data.hits || [];
  const top    = Array.isArray(items) ? items.slice(0, TOP_ENGRAMS) : [];

  const blocks = [
    {
      type: "header",
      text: { type: "plain_text", text: truncate(question, 140), emoji: false },
    },
  ];

  if (answer) {
    blocks.push({
      type: "section",
      text: { type: "mrkdwn", text: truncate(answer, 2800) },
    });
  }

  if (top.length > 0) {
    blocks.push({ type: "divider" });
    for (const r of top) {
      const surface = String(r.surface || r.meta?.surface || "—");
      const ts      = String(r.ts || r.timestamp || "");
      const snippet = truncate(String(r.payload || r.text || ""), ENGRAM_SNIPPET_CHARS);
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: `*${escapeMd(surface)}* · _${escapeMd(ts)}_\n${escapeMd(snippet)}`,
        },
      });
    }
  } else if (!answer) {
    blocks.push({
      type: "section",
      text: { type: "mrkdwn", text: "_No matching engrams._" },
    });
  }

  blocks.push({
    type: "context",
    elements: [
      {
        type: "mrkdwn",
        text: "<https://eidetic.works/dashboard|View all in dashboard →>",
      },
    ],
  });

  return blocks;
}

// ---------------------------------------------------------------------------
// HMAC verification (constant-time via crypto.subtle.verify)
// ---------------------------------------------------------------------------

async function verifySlackSignature({ signingSecret, signature, timestamp, rawBody }) {
  if (!signingSecret || !signature || !timestamp) return false;
  if (!signature.startsWith("v0=")) return false;

  const tsNum = Number(timestamp);
  if (!Number.isFinite(tsNum)) return false;
  const nowSec = Math.floor(Date.now() / 1000);
  if (Math.abs(nowSec - tsNum) > MAX_TIMESTAMP_SKEW_SEC) return false;

  const baseString = `v0:${timestamp}:${rawBody}`;
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(signingSecret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"],
  );

  const sigHex = signature.slice(3); // strip "v0="
  const sigBytes = hexToBytes(sigHex);
  if (!sigBytes) return false;

  return crypto.subtle.verify(
    "HMAC",
    key,
    sigBytes,
    new TextEncoder().encode(baseString),
  );
}

function hexToBytes(hex) {
  if (hex.length % 2 !== 0) return null;
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) {
    const byte = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
    if (Number.isNaN(byte)) return null;
    out[i] = byte;
  }
  return out;
}

// ---------------------------------------------------------------------------
// /slack-setup — HTML form for the user to paste bridge URL + token
// ---------------------------------------------------------------------------

function renderSetupPage(url) {
  const team = url.searchParams.get("team_id") || "";
  const user = url.searchParams.get("user_id") || "";
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Eidetic for Slack — Setup</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body { font: 16px/1.5 system-ui, sans-serif; max-width: 560px; margin: 4rem auto; padding: 0 1rem; color: #222; }
  h1 { font-size: 1.4rem; margin: 0 0 .5rem; }
  p  { color: #555; }
  label { display: block; margin: 1rem 0 .25rem; font-weight: 600; }
  input[type=text], input[type=password] { width: 100%; padding: .55rem .65rem; border: 1px solid #ccc; border-radius: 6px; font: inherit; }
  button { margin-top: 1.25rem; padding: .65rem 1.1rem; border: 0; border-radius: 6px; background: #1264a3; color: #fff; font: inherit; cursor: pointer; }
  small { color: #777; }
  .err { color: #b00020; }
</style>
</head>
<body>
  <h1>Connect your eidetic-daemon to Slack</h1>
  <p>Paste the Cloudflare-tunnel URL of your local <code>eideticd -bridge</code> and the bearer token from <code>~/.eidetic/bridge-token</code>. Both stay in Cloudflare Workers KV; nobody else in your workspace can read them.</p>
  <form method="POST" action="/slack-setup">
    <input type="hidden" name="team_id" value="${escapeHtml(team)}">
    <input type="hidden" name="user_id" value="${escapeHtml(user)}">
    <label for="bridge_url">Bridge URL</label>
    <input id="bridge_url" name="bridge_url" type="text"
           placeholder="https://something.trycloudflare.com" required>
    <small>Must be HTTPS on <code>*.trycloudflare.com</code> or <code>*.cloudflare.com</code>.</small>
    <label for="token">Bearer token</label>
    <input id="token" name="token" type="password" required>
    <small>Contents of <code>~/.eidetic/bridge-token</code> on the machine running the daemon.</small>
    <button type="submit">Save</button>
  </form>
</body>
</html>`;
  return new Response(html, {
    status: 200,
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
}

async function handleSetupSubmit(request, env) {
  const rawBody = await request.text();
  const form = parseFormUrlEncoded(rawBody);
  const teamId    = form.team_id    || "";
  const userId    = form.user_id    || "";
  const bridgeUrl = (form.bridge_url || "").trim();
  const token     = (form.token      || "").trim();

  if (!teamId || !userId) {
    return new Response("Missing team_id / user_id — open setup via the slash-command prompt.", { status: 400 });
  }
  if (!isAllowedBridgeUrl(bridgeUrl)) {
    return new Response(
      "Bridge URL must be HTTPS on *.trycloudflare.com or *.cloudflare.com. " +
      "Wider hostnames are intentionally rejected so a misconfigured Slack " +
      "install can't be redirected at an arbitrary internet endpoint.",
      { status: 400 },
    );
  }
  if (!token || token.length < 16) {
    return new Response("Bearer token looks too short — paste the full contents of ~/.eidetic/bridge-token.", { status: 400 });
  }

  await env.EIDETIC_SLACK_KV.put(
    kvKey(teamId, userId),
    JSON.stringify({ bridge_url: bridgeUrl, token, updated_at: new Date().toISOString() }),
  );

  const html = `<!doctype html><meta charset="utf-8">
<title>Saved</title>
<body style="font: 16px/1.5 system-ui, sans-serif; max-width: 560px; margin: 4rem auto; padding: 0 1rem;">
<h1>Saved.</h1>
<p>Run <code>/eidetic &lt;question&gt;</code> in any Slack channel. The Worker will route through your bridge URL and reply just to you.</p>
</body>`;
  return new Response(html, {
    status: 200,
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
}

// Bridge URL allowlist — keep the surface tight.
// `*.trycloudflare.com` is the default tunnel hostname.
// `*.cloudflare.com` covers Named Tunnels and custom workers proxies.
// Document in README §Bridge-URL-allowlist if you need to widen this.
function isAllowedBridgeUrl(raw) {
  let u;
  try { u = new URL(raw); } catch { return false; }
  if (u.protocol !== "https:") return false;
  const host = u.hostname.toLowerCase();
  return host.endsWith(".trycloudflare.com") || host.endsWith(".cloudflare.com");
}

// ---------------------------------------------------------------------------
// /slack/oauth — OAuth install flow
// ---------------------------------------------------------------------------
//
// Wired here as a scaffold: the user clicks "Add to Slack" on
// eidetic.works/slack-setup, Slack redirects them back here with ?code=...,
// we exchange the code for an access_token via oauth.v2.access, then redirect
// them to the per-user setup form pre-populated with their team_id + user_id.

async function handleOauth(request, env) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  if (!code) {
    return new Response("Missing ?code= from Slack OAuth redirect.", { status: 400 });
  }
  if (!env.SLACK_CLIENT_ID || !env.SLACK_CLIENT_SECRET) {
    return new Response("OAuth client not configured on this Worker.", { status: 500 });
  }

  const params = new URLSearchParams({
    code,
    client_id: env.SLACK_CLIENT_ID,
    client_secret: env.SLACK_CLIENT_SECRET,
  });
  const res = await fetch("https://slack.com/api/oauth.v2.access", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: params.toString(),
  });
  const data = await res.json().catch(() => ({}));
  if (!data.ok) {
    return new Response(`Slack OAuth failed: ${data.error || "unknown"}`, { status: 400 });
  }

  const teamId = data.team?.id || "";
  const userId = data.authed_user?.id || "";

  // Redirect to setup form pre-filled with team/user so the user only has to
  // paste bridge URL + token.
  const redirect = new URL(url);
  redirect.pathname = "/slack-setup";
  redirect.search   = `?team_id=${encodeURIComponent(teamId)}&user_id=${encodeURIComponent(userId)}`;
  return Response.redirect(redirect.toString(), 302);
}

// ---------------------------------------------------------------------------
// KV helpers
// ---------------------------------------------------------------------------

function kvKey(teamId, userId) {
  return `team:${teamId}:user:${userId}`;
}

async function loadUserConfig(env, teamId, userId) {
  const raw = await env.EIDETIC_SLACK_KV.get(kvKey(teamId, userId));
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

// ---------------------------------------------------------------------------
// Generic helpers
// ---------------------------------------------------------------------------

function parseFormUrlEncoded(body) {
  const out = {};
  for (const pair of body.split("&")) {
    if (!pair) continue;
    const eq = pair.indexOf("=");
    const k = eq === -1 ? pair : pair.slice(0, eq);
    const v = eq === -1 ? "" : pair.slice(eq + 1);
    out[decodeURIComponent(k.replace(/\+/g, " "))] =
      decodeURIComponent(v.replace(/\+/g, " "));
  }
  return out;
}

function ephemeral(text) {
  return json({ response_type: "ephemeral", text });
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function truncate(s, n) {
  if (!s) return "";
  return s.length > n ? `${s.slice(0, n - 1)}…` : s;
}

// Minimal Slack mrkdwn escape — keep `*`, `_`, `~`, `<`, `>`, `` ` `` safe.
function escapeMd(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function setupUrlFor(request) {
  const u = new URL(request.url);
  u.pathname = "/slack-setup";
  u.search = "";
  return u.toString();
}
