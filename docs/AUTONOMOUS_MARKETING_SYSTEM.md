# GentleQuest Autonomous Marketing System

> Set-and-forget marketing pipeline. Three daemons + Gemini 2.5 Flash content generation.
> Runs for months with zero daily effort. No agent nudging needed.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GEMINI 2.5 FLASH (free tier)                  │
│         Generates new content when queue runs low                │
└──────────────┬──────────────────────────────────┬───────────────┘
               │ tweets, posts, articles           │ blog posts
               ▼                                  ▼
┌──────────────────────┐          ┌───────────────────────────────┐
│  gq_content_queue.json│         │  content/scheduled/*.md       │
│  (39+ pre-written +   │         │  (staggered blog posts)       │
│   Gemini-generated)   │         │                               │
└──────────┬───────────┘          └──────────┬────────────────────┘
           │                                 │
           ▼                                 ▼
┌──────────────────────┐          ┌───────────────────────────────┐
│  autonomous-publisher │         │  blog-staggered               │
│  (launchd, hourly)    │         │  (launchd, daily 2pm UTC)     │
│                       │         │                               │
│  Reads queue          │         │  Moves 1 post/day             │
│  Fires due items      │         │  from scheduled/ to blog/     │
│  Auto-generates if    │         │  Rebuilds Astro site          │
│  queue < 5 pending    │         │  Deploys to CF Pages          │
└──┬──────┬──────┬──────┘          └───────────────────────────────┘
   │      │      │
   ▼      ▼      ▼
┌──────┐┌──────┐┌──────┐
│Buffer││Dev.to││Reddit│
│ API  ││ API  ││ API  │
└──┬───┘└──────┘└──────┘
   │
   ├──→ Twitter/X (2x/day)
   ├──→ LinkedIn (1x/day)
   └──→ Instagram (available)
```

---

## Components

### 1. Autonomous Publisher Daemon

**Launchd label:** `com.gentlequest.autonomous-publisher`
**Schedule:** Every hour at minute 0
**Script:** `scripts/gq_autonomous_publisher.py --once`
**Log:** `~/Library/Logs/gq_autonomous_publisher.log`

**What it does:**
1. Reads `gq_content_queue.json`
2. Finds items where `scheduled_for` time has passed
3. Publishes each item to its target channel
4. If pending items < 5, calls Gemini 2.5 Flash to generate 10 new items
5. Saves state to `gq_publisher_state.json`

**Channels:**

| Channel | Target | API | Credential location |
|---------|--------|-----|---------------------|
| Buffer | Twitter/X | GraphQL API | macOS keychain (`buffer-personal-pipeline`) |
| Buffer | LinkedIn | GraphQL API | Same Buffer token |
| Buffer | Instagram | GraphQL API | Same Buffer token |
| Dev.to | Dev.to articles | REST API | macOS keychain (`devto-api-key`) — **needs operator setup** |
| Reddit | r/ADHD, r/Anxiety, r/Habits | OAuth2 API | macOS keychain (`reddit-client-id`) — **needs operator setup** |
| IndieHackers | IH groups | Browser automation | Browser session — **needs operator login** |

### 2. Blog Staggered Publisher

**Launchd label:** `com.gentlequest.blog-staggered`
**Schedule:** Daily at 14:00 UTC (10am EST)
**Script:** `scripts/gq_blog_staggered.sh`
**Log:** `~/Library/Logs/gq_blog_staggered.log`

**What it does:**
1. Finds the oldest post in `gentlequest-blog/src/content/scheduled/`
2. Moves it to `gentlequest-blog/src/content/blog/`
3. Rebuilds the Astro site (`landing-page/npm run build`)
4. Deploys to Cloudflare Pages (`gentlequest-www` project)
5. Repeats daily until `scheduled/` is empty

**Current schedule:**

| Date | Post | Status |
|------|------|--------|
| June 27 | adhd-paralysis-why-you-cant-start | LIVE |
| June 28 | night-anxiety-why-your-brain-wont-shut-off | scheduled |
| June 29 | overwhelmed-start-with-one-breath | scheduled |
| June 30 | productivity-guilt-how-to-let-it-go | scheduled |
| July 1 | why-just-do-it-doesnt-work-adhd | scheduled |

Gemini-generated blog posts are automatically added to `scheduled/` by the autonomous publisher, so the pipeline keeps producing new blog posts indefinitely.

### 3. YouTube Shorts

**Script:** `marketing/shorts/upload_youtube.py`
**Token:** `marketing/shorts/youtube_token.json`
**Status:** 6 shorts (v7-v12) uploaded. 6 more (v13-v18) ready — **needs OAuth re-auth**.

---

## Content Generation

### How it works

The publisher daemon checks the queue on every hourly run. When pending items drop below 5, it calls Gemini 2.5 Flash to generate 10 new items with staggered schedules.

### Content types and rotation

**Tweets** (weight: 3)
- 270 chars max, vulnerable/authentic tone
- 20 rotating topics (ADHD paralysis, streaks, night anxiety, grounding, guilt, overwhelm, body doubling, burnout, etc.)
- First person perspective ("I", "my")
- No links (publisher appends if needed)
- Scheduled 4 hours apart (6 tweets/day)

**LinkedIn posts** (weight: 2)
- 150-300 words, professional but authentic
- 8 rotating topics (neurodivergent-first design, anti-productivity, mood-first app, etc.)
- Hashtags: #mentalhealth #adhd #wellness
- Scheduled 24 hours apart (1 post/day)

**Blog posts** (weight: 1)
- 800-1200 words, markdown format
- 10 rotating topics
- Saved to `content/scheduled/` — picked up by blog-staggered daemon
- Scheduled 2 days apart

**Dev.to articles** (weight: 1)
- 1000-1500 words, building-in-public perspective
- Tags: mentalhealth, adhd, productivity, wellness
- Scheduled 7 days apart (1 article/week)

### Gemini API details

- **Model:** `gemini-2.5-flash` (free tier, ~$0 cost at this volume)
- **Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`
- **Token limits:** 1000 (tweets), 2000 (LinkedIn), 4000 (blog), 6000 (Dev.to)
- **Temperature:** 0.9 (high creativity)
- **API key:** loaded from `/Users/lokeshgarg/ai-mvp-backend/.env` (`GEMINI_API_KEY`)

> **Note:** Gemini 2.5 Flash is a thinking model. It uses ~800 tokens for internal reasoning before generating output. Token limits must be set high enough to accommodate both thinking and output. This is why tweets need 1000 tokens even though the output is only ~200 chars.

---

## Content Queue Format

File: `scripts/gq_content_queue.json`

```json
{
  "items": [
    {
      "id": "tweet_001",
      "channel": "buffer",
      "target": "twitter",
      "text": "Most productivity apps make ADHD worse...",
      "scheduled_for": "2026-06-27T13:00:00Z",
      "status": "pending"
    },
    {
      "id": "linkedin_001",
      "channel": "buffer",
      "target": "linkedin",
      "text": "Most productivity apps make ADHD worse...\n\nThey demand more...",
      "scheduled_for": "2026-06-27T13:30:00Z",
      "status": "pending"
    },
    {
      "id": "devto_001",
      "channel": "devto",
      "title": "Why I Built an Anti-Productivity App",
      "body_markdown": "Standard productivity apps make my ADHD worse...",
      "tags": ["mentalhealth", "adhd", "productivity", "flutter"],
      "published": true,
      "scheduled_for": "2026-06-28T14:00:00Z",
      "status": "pending"
    }
  ]
}
```

**Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Unique identifier (used for dedup) |
| `channel` | yes | `buffer`, `devto`, `reddit`, `indiehackers`, or `blog` |
| `target` | for buffer | `twitter`, `linkedin`, or `instagram` |
| `text` | for buffer | Post text (280 char limit for Twitter) |
| `title` | for devto | Article title |
| `body_markdown` | for devto | Article body in markdown |
| `tags` | for devto | Array of tags |
| `scheduled_for` | yes | ISO 8601 datetime (UTC, `Z` suffix) |
| `status` | yes | `pending`, `posted`, or `failed` |
| `generated` | optional | `true` if Gemini-generated (for tracking) |

---

## State Files

| File | Purpose |
|------|---------|
| `scripts/gq_content_queue.json` | Content queue (all items) |
| `scripts/gq_publisher_state.json` | Posted IDs + last run timestamp |
| `scripts/gq_publisher_log.jsonl` | Append-only log of every publish attempt |
| `~/Library/Logs/gq_autonomous_publisher.log` | launchd stdout/stderr |
| `~/Library/Logs/gq_blog_staggered.log` | Blog staggered daemon log |

---

## CLI Commands

```bash
# Check queue status
python3 scripts/gq_autonomous_publisher.py --status

# Process queue once (publishes due items, auto-generates if low)
python3 scripts/gq_autonomous_publisher.py --once

# Dry run (show what would fire without posting)
python3 scripts/gq_autonomous_publisher.py --dry-run

# Force-generate new content now
python3 scripts/gq_autonomous_publisher.py --generate

# Generate a specific number of items
python3 scripts/gq_autonomous_publisher.py --generate --generate-count 20
```

---

## Launchd Management

```bash
# Check daemons are loaded
launchctl list | grep gentlequest

# Reload autonomous publisher
launchctl unload ~/Library/LaunchAgents/com.gentlequest.autonomous-publisher.plist
launchctl load ~/Library/LaunchAgents/com.gentlequest.autonomous-publisher.plist

# Reload blog staggered
launchctl unload ~/Library/LaunchAgents/com.gentlequest.blog-staggered.plist
launchctl load ~/Library/LaunchAgents/com.gentlequest.blog-staggered.plist

# Check logs
tail -20 ~/Library/Logs/gq_autonomous_publisher.log
tail -20 ~/Library/Logs/gq_blog_staggered.log
```

---

## Credentials

All credentials are stored in macOS keychain or `.env` files. No secrets in the repo.

| Service | Keychain name | Status |
|---------|---------------|--------|
| Buffer API | `buffer-personal-pipeline` | LIVE (verified) |
| Dev.to API | `devto-api-key` | **Needs operator setup** |
| Reddit client ID | `reddit-client-id` | **Needs operator setup** |
| Reddit client secret | `reddit-client-secret` | **Needs operator setup** |
| Reddit refresh token | `reddit-refresh-token` | **Needs operator setup** |
| Gemini API | `.env` file (`GEMINI_API_KEY`) | LIVE (verified) |
| YouTube OAuth | `marketing/shorts/youtube_token.json` | **Needs re-auth** |

### Operator setup (one-time, ~15 min)

See: `docs/ops/OPERATOR_CARD_AUTONOMOUS_PUBLISHER_2026-06-26.md`

---

## Buffer API Details

The publisher uses Buffer's GraphQL API (v1 REST API is deprecated).

**Endpoint:** `https://api.buffer.com/graphql`
**Auth:** `Authorization: Bearer <token>`

**Organization ID:** `6a1a4298084c61eaab66f567`

**Channel IDs:**

| Channel | ID |
|---------|-----|
| Twitter/X | `6a1a4446c687a22dd43f47ee` |
| LinkedIn | `6a1a44c9c687a22dd43f4ad3` |
| Instagram | `6a1a6bbcc687a22dd43fd1cf` |

**Create post mutation:**

```graphql
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    __typename
    ... on PostActionSuccess { post { id } }
    ... on NotFoundError { message }
    ... on UnauthorizedError { message }
    ... on UnexpectedError { message }
    ... on RestProxyError { message link code }
    ... on LimitReachedError { message }
    ... on InvalidInputError { message }
  }
}
```

**Variables:**

```json
{
  "input": {
    "channelId": "<channel_id>",
    "schedulingType": "automatic",
    "mode": "addToQueue",
    "assets": [],
    "text": "Post text"
  }
}
```

---

## Blog Architecture

The blog is built with [Astro](https://astro.build) and deployed to Cloudflare Pages.

**Repo structure:**
```
gentlequest/
├── gentlequest-blog/           # Astro blog
│   ├── src/content/
│   │   ├── blog/               # Live posts (rendered)
│   │   └── scheduled/          # Scheduled posts (not rendered)
│   └── dist/                   # Build output
├── landing-page/               # Main landing page
│   ├── dist/                   # Build output (includes blog/)
│   └── package.json            # Build script copies blog to landing-page/dist/blog/
└── scripts/
    ├── gq_autonomous_publisher.py
    ├── gq_blog_staggered.sh
    └── gq_content_queue.json
```

**Build process:**
1. `cd landing-page && npm run build`
2. Vite builds the landing page
3. Script runs `cd ../gentlequest-blog && npm run build`
4. Script copies `gentlequest-blog/dist/*` to `landing-page/dist/blog/`
5. `npx wrangler pages deploy dist --project-name=gentlequest-www`

**Cloudflare Pages project:** `gentlequest-www`
**Domains:** `www.gentlequest.app`, `gentlequest-www.pages.dev`

---

## Content Backlog

### Pre-written (39 items)

| Type | Count | Schedule |
|------|-------|----------|
| Tweets | 30 | June 27 - July 11 (2x/day) |
| LinkedIn posts | 5 | June 27 - July 5 (1x/day) |
| Dev.to articles | 3 | June 28, July 1, July 4 (1x/week) |
| IndieHackers post | 1 | June 27 (one-time) |

### Gemini-generated (ongoing)

When the queue drops below 5 pending items, the daemon generates 10 new items. At the current posting rate (2 tweets/day + 1 LinkedIn post/day + 1 blog post/2 days + 1 Dev.to article/week), the system consumes ~4 items/day. Generation happens every ~2.5 days automatically.

**Estimated monthly output:**
- ~60 tweets
- ~30 LinkedIn posts
- ~15 blog posts
- ~4 Dev.to articles

All at ~$0 cost (Gemini 2.5 Flash free tier).

---

## Safety and Guardrails

### Content safety
- All Gemini-generated content follows the GentleQuest brand voice (vulnerable, authentic, anti-productivity)
- No crisis/suicide content is generated (topics are about coping techniques, not crisis response)
- No competitor mentions (Woebot, Wysa, Headspace, BetterHelp are never referenced)
- No medical advice (content is peer-perspective, not professional advice)

### Rate limiting
- 5-second delay between posts within a single run
- Hourly cron (not more frequent)
- Buffer has its own rate limiting per channel

### Error handling
- Failed items are marked `status: "failed"` with error message
- Failed items are not retried automatically (to avoid spam)
- All actions logged to `gq_publisher_log.jsonl`
- launchd logs to `~/Library/Logs/gq_autonomous_publisher.log`

### Kill switches
- `launchctl unload ~/Library/LaunchAgents/com.gentlequest.autonomous-publisher.plist` — stops the publisher
- `launchctl unload ~/Library/LaunchAgents/com.gentlequest.blog-staggered.plist` — stops the blog staggered
- Delete `gq_content_queue.json` to clear all pending content
- Set `status: "posted"` on items to skip them

---

## File Inventory

| File | Purpose |
|------|---------|
| `scripts/gq_autonomous_publisher.py` | Main publisher daemon (880 lines) |
| `scripts/gq_content_queue.json` | Content queue (39+ items) |
| `scripts/gq_blog_staggered.sh` | Blog staggered publisher script |
| `docs/ops/OPERATOR_CARD_AUTONOMOUS_PUBLISHER_2026-06-26.md` | One-time setup instructions |
| `docs/GTM_CONTENT_QUEUE.md` | Pre-written content for manual channels |
| `docs/AUTONOMOUS_MARKETING_SYSTEM.md` | This document |
| `~/Library/LaunchAgents/com.gentlequest.autonomous-publisher.plist` | launchd config (hourly) |
| `~/Library/LaunchAgents/com.gentlequest.blog-staggered.plist` | launchd config (daily) |
| `gentlequest-blog/src/content/scheduled/` | Staged blog posts |
| `gentlequest-blog/src/content/blog/` | Live blog posts |
| `marketing/shorts/upload_youtube.py` | YouTube shorts uploader |
| `marketing/shorts/youtube_token.json` | YouTube OAuth token |

---

## Troubleshooting

### "No pending items" but items exist
Items may have future `scheduled_for` dates. Check with `--status`.

### Buffer posts not appearing
1. Check Buffer token: `security find-generic-password -s "buffer-personal-pipeline" -w`
2. Check Buffer dashboard: https://publish.buffer.com
3. Check log: `tail -20 ~/Library/Logs/gq_autonomous_publisher.log`

### Gemini generation fails
1. Check API key: `grep GEMINI_API_KEY /Users/lokeshgarg/ai-mvp-backend/.env`
2. Test manually: `python3 scripts/gq_autonomous_publisher.py --generate --generate-count 1`
3. Gemini free tier has rate limits — generation may fail during peak hours

### Blog posts not deploying
1. Check blog-staggered log: `tail -20 ~/Library/Logs/gq_blog_staggered.log`
2. Check if scheduled posts exist: `ls gentlequest-blog/src/content/scheduled/`
3. Run manually: `bash scripts/gq_blog_staggered.sh`

### Daemon not running
1. Check: `launchctl list | grep gentlequest`
2. Reload: `launchctl unload && launchctl load ~/Library/LaunchAgents/com.gentlequest.*.plist`
3. Check system logs: `log show --predicate 'process == "python3"' --last 1h`
