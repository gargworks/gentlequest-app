# Eidetic for Notion

Bridges a Notion database into your local `eideticd` daemon. Each Notion page
becomes one engram (`surface=notion`) so the contents are searchable alongside
everything else the daemon indexes.

```
Notion DB row  ──webhook OR poll──▶  Cloudflare Worker (or local script)
                                            │
                                            │ render page → plain text
                                            ▼
                              POST /engrams to user's eideticd
                                  (via Cloudflare tunnel)
                                            │
                                            ▼
                                   indexed, searchable
```

The Notion integration is intentionally **single-tenant per deploy**: an
internal Notion integration token is workspace-scoped, and one operator
typically runs one DB → daemon pipeline. This is the opposite of the Slack /
Discord / Telegram integrations, which are multi-tenant on a single Worker.

## Files

| File                       | Purpose                                                          |
|----------------------------|------------------------------------------------------------------|
| `worker.js`                | Pure ES-module Worker. No deps. Webhook + polling + setup.       |
| `wrangler.toml`            | Worker config + KV binding + (commented) custom domain.          |
| `scripts/notion-poll.sh`   | Self-hosted polling alternative (cron-friendly, no Worker).      |
| `README.md`                | You are here.                                                    |

## Routes the Worker exposes

| Method | Path                | Purpose                                                  |
|--------|---------------------|----------------------------------------------------------|
| GET    | `/healthz`          | Liveness probe.                                          |
| GET    | `/notion/setup`     | HTML form: paste Notion token + DB ID + bridge URL.      |
| POST   | `/notion/setup`     | Save form values into KV (gated by `ADMIN_SECRET`).      |
| POST   | `/notion/webhook`   | Notion webhook receiver. HMAC-verified, async sync.      |
| GET    | `/notion/poll`      | Cron-friendly full-DB checkpoint sync. Gated by admin.   |

## Webhooks vs polling — which to use?

Notion supports webhooks but **the API is in beta**. The trigger surface is
narrow (page added, page property changed, etc.), they require a separately-
managed signing secret, and production approval is gated on Notion's review.

**Polling is the primary path.** It uses GA APIs only and works for every
plan. The Worker keeps a per-DB checkpoint (`last_edited_time`) in KV so each
poll only fetches pages that changed since the last successful tick:

```
*/15 * * * * curl -H "X-Admin-Secret: $ADMIN_SECRET" \
    https://notion.eidetic.works/notion/poll
```

Webhooks are still wired up — they're a perf optimisation that drops the
median sync latency from ~7.5 min (cron midpoint) to ~5 sec. Flip from
polling to webhooks (or run both) as soon as the beta meets your needs;
the same `db_id → user` index serves both paths.

## One-time setup (you, the operator)

### 1. Create the Notion internal integration

1. Go to <https://www.notion.so/my-integrations> → **New integration**.
2. Pick the target workspace; set type to **Internal**.
3. Capabilities: tick **Read content**. That's enough for read-only sync;
   add **Update content** later if/when you implement the reverse flow.
4. Save. Copy the **Internal Integration Secret** (starts with `secret_` or
   `ntn_`). This is the `NOTION_TOKEN` you'll paste in the setup form.

### 2. Share the database with the integration

Notion integrations are sandboxed by default — they can't read a DB until
the DB owner explicitly shares it.

1. Open your target database in Notion.
2. Click the **·· · menu** at the top right → **Add connections**.
3. Pick the integration you created in step 1. Notion will confirm.
4. Note the **database ID** — it's the 32-character hex blob in the URL:
   `notion.so/<workspace>/<32hex>?v=...` (dashes are optional; the Worker
   strips them).

### 3. Pick a deployment path

#### Path A — managed Worker (recommended for "set and forget")

```bash
cd integrations/notion-sync

# KV
wrangler kv:namespace create EIDETIC_NOTION_KV
wrangler kv:namespace create EIDETIC_NOTION_KV --preview
# Paste both IDs into wrangler.toml.

# Required secret — gates /notion/setup (POST) and /notion/poll
openssl rand -hex 32 | wrangler secret put ADMIN_SECRET

# Optional — only if you wire up the Notion webhook beta
wrangler secret put NOTION_WEBHOOK_SECRET

wrangler deploy
```

Confirm `GET /healthz` returns `{"ok":true,"service":"eidetic-notion"}`.

Then in a browser, visit `/notion/setup` and submit:
- `admin_secret` — the value you set above
- `notion_token` — from step 1
- `db_id` — from step 2
- `bridge_url` — your `eideticd -bridge` Cloudflare tunnel URL
- `bridge_token` — contents of `~/.eidetic/bridge-token`

Save. Trigger the first sync:

```bash
curl -H "X-Admin-Secret: $ADMIN_SECRET" \
     https://<worker-host>/notion/poll
```

That call returns `{"ok":true,"scanned":N,"posted":N,...}`. Add a cron entry
to hit `/notion/poll` every 15 min, or wire `/notion/webhook` into Notion's
webhook beta when you're ready.

##### op-assistant deploy

If you have the op-assistant lane wired up, the deploy is one nudge:

