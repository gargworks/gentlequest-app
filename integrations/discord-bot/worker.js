// Eidetic — Discord Bot Worker
//
// Lets any Discord user run `/eidetic <question>` in any channel/guild/DM and
// have it answered by THEIR own eideticd daemon (exposed via Cloudflare
// tunnel). The Worker is a thin Ed25519-verifying relay; no engram content is
// ever stored here. The user's bridge URL + bearer token live in Workers KV,
// keyed by Discord user_id (see ADR-020 — no PII beyond Discord IDs).
//
// Routes:
//   GET  /healthz             — Worker liveness probe.
//   GET  /discord-setup       — HTML form: user pastes bridge URL + token +
//                               their Discord user_id (enable Developer Mode
//                               in Discord → right-click profile → Copy ID).
//   POST /discord-setup       — Form submit handler; writes config to KV.
//   POST /discord/interactions — Discord webhook receiver (Ed25519-verified).
//   GET  /discord/oauth       — OAuth install callback (optional; lets us
//                               pre-fill the setup form with the Discord
//                               user_id after the user authorises the app).
//
// Secrets (wrangler secret put):
//   DISCORD_PUBLIC_KEY        — Ed25519 public key (hex). Found in
//                               Discord Developer Portal → General Information.
//   DISCORD_APPLICATION_ID    — Discord application ID (snowflake).
//   DISCORD_BOT_TOKEN         — Bot token (only needed by register-commands.js
//                               and the OAuth callback; the interactions
//                               handler itself does not use it).
//   DISCORD_CLIENT_SECRET     — OAuth client secret (only used by
//                               /discord/oauth if you wire that flow).
//
// KV bindings:
//   EIDETIC_DISCORD_KV        — namespace storing user:<discord_user_id>
//                             values: JSON {bridge_url, token, configured_at}
//
// Trust boundary (per ADR-020, mirroring slack-app):
//   - Bridge URL + bearer token ARE customer-provided sensitive data.
//   - Stored in Workers KV (encryption-at-rest = Cloudflare-managed key).
//   - Only Discord user_id is retained as key. Guild_id is captured at
//     ask-time for telemetry only and never persisted alongside the token.
//   - Token is read only on the synchronous /discord/interactions path and
//     forwarded to the user's own bridge URL over HTTPS. Never logged.
//
// ---------------------------------------------------------------------------
// Ed25519 verification approach
// ---------------------------------------------------------------------------
// Discord signs every interaction with Ed25519 over `timestamp || raw body`,
// keyed by the application's public key. They REQUIRE the Worker to return
// HTTP 401 on any invalid signature — during interactions-endpoint setup
// Discord probes with deliberately bad signatures and disables the endpoint
// if you return 200.
//
// Cloudflare Workers' Web Crypto added Ed25519 support via two algorithm
// identifiers:
//   1. "Ed25519"        — the W3C Secure Curves standard name (newer).
//   2. "NODE-ED25519"   — a Cloudflare/Node-compatible legacy alias.
//
// We try the standard identifier first; if it throws (older Workers
// compatibility date), we transparently fall back to NODE-ED25519. Both
// paths use the same raw 32-byte public key and 64-byte signature, so the
// fallback is purely an `importKey` algorithm-name swap.
//
// We deliberately avoid bundling tweetnacl: keeping the Worker pure ES with
// no node_modules makes wrangler deploys and the scaffold story simple.
// Workers runtimes that don't speak either Ed25519 identifier will fail
// closed (verifySignature returns false → 401), which is the correct safe
// default for a public webhook.

const DISCORD_INTERACTION_TYPE = {
  PING: 1,
  APPLICATION_COMMAND: 2,
};

const DISCORD_INTERACTION_CALLBACK_TYPE = {
  PONG: 1,
  CHANNEL_MESSAGE_WITH_SOURCE: 4,
};

const DISCORD_MESSAGE_FLAGS = {
  EPHEMERAL: 1 << 6, // 64
};

const BRIDGE_FETCH_TIMEOUT_MS = 12_000;
const TOP_ENGRAMS = 3;
const ENGRAM_SNIPPET_CHARS = 240;
const COMMAND_NAME = "eidetic";
const SETUP_URL_PUBLIC = "https://eidetic.works/discord-setup";

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === "/healthz") {
      return json({ ok: true, service: "eidetic-discord" });
    }

    if (url.pathname === "/discord-setup") {
      if (request.method === "GET")  return renderSetupPage(url);
      if (request.method === "POST") return handleSetupSubmit(request, env);
      return new Response("method not allowed", { status: 405 });
    }

    if (url.pathname === "/discord/interactions") {
      if (request.method !== "POST") {
        return new Response("method not allowed", { status: 405 });
      }
      return handleInteraction(request, env, ctx);
    }

    if (url.pathname === "/discord/oauth") {
      if (request.method !== "GET") {
        return new Response("method not allowed", { status: 405 });
      }
      return handleOauth(request, env);
    }

    return new Response("not found", { status: 404 });
  },
};

