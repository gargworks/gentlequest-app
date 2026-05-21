# eidetic-analytics

Privacy-safe conversion funnel Worker. Counts the funnel from landing → install → ping → purchase using Cloudflare Analytics Engine.

## Funnel events

| Event              | Where it fires                                                |
| ------------------ | ------------------------------------------------------------- |
| `landing_view`     | Landing page visit (pixel or `fetch` from `<script>`)         |
| `install_sh_fetch` | `install.sh` downloaded (origin Worker or 302 wrapper)        |
| `mcp_ping`         | `eidetic-mcp` `/ping` route — 204 telemetry-free hit          |
| `purchase`         | Gumroad webhook (fire from `gumroad-kit-sync` after success)  |
| `dashboard_open`   | Local dashboard opened (fire from the Tauri shell)            |

Optional dimensions: `surface` (`macos` / `linux` / `windows`), `tier` (`pro` / `annual` / `founder` / `team`).

## ADR-020 compliance

This Worker is the only piece of infrastructure allowed to write conversion data, and it does so under three hard guards:

1. **No PII keys accepted.** Any payload containing `email`, `ip`, `user_id`, or `device_id` is rejected with `400` — even if the value is empty.
2. **Unknown keys are silently dropped.** Only `event`, `surface`, `tier` are retained from the request; nothing else reaches Analytics Engine.
3. **IP and User-Agent are never read.** The Worker does not inspect `request.headers.get("cf-connecting-ip")` or `user-agent`, and never logs them. Analytics Engine receives only the three enum fields above.

Result: there is no per-install tracking ID and no way to join an analytics row back to a user.

## Routes

### `POST /event`
CORS-enabled. Body: `{event, surface?, tier?}`. Returns `204`.

```js
fetch("https://eidetic-analytics.<your-subdomain>.workers.dev/event", {
  method:  "POST",
  headers: { "Content-Type": "application/json" },
  body:    JSON.stringify({ event: "landing_view", surface: "macos" }),
});
```

### `GET /event?e=<event>&s=<surface>&t=<tier>`
Pixel-style tracking. Returns a 1×1 transparent GIF (always 200, even on validation failure — avoids leaking validation outcome to browsers).

```html
<img src="https://eidetic-analytics.<your-subdomain>.workers.dev/event?e=landing_view"
     width="1" height="1" alt="" />
```

### `GET /stats?days=7`
Admin-only. `Authorization: Bearer $ADMIN_SECRET`. Returns:

```json
{
  "days": 7,
  "landing_views": 1240,
  "install_fetches": 312,
  "pings": 188,
  "purchases": 9,
  "dashboard_opens": 142,
  "conv_rate": 0.0073
}
```

Returns `503 analytics not yet provisioned` if the `ANALYTICS` binding, `ANALYTICS_ACCOUNT_ID`, or `ANALYTICS_API_TOKEN` is missing. Returns `401` if the Bearer token does not match `ADMIN_SECRET`.

## Deploy

```bash
cd workers/eidetic-analytics

# Secrets
CLOUDFLARE_API_TOKEN=<workers-token> wrangler secret put ADMIN_SECRET
CLOUDFLARE_API_TOKEN=<workers-token> wrangler secret put ANALYTICS_ACCOUNT_ID
CLOUDFLARE_API_TOKEN=<workers-token> wrangler secret put ANALYTICS_API_TOKEN

# Ship
CLOUDFLARE_API_TOKEN=<workers-token> wrangler deploy
```

The `ANALYTICS` binding is declared in `wrangler.toml` under `[[analytics_engine_datasets]]` (dataset name `eidetic_funnel`) — Cloudflare provisions it on first deploy.

`ANALYTICS_API_TOKEN` needs the **Account → Account Analytics → Read** permission so the Worker can query its own dataset via the SQL API.

## Failure modes

- **No `ANALYTICS` binding** (pre-deploy / wrong env): the Worker logs a warning and returns `204` anyway. The caller does not break; the event is silently dropped.
- **No `ADMIN_SECRET`** set: `/stats` returns `401` for every request.
- **No `ANALYTICS_ACCOUNT_ID` / `ANALYTICS_API_TOKEN`**: `/stats` returns `503 analytics not yet provisioned`.

## Landing snippet

Drop into landing `<body>` (pixel — survives JS-disabled browsers):

```html
<img src="https://eidetic-analytics.<your-subdomain>.workers.dev/event?e=landing_view"
     width="1" height="1" alt="" style="position:absolute;left:-9999px" />
```

Or wire to button clicks (JS):

```html
<script>
  function track(event, extra) {
    fetch("https://eidetic-analytics.<your-subdomain>.workers.dev/event", {
      method:  "POST",
      mode:    "no-cors",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(Object.assign({ event }, extra || {})),
    }).catch(() => {});
  }
  track("landing_view");
  document.querySelectorAll("a.install-cta")
    .forEach(a => a.addEventListener("click", () => track("install_sh_fetch", { surface: "macos" })));
</script>
```
