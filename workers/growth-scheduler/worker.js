// growth-scheduler — multi-channel content publisher + weekly-digest generator.
//
// Reads queued posts from CONTENT_QUEUE KV, fires per-channel adapters on cron,
// logs to ANALYTICS for funnel measurement, deduplicates via POSTED_LOG.
//
// HTTP endpoints (admin-only):
//   POST /queue        — enqueue a draft. Body: {channel, text, scheduled_for?, thread?}
//   GET  /queue        — list pending drafts.
//   GET  /growth       — dashboard JSON: queue depth, posted count, last error.
//   GET  /healthz      — 200 OK + version stamp.
//
// Cron entrypoints (declared in wrangler.toml):
//   "13 * * * *"     — hourly: process X queue (rate-limited).
//   "27 13 * * *"    — daily ~9am EST: process LinkedIn queue.
//   "33 6 * * 0"     — Sunday: run weekly-digest generator.
//
// After Lokesh sets BUFFER_ACCESS_TOKEN + the per-channel profile IDs (one
// signup at buffer.com, ~10 min), posting becomes a function of time.

const VERSION = "0.0.1";

// ─── Shared helpers ────────────────────────────────────────────────────────

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

function jsonResponse(body, status = 200, extra = {}) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { "Content-Type": "application/json", ...CORS, ...extra },
  });
}

function noContent() {
  return new Response(null, { status: 204, headers: CORS });
}

function logEvent(env, eventName, attrs = {}) {
  if (!env.ANALYTICS || typeof env.ANALYTICS.writeDataPoint !== "function") {
    return;
  }
  try {
    env.ANALYTICS.writeDataPoint({
      blobs: [eventName, attrs.channel || "", attrs.id || ""],
      doubles: [1],
      indexes: [eventName],
    });
  } catch (err) {
    console.warn("analytics writeDataPoint failed:", err && err.message);
  }
}

function requireAdmin(request, env) {
  const expected = env.ADMIN_SECRET ? `Bearer ${env.ADMIN_SECRET}` : null;
  const got = request.headers.get("authorization") || "";
  if (!expected || got !== expected) {
    return jsonResponse({ error: "unauthorized" }, 401);
  }
  return null;
}