```
[OPS-HANDOFF] deploy eidetic-notion worker
repo: integrations/notion-sync
secrets: ADMIN_SECRET
custom_domain: notion.eidetic.works
```

#### Path B — self-hosted polling script (no Worker)

If you don't want Cloudflare in the loop, run `scripts/notion-poll.sh` from
the same machine as `eideticd`:

```bash
chmod +x scripts/notion-poll.sh

# Smoke test (dry-run prints engram JSON instead of POSTing)
scripts/notion-poll.sh \
    --token "$NOTION_TOKEN" \
    --db    "$NOTION_DB_ID" \
    --bridge "http://127.0.0.1:8787" \
    --dry-run --verbose

# Add to crontab
crontab -e
*/15 * * * * /path/to/scripts/notion-poll.sh \
    --token "$NOTION_TOKEN" \
    --db    "$NOTION_DB_ID"
```

The script reuses the same checkpoint logic as the Worker (`last_edited_time`
in `~/.eidetic/notion/<db_id>.last_edited`). Bridge URL defaults to
`http://127.0.0.1:8787`; bridge token defaults to `~/.eidetic/bridge-token`.
Requires `bash 4+`, `curl`, `jq`.

## Engram payload format

Each Notion page becomes one engram:

```json
{
  "surface": "notion",
  "title":   "<page title>",
  "payload": "<page body rendered as plain text, one block per line>",
  "meta": {
    "notion_page_id":     "<32-char hex>",
    "notion_db_id":       "<32-char hex>",
    "notion_url":         "https://www.notion.so/...",
    "last_edited_time":   "2026-05-19T12:34:56.789Z",
    "truncated":          false
  }
}
```

The plain-text render walks all top-level blocks (paragraph, headings,
bullets, todos, code, quote, callout, etc.) and drops the block hierarchy.
Unsupported blocks (image, file, video, child_page) are skipped silently
because they don't contribute to full-text search.

Bodies are capped at 32 000 characters per page. `meta.truncated=true` flags
that the payload was clipped — the original is always recoverable via
`meta.notion_url`.

## Bridge URL allowlist

Same posture as the Slack / Discord / Telegram integrations: only
`https://*.trycloudflare.com` and `https://*.cloudflare.com` are accepted by
the Worker setup form. Wider hostnames are rejected so a misconfigured
install can't be redirected at an arbitrary internet endpoint. To widen the
allowlist, edit `isAllowedBridgeUrl()` in `worker.js`.

The self-hosted `scripts/notion-poll.sh` does not enforce this allowlist —
it's expected to point at `http://127.0.0.1:8787` (loopback) or a local
network address.

## Privacy

Per ADR-020, mirroring the other integrations:

- **Notion page content is never stored on Cloudflare.** The Worker reads it
  in-memory during a poll/webhook turn, POSTs it to your daemon, and drops it.
- **The only thing in KV** is the per-DB checkpoint timestamp (an ISO 8601
  string) and the per-user config blob (Notion token + bridge URL + tokens).
  No page IDs, titles, or content.
- **The DB ID** appears in Worker request logs (it's part of the route path
  in some paginated calls). Treat the DB ID as a routing key, not a secret.
- **The Notion integration token** is workspace-scoped: it can read every DB
  the workspace owner has shared with the integration. Keep the integration
  shared with only the DBs you want indexed.
- **The bridge bearer token** is forwarded only to the URL the operator
  configured. Never logged.

## Reverse flow (eidetic → Notion) — future work

This scaffold only handles Notion → eidetic. Pushing engrams back to Notion
as DB rows (e.g. to surface eidetic search results in a Notion view) is out
of scope for v1 and would need:

1. A second integration capability tick (**Update content**) on the Notion
   side.
2. A schema-mapping config (which engram fields populate which DB
   properties) — Notion DBs are strongly-typed, engrams are not.
3. A separate idempotency key store so we don't double-insert rows when the
   daemon replays.

Open an issue under `nucleus-bug` if you need this — we'll scope it as a
follow-on with its own ADR.

## Troubleshooting

| Symptom                                            | Cause / fix                                                                                  |
|----------------------------------------------------|----------------------------------------------------------------------------------------------|
| `Notion DB lookup failed (HTTP 404)` on setup      | DB not shared with the integration. Open the DB → ··· → Add connections.                     |
| `Notion DB lookup failed (HTTP 401)` on setup      | Token is wrong, revoked, or copied with a trailing newline.                                  |
| `/notion/poll` returns `{"ok":true,"scanned":0}`   | Either no pages changed since checkpoint, or the integration only sees an empty subset.      |
| `/notion/poll` returns `403 forbidden`             | `X-Admin-Secret` header missing or wrong.                                                    |
| Webhook returns 401                                | `NOTION_WEBHOOK_SECRET` doesn't match what you configured in Notion's webhook UI.            |
| Engram count seems low after a re-sync             | Checkpoint advanced past pages that errored. Delete the checkpoint key in KV to force full.  |
| Cron runs but nothing arrives in the daemon        | Test `scripts/notion-poll.sh --dry-run --verbose` first — confirms Notion side is healthy.   |
