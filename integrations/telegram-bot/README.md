# Eidetic for Telegram

A Cloudflare Worker that turns `/eidetic <question>` in any Telegram chat
into an ask against the user's **own** local `eideticd` daemon. The Worker
is a thin secret-token-verified relay; engram and message contents are never
stored on Cloudflare.

```
Telegram user ──/eidetic …──▶  Telegram  ──POST + secret header──▶  Cloudflare Worker
                                                                            │
                                                                            ▼
                                                                     Workers KV
                                                                     (bot token + bridge URL + bridge token)
                                                                            │
                                                                            ▼
                                                          user's eideticd (via Cloudflare tunnel)
                                                                            │
                                                                            ▼
                                                          Worker formats MarkdownV2 reply
                                                                            │
                                                                            ▼
                                                       sendMessage as a reply to the original
```

## Files

| File              | Purpose                                                |
|-------------------|--------------------------------------------------------|
| `worker.js`       | Pure ES-module Worker. No deps.                        |
| `wrangler.toml`   | Worker config + KV binding + (commented) custom domain. |
| `README.md`       | You are here.                                          |

## Routes the Worker exposes

| Method | Path                                  | Purpose                                                                                  |
|--------|---------------------------------------|------------------------------------------------------------------------------------------|
| GET    | `/healthz`                            | Liveness probe.                                                                          |
| POST   | `/telegram/webhook`                   | Telegram Update receiver. Verifies `X-Telegram-Bot-Api-Secret-Token`. Always returns 200. |
| GET    | `/telegram-setup`                     | HTML form: paste bot token + bridge URL + bearer token + Telegram user ID.               |
| POST   | `/telegram-setup`                     | Verify bot token via `getMe`; save config to KV.                                         |
| GET    | `/telegram-setup/install/<bot_token>` | One-shot `setWebhook` caller. Tells Telegram to forward updates to this Worker.          |

## Webhook secret verification — design choice

Telegram's webhook auth model is different from Slack (HMAC) and Discord
(Ed25519): when you call `setWebhook` you pass a `secret_token` parameter,
and Telegram echoes that exact string back in the
`X-Telegram-Bot-Api-Secret-Token` header on every webhook POST. There is
no payload signature — verification is a single equality check against a
shared secret.

The Worker does a **constant-time** byte-by-byte compare (XOR-accumulating
mismatches across the full string length) instead of a naive `===`. The
naive operator short-circuits on the first mismatching byte, which on a
fast-enough network lets a timing attacker learn the secret one character
at a time.

Implementation lives in `constantTimeEqual(a, b)` in `worker.js`.

### Always return 200

Telegram's webhook delivery retries indefinitely on any non-2xx response.
A misbehaving Worker that returns 4xx/5xx on a malformed update will get
the same update redelivered for hours. The Worker therefore:

1. Always returns 200 from `/telegram/webhook`, even on bad secret / bad
   JSON / unsupported update type.
2. Logs the rejection cause to `console.warn` (visible in `wrangler tail`)
   so the operator can debug without DOS-ing the Worker.

The setup / install routes return real HTTP statuses — Telegram doesn't
retry those.

## One-time setup (you, the operator)

### 1. Create the bot via @BotFather

