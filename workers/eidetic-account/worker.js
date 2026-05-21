// Eidetic Pro customer self-serve account dashboard.
//
// Customers paste their `api_key` (issued by scripts/gen_pro_key.sh) and see:
//   - account metadata (email, device_id, member-since)
//   - the list of engram backups stored in R2 for their device
//   - per-backup download links (api_key required, hashed + verified server-side)
//
// The api_key is NEVER stored or logged in plaintext. Every request hashes the
// pasted key, takes the first 6 hex chars of the SHA-256, and only that prefix
// is logged for diagnostics. Diff-of-key-hashes uses crypto.subtle.timingSafeEqual
// when available, falling back to a constant-time JS loop.
//
// Routes:
//   GET  /                  → inline HTML sign-in page
//   POST /lookup            → {api_key} → {email, device_id, added, backups[]}
//   GET  /download          → ?key=engrams/<device_id>/<file>&api_key=<key>
//                             → 200 stream the R2 object (Content-Disposition: attachment)
//
// Bindings (see wrangler.toml):
//   EIDETIC_KEYS_KV   — KV namespace (id 34d23af4669a40bd907f5c58c56802e8)
//                       Keys are SHA-256(api_key) hex. Values are JSON
//                       {email, device_id, added (ISO)}.
//   EIDETIC_ENGRAMS_R2 — R2 bucket (eidetic-engrams) holding
//                        engrams/<device_id>/engrams-<unix_ts>.db
//
// Errors:
//   400 invalid request shape
//   401 hash didn't match any stored key
//   403 key owns a different device_id than the requested object
//   404 unknown route
//   500 R2/KV transport failure

const BACKUP_LIST_CAP = 50;
const KEY_OBJECT_PREFIX = "engrams/";
const KEY_OBJECT_RE = /^engrams\/[A-Za-z0-9_-]{1,128}\/engrams-\d+\.db$/;

