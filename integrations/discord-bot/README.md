# Eidetic for Discord

A Cloudflare Worker that turns `/eidetic <question>` in any Discord channel
into an ask against the user's **own** local `eideticd` daemon. The Worker
is a thin Ed25519-verified relay; engram contents are never stored on
Cloudflare.

```
Discord user ──/eidetic …──▶  Discord  ──Ed25519 POST──▶  Cloudflare Worker
                                                                  │
                                                                  ▼
                                                           Workers KV
                                                           (bridge URL + token)
                                                                  │
                                                                  ▼
                                                user's eideticd (via Cloudflare tunnel)
                                                                  │
                                                                  ▼
                                                Worker formats Discord embed
                                                                  │
                                                                  ▼
                                                ephemeral message to the asker only
```

## Files

| File                    | Purpose                                                |
|-------------------------|--------------------------------------------------------|
| `worker.js`             | Pure ES-module Worker. No deps.                        |
| `register-commands.js`  | One-shot Node script: registers `/eidetic` with Discord. |
| `wrangler.toml`         | Worker config + KV binding + (commented) custom domain. |
| `README.md`             | You are here.                                          |

## Routes the Worker exposes

| Method | Path                       | Purpose                                                                 |
|--------|----------------------------|-------------------------------------------------------------------------|
| GET    | `/healthz`                 | Liveness probe.                                                         |
| GET    | `/discord-setup`           | HTML form: paste bridge URL + bearer token + Discord user ID.           |
| POST   | `/discord-setup`           | Save form values into KV.                                               |
| POST   | `/discord/interactions`    | Discord webhook receiver. Ed25519-verified. Handles PING + APPLICATION_COMMAND. |
| GET    | `/discord/oauth`           | Optional OAuth `identify` callback that pre-fills the setup form.       |

## Ed25519 verification — design choice

Discord signs every interaction with Ed25519 over `timestamp || raw body`,
keyed by the application's public key. They REQUIRE the Worker to return
HTTP 401 on any invalid signature — during interactions-endpoint setup
Discord probes with deliberately bad signatures and **disables the
endpoint** if you return anything else.

The Worker uses Cloudflare Workers' Web Crypto Ed25519 support:

1. Tries `crypto.subtle.importKey('raw', pub, { name: 'Ed25519' }, …)` first
   — the W3C Secure Curves standard identifier, now GA on recent Workers
   compatibility dates.
2. On `importKey` failure (older compatibility date, runtime mismatch),
   falls back to the Cloudflare/Node-compatible alias
   `{ name: 'NODE-ED25519', namedCurve: 'NODE-ED25519' }`.
3. If both paths throw, returns `false` — fails closed; we deliberately
   do **not** bundle `tweetnacl` or a hand-rolled Ed25519, because a
   Worker that can't verify Discord's signatures shouldn't pretend to.

Why not bundle `tweetnacl`?

- Keeps `worker.js` pure ES, zero `npm install`, zero supply-chain risk.
- Workers runtimes from late 2024 onward already speak one of the two
  identifiers above; the fallback covers the gap.
- Bundling adds ~40 KB and forces a build step, both of which would
  drift this scaffold away from the slack-app pattern next door.

If you ever need to support a Workers runtime that speaks neither
identifier, prefer flipping `compatibility_date` forward in
`wrangler.toml` rather than vendoring crypto.

Implementation lives in `verifyDiscordSignature(...)` in `worker.js`.

## One-time setup (you, the operator)

### 1. Create the Discord application

1. Go to <https://discord.com/developers/applications> → **New Application**.
2. Pick a name (e.g. `Eidetic`). Note the **Application ID** on the
   **General Information** tab.
3. Copy the **Public Key** (hex) from the same tab — this is the Ed25519
   key the Worker will verify against.
4. Open the **Bot** tab → **Reset Token** → copy the bot token (you'll need
   it for `register-commands.js`). Do not enable any privileged intents;
   the bot only needs slash-command interactions.
5. Open **OAuth2 → URL Generator**, tick **`bot`** + **`applications.commands`**
   under "scopes", and **(optionally)** `identify` if you want the
   `/discord/oauth` pre-fill path. The default empty bot permissions are
   sufficient — Eidetic only sends ephemeral replies, no message-write
   permission needed.
6. The generator outputs an "install URL". Save it; users will visit it
   to add the bot to their server.

### 2. Create the KV namespace and secrets