1. In Telegram, message [`@BotFather`](https://t.me/BotFather).
2. Send `/newbot`. Pick a display name and a unique username ending in
   `bot` (e.g. `EideticAskBot`).
3. BotFather replies with a token like
   `7891234567:AAH-d3xyz_thirty_or_so_mixedcase_chars`. **This is the bot
   token** — treat it like a password.
4. (Optional but recommended) send `/setcommands` → pick your bot →
   paste:
   ```
   eidetic - Ask your eidetic daemon
   ```
   so `/eidetic` shows up in Telegram's slash-command picker.
5. (Optional) `/setprivacy` → pick your bot → **Enable**. With privacy
   mode on, the bot only sees messages that start with `/` or @-mention
   it — which is all we care about. Reduces what Telegram even forwards.

### 2. Create the KV namespace and the webhook secret

```bash
cd integrations/telegram-bot

# KV
wrangler kv:namespace create EIDETIC_TELEGRAM_KV
wrangler kv:namespace create EIDETIC_TELEGRAM_KV --preview
# Paste both IDs into wrangler.toml.

# Webhook secret (Telegram will echo this back on every POST).
# Use a strong random hex string.
openssl rand -hex 32 | wrangler secret put WEBHOOK_SECRET

# Optional admin bot token — only needed if you want to call
# /telegram-setup/install WITHOUT a token in the URL path.
wrangler secret put ADMIN_BOT_TOKEN
```

### 3. Deploy the Worker

```bash
wrangler deploy
```

The output prints the Worker URL (e.g.
`https://eidetic-telegram.lokesh.workers.dev`). Confirm
`GET /healthz` returns `{"ok":true,"service":"eidetic-telegram"}`.

### 4. Tell Telegram to send updates to the Worker

Open in a browser (one-shot install):

```
https://<WORKER_HOST>/telegram-setup/install/<YOUR_BOT_TOKEN>
```

The Worker calls Telegram's `setWebhook` with this Worker's
`/telegram/webhook` URL and the `secret_token` you set via
`wrangler secret put WEBHOOK_SECRET`. From this point on, Telegram POSTs
every `message` update to the Worker and includes the secret in the
`X-Telegram-Bot-Api-Secret-Token` header.

If you rotate `WEBHOOK_SECRET`, re-visit the install URL to refresh
Telegram's stored copy.

## How a user installs the bot

The flow is **simpler than Slack and Discord** — no OAuth, no install
flow. Each user creates **their own** bot (one bot per user, since the
bot token doubles as the send-as identity):

1. The user follows step 1 above (`/newbot` with @BotFather) and gets
   their own bot token.
2. They get their Telegram user ID by sending `/start` to
   [`@userinfobot`](https://t.me/userinfobot) — it replies with their
   numeric ID.
3. They visit `https://<WORKER_HOST>/telegram-setup` (or
   `https://eidetic.works/telegram-setup` if you proxy it), and paste:
   - **Telegram user ID** — 5–15 digit numeric ID from @userinfobot.
   - **Bot token** — from BotFather. The Worker verifies it via Telegram
     `getMe` before writing to KV.
   - **Bridge URL** — their Cloudflare-tunnel URL, e.g.
     `https://random-words.trycloudflare.com`. The Worker enforces an
     allowlist: HTTPS + `*.trycloudflare.com` or `*.cloudflare.com` only.
   - **Bearer token** — contents of `~/.eidetic/bridge-token` from the
     machine running `eideticd -bridge :8421`.
4. After save, the success page links them to
   `/telegram-setup/install/<their-bot-token>` to register their bot's
   webhook with the same Worker.
5. They DM their bot with `/eidetic question: …`, or add it to a group
   and run `/eidetic@<their-bot-name> question: …`. The Worker replies as
   a thread reply to the original message.

## How the user runs their daemon

```bash
# On the user's local machine:
eideticd -bridge :8421                            # starts the HTTP bridge
cloudflared tunnel --url http://127.0.0.1:8421    # opens a public HTTPS URL
```

Paste the printed `https://…trycloudflare.com` URL into the setup form.

## Round-trip

`/eidetic <q>` in any chat →
Telegram POSTs the Update to the Worker with the secret token header →
Worker constant-time-compares the header against `WEBHOOK_SECRET` (200
on success or any failure to suppress Telegram retries) →
Worker matches `/eidetic` in `message.text`, loads `bot_token + bridge_url
+ token` from KV by `message.from.id` →
Worker calls `GET <bridge>/ask?question=…` with `Authorization: Bearer
<token>` and 12s timeout →
Worker formats `{answer, results}` as MarkdownV2 and calls
`POST https://api.telegram.org/bot<bot_token>/sendMessage` with
`reply_parameters.message_id` set to the original message — the reply
threads to the user's question.

## MarkdownV2 escaping

Telegram MarkdownV2 is strict: any of `_*[]()~\`>#+-=|{}.!` outside of
matched markdown constructs must be backslash-escaped or Telegram returns
400 "can't parse entities". The Worker's `escapeMdV2(s)` helper:

```
\ → \\
_ * [ ] ( ) ~ ` > # + - = | { } . ! → prefixed with \
```

The backslash itself is escaped first so we don't double-escape the
backslashes we just inserted. Free-form fields (question text, answer,
engram surface/timestamp/snippet) all flow through `escapeMdV2`; structural
markdown (bold/italic/code wrappers) is hand-written and intentionally
NOT escaped.

## Bridge URL allowlist

The Worker rejects any bridge URL that isn't HTTPS on
`*.trycloudflare.com` or `*.cloudflare.com`. This keeps the surface tight:

- A misconfigured or stolen install can't be redirected at an arbitrary
  internet endpoint.
- Cloudflare-tunnel hostnames are the documented happy path for
  `eideticd`.

To widen this list — for example, to support a user's own custom domain
proxied via Cloudflare — edit `isAllowedBridgeUrl()` in `worker.js` and
document the rationale alongside it. Do **not** allow plain `http://` or
non-Cloudflare hostnames without explicit operator review.

## Privacy / Trust boundary (per ADR-020)

What the Worker stores in KV (per Telegram `user_id`):

- `bot_token` — user-provided bot token (so we can call `sendMessage` as
  their bot).
- `bridge_url` — user-provided Cloudflare-tunnel URL.
- `token` — user-provided bearer token to their own daemon.
- `configured_at` — ISO timestamp of the last setup save.

What the Worker does **not** store:

- No message content, ever. Inbound `text` and the parsed `question` are
  only held in memory for the duration of the request.
- No engram contents. Daemon responses are formatted into the
  `sendMessage` body and discarded after the reply.
- No Telegram chat IDs, usernames, first names, last names, or message
  IDs — `chat_id` + `message_id` are only used to address the reply.

Trust boundary:

- Bot token + bridge URL + bearer token **are** customer-provided
  sensitive data. They live in Workers KV, which is encrypted at rest
  using Cloudflare-managed keys (not customer-managed).
- The bot token shows up in the URL path of `/telegram-setup/install/`
  (so the operator can install a webhook with a single browser GET).
  That request appears in Cloudflare's request logs. If your threat
  model includes Cloudflare-log access, change the install handler to
  read the token from a POST body instead.
- The bot token + daemon token are read only on the asynchronous
  `ctx.waitUntil` path of `/telegram/webhook` and forwarded over HTTPS
  to Telegram + the user's bridge URL. Neither is ever logged.

## Troubleshooting

- **Bot doesn't reply at all.** Check `wrangler tail` for a
  `telegram: bad webhook secret token` warning — Telegram is hitting the
  Worker but the secret doesn't match. Re-run
  `/telegram-setup/install/<bot_token>` after the latest
  `wrangler secret put WEBHOOK_SECRET` to refresh Telegram's copy.
- **Bot replies "Configure your bridge URL …" on every invocation.**
  The user's Telegram numeric ID in KV doesn't match the
  `message.from.id` Telegram is sending. Have them re-send `/start` to
  `@userinfobot`, copy the ID exactly, and re-submit the setup form.
- **Reply arrives as raw markdown with backslashes everywhere.** The
  MarkdownV2 escape is doing its job but you put structural markdown
  inside an escaped field by mistake. See the `renderAnswerMarkdown`
  function — bold/italic wrappers are intentionally outside the
  `escapeMdV2` boundary.
- **`bridge HTTP 401`.** The bearer token in KV doesn't match
  `~/.eidetic/bridge-token`. Re-submit the setup form.
- **`bridge HTTP 5xx` or timeout.** The Cloudflare tunnel disconnected,
  or the daemon isn't running. Restart `cloudflared tunnel` + `eideticd`
  and confirm the URL still works in a browser.
- **Telegram refuses `setWebhook` ("HTTPS url must be provided for
  webhook").** Your Worker URL is `.workers.dev`/your-custom-domain;
  confirm it's HTTPS and reachable from the public internet. Telegram
  requires a real CA-issued cert (Cloudflare provides this by default).
- **Telegram `sendMessage` returns 400 "can't parse entities".** A
  free-form field bypassed `escapeMdV2`. Search the rendering path for
  any concatenation that puts unsanitised user-supplied text into the
  output without going through the escape helper.

## Local sanity check

```bash
node --check worker.js   # syntax check, no execution
```

No test harness in this scaffold — wire one in `tests/` once the live
install flow settles and you know which edge cases need regression
coverage (bad secret token, malformed JSON, command with no question,
KV miss, bridge timeout, MarkdownV2 escape edge cases, oversized message
truncation, `/eidetic@BotName` group-chat variant).

## Deploy reminders

- Deploy from a **Workers:Edit** API token, not the Pages-only token.
- The first `wrangler deploy` will fail until the KV namespace IDs are
  pasted into `wrangler.toml`.
- After deploying, `curl https://<WORKER_HOST>/healthz` should return
  `{"ok":true,"service":"eidetic-telegram"}`.
- Call `/telegram-setup/install/<bot_token>` AFTER the Worker is live
  and `/healthz` is green — Telegram's `setWebhook` verifies the URL
  is reachable before storing it.
