# Eidetic for Slack

A Cloudflare Worker that turns `/eidetic <question>` in any Slack channel into
an ask against the user's **own** local `eideticd` daemon. The Worker is a
thin HMAC-verified relay; engram contents are never stored on Cloudflare.

```
Slack user  ──/eidetic …──▶  Slack  ──HMAC POST──▶  Cloudflare Worker
                                                          │
                                                          ▼
                                                   Workers KV
                                                   (bridge URL + token)
                                                          │
                                                          ▼
                                          user's eideticd (via Cloudflare tunnel)
                                                          │
                                                          ▼
                                          Worker formats Block Kit reply
                                                          │
                                                          ▼
                                          ephemeral message to the asker only
```

## Files

| File             | Purpose                                                  |
|------------------|----------------------------------------------------------|
| `worker.js`      | Pure ES-module Worker. No deps.                          |
| `wrangler.toml`  | Worker config + KV binding + (commented) custom domain.  |
| `manifest.yaml`  | Slack app manifest — slash command + OAuth + scopes.     |
| `README.md`      | You are here.                                            |

## Routes the Worker exposes

| Method | Path              | Purpose                                                  |
|--------|-------------------|----------------------------------------------------------|
| GET    | `/healthz`        | Liveness probe.                                          |
| GET    | `/slack-setup`    | HTML form: paste bridge URL + bearer token.              |
| POST   | `/slack-setup`    | Save form values into KV.                                |
| POST   | `/slack/command`  | Slash-command receiver. HMAC-verified. Async daemon call.|
| GET    | `/slack/oauth`    | OAuth install callback (token exchange + redirect).      |

## One-time setup (you, the operator)

### 1. Create the Slack app

1. Go to https://api.slack.com/apps → **Create New App** → **From a manifest**.
2. Pick your workspace.
3. Paste the contents of `manifest.yaml`. Replace every `<WORKER_HOST>` with
   the hostname your Worker will be deployed at (e.g.
   `eidetic-slack.<your-subdomain>.workers.dev` initially, later
   `slack.eidetic.works`).
4. Click **Create**. Note the **Signing Secret**, **Client ID**, and
   **Client Secret** from the **Basic Information** tab.

### 2. Create the KV namespace and secrets

```bash
cd integrations/slack-app

# KV
wrangler kv:namespace create EIDETIC_SLACK_KV
wrangler kv:namespace create EIDETIC_SLACK_KV --preview
# Paste both IDs into wrangler.toml.

# Secrets (these prompt for the value)
wrangler secret put SLACK_SIGNING_SECRET   # from Slack → Basic Information
wrangler secret put SLACK_CLIENT_ID
wrangler secret put SLACK_CLIENT_SECRET
```

### 3. Deploy

```bash
wrangler deploy
```

The output prints the Worker URL (e.g.
`https://eidetic-slack.lokesh.workers.dev`). Confirm `GET /healthz`
returns `{"ok":true,"service":"eidetic-slack"}`.

### 4. Wire the Slack app to the deployed Worker

If you used a different hostname than the placeholder, go back to your
Slack app config and update:

- **Slash Commands → /eidetic** → Request URL: `https://<WORKER_HOST>/slack/command`
- **OAuth & Permissions → Redirect URLs**: `https://<WORKER_HOST>/slack/oauth`

Click **Save** in both places. Re-install the app to your workspace from
**Install App** → **Reinstall to Workspace**.

## How a user installs into their own workspace

1. The "Add to Slack" button on `eidetic.works/slack-setup` hits Slack's
   OAuth URL with the app's `client_id` + `scope=commands`.
2. Slack redirects them to `/slack/oauth?code=…` on the Worker.
3. The Worker exchanges the code for the team + user, then redirects to
   `/slack-setup?team_id=…&user_id=…`.