```bash
cd integrations/discord-bot

# KV
wrangler kv:namespace create EIDETIC_DISCORD_KV
wrangler kv:namespace create EIDETIC_DISCORD_KV --preview
# Paste both IDs into wrangler.toml.

# Secrets (these prompt for the value)
wrangler secret put DISCORD_PUBLIC_KEY      # hex from Developer Portal → General Information
wrangler secret put DISCORD_APPLICATION_ID  # snowflake from the same page
wrangler secret put DISCORD_BOT_TOKEN       # only used by /discord/oauth (and register-commands.js)
wrangler secret put DISCORD_CLIENT_SECRET   # only used by /discord/oauth
```

`DISCORD_BOT_TOKEN` and `DISCORD_CLIENT_SECRET` are optional for the core
slash-command flow. They are required only if you enable the
`/discord/oauth` pre-fill route. The Worker treats their absence as
"OAuth disabled" rather than failing the deploy.

### 3. Deploy the Worker

```bash
wrangler deploy
```

The output prints the Worker URL (e.g.
`https://eidetic-discord.lokesh.workers.dev`). Confirm
`GET /healthz` returns `{"ok":true,"service":"eidetic-discord"}`.

### 4. Point Discord at the Worker

1. Back in the Developer Portal → **General Information** → set
   **Interactions Endpoint URL** to
   `https://<WORKER_HOST>/discord/interactions`.
2. Click **Save Changes**. Discord will immediately probe the endpoint:
   - Sends a `type: 1` (PING) with a valid signature — Worker must reply
     `{"type": 1}`.
   - Sends a deliberately bad signature — Worker must reply 401.
   - If either fails, Discord refuses to save the URL.

### 5. Register the `/eidetic` slash command

```bash
DISCORD_APPLICATION_ID=... \
DISCORD_BOT_TOKEN=...      \
  node integrations/discord-bot/register-commands.js
```

For instant iteration during development (skip the up-to-1h global cache),
also export `DISCORD_DEV_GUILD_ID`:

```bash
DISCORD_APPLICATION_ID=... \
DISCORD_BOT_TOKEN=...      \
DISCORD_DEV_GUILD_ID=...   \
  node integrations/discord-bot/register-commands.js
```

The script PUTs the entire command list at the chosen scope, so it's
idempotent — re-run any time you tweak the schema in
`register-commands.js`.

## How a user installs the bot into their server

1. The user visits the OAuth install URL from step 1.6 (you'll surface
   this on `eidetic.works/discord-setup` next to the "Set up" form).
2. They pick a server and click **Authorize**. Discord adds the bot with
   only the slash-command surface — no permission to read message history.
3. They visit `https://<WORKER_HOST>/discord-setup` (or the public link
   `https://eidetic.works/discord-setup` if you proxy it), enable
   **Developer Mode** in Discord settings, right-click their own profile
   to **Copy User ID**, and paste:
   - **Discord user ID** — 15–21 digit snowflake. Must match the user
     who invokes `/eidetic`.
   - **Bridge URL** — their Cloudflare-tunnel URL, e.g.
     `https://random-words.trycloudflare.com`. The Worker enforces an
     allowlist: HTTPS + `*.trycloudflare.com` or `*.cloudflare.com` only.
   - **Bearer token** — contents of `~/.eidetic/bridge-token` from the
     machine running `eideticd -bridge :8421`.
4. Worker stores `{bridge_url, token, configured_at}` in KV under
   `user:<discord_user_id>`.
5. The user runs `/eidetic question: …` in any channel of any server the
   bot is in, or in a DM with the bot. Only they see the reply.

## How the user runs their daemon

```bash
# On the user's local machine:
eideticd -bridge :8421                            # starts the HTTP bridge
cloudflared tunnel --url http://127.0.0.1:8421    # opens a public HTTPS URL
```

Paste the printed `https://…trycloudflare.com` URL into the setup form.

## Round-trip

`/eidetic question:<q>` →
Discord HMACs-with-Ed25519 a POST to the Worker →
Worker verifies sig (401 on fail), loads `bridge_url+token` from KV by
caller's `user.id` →
Worker calls `GET <bridge>/ask?question=…` with `Authorization: Bearer
<token>` and 12s timeout →
Worker formats `{answer, results}` into a Discord embed and returns a
type 4 (CHANNEL_MESSAGE_WITH_SOURCE) response with `flags: 64`
(ephemeral) — only the asker sees the reply.

