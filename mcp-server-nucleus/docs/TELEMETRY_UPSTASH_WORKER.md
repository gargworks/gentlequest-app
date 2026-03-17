# Nucleus Telemetry – Upstash + Cloudflare Worker Architecture (10k Users)

## Overview

This doc captures the "Mac + Cloudflare Worker + Upstash" architecture that lets Nucleus support ~10k users on a **$0 infra** footprint, before we ever move the backend to Oracle or any other VM.

## Final Architecture (10k Users)

```
Nucleus SDK
    ↓
Cloudflare Worker (always on)
    ↓          ↓
  Mac up?    Mac down?
    ↓             ↓
Tunnel →     Upstash Queue
localhost        ↓
  :4317      Mac wakes up
             → drain → :4317
```

- Nucleus SDK sends OTLP spans as HTTP POSTs to the Cloudflare Worker.
- Worker first tries the **Mac tunnel endpoint**; if reachable, it forwards directly.
- If the Mac/tunnel is down or times out, Worker **pushes spans into Upstash**.
- When the Mac comes back up, a **drain script** runs and flushes queued spans from Upstash into the local OTel Collector at `localhost:4317`.

## Cloudflare Worker Logic (Pseudocode)

```javascript
export default {
  async fetch(request, env) {
    const span = await request.arrayBuffer();

    try {
      // Try Mac tunnel first
      const res = await fetch("https://telemetry.nucleus.sh", {
        method: "POST",
        body: span,
        signal: AbortSignal.timeout(2000) // 2s timeout
      });
      if (res.ok) return new Response("ok");
    } catch {
      // Mac offline — buffer to Upstash
      await env.UPSTASH.rpush("nucleus:spans", span);
    }

    return new Response("queued");
  }
}
```

- OTLP payload remains opaque to the Worker; it just forwards raw bytes.
- 2s timeout keeps latency low and prevents Worker from stalling under Mac issues.
- Queue key convention: `nucleus:spans`.

## Free-Tier Capacity @ 10k Users

| Service            | Free limit        | Estimated usage @ 10k users |
|--------------------|-------------------|------------------------------|
| Cloudflare Worker  | 100k req/day      | ~10k req/day ✅              |
| Upstash Redis      | 10k cmd/day       | Only when Mac is off ✅      |
| Cloudflare Tunnel  | Unlimited         | Direct pass-through ✅       |

- Under normal conditions (Mac up), almost all traffic goes directly through the tunnel.
- Upstash is only used as a **fallback buffer**, keeping its command count very low.
- This keeps the entire architecture at **$0** well past 10k active users.

## Next Steps

- Implement the Worker and test against the current local OTel Collector.
- Add a small drain script on Mac startup to flush `nucleus:spans` into `localhost:4317`.
- Once we outgrow this, we can swap the Mac for an Oracle VM without changing the Worker or SDK.