function newDraftId() {
  // Sortable + opaque. Cron + queue iterate keys in lex order so newer drafts
  // surface after older ones for the same channel.
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

// ─── KV layout ─────────────────────────────────────────────────────────────
//
// CONTENT_QUEUE:
//   key: `queue:<channel>:<draftId>`
//   value: JSON { id, channel, text, scheduled_for?, thread?, created_at, status }
//
// POSTED_LOG:
//   key: `posted:<channel>:<draftId>`
//   value: JSON { id, channel, posted_at, provider_id, provider_response_status }
//
// Both have a 60-day TTL by default so noisy keyspace doesn't accumulate.

const QUEUE_KEY = (channel, id) => `queue:${channel}:${id}`;
const POSTED_KEY = (channel, id) => `posted:${channel}:${id}`;
const TTL_60_DAYS = 60 * 24 * 60 * 60;

async function enqueueDraft(env, draft) {
  const id = draft.id || newDraftId();
  const channel = (draft.channel || env.DEFAULT_CHANNEL || "buffer").toLowerCase();
  const entry = {
    id,
    channel,
    text: draft.text,
    scheduled_for: draft.scheduled_for || null,
    thread: Array.isArray(draft.thread) ? draft.thread : null,
    target: draft.target || null, // e.g. "x" | "linkedin" | "substack" when channel=buffer
    created_at: Date.now(),
    status: "pending",
  };
  await env.CONTENT_QUEUE.put(QUEUE_KEY(channel, id), JSON.stringify(entry), {
    expirationTtl: TTL_60_DAYS,
  });
  logEvent(env, "growth_enqueue", { channel, id });
  return entry;
}

async function listQueue(env, channel = null) {
  const prefix = channel ? `queue:${channel}:` : "queue:";
  const list = await env.CONTENT_QUEUE.list({ prefix, limit: 200 });
  const out = [];
  for (const key of list.keys) {
    const raw = await env.CONTENT_QUEUE.get(key.name);
    if (raw) {
      try {
        out.push(JSON.parse(raw));
      } catch {
        // skip corrupt entry
      }
    }
  }
  return out;
}

async function markPosted(env, entry, providerResult) {
  // Delete the queue entry + write the posted log entry atomically-enough.
  // KV is eventually consistent; the idempotency check below catches the
  // edge case where a duplicate cron sees the queue entry mid-flight.
  await env.CONTENT_QUEUE.delete(QUEUE_KEY(entry.channel, entry.id));
  await env.POSTED_LOG.put(
    POSTED_KEY(entry.channel, entry.id),
    JSON.stringify({
      id: entry.id,
      channel: entry.channel,
      target: entry.target,
      posted_at: Date.now(),
      provider_id: providerResult.provider_id || null,
      provider_status: providerResult.status,
    }),
    { expirationTtl: TTL_60_DAYS },
  );
  logEvent(env, "growth_posted", { channel: entry.channel, id: entry.id });
}

async function alreadyPosted(env, channel, id) {
  const got = await env.POSTED_LOG.get(POSTED_KEY(channel, id));
  return !!got;
}

// ─── Adapters ──────────────────────────────────────────────────────────────
//
// Each adapter is `async (env, entry) => { provider_id?, status }`.
// On non-2xx provider response, throw — the worker logs + leaves the queue
// entry in place for retry on the next cron tick.

async function adapterBuffer(env, entry) {
  if (!env.BUFFER_ACCESS_TOKEN) {
    throw new Error("BUFFER_ACCESS_TOKEN not set — see DISTRIBUTION_AUTOPILOT.md");
  }
  // Buffer profile selection: per target sub-channel.
  // entry.target lets ONE buffer adapter post to X, LinkedIn, or Substack —
  // selecting the right profile_id from secrets.
  const profileMap = {
    x: env.BUFFER_PROFILE_X,
    twitter: env.BUFFER_PROFILE_X,
    linkedin: env.BUFFER_PROFILE_LINKEDIN,
    substack: env.BUFFER_PROFILE_SUBSTACK,
  };
  const target = (entry.target || "x").toLowerCase();
  const profileId = profileMap[target];
  if (!profileId) {
    throw new Error(`No Buffer profile configured for target=${target}`);
  }

  // Buffer API v1 /updates/create.json. Form-encoded body, multi-value
  // `profile_ids[]` for fan-out (we use 1 profile per call here).
  const formBody = new URLSearchParams();
  formBody.set("access_token", env.BUFFER_ACCESS_TOKEN);
  formBody.append("profile_ids[]", profileId);
  formBody.set("text", entry.text);
  // Default: post to top of queue (Buffer's scheduled cadence picks the slot).
  // Set `now=true` for immediate post (rare; usually we want Buffer to space).
  // Set `scheduled_at` (unix sec) to pin a time.
  if (entry.scheduled_for) {
    formBody.set("scheduled_at", String(Math.floor(entry.scheduled_for / 1000)));
  }

  const res = await fetch("https://api.bufferapp.com/1/updates/create.json", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formBody,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || body.success === false) {
    throw new Error(`Buffer ${target}: HTTP ${res.status} ${JSON.stringify(body).slice(0, 200)}`);
  }
  const providerId = body.updates && body.updates[0] && body.updates[0].id;
  return { provider_id: providerId, status: res.status };
}

// X API v2 direct publisher — fallback when Buffer not configured.
// Requires Lokesh to enable Basic tier ($100/mo) or be on a grandfathered
// Free tier with write access. Most users will prefer Buffer; this exists
// for "All of these and more" coverage.
async function adapterXNative(env, entry) {
  if (!env.X_BEARER_TOKEN) {
    throw new Error("X_BEARER_TOKEN not set");
  }
  const text = entry.text;
  if (entry.thread && entry.thread.length > 1) {
    throw new Error("X-native threading not implemented; use Buffer for threads");
  }
  const res = await fetch("https://api.x.com/2/tweets", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${env.X_BEARER_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(`X-native: HTTP ${res.status} ${JSON.stringify(body).slice(0, 200)}`);
  }
  return { provider_id: body.data && body.data.id, status: res.status };
}

// Dispatch table — keyed by entry.channel.
const ADAPTERS = {
  buffer: adapterBuffer,
  "x-native": adapterXNative,
};

async function publishEntry(env, entry) {
  // Idempotency guard against cron racing.
  if (await alreadyPosted(env, entry.channel, entry.id)) {
    return { skipped: true, reason: "already posted" };
  }
  const adapter = ADAPTERS[entry.channel];
  if (!adapter) {
    throw new Error(`Unknown channel: ${entry.channel}`);
  }
  const providerResult = await adapter(env, entry);
  await markPosted(env, entry, providerResult);
  return { posted: true, provider_id: providerResult.provider_id, status: providerResult.status };
}

// ─── Cron processors ───────────────────────────────────────────────────────

async function processChannel(env, channel, cap) {
  // Pull all queued entries for this channel, oldest first (queue key is
  // sortable by created_at via base36 timestamp prefix).
  const entries = await listQueue(env, channel);
  entries.sort((a, b) => a.created_at - b.created_at);
  let posted = 0;
  const errors = [];
  for (const entry of entries) {
    if (posted >= cap) break;
    if (entry.scheduled_for && entry.scheduled_for > Date.now()) {
      continue; // skip future-scheduled posts; cron will revisit.
    }
    try {
      const result = await publishEntry(env, entry);
      if (result.posted) posted++;
    } catch (err) {
      errors.push({ id: entry.id, error: err && err.message });
      logEvent(env, "growth_error", { channel, id: entry.id });
    }
  }
  return { channel, posted, attempted: entries.length, errors };
}

// Weekly-digest generator: reads recent commit log (via GitHub API) on
// SHIPPED.md + auto-enqueues a Substack draft. Cron-fires Sunday morning.
async function generateWeeklyDigest(env) {
  // Skip if a digest was already enqueued in the last 6 days (idempotency
  // against multiple Sunday firings or cron jitter).
  const recent = await listQueue(env, "buffer");
  const sixDaysAgo = Date.now() - 6 * 24 * 60 * 60 * 1000;
  const fresh = recent.find((e) =>
    e.target === "substack" && e.created_at > sixDaysAgo && e.text.startsWith("# Week of"),
  );
  if (fresh) {
    return { skipped: true, reason: `digest already enqueued at ${new Date(fresh.created_at).toISOString()}` };
  }
  // Pull last 7 days of commits on the daemon repo. Public unauth = 60 req/hr.
  const since = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
  const res = await fetch(
    `https://api.github.com/repos/eidetic-works/eidetic-daemon/commits?since=${encodeURIComponent(since)}&per_page=100`,
    {
      headers: { "Accept": "application/vnd.github+json", "User-Agent": "growth-scheduler/0.0.1" },
    },
  );
  if (!res.ok) {
    throw new Error(`github commits: HTTP ${res.status}`);
  }
  const commits = await res.json();
  const lines = commits
    .filter((c) => c && c.commit && c.commit.message)
    .map((c) => `- ${c.commit.message.split("\n")[0]} (${c.sha.slice(0, 7)})`);
  const now = new Date();
  const title = `Week of ${now.toISOString().slice(0, 10)} — what shipped`;
  const text = [
    `# ${title}`,
    "",
    `Auto-generated weekly digest. ${lines.length} commits landed this week.`,
    "",
    ...lines,
    "",
    "---",
    "Try it: eidetic.works — free tier, no signup.",
  ].join("\n");
  const draft = await enqueueDraft(env, {
    channel: "buffer",
    target: "substack",
    text,
  });
  return { generated: true, draft_id: draft.id, commit_count: lines.length };
}

// ─── Worker entrypoints ────────────────────────────────────────────────────

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/healthz") {
      return jsonResponse({ ok: true, service: "growth-scheduler", version: VERSION });
    }

    if (url.pathname === "/queue" && request.method === "POST") {
      const guard = requireAdmin(request, env);
      if (guard) return guard;
      let body;
      try {
        body = await request.json();
      } catch {
        return jsonResponse({ error: "invalid json" }, 400);
      }
      if (!body.text || typeof body.text !== "string") {
        return jsonResponse({ error: "text required" }, 400);
      }
      const entry = await enqueueDraft(env, body);
      return jsonResponse({ ok: true, entry }, 201);
    }

    if (url.pathname === "/queue" && request.method === "GET") {
      const guard = requireAdmin(request, env);
      if (guard) return guard;
      const channel = url.searchParams.get("channel");
      const entries = await listQueue(env, channel);
      return jsonResponse({ count: entries.length, entries });
    }

    if (url.pathname === "/growth" && request.method === "GET") {
      const guard = requireAdmin(request, env);
      if (guard) return guard;
      const all = await listQueue(env);
      const byChannel = {};
      for (const e of all) {
        byChannel[e.channel] = (byChannel[e.channel] || 0) + 1;
      }
      // Posted counts — KV list scan over POSTED_LOG. Cheap enough at expected scale.
      const postedList = await env.POSTED_LOG.list({ prefix: "posted:", limit: 1000 });
      const postedByChannel = {};
      for (const k of postedList.keys) {
        const parts = k.name.split(":"); // posted:<channel>:<id>
        if (parts.length >= 2) postedByChannel[parts[1]] = (postedByChannel[parts[1]] || 0) + 1;
      }
      return jsonResponse({
        version: VERSION,
        queue_depth_by_channel: byChannel,
        queue_depth_total: all.length,
        posted_total: postedList.keys.length,
        posted_by_channel: postedByChannel,
      });
    }

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS });
    }

    return new Response("not found", { status: 404 });
  },

  async scheduled(controller, env, _ctx) {
    // Fan out by which cron triggered (matched by minute pattern).
    const minute = new Date(controller.scheduledTime).getUTCMinutes();
    const hour = new Date(controller.scheduledTime).getUTCHours();
    const dow = new Date(controller.scheduledTime).getUTCDay();
    const out = [];

    // "13 * * * *" — hourly: X queue (cap 1/hour).
    if (minute === 13) {
      const cap = parseInt(env.X_PER_HOUR_CAP || "1", 10);
      out.push(await processChannel(env, "buffer", cap));
      out.push(await processChannel(env, "x-native", cap));
    }
    // "27 13 * * *" — daily LinkedIn (cap 1/day). Worker doesn't distinguish
    // target sub-channels at queue-key level so cap here is a soft hint;
    // adapter selects on entry.target. For now we just run buffer adapter
    // again; future: tag entries with allowed_after_ts to enforce time slots.
    if (minute === 27 && hour === 13) {
      out.push({ note: "LinkedIn slot hit; processChannel ran via hourly minute=13 as well" });
    }
    // "33 6 * * 0" — Sunday weekly-digest.
    if (minute === 33 && hour === 6 && dow === 0) {
      try {
        out.push({ weekly_digest: await generateWeeklyDigest(env) });
      } catch (err) {
        out.push({ weekly_digest_error: err && err.message });
        logEvent(env, "growth_digest_error");
      }
    }
    return out;
  },
};