4. The user pastes:
   - **Bridge URL** — their Cloudflare-tunnel URL, e.g.
     `https://random-words.trycloudflare.com`. The Worker enforces an
     allowlist: HTTPS + `*.trycloudflare.com` or `*.cloudflare.com` only
     (see *Bridge URL allowlist* below).
   - **Bearer token** — contents of `~/.eidetic/bridge-token` from the
     machine running `eideticd -bridge :8421`.
5. Worker stores `{bridge_url, token}` in KV under
   `team:<team_id>:user:<user_id>`.
6. The user runs `/eidetic …` in any channel. Only they see the response.

## How the user runs their daemon

```bash
# On the user's local machine:
eideticd -bridge :8421                            # starts the HTTP bridge
cloudflared tunnel --url http://127.0.0.1:8421    # opens a public HTTPS URL
```

Paste the printed `https://…trycloudflare.com` URL into the setup form.

## HMAC verification

Slack signs every slash-command request with HMAC-SHA256 over the string
`v0:<X-Slack-Request-Timestamp>:<raw body>` keyed by the app's Signing
Secret. The Worker:

1. Reads the raw body with `await request.text()` BEFORE parsing it, so the
   bytes match exactly what Slack signed.
2. Rejects requests where `X-Slack-Request-Timestamp` is more than 5 minutes
   from `Date.now()` — Slack's documented replay window.
3. Uses `crypto.subtle.importKey` + `crypto.subtle.verify` so the comparison
   is constant-time at the platform level. Hex parsing is upfront so a
   malformed signature returns false before the verify call.

Implementation lives in `verifySlackSignature(...)` in `worker.js`.

## Bridge URL allowlist

The Worker rejects any bridge URL that isn't HTTPS on
`*.trycloudflare.com` or `*.cloudflare.com`. This keeps the surface tight:

- A misconfigured or stolen Slack install can't be redirected at an
  arbitrary internet endpoint.
- Cloudflare-tunnel hostnames are the documented happy path for
  `eideticd`.

To widen this list — for example, to support a user's own custom domain
proxied via Cloudflare — edit `isAllowedBridgeUrl()` in `worker.js` and
document the rationale alongside it. Do **not** allow plain `http://` or
non-Cloudflare hostnames without explicit operator review.

## Privacy / Trust boundary (per ADR-020)

What the Worker stores in KV (per `team_id`+`user_id`):

- `bridge_url` — user-provided Cloudflare-tunnel URL.
- `token` — user-provided bearer token to their own daemon.
- `updated_at` — ISO timestamp of the last setup save.

What the Worker does **not** store:

- No engram contents, ever. Daemon responses are formatted into a Slack
  Block Kit payload and forwarded directly via Slack's `response_url`.
- No Slack user names, emails, channel IDs, or message text other than the
  question itself (which is only held in memory for the duration of the
  request).

Trust boundary:

- Bridge URL + bearer token **are** customer-provided sensitive data.
  They live in Workers KV, which is encrypted at rest using
  Cloudflare-managed keys (not customer-managed). If you need
  customer-managed-key isolation, route via a Worker-bound D1 instance
  with CMK on a paid Cloudflare plan instead. Documented here so users can
  make an informed choice before pasting their token.
- The token is read only on the synchronous `/slack/command` path and
  forwarded over HTTPS to the user's own bridge URL. It is never logged.

## Local sanity check

```bash
node --check worker.js          # syntax check, no execution
```

The Worker has no test harness in this scaffold — wire one in `tests/`
once the live install flow settles and you know which edge cases need
regression coverage (HMAC failure modes, KV miss, bridge timeout).

## Deploy reminders

- Deploy from a **Workers:Edit** API token, not the Pages-only token.
  See `workers/gumroad-kit-sync/wrangler.toml` for the established
  pattern in this repo.
- The first `wrangler deploy` will fail until the KV namespace IDs are
  pasted into `wrangler.toml`.
- After deploying, `curl https://<WORKER_HOST>/healthz` should return
  `{"ok":true,"service":"eidetic-slack"}`.
