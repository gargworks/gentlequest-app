#!/bin/bash
# GentleQuest blog staggered publisher
# Moves one scheduled post per day from content/scheduled/ to content/blog/
# Then rebuilds and deploys the landing page (which includes the blog)

set -e

# launchd runs with a minimal PATH that lacks node/npx/wrangler, so the
# deploy step silently fails when this runs on a schedule rather than by hand.
export PATH="$HOME/.nvm/versions/node/v22.18.0/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.npm-global/bin"

BLOG_DIR="/Users/lokeshgarg/gentlequest/gentlequest-blog/src/content/blog"
SCHEDULED_DIR="/Users/lokeshgarg/gentlequest/gentlequest-blog/src/content/scheduled"
LANDING_DIR="/Users/lokeshgarg/gentlequest/landing-page"
LOG_FILE="/Users/lokeshgarg/Library/Logs/gq_blog_staggered.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if there are scheduled posts
if [ ! -d "$SCHEDULED_DIR" ] || [ -z "$(ls -A "$SCHEDULED_DIR" 2>/dev/null)" ]; then
    log "No scheduled posts found. Exiting."
    exit 0
fi

# Get today's date in YYYY-MM-DD format
TODAY=$(date -u +%Y-%m-%d)

# Get the oldest scheduled post (by pubDate) that is due today or earlier
# Read the pubDate from frontmatter and pick the earliest that has reached its pubDate
OLDEST_POST=""
OLDEST_DATE="9999-99-99"

for post in "$SCHEDULED_DIR"/*.md; do
    [ -e "$post" ] || continue
    pub_date=$(grep "^pubDate:" "$post" | head -1 | sed 's/pubDate: *//' | tr -d '"')
    # Only consider posts whose pubDate is today or earlier
    if [[ "$pub_date" < "$TODAY" || "$pub_date" == "$TODAY" ]]; then
        if [ "$pub_date" \< "$OLDEST_DATE" ]; then
            OLDEST_DATE="$pub_date"
            OLDEST_POST="$post"
        fi
    fi
done

if [ -z "$OLDEST_POST" ]; then
    log "No scheduled posts due yet (today=$TODAY). Exiting."
    exit 0
fi

POST_NAME=$(basename "$OLDEST_POST")
log "Publishing: $POST_NAME (pubDate: $OLDEST_DATE)"

# Move the post to the blog directory
mv "$OLDEST_POST" "$BLOG_DIR/"
log "Moved $POST_NAME to blog/"

# Rebuild and deploy
log "Rebuilding landing page + blog..."
cd "$LANDING_DIR"
npm run build >> "$LOG_FILE" 2>&1

log "Deploying to Cloudflare Pages..."
# --branch=main is load-bearing: without it wrangler infers the current git
# branch and ships a PREVIEW deploy, so production never actually updates.
npx wrangler pages deploy dist --project-name=gentlequest-www --branch=main --commit-dirty=true >> "$LOG_FILE" 2>&1

log "Done. Published $POST_NAME"

# Count remaining scheduled posts
REMAINING=$(ls -1 "$SCHEDULED_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
log "Remaining scheduled posts: $REMAINING"

if [ "$REMAINING" -eq 0 ]; then
    log "All scheduled posts published. Blog staggering complete."
fi