async function sha256Hex(input) {
  const data = new TextEncoder().encode(input || "");
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

// Constant-time string compare. Both inputs are hex strings of the same length
// in our usage (SHA-256 → 64 hex chars), but we still guard against mismatch.
function timingSafeEqualHex(a, b) {
  if (typeof a !== "string" || typeof b !== "string") return false;
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function logHashPrefix(hash, tag) {
  // Only the first 6 hex chars (24 bits) leak. Enough to correlate logs for one
  // user across a session without re-identifying them or letting an attacker
  // brute-force the key from logs.
  const prefix = hash.slice(0, 6);
  console.log(`[${tag}] hash_prefix=${prefix}`);
}

// Look up the KV record for a given api_key. Returns null on miss.
// The returned object always includes `hashHex` so callers can pass it to
// subsequent verification (e.g. cross-checking device_id on /download).
async function lookupKey(env, apiKey) {
  if (typeof apiKey !== "string" || apiKey.length < 16 || apiKey.length > 200) {
    return null;
  }
  const hashHex = await sha256Hex(apiKey);
  const raw = await env.EIDETIC_KEYS_KV.get(hashHex);
  if (!raw) {
    logHashPrefix(hashHex, "lookup_miss");
    return null;
  }
  let rec;
  try {
    rec = JSON.parse(raw);
  } catch {
    logHashPrefix(hashHex, "lookup_bad_json");
    return null;
  }
  logHashPrefix(hashHex, "lookup_hit");
  return { hashHex, rec };
}

async function listBackups(env, deviceId) {
  // R2 list — `engrams/<device_id>/` prefix. Cap to BACKUP_LIST_CAP newest.
  const prefix = `${KEY_OBJECT_PREFIX}${deviceId}/`;
  const listed = await env.EIDETIC_ENGRAMS_R2.list({
    prefix,
    limit: 1000, // wide net; we sort + cap below
  });
  const rows = (listed?.objects || []).map((o) => ({
    key: o.key,
    size: o.size,
    uploaded_at: o.uploaded ? o.uploaded.toISOString() : null,
  }));
  rows.sort((a, b) => (b.uploaded_at || "").localeCompare(a.uploaded_at || ""));
  return rows.slice(0, BACKUP_LIST_CAP);
}

async function handleLookup(request, env) {
  if (request.method !== "POST") {
    return json({ error: "method not allowed" }, 405);
  }
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid json body" }, 400);
  }
  const apiKey = (body?.api_key || "").toString();
  if (!apiKey) {
    return json({ error: "missing api_key" }, 400);
  }

  const found = await lookupKey(env, apiKey);
  if (!found) {
    return json({ error: "invalid api_key" }, 401);
  }

  const { rec } = found;
  let backups = [];
  try {
    backups = await listBackups(env, rec.device_id);
  } catch (e) {
    console.log(`[lookup_r2_err] ${e && e.message}`);
    return json({ error: "backup lookup failed" }, 500);
  }

  return json({
    email: rec.email || null,
    device_id: rec.device_id || null,
    added: rec.added || null,
    backups,
  });
}

async function handleDownload(request, env, url) {
  const objectKey = url.searchParams.get("key") || "";
  const apiKey = url.searchParams.get("api_key") || "";

  if (!objectKey || !apiKey) {
    return new Response("missing key or api_key", { status: 400 });
  }
  if (!KEY_OBJECT_RE.test(objectKey)) {
    return new Response("invalid object key", { status: 400 });
  }

  const found = await lookupKey(env, apiKey);
  if (!found) {
    return new Response("invalid api_key", { status: 401 });
  }

  // Extract the device_id from the requested key and constant-time-compare
  // against the device_id bound to this api_key.
  const parts = objectKey.split("/");
  const requestedDevice = parts[1] || "";
  const ownedDevice = (found.rec.device_id || "").toString();
  if (!timingSafeEqualHex(requestedDevice, ownedDevice)) {
    logHashPrefix(found.hashHex, "download_device_mismatch");
    return new Response("forbidden", { status: 403 });
  }

  const obj = await env.EIDETIC_ENGRAMS_R2.get(objectKey);
  if (!obj) {
    return new Response("not found", { status: 404 });
  }

  const filename = parts[parts.length - 1] || "engrams.db";
  const headers = new Headers();
  headers.set("Content-Type", "application/octet-stream");
  headers.set(
    "Content-Disposition",
    `attachment; filename="${filename.replace(/[^A-Za-z0-9._-]/g, "_")}"`
  );
  if (obj.size != null) headers.set("Content-Length", String(obj.size));
  if (obj.httpEtag) headers.set("ETag", obj.httpEtag);
  return new Response(obj.body, { status: 200, headers });
}

const PAGE_HTML = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Your Eidetic Pro Account</title>
<style>
  :root {
    --bg: #0a0a0a;
    --bg-card: #121214;
    --bg-input: #050505;
    --fg: #e5e7eb;
    --fg-dim: #9ca3af;
    --teal: #5eead4;
    --teal-dim: #2dd4bf;
    --border: #1f1f23;
    --danger: #f87171;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 32px 16px 80px;
    background: var(--bg);
    color: var(--fg);
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 14px;
    line-height: 1.55;
    min-height: 100vh;
  }
  .wrap { max-width: 760px; margin: 0 auto; }
  h1 {
    color: var(--teal);
    font-size: 22px;
    margin: 0 0 4px;
    letter-spacing: -0.01em;
  }
  .sub { color: var(--fg-dim); margin: 0 0 28px; font-size: 13px; }
  .card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 20px;
    margin-bottom: 16px;
  }
  label {
    display: block;
    color: var(--fg-dim);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
  }
  textarea {
    width: 100%;
    min-height: 88px;
    background: var(--bg-input);
    color: var(--fg);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 10px 12px;
    font: inherit;
    resize: vertical;
  }
  textarea:focus { outline: none; border-color: var(--teal); }
  button {
    margin-top: 12px;
    background: var(--teal);
    color: #042f2e;
    border: 0;
    padding: 10px 18px;
    border-radius: 4px;
    font: inherit;
    font-weight: 600;
    cursor: pointer;
  }
  button:hover { background: var(--teal-dim); }
  button:disabled { opacity: 0.6; cursor: wait; }
  .meta-grid {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 8px 16px;
  }
  .meta-grid .k { color: var(--fg-dim); }
  .meta-grid .v { word-break: break-all; }
  table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 8px;
  }
  th, td {
    text-align: left;
    padding: 8px 6px;
    border-bottom: 1px solid var(--border);
    font-size: 13px;
  }
  th { color: var(--fg-dim); font-weight: 500; }
  td.size, th.size { text-align: right; white-space: nowrap; }
  td.dl, th.dl { text-align: right; }
  a.dl-btn {
    color: var(--teal);
    text-decoration: none;
    border: 1px solid var(--teal);
    padding: 4px 10px;
    border-radius: 3px;
    font-size: 12px;
  }
  a.dl-btn:hover { background: rgba(94, 234, 212, 0.08); }
  .err {
    color: var(--danger);
    border-left: 2px solid var(--danger);
    padding-left: 10px;
  }
  .empty { color: var(--fg-dim); font-style: italic; padding: 8px 0; }
  .privacy {
    margin-top: 24px;
    color: var(--fg-dim);
    font-size: 12px;
    border-top: 1px solid var(--border);
    padding-top: 16px;
  }
  .privacy strong { color: var(--fg); }