// ---------------------------------------------------------------------------
// /discord/interactions — Ed25519-verified webhook
// ---------------------------------------------------------------------------

async function handleInteraction(request, env, ctx) {
  // Discord signs the raw bytes of `timestamp || body`, so we must read the
  // body as text BEFORE parsing JSON to make sure the bytes match.
  const rawBody  = await request.text();
  const sig      = request.headers.get("x-signature-ed25519") || "";
  const ts       = request.headers.get("x-signature-timestamp") || "";

  // Discord REQUIRES 401 on any verification failure. They probe the
  // endpoint with bad signatures during setup and disable it if it returns
  // anything else (200 included). See note in the Ed25519 block above.
  const verified = await verifyDiscordSignature({
    publicKeyHex: env.DISCORD_PUBLIC_KEY,
    signatureHex: sig,
    timestamp: ts,
    rawBody,
  });
  if (!verified) {
    return new Response("invalid request signature", { status: 401 });
  }

  let body;
  try {
    body = JSON.parse(rawBody);
  } catch {
    return new Response("invalid JSON", { status: 400 });
  }

  const type = body.type;
  if (type !== DISCORD_INTERACTION_TYPE.PING &&
      type !== DISCORD_INTERACTION_TYPE.APPLICATION_COMMAND) {
    // Anything other than PING or APPLICATION_COMMAND is out of scope for
    // this scaffold (MESSAGE_COMPONENT, MODAL_SUBMIT, autocomplete, etc.).
    // Return 400 so Discord knows we don't speak that interaction.
    return new Response("unsupported interaction type", { status: 400 });
  }

  if (type === DISCORD_INTERACTION_TYPE.PING) {
    // Discord's initial reachability probe.
    return json({ type: DISCORD_INTERACTION_CALLBACK_TYPE.PONG });
  }

  // APPLICATION_COMMAND
  const cmdName = body.data?.name || "";
  if (cmdName !== COMMAND_NAME) {
    return ephemeralReply(`Unknown command: \`${escapeMd(cmdName)}\``);
  }

  // /eidetic <question>
  const opts = Array.isArray(body.data?.options) ? body.data.options : [];
  const questionOpt = opts.find((o) => o?.name === "question");
  const question = String(questionOpt?.value || "").trim();

  // Discord delivers the user object in `body.member.user` when the command
  // is invoked in a guild, and in `body.user` for DM invocations.
  const userId  = body.member?.user?.id || body.user?.id || "";
  const guildId = body.guild_id || "";

  if (!userId) {
    return ephemeralReply("Could not determine your Discord user ID.");
  }
  if (!question) {
    return ephemeralReply("Usage: `/eidetic question:<your question>`");
  }

  const config = await loadUserConfig(env, userId);
  if (!config) {
    return ephemeralReply(
      `Configure your bridge URL at ${SETUP_URL_PUBLIC} ` +
      `(one-time; uses your Discord user ID: \`${userId}\`).`
    );
  }

  // Synchronous round-trip: unlike Slack, Discord's "type 4 with embeds"
  // path is the simplest scaffold. If the bridge ever exceeds ~2.5s
  // wall-clock, swap to a deferred response (type 5) + follow-up webhook.
  // Documented in README §Deferred-responses.
  try {
    const data = await askBridge(config.bridge_url, config.token, question);
    return json({
      type: DISCORD_INTERACTION_CALLBACK_TYPE.CHANNEL_MESSAGE_WITH_SOURCE,
      data: {
        flags: DISCORD_MESSAGE_FLAGS.EPHEMERAL,
        embeds: renderAnswerEmbeds(question, data),
      },
    });
  } catch (err) {
    // Surface failures back to the user (ephemerally) so they can act on
    // them. We intentionally don't leak the bridge URL.
    return ephemeralReply(
      `Bridge call failed: ${truncate(String(err.message || err), 200)}`
    );
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

// ---------------------------------------------------------------------------
// Discord embed rendering
// ---------------------------------------------------------------------------

function renderAnswerEmbeds(question, data) {
  const answer = data.answer || data.instructions || data.response || "";
  const items  = data.results || data.engrams || data.hits || [];
  const top    = Array.isArray(items) ? items.slice(0, TOP_ENGRAMS) : [];

  const embed = {
    title: truncate(question, 240),
    color: 0x1264a3, // matches Slack accent — easy on-brand swap later.
    description: truncate(answer || "_No matching engrams._", 3800),
    fields: [],
    footer: { text: "Eidetic · /eidetic — only you can see this reply" },
  };

  for (const r of top) {
    const surface = String(r.surface || r.meta?.surface || "—");
    const ts      = String(r.ts || r.timestamp || "");
    const snippet = truncate(String(r.payload || r.text || ""), ENGRAM_SNIPPET_CHARS);
    embed.fields.push({
      name: truncate(`${surface} · ${ts}`, 240),
      value: truncate(snippet || "_(empty)_", 1000),
      inline: false,
    });
  }

  return [embed];
}

// ---------------------------------------------------------------------------
// Ed25519 verification — Web Crypto, with NODE-ED25519 fallback
// ---------------------------------------------------------------------------

async function verifyDiscordSignature({ publicKeyHex, signatureHex, timestamp, rawBody }) {
  if (!publicKeyHex || !signatureHex || !timestamp) return false;

  const pubBytes = hexToBytes(publicKeyHex);
  const sigBytes = hexToBytes(signatureHex);
  if (!pubBytes || pubBytes.length !== 32) return false;
  if (!sigBytes || sigBytes.length !== 64) return false;

  // Per Discord docs: message = utf8(timestamp) || raw_body_bytes.
  const tsBytes   = new TextEncoder().encode(timestamp);
  const bodyBytes = new TextEncoder().encode(rawBody);
  const message   = new Uint8Array(tsBytes.length + bodyBytes.length);
  message.set(tsBytes, 0);
  message.set(bodyBytes, tsBytes.length);

  // Try the modern W3C Secure Curves identifier first; fall back to the
  // older NODE-ED25519 alias for Workers on pre-Ed25519 compatibility dates.
  try {
    const key = await crypto.subtle.importKey(
      "raw",
      pubBytes,
      { name: "Ed25519" },
      false,
      ["verify"],
    );
    return await crypto.subtle.verify("Ed25519", key, sigBytes, message);
  } catch (_) {
    try {
      const key = await crypto.subtle.importKey(
        "raw",
        pubBytes,
        { name: "NODE-ED25519", namedCurve: "NODE-ED25519" },
        false,
        ["verify"],
      );
      return await crypto.subtle.verify("NODE-ED25519", key, sigBytes, message);
    } catch (_e2) {
      // Both paths failed — fail closed. Don't bundle a JS Ed25519
      // implementation here; a Worker with no Ed25519 support shouldn't
      // accept Discord interactions at all.
      return false;
    }
  }
}

function hexToBytes(hex) {
  if (typeof hex !== "string" || hex.length === 0 || hex.length % 2 !== 0) {
    return null;
  }
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) {
    const byte = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
    if (Number.isNaN(byte)) return null;
    out[i] = byte;
  }
  return out;
}

// ---------------------------------------------------------------------------
// /discord-setup — HTML form for the user to paste bridge URL + token
// ---------------------------------------------------------------------------

function renderSetupPage(url) {
  const prefilledUser = url.searchParams.get("user_id") || "";
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Eidetic for Discord — Setup</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body { font: 16px/1.5 system-ui, sans-serif; max-width: 560px; margin: 4rem auto; padding: 0 1rem; color: #222; }
  h1 { font-size: 1.4rem; margin: 0 0 .5rem; }
  p  { color: #555; }
  label { display: block; margin: 1rem 0 .25rem; font-weight: 600; }
  input[type=text], input[type=password] { width: 100%; padding: .55rem .65rem; border: 1px solid #ccc; border-radius: 6px; font: inherit; }
  button { margin-top: 1.25rem; padding: .65rem 1.1rem; border: 0; border-radius: 6px; background: #5865f2; color: #fff; font: inherit; cursor: pointer; }
  small { color: #777; }
  code { background: #f1f1f4; padding: .1rem .3rem; border-radius: 4px; }
</style>
</head>
<body>
  <h1>Connect your eidetic-daemon to Discord</h1>
  <p>Paste the Cloudflare-tunnel URL of your local <code>eideticd -bridge</code>,
     the bearer token from <code>~/.eidetic/bridge-token</code>, and your
     Discord <strong>user ID</strong>. All three stay in Cloudflare Workers KV;
     nobody else (including other people in your servers) can read them.</p>
  <p><small>To find your Discord user ID: open Discord → User Settings →
     Advanced → enable <em>Developer Mode</em>. Then right-click your own
     profile in any channel and choose <em>Copy User ID</em>.</small></p>
  <form method="POST" action="/discord-setup">
    <label for="discord_user_id">Discord user ID</label>
    <input id="discord_user_id" name="discord_user_id" type="text"
           value="${escapeHtml(prefilledUser)}"
           placeholder="e.g. 123456789012345678" required pattern="[0-9]{15,21}">
    <small>15–21 digit snowflake ID. Must match the user invoking <code>/eidetic</code>.</small>
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
  const userId    = (form.discord_user_id || "").trim();
  const bridgeUrl = (form.bridge_url      || "").trim();
  const token     = (form.token           || "").trim();

  if (!/^\d{15,21}$/.test(userId)) {
    return new Response(
      "Discord user ID must be a 15–21 digit snowflake. Enable Developer Mode and Copy User ID from your own profile.",
      { status: 400 },
    );
  }
  if (!isAllowedBridgeUrl(bridgeUrl)) {
    return new Response(
      "Bridge URL must be HTTPS on *.trycloudflare.com or *.cloudflare.com. " +
      "Wider hostnames are intentionally rejected so a misconfigured install " +
      "can't be redirected at an arbitrary internet endpoint.",
      { status: 400 },
    );
  }
  if (!token || token.length < 16) {
    return new Response(
      "Bearer token looks too short — paste the full contents of ~/.eidetic/bridge-token.",
      { status: 400 },
    );
  }

  await env.EIDETIC_DISCORD_KV.put(
    kvKey(userId),
    JSON.stringify({
      bridge_url: bridgeUrl,
      token,
      configured_at: new Date().toISOString(),
    }),
  );

  const html = `<!doctype html><meta charset="utf-8">
<title>Saved</title>
<body style="font: 16px/1.5 system-ui, sans-serif; max-width: 560px; margin: 4rem auto; padding: 0 1rem;">
<h1>Saved.</h1>
<p>Run <code>/eidetic question:&lt;your question&gt;</code> in any Discord channel.
   The Worker will route through your bridge URL and reply only to you (ephemerally).</p>
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
// /discord/oauth — optional install callback
// ---------------------------------------------------------------------------
//
// Wired here as a scaffold: when the user clicks "Add to Discord" with the
// `identify` scope, Discord redirects them back with ?code=…. We exchange
// the code for the user's identity (purely so we can pre-fill their
// snowflake on the setup form) and redirect to /discord-setup?user_id=…
// The bot install itself uses Discord's separate "Authorize" flow with the
// `bot` scope — that doesn't produce a code on our redirect.

async function handleOauth(request, env) {
  const url  = new URL(request.url);
  const code = url.searchParams.get("code");
  if (!code) {
    return new Response("Missing ?code= from Discord OAuth redirect.", { status: 400 });
  }
  if (!env.DISCORD_APPLICATION_ID || !env.DISCORD_CLIENT_SECRET) {
    return new Response("OAuth client not configured on this Worker.", { status: 500 });
  }

  const redirectUri = `${url.origin}/discord/oauth`;
  const params = new URLSearchParams({
    client_id:     env.DISCORD_APPLICATION_ID,
    client_secret: env.DISCORD_CLIENT_SECRET,
    grant_type:    "authorization_code",
    code,
    redirect_uri:  redirectUri,
  });
  const tokRes = await fetch("https://discord.com/api/v10/oauth2/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: params.toString(),
  });
  const tok = await tokRes.json().catch(() => ({}));
  if (!tokRes.ok || !tok.access_token) {
    return new Response(`Discord OAuth failed: ${tok.error || "unknown"}`, { status: 400 });
  }

  // Look up the user's id (requires the `identify` scope).
  const meRes = await fetch("https://discord.com/api/v10/users/@me", {
    headers: { Authorization: `Bearer ${tok.access_token}` },
  });
  const me = await meRes.json().catch(() => ({}));
  const userId = me.id || "";

  // Redirect to setup form pre-filled with the user's snowflake.
  const redirect = new URL(url);
  redirect.pathname = "/discord-setup";
  redirect.search   = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
  return Response.redirect(redirect.toString(), 302);
}

// ---------------------------------------------------------------------------
// KV helpers
// ---------------------------------------------------------------------------

function kvKey(userId) {
  return `user:${userId}`;
}

async function loadUserConfig(env, userId) {
  const raw = await env.EIDETIC_DISCORD_KV.get(kvKey(userId));
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

function ephemeralReply(text) {
  return json({
    type: DISCORD_INTERACTION_CALLBACK_TYPE.CHANNEL_MESSAGE_WITH_SOURCE,
    data: {
      flags: DISCORD_MESSAGE_FLAGS.EPHEMERAL,
      content: truncate(text, 1900),
    },
  });
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

// Minimal Discord markdown escape — leave content safe-ish for embed fields.
function escapeMd(s) {
  return String(s)
    .replace(/`/g, "ˋ")
    .replace(/\\/g, "\\\\");
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
