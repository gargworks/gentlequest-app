# Operator Card — GentleQuest Autonomous Publisher Setup

**Date:** 2026-06-26
**Time needed:** ~15 minutes
**Goal:** Make GentleQuest marketing run itself for months with zero daily effort

---

## What's already done (no action needed)

- 5 SEO blog posts published on www.gentlequest.app/blog (live now)
- 30 tweets + 5 LinkedIn posts pre-written in content queue
- 3 Dev.to articles pre-written in content queue
- 1 IndieHackers post pre-written in content queue
- Buffer API verified working (Twitter + LinkedIn + Instagram connected)
- First test tweet successfully queued in Buffer
- launchd daemon installed (`com.gentlequest.autonomous-publisher`) — runs hourly, fires due content automatically
- YouTube shorts v7-v12 already uploaded (6 videos live)
- YouTube shorts v13-v18 metadata added, ready to upload

---

## What needs your 15 minutes

### Item 1: Dev.to API key (2 min)

**Why:** Enables auto-publishing articles to Dev.to (3 articles queued)

1. Go to https://dev.to/settings/extensions
2. Scroll to "DEV Community API Keys"
3. Click "Generate API Key"
4. Copy the key
5. Run this in terminal (replace `YOUR_KEY`):
```bash
security add-generic-password -a "lokeshgarg" -s "devto-api-key" -w "YOUR_KEY"
```

### Item 2: YouTube re-auth (3 min)

**Why:** YouTube token has wrong scopes. Need to re-auth to upload v13-v18.

1. Run in terminal:
```bash
python3 /Users/lokeshgarg/gentlequest/marketing/shorts/upload_youtube.py v13_weekly v14_journal_chips v15_breathing v16_compliance v17_contacts v18_honest --privacy unlisted
```
2. Browser will open asking for Google OAuth consent
3. Click "Allow" for YouTube upload permissions
4. 6 new shorts will upload automatically (~2 min total)

### Item 3: Reddit API app (5 min)

**Why:** Enables auto-posting comments to Reddit via API (no browser automation needed, no ban risk)

1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app"
3. Fill in:
   - **name:** `gentlequest-publisher`
   - **App type:** select "script"
   - **description:** `Autonomous publisher for GentleQuest`
   - **about url:** `https://gentlequest.app`
   - **redirect uri:** `http://localhost:8080`
4. Click "create app"
5. Copy the **client ID** (short string under the app name) and **client secret**
6. Run in terminal (replace values):
```bash
security add-generic-password -a "lokeshgarg" -s "reddit-client-id" -w "YOUR_CLIENT_ID"
security add-generic-password -a "lokeshgarg" -s "reddit-client-secret" -w "YOUR_CLIENT_SECRET"
```
7. Get a refresh token (one-time, I'll handle this after you do steps 1-6)

### Item 4: IndieHackers login (2 min)

**Why:** Browser automation needs you logged in to IH once

1. Go to https://www.indiehackers.com in your browser
2. Log in (or sign up if you don't have an account)
3. That's it — the publisher will use your browser session

### Item 5: Verify the daemon is running (1 min)

```bash
# Check it's loaded
launchctl list | grep gentlequest.autonomous

# Check status
python3 /Users/lokeshgarg/gentlequest/scripts/gq_autonomous_publisher.py --status

# Check the log
tail -5 ~/Library/Logs/gq_autonomous_publisher.log
```

---

## After setup: what happens automatically

| Channel | Frequency | Content queued | Duration |
|---------|-----------|---------------|----------|
| Twitter/X | 2x/day | 30 tweets | 15 days |
| LinkedIn | 1x/day | 5 posts | 5 days |
| Dev.to | 1/week | 3 articles | 3 weeks |
| YouTube | 6 videos (one-time) | v13-v18 | immediate |
| Reddit | (after API setup) | comments from queue | ongoing |
| IndieHackers | 1 post (one-time) | already written | immediate |
| Blog | 5 posts (live now) | SEO indexed over 2-4 weeks | ongoing |

**The daemon runs hourly.** It checks the queue, finds items that are due, and publishes them. No agent nudging needed. No daily effort needed.

---

## To add more content later

Just edit `/Users/lokeshgarg/gentlequest/scripts/gq_content_queue.json` and add items. The daemon will pick them up automatically on the next hourly run.

Format:
```json
{
  "id": "unique_id",
  "channel": "buffer",  // or "devto", "reddit", "indiehackers"
  "target": "twitter",  // or "linkedin", "instagram"
  "text": "Your post text",
  "scheduled_for": "2026-07-15T13:00:00Z",
  "status": "pending"
}
```