</style>
</head>
<body>
<div class="wrap">
  <h1>Your Eidetic Pro Account</h1>
  <p class="sub">Paste the <code>api_key</code> from your <code>sync.json</code> to view your account and backups.</p>

  <div class="card">
    <form id="login-form">
      <label for="api_key">api_key</label>
      <textarea id="api_key" name="api_key" autocomplete="off" spellcheck="false" placeholder="paste the 43-character key here"></textarea>
      <button type="submit" id="submit-btn">Sign in</button>
    </form>
  </div>

  <div id="results"></div>

  <div class="privacy">
    <strong>Privacy.</strong> We never store your <code>api_key</code>. Each request hashes it server-side
    (SHA-256) and looks up the metadata by hash. Only the first 6 characters of that hash appear in our
    diagnostic logs &mdash; never the key itself.
  </div>
</div>

<script>
  const form = document.getElementById("login-form");
  const out  = document.getElementById("results");
  const btn  = document.getElementById("submit-btn");

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function humanSize(bytes) {
    if (bytes == null) return "?";
    const u = ["B", "KB", "MB", "GB", "TB"];
    let i = 0, n = Number(bytes);
    while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
    return n.toFixed(n >= 100 || i === 0 ? 0 : 1) + " " + u[i];
  }

  function humanDate(iso) {
    if (!iso) return "?";
    try {
      const d = new Date(iso);
      if (isNaN(d.getTime())) return iso;
      return d.toLocaleString(undefined, {
        year: "numeric", month: "short", day: "2-digit",
        hour: "2-digit", minute: "2-digit",
      });
    } catch { return iso; }
  }

  function render(data, apiKey) {
    const rows = (data.backups || []).map((b) => {
      const dlUrl = "/download?key=" + encodeURIComponent(b.key) +
                    "&api_key=" + encodeURIComponent(apiKey);
      return '<tr>' +
        '<td>' + esc(humanDate(b.uploaded_at)) + '</td>' +
        '<td class="size">' + esc(humanSize(b.size)) + '</td>' +
        '<td class="dl"><a class="dl-btn" href="' + esc(dlUrl) + '">download</a></td>' +
      '</tr>';
    }).join("");

    const tableHtml = rows
      ? '<table><thead><tr><th>backup</th><th class="size">size</th><th class="dl"></th></tr></thead><tbody>' + rows + '</tbody></table>'
      : '<div class="empty">No backups uploaded yet. Run <code>eidetic sync</code> on your device.</div>';

    out.innerHTML =
      '<div class="card">' +
        '<div class="meta-grid">' +
          '<div class="k">email</div><div class="v">' + esc(data.email || "?") + '</div>' +
          '<div class="k">device_id</div><div class="v">' + esc(data.device_id || "?") + '</div>' +
          '<div class="k">member since</div><div class="v">' + esc(humanDate(data.added)) + '</div>' +
          '<div class="k">backups</div><div class="v">' + (data.backups ? data.backups.length : 0) + '</div>' +
        '</div>' +
      '</div>' +
      '<div class="card">' + tableHtml + '</div>';
  }

  function renderError(msg) {
    out.innerHTML = '<div class="card err">' + esc(msg) + '</div>';
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const apiKey = document.getElementById("api_key").value.trim();
    if (!apiKey) { renderError("Paste your api_key first."); return; }
    btn.disabled = true; btn.textContent = "Signing in...";
    try {
      const res = await fetch("/lookup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) { renderError(data.error || ("HTTP " + res.status)); return; }
      render(data, apiKey);
    } catch (err) {
      renderError("Network error: " + (err && err.message ? err.message : err));
    } finally {
      btn.disabled = false; btn.textContent = "Sign in";
    }
  });
</script>
</body>
</html>`;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const { pathname } = url;

    if (pathname === "/" || pathname === "") {
      if (request.method !== "GET") {
        return new Response("method not allowed", { status: 405 });
      }
      return new Response(PAGE_HTML, {
        status: 200,
        headers: {
          "Content-Type": "text/html; charset=utf-8",
          "Cache-Control": "public, max-age=300",
          "Referrer-Policy": "no-referrer",
        },
      });
    }

    if (pathname === "/lookup") {
      if (!env.EIDETIC_KEYS_KV || !env.EIDETIC_ENGRAMS_R2) {
        return json({ error: "bindings not configured" }, 503);
      }
      return handleLookup(request, env);
    }

    if (pathname === "/download") {
      if (request.method !== "GET") {
        return new Response("method not allowed", { status: 405 });
      }
      if (!env.EIDETIC_KEYS_KV || !env.EIDETIC_ENGRAMS_R2) {
        return new Response("bindings not configured", { status: 503 });
      }
      return handleDownload(request, env, url);
    }

    if (pathname === "/ping") {
      return new Response(null, { status: 204 });
    }

    return new Response("not found", { status: 404 });
  },
};
