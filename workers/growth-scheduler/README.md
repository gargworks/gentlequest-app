# growth-scheduler

Multi-channel content publisher + weekly-digest generator. Makes distribution a function of time, not effort.

## What it does

1. **Queue.** You POST drafts (X tweet, LinkedIn post, Substack article) to `/queue`. They land in `CONTENT_QUEUE` KV.
2. **Cron fires.** Hourly + daily + weekly triggers process the queue, one post per channel per slot.
3. **Adapter publishes.** First adapter is **Buffer** — one signup at buffer.com covers X + LinkedIn + Substack. Optional fallback adapters for X API v2 native.
4. **Idempotency log.** `POSTED_LOG` KV records every successful publish so cron races never double-post.
5. **Weekly digest.** Sunday cron pulls last week's commits on `eidetic-daemon`, generates a Substack draft, enqueues it. Zero human in loop.
6. **Analytics.** Every enqueue/post/error logs to `eidetic-analytics` ANALYTICS binding. `GET /stats` on that worker sees the funnel.

## One-time setup (Lokesh-keyboard, ~10 min)

See `docs/DISTRIBUTION_AUTOPILOT.md` (single source of truth) for the canonical setup walkthrough. The short version:

1. Create KV namespaces:
   ```sh
   unset CLOUDFLARE_API_TOKEN
   wrangler kv namespace create CONTENT_QUEUE  # paste returned id into wrangler.toml
   wrangler kv namespace create POSTED_LOG     # paste returned id into wrangler.toml
   ```
2. Sign up at https://buffer.com (free tier = 3 channels + 10 queued posts/channel). Connect X (@eidetic_works), LinkedIn (the brand page), Substack (the newsletter).
3. Get Buffer access token + profile IDs:
   ```sh
   # From buffer.com/developers/api → create an app → access token
   wrangler secret put BUFFER_ACCESS_TOKEN
   # From buffer.com/profile (each channel) → profile_id in URL
   wrangler secret put BUFFER_PROFILE_X
   wrangler secret put BUFFER_PROFILE_LINKEDIN
   wrangler secret put BUFFER_PROFILE_SUBSTACK
   ```
4. Set admin secret for the dashboard:
   ```sh
   wrangler secret put ADMIN_SECRET     # paste a random hex string
   ```
5. Deploy:
   ```sh
   wrangler deploy
   ```

## After setup

```sh
# Enqueue a draft
curl -X POST https://growth-scheduler.morning-lake-f944.workers.dev/queue \
  -H "Authorization: Bearer $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"channel":"buffer","target":"x","text":"shipped v0.0.62 today: <feature>"}'

# Inspect the queue
curl -H "Authorization: Bearer $ADMIN_SECRET" \
  https://growth-scheduler.morning-lake-f944.workers.dev/queue

# Dashboard
curl -H "Authorization: Bearer $ADMIN_SECRET" \
  https://growth-scheduler.morning-lake-f944.workers.dev/growth
```

## Cron schedule

| Cron | UTC | What |
|---|---|---|
| `13 * * * *` | every hour at :13 | Process buffer + x-native queue, cap 1/hour |
| `27 13 * * *` | daily 13:27 (~9am EST) | LinkedIn slot marker (cap enforced via cap=1) |
| `33 6 * * 0` | Sunday 06:33 | Auto-generate weekly digest → enqueue Substack draft |

## Per-entry shape

```jsonc
{
  "channel": "buffer",         // 'buffer' (recommended) | 'x-native'
  "target": "x",               // for channel=buffer: 'x' | 'linkedin' | 'substack'
  "text": "the post content",
  "thread": null,              // [str, str, ...] for X threads (buffer only)
  "scheduled_for": null        // optional unix ms; cron skips until then
}
```

## Why Buffer first

| Option | Channels | Cost | Setup time | Notes |
|---|---|---|---|---|
| **Buffer (free)** | X + LinkedIn + Substack + more | $0 | 10 min | 3 channels, 10 queued/ch free forever; covers the 3 we care about |
| Typefully | X only | $0 → $12.50/mo | 5 min | Best X-native thread UX; LinkedIn requires Pro |
| Own X API v2 | X only | $100/mo | 1 day (review) | Most owned; cron rate-limit headroom; cost prohibitive for a free tier launch |
| LinkedIn Marketing API | LinkedIn | $0 + review | weeks (gated) | Real review process; not viable for solo founder timeline |

After Buffer is live: X + LinkedIn + Substack are all posted by clock alone. Lokesh's job ends at "paste post into queue" (or our cron does it from SHIPPED.md delta).

## Adding a new adapter

```js
// worker.js
async function adapterTypefully(env, entry) {
  if (!env.TYPEFULLY_API_KEY) throw new Error("TYPEFULLY_API_KEY not set");
  const res = await fetch("https://api.typefully.com/v1/drafts/", {
    method: "POST",
    headers: { "Authorization": `Bearer ${env.TYPEFULLY_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({ content: entry.text, threadify: !!entry.thread }),
  });
  if (!res.ok) throw new Error(`Typefully: HTTP ${res.status}`);
  const body = await res.json();
  return { provider_id: body.id, status: res.status };
}

const ADAPTERS = { buffer: adapterBuffer, "x-native": adapterXNative, typefully: adapterTypefully };
```