## Bridge URL allowlist

The Worker rejects any bridge URL that isn't HTTPS on
`*.trycloudflare.com` or `*.cloudflare.com`. This keeps the surface tight:

- A misconfigured or stolen Discord install can't be redirected at an
  arbitrary internet endpoint.
- Cloudflare-tunnel hostnames are the documented happy path for
  `eideticd`.

To widen this list — for example, to support a user's own custom domain
proxied via Cloudflare — edit `isAllowedBridgeUrl()` in `worker.js` and
document the rationale alongside it. Do **not** allow plain `http://` or
non-Cloudflare hostnames without explicit operator review.

## Privacy / Trust boundary (per ADR-020)

What the Worker stores in KV (per Discord `user_id`):

- `bridge_url` — user-provided Cloudflare-tunnel URL.
- `token` — user-provided bearer token to their own daemon.
- `configured_at` — ISO timestamp of the last setup save.

What the Worker does **not** store:

- No engram contents, ever. Daemon responses are formatted into a Discord
  embed and returned in the synchronous interaction response.
- No Discord user names, avatars, guild IDs, channel IDs, or message text
  other than the `question` itself (which is only held in memory for the
  duration of the request).

Trust boundary:

- Bridge URL + bearer token **are** customer-provided sensitive data.
  They live in Workers KV, which is encrypted at rest using
  Cloudflare-managed keys (not customer-managed). If you need
  customer-managed-key isolation, route via a Worker-bound D1 instance
  with CMK on a paid Cloudflare plan instead.
- The token is read only on the synchronous `/discord/interactions` path
  and forwarded over HTTPS to the user's own bridge URL. It is never
  logged.

## Deferred responses (future work)

The scaffold answers synchronously: the bridge call must complete inside
Discord's 3-second initial-response budget. For slower daemons, swap the
APPLICATION_COMMAND handler to:

1. Immediately return type 5 (DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE) with
   `flags: 64`.
2. From `ctx.waitUntil(...)`, PATCH the original response via
   `https://discord.com/api/v10/webhooks/<APP_ID>/<INTERACTION_TOKEN>/messages/@original`
   with the embed once the bridge replies.

This costs one extra Discord round-trip but unlocks a 15-minute response
window. Document in this section the day you flip the switch.

## Troubleshooting

- **Discord refuses to save the Interactions Endpoint URL.** The Worker
  is returning 200 on a bad signature instead of 401. Confirm by
  `curl -X POST -d 'x' -H 'x-signature-ed25519: 00' -H 'x-signature-timestamp: 0'
  https://<WORKER_HOST>/discord/interactions` → must be 401.
- **`/eidetic` doesn't appear in the slash-command picker.** Either the
  global command is still propagating (up to an hour) or
  `register-commands.js` errored. Re-run with `DISCORD_DEV_GUILD_ID`
  set to your test server's ID for instant feedback.
- **"Configure your bridge URL at …" reply on every invocation.** The
  user pasted a snowflake that doesn't match the one Discord sends in the
  interaction. Have them re-copy their user ID via Developer Mode and
  re-submit the setup form.
- **`bridge HTTP 401`.** The bearer token in KV doesn't match
  `~/.eidetic/bridge-token`. Re-submit the setup form.
- **`bridge HTTP 5xx` or timeout.** The Cloudflare tunnel disconnected,
  or the daemon isn't running. Restart `cloudflared tunnel` + `eideticd`
  and confirm the URL still works in a browser.

## Local sanity check

```bash
node --check worker.js              # syntax check, no execution
node --check register-commands.js   # syntax check, no execution
```

No test harness in this scaffold — wire one in `tests/` once the live
install flow settles and you know which edge cases need regression
coverage (Ed25519 verify failure modes, KV miss, bridge timeout,
unsupported interaction type, oversized embed truncation).

## Deploy reminders

- Deploy from a **Workers:Edit** API token, not the Pages-only token.
- The first `wrangler deploy` will fail until the KV namespace IDs are
  pasted into `wrangler.toml`.
- After deploying, `curl https://<WORKER_HOST>/healthz` should return
  `{"ok":true,"service":"eidetic-discord"}`.
- Set the **Interactions Endpoint URL** in the Discord Developer Portal
  AFTER the Worker is live and `/healthz` is green — otherwise Discord's
  ping probe will fail and refuse to save the URL.
