# eidetic-account

Customer-facing Pro account dashboard for Eidetic. A Pro customer pastes the
`api_key` from their `sync.json` and sees:

- their account record (email, device_id, when they were added)
- the list of engram backups stored in R2 for their device
- a per-backup download button

No password infra. The `api_key` itself is the credential; every request hashes
it (SHA-256) server-side and looks the customer up by hash in KV.

---

## Routes

| Route              | Behaviour                                                                 |
| ------------------ | ------------------------------------------------------------------------- |
| `GET  /`           | Inline HTML sign-in page (dark + teal, monospace, matches landing palette) |
| `POST /lookup`     | `{api_key}` → `{email, device_id, added, backups:[{key,size,uploaded_at}]}` (newest first, cap 50) |
| `GET  /download`   | `?key=engrams/<device_id>/<file>.db&api_key=<key>` → streams the R2 object with `Content-Disposition: attachment` |
| `GET  /ping`       | 204 (health probe)                                                        |

### Error codes

| Status | Reason                                                              |
| ------ | ------------------------------------------------------------------- |
| 400    | Malformed request (missing fields, bad object-key shape)            |
| 401    | SHA-256(api_key) did not match any KV row                           |
| 403    | Key is valid but the requested object key belongs to a different `device_id` |
| 404    | Object missing from R2                                              |
| 503    | Bindings not configured (deployment misconfig)                      |

---

## Bindings

Both bindings already exist on the `eidetic-sync` worker. This worker re-binds
them read-only.

```toml
[[kv_namespaces]]
binding = "EIDETIC_KEYS_KV"
id      = "34d23af4669a40bd907f5c58c56802e8"

[[r2_buckets]]
binding     = "EIDETIC_ENGRAMS_R2"
bucket_name = "eidetic-engrams"
```

KV value shape (written by `scripts/gen_pro_key.sh`):

```json
{"email":"...","device_id":"...","added":"2026-05-20T12:34:56Z"}
```

R2 object layout (written by the `eidetic` CLI on `eidetic sync`):

```
engrams/<device_id>/engrams-<unix_ts>.db
```

---

## Deploy

```bash
cd workers/eidetic-account

# 1. (Optional) wrangler dev for local smoke-testing
CLOUDFLARE_API_TOKEN=<workers-token> wrangler dev

# 2. Ship it
CLOUDFLARE_API_TOKEN=<workers-token> wrangler deploy
```

No secrets to set. The api_key check is purely a KV lookup.

### DNS routing (subdomain)

```
Cloudflare dashboard → DNS → Records
  Type    CNAME
  Name    account
  Target  eidetic-account.<account>.workers.dev
  Proxy   ON (orange cloud)

Cloudflare dashboard → Workers → Routes
  account.eidetic.works/*    → eidetic-account
```

Customers visit `https://account.eidetic.works/`.

---

## UX walkthrough

1. Customer lands on `https://account.eidetic.works/`. Page is a single dark
   panel with a `Your Eidetic Pro Account` heading, a paste textarea, and a
   teal `Sign in` button. No analytics, no third-party scripts.
2. They paste the 43-character `api_key` from `sync.json` and click `Sign in`.
   The browser POSTs `{api_key}` to `/lookup` (same-origin, no CORS).
3. Worker hashes the key, looks up `EIDETIC_KEYS_KV`, then `EIDETIC_ENGRAMS_R2.list()`
   under `engrams/<device_id>/`. Newest 50 backups are returned.
4. Page renders two cards:
   - **Account card** — email, device_id, member-since, backup count.
   - **Backups table** — timestamp (human-readable), size (KB/MB/GB), and a
     teal `download` button per row.
5. Clicking `download` issues `GET /download?key=...&api_key=...`. The worker
   re-hashes the api_key, re-verifies it matches a KV row, then checks that the
   `device_id` embedded in the requested object key matches the one bound to
   that api_key (constant-time compare). Match → R2 object streams down with
   `Content-Disposition: attachment`. Mismatch → 403.

---

## Privacy

- The `api_key` is never persisted by this worker.
- Logs include only the first 6 hex characters of `SHA-256(api_key)` for
  diagnostic correlation (`hash_prefix=abc123`). 24 bits is enough to follow
  one user across a session without giving an attacker a useful brute-force
  surface.
- Page sets `Referrer-Policy: no-referrer` so the api_key (if it ever lands in
  a URL via the download link) isn't leaked to outbound resources.
- Page sets `<meta name="robots" content="noindex,nofollow">`. The account
  surface is unlisted; customers reach it via a direct link in their welcome
  email.
- `/download` is necessarily a `GET` (browsers don't send `POST` bodies on a
  click-link download), so the api_key does land in the URL query for that
  request. This is the standard tradeoff for download-link auth. Server-side
  we still hash + lookup before serving.

---

## Operational notes

- **Read-only.** This worker performs no writes to KV or R2. Safe to redeploy
  any time; can be removed/re-added without data risk.
- **No admin surface.** Auth is the customer's own api_key. If a key needs to
  be revoked, delete the corresponding hash row from `EIDETIC_KEYS_KV` (the
  worker will return 401 on the next request, no extra step needed).
- **Backup cap.** Hard-coded to the newest 50 entries. If a customer ever
  exceeds that, raise `BACKUP_LIST_CAP` in `worker.js` or paginate.
- **Device-id substitution attack.** A leaked api_key would let an attacker
  download that customer's backups; that's the same threat model as any
  bearer-token system. They cannot pivot to other customers' backups because
  `/download` rejects mismatched device_ids in constant time.

---

## Why this exists

Before this worker, a Pro purchase ended with: operator runs
`scripts/gen_pro_key.sh`, emails the customer their `sync.json`, customer has
no place to inspect their own state. First time they want to know "is my
sync working" or "where are my backups", they email back.

This worker is the answer they should self-serve: same KV + R2 the sync
pipeline already maintains, exposed read-only with the api_key as the auth
primitive.
