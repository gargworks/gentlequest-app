# Operator steps: Provision Buffer for GentleQuest X + FB distribution

## Why
The distribution officer pipeline (in ai-mvp-backend) can auto-post to X and
Facebook via Buffer, but the Buffer account for GentleQuest isn't provisioned
yet. The config calls it "Buffer C — not yet provisioned."

## Steps (5 min)

### 1. Create Buffer account
- Go to https://buffer.com → Sign up
- Use email: `gentlequest@eidetic.works` (or `buffer@eidetic.works`)
- This is the "Buffer C" account per `brand_identity_routing.json`

### 2. Connect channels
- In Buffer, go to **Settings → Channels**
- Connect **X/Twitter** → authorize as `@gentlequest`
- Connect **Facebook Page** → create or connect a GentleQuest Facebook page
- (Optional) Connect **Instagram** → `@gentlequest` if it exists

### 3. Get Buffer API key
- Go to https://publish.buffer.com/settings/api
- Copy the **Access Token** (it's a long string starting with something like `1/`)

### 4. Get channel IDs
Run this with your Buffer access token:
```bash
curl -H 'Authorization: Bearer YOUR_BUFFER_TOKEN' \
  -d '{"query":"{channels{id service}}"}' \
  https://api.buffer.com/graphql
```
Note the channel IDs for X and Facebook.

### 5. Set as Cloudflare Worker secrets
```bash
cd ~/ai-mvp-backend/workers/growth-scheduler
npx wrangler secret put BUFFER_API_KEY    # paste Buffer token
npx wrangler secret put BUFFER_CHANNEL_X  # paste X channel ID
npx wrangler secret put BUFFER_CHANNEL_FB # paste FB channel ID
```

### 6. Tell me "done"
I'll verify the worker can post and set up the auto-posting schedule for
each short as it goes live on YouTube.

## What happens after
- Each time a GQ short publishes on YouTube, a matching post auto-fires to
  @gentlequest on X and the GentleQuest Facebook page
- Posts include the YouTube link + a short hook from the pinned comments
- The distribution officer pipeline handles classification + safety checks
