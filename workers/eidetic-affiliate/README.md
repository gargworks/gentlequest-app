# eidetic-affiliate

Cloudflare Worker that:

1. Resolves vanity URLs like `https://eidetic.works/ref/joe123` to the Gumroad
   product page with `?wanted=true&affiliate=joe123`.
2. Logs each click into Cloudflare KV (`EIDETIC_AFFILIATES_KV`) for stats.
3. Exposes a tiny Bearer-auth admin surface to register affiliates and read
   click counts.

Privacy: IPs and User-Agents are SHA-256-hashed before storage. No raw PII is
written anywhere.

---

## Routes

| Route                              | Behaviour                                                            |
| ---------------------------------- | -------------------------------------------------------------------- |
| `GET /ref/<code>`                  | 302 → `…/l/eidetic-pro?wanted=true&affiliate=<code>` (Pro $29/mo)    |
| `GET /ref/<code>/team`             | 302 → `…/l/eidetic-team?…` (Team $99/mo)                             |
| `GET /ref/<code>/founder`          | 302 → `…/l/eidetic-pro-founder?…` (Founder $499 lifetime)            |
| `GET /ref/<code>/annual`           | 302 → `…/l/eidetic-pro-annual?…` (Annual $299/yr)                    |
| `GET /admin/codes`                 | List all known affiliate codes                                       |
| `POST /admin/codes`                | Register a new affiliate code (body: `{code,name,email,created_at}`) |
| `GET /admin/clicks?code=<code>`    | `{code, clicks, last_seen, distinct_ip_count}`                       |
| `GET /ping`                        | 204 (health probe)                                                   |

`<code>` must match `/^[a-zA-Z0-9_-]{2,32}$/`.

---

## Deploy

```bash
cd workers/eidetic-affiliate

# 1. Create the KV namespace (one-time)
CLOUDFLARE_API_TOKEN=<workers-token> wrangler kv:namespace create EIDETIC_AFFILIATES_KV
# Paste the returned id into wrangler.toml under [[kv_namespaces]].

# 2. Set the admin bearer secret (one-time, rotatable)
CLOUDFLARE_API_TOKEN=<workers-token> wrangler secret put ADMIN_SECRET
# Suggested value: `openssl rand -hex 32`

# 3. Deploy
CLOUDFLARE_API_TOKEN=<workers-token> wrangler deploy
```

Until `ADMIN_SECRET` is set, the `/admin/*` endpoints return `503 admin not
configured` — by design, so you can ship the public `/ref/*` surface first and
lock down admin later.

Add a route in the Cloudflare dashboard (Workers → Routes):

```
eidetic.works/ref/*    → eidetic-affiliate
eidetic.works/admin/*  → eidetic-affiliate
```

---

## Register an affiliate

```bash
ADMIN=<the ADMIN_SECRET value>

curl -X POST https://eidetic-affiliate.<account>.workers.dev/admin/codes \
  -H "Authorization: Bearer $ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"code":"joe123","name":"Joe Example","email":"joe@example.com"}'
```

Their vanity link is now `https://eidetic.works/ref/joe123`.

---

## Check stats

```bash
curl -H "Authorization: Bearer $ADMIN" \
  "https://eidetic-affiliate.<account>.workers.dev/admin/clicks?code=joe123"
# → {"code":"joe123","registered":true,"clicks":42,"last_seen":1716220000,"distinct_ip_count":31,"raw_event_count":42}

curl -H "Authorization: Bearer $ADMIN" \
  "https://eidetic-affiliate.<account>.workers.dev/admin/codes"
# → {"count":N,"codes":[…]}
```

---

## KV layout

```
code:<code>                      JSON  {name, email, created_at, click_count, last_click_ts, auto_created}
click:<code>:<unix_ts>:<hash6>   JSON  {ip_hash, ua_hash, referrer}   TTL=90d
```

`auto_created: true` means a click was logged for an unknown code (an attacker
or pre-registered link); aggregate counts still accumulate so you can spot
demand from people who haven't been onboarded yet.

---

## Gumroad attribution flow

```
visitor clicks  →  eidetic.works/ref/joe123
                       │
                       ▼
   this worker logs the click and 302s to:
   https://eideticworks.gumroad.com/l/eidetic-pro?wanted=true&affiliate=joe123
                       │
                       ▼
   visitor buys; Gumroad sends sale webhook to gumroad-kit-sync
                       │
                       ▼
   webhook payload includes the `affiliate` query field (passed through
   from the URL); also potentially `wanted_affiliate` if Gumroad's native
   affiliate program is enabled.
```

### Hook into `gumroad-kit-sync`

This worker does NOT modify `gumroad-kit-sync`. The integration path is:

1. In `workers/gumroad-kit-sync/worker.js`, in the webhook body-parse block,
   also read:
   ```js
   const affiliateCode = body.get?.("affiliate")
                      || body.affiliate
                      || body.get?.("wanted_affiliate")
                      || body.wanted_affiliate
                      || "";
   ```
2. If `affiliateCode` is non-empty, write a `payout:<code>:<sale_id>` row to
   `EIDETIC_AFFILIATES_KV` (or a separate payouts namespace) capturing
   `{sale_id, email, product_permalink, gross_cents, ts}`. That row is what
   the 20% recurring payout job reads at month-end.
3. Optionally, include the affiliate code in the Telegram operator ping so
   Lokesh knows which partner drove the sale.

Keeping the writer separate (this worker logs clicks; gumroad-kit-sync logs
sales) means either worker can be redeployed independently without touching
the other.

---

## Operational notes

- **Click TTL**: 90 days. Aggregate `click_count` on `code:<code>` is
  permanent; only the per-event rows expire.
- **Distinct-IP count** in `/admin/clicks` is computed by walking the
  `click:<code>:*` prefix — fine for low-volume affiliates, may need a
  cached pre-aggregate at scale.
- **Race on `click_count`**: KV is eventually consistent, so two concurrent
  clicks can both read the same counter and increment. The aggregate is
  best-effort; `raw_event_count` from `/admin/clicks` is the source of truth.
- **CORS**: not needed — every endpoint is a server-side redirect or an
  admin call made from a trusted shell, never from a browser fetch.
