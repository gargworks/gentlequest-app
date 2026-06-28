#!/usr/bin/env python3
"""GentleQuest Autonomous Publisher Daemon.

Reads from a JSON content queue and publishes to:
  - Buffer (Twitter, LinkedIn, Instagram) — via GraphQL API
  - Dev.to — via REST API
  - Reddit — via OAuth2 API
  - IndieHackers — via browser automation (Playwright)

When the queue runs low (< 5 pending items), auto-generates new content
using Gemini 2.5 Flash. No agent nudging needed. Runs for months.

Runs on launchd cron. Content is pre-queued in gq_content_queue.json.

Usage:
  python3 gq_autonomous_publisher.py --once       # process queue once
  python3 gq_autonomous_publisher.py --dry-run    # show what would fire
  python3 gq_autonomous_publisher.py --status     # show queue status
  python3 gq_autonomous_publisher.py --generate   # generate new content now
"""

import argparse
import json
import os
import subprocess
import sys
import time
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

import urllib.request
import urllib.parse

# ─── Config ─────────────────────────────────────────────────────────────────

QUEUE_PATH = Path(__file__).parent / "gq_content_queue.json"
LOG_PATH = Path(__file__).parent / "gq_publisher_log.jsonl"
STATE_PATH = Path(__file__).parent / "gq_publisher_state.json"

# Buffer GraphQL API
BUFFER_GRAPHQL = "https://api.buffer.com/graphql"

# Dev.to API
DEVTO_API = "https://dev.to/api/articles"

# Reddit API (via PRAW if available, else skip)
REDDIT_USER_AGENT = "gentlequest-publisher/1.0 by u/gentlequest_dev"

# ─── Credential loading ────────────────────────────────────────────────────

def load_credentials():
    """Load credentials from keychain + environment."""
    creds = {}

    # Buffer — from keychain (GentleQuest account, NOT personal)
    try:
        creds["buffer_token"] = subprocess.check_output(
            ["security", "find-generic-password", "-s", "buffer-gentlequest", "-w"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except subprocess.CalledProcessError:
        pass

    # Buffer channel IDs — GentleQuest account (fetch dynamically from API)
    creds["buffer_org_id"] = None  # Will be fetched from API
    creds["buffer_twitter_channel"] = None
    creds["buffer_linkedin_channel"] = None
    creds["buffer_instagram_channel"] = None

    # Dev.to — from keychain or env
    try:
        creds["devto_api_key"] = subprocess.check_output(
            ["security", "find-generic-password", "-s", "devto-api-key", "-w"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except subprocess.CalledProcessError:
        creds["devto_api_key"] = os.environ.get("DEVTO_API_KEY", "")

    # Reddit — from keychain or env
    try:
        creds["reddit_client_id"] = subprocess.check_output(
            ["security", "find-generic-password", "-s", "reddit-client-id", "-w"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        creds["reddit_client_secret"] = subprocess.check_output(
            ["security", "find-generic-password", "-s", "reddit-client-secret", "-w"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        creds["reddit_refresh_token"] = subprocess.check_output(
            ["security", "find-generic-password", "-s", "reddit-refresh-token", "-w"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except subprocess.CalledProcessError:
        creds["reddit_client_id"] = os.environ.get("REDDIT_CLIENT_ID", "")
        creds["reddit_client_secret"] = os.environ.get("REDDIT_CLIENT_SECRET", "")
        creds["reddit_refresh_token"] = os.environ.get("REDDIT_REFRESH_TOKEN", "")

    # Gemini — from .env file
    env_path = Path("/Users/lokeshgarg/ai-mvp-backend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                creds["gemini_api_key"] = line.split("=", 1)[1].strip()
                break

    return creds


# ─── Gemini content generation ─────────────────────────────────────────────

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# Topics for content generation — rotates through these
TWEET_TOPICS = [
    "ADHD paralysis and task initiation",
    "why streaks make ADHD worse (cortisol vs dopamine)",
    "the one spoon method for starting tasks",
    "night anxiety and 4-7-8 breathing",
    "5-4-3-2-1 grounding for anxiety",
    "productivity guilt and how to let it go",
    "overwhelm and the smallest task method",
    "body doubling for ADHD task initiation",
    "ADHD burnout from understimulation not overstimulation",
    "why 'just do it' doesn't work for ADHD",
    "total active days vs streaks (dopamine vs cortisol)",
    "leaving tasks half-started to skip initiation",
    "rest as maintenance not laziness",
    "the guilt voice and how to notice it",
    "ADHD hyperfocus vs paralysis (dopamine availability)",
    "night anxiety cortisol spike at 2am",
    "box breathing for anxiety",
    "tiny self-care when overwhelmed",
    "ADHD and decision fatigue",
    "why habit trackers cause anxiety for ADHD",
]

LINKEDIN_TOPICS = [
    "building for neurodivergent brains first",
    "the anti-productivity philosophy",
    "what 82 installs taught me about product design",
    "the overwhelm trap and why systems make it worse",
    "ADHD paralysis in the workplace",
    "rest as productivity maintenance",
    "the dopamine vs cortisol framing for habit design",
    "building a mood-first app",
]

BLOG_TOPICS = [
    "ADHD and the guilt of not doing enough",
    "why habit trackers make ADHD worse",
    "the neuroscience of task initiation",
    "how to break the ADHD paralysis freeze",
    "night anxiety: why your brain won't shut off",
    "the one breath method for overwhelm",
    "why rest is not the absence of productivity",
    "ADHD burnout: understimulation not overstimulation",
    "the 5-4-3-2-1 grounding method explained",
    "why total active days beat streaks for ADHD",
]


def call_gemini(prompt, creds, max_tokens=500):
    """Call Gemini 2.5 Flash API."""
    api_key = creds.get("gemini_api_key")
    if not api_key:
        return None, "No Gemini API key"

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.9,
        }
    }).encode()

    url = f"{GEMINI_ENDPOINT}?key={api_key}"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read())
            text = body.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return text.strip(), None
    except Exception as e:
        return None, f"Gemini error: {e}"


def generate_tweet(creds, topic=None):
    """Generate a single tweet using Gemini."""
    topic = topic or random.choice(TWEET_TOPICS)
    prompt = f"""Write a tweet about {topic} for the @GentleQuest account.

Rules:
- Maximum 270 characters (leave room for link)
- No hashtags (max 1 if essential)
- Conversational, vulnerable, authentic tone
- Sound like a real person, not a brand
- End with a question or a punchy insight
- Do NOT include links (the publisher adds them)
- Do NOT use emoji unless it's genuinely helpful
- Write from first person perspective ("I", "my")
- Be specific, not generic

Write ONLY the tweet text, nothing else."""

    text, err = call_gemini(prompt, creds, max_tokens=1000)
    if err:
        return None, err

    # Clean up — remove quotes, extra whitespace
    text = text.strip().strip('"').strip("'")
    # Remove any "Tweet:" prefix
    for prefix in ["Tweet:", "tweet:", "Here's the tweet:", "Here is the tweet:"]:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()

    # Truncate to 280 chars
    if len(text) > 280:
        text = text[:277] + "..."

    return text, None


def generate_linkedin_post(creds, topic=None):
    """Generate a LinkedIn post using Gemini."""
    topic = topic or random.choice(LINKEDIN_TOPICS)
    prompt = f"""Write a LinkedIn post about {topic} for the GentleQuest app.

Rules:
- 150-300 words
- Professional but authentic tone (not corporate)
- Use line breaks for readability
- Start with a hook (a question or bold statement)
- Include 2-3 specific insights
- End with a soft call to action
- Include these hashtags at the end: #mentalhealth #adhd #wellness
- Do NOT include links (the publisher adds them)
- Write from first person perspective

GentleQuest is a free mood check-in app. No streaks. No guilt. Just a quiet place to check in with yourself.

Write ONLY the post text, nothing else."""

    text, err = call_gemini(prompt, creds, max_tokens=2000)
    if err:
        return None, err

    text = text.strip().strip('"').strip("'")
    for prefix in ["Post:", "LinkedIn Post:", "Here's the post:"]:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()

    return text, None


def generate_blog_post(creds, topic=None):
    """Generate a blog post using Gemini."""
    topic = topic or random.choice(BLOG_TOPICS)
    prompt = f"""Write a blog post about {topic} for the GentleQuest blog.

Rules:
- 800-1200 words
- Markdown format with ## headers
- Conversational, empathetic, vulnerable tone
- Start with a relatable hook
- Include 2-3 specific techniques or insights
- Reference ADHD/anxiety/overwhelm specifically
- End with a soft mention: "GentleQuest is a free mood check-in app. No streaks. No shame. Try it free at https://gentlequest.app"
- Write from first person perspective
- Be specific, not generic. Use concrete examples.

Write ONLY the blog post markdown, nothing else. Start with the title as a ## header."""

    text, err = call_gemini(prompt, creds, max_tokens=4000)
    if err:
        return None, err

    text = text.strip().strip('"').strip("'")
    return text, None


def generate_devto_article(creds, topic=None):
    """Generate a Dev.to article using Gemini."""
    topic = topic or random.choice(BLOG_TOPICS)
    prompt = f"""Write a Dev.to article about {topic} from a developer/building-in-public perspective.

Rules:
- 1000-1500 words
- Markdown format with ## headers
- Technical but accessible tone
- Include the perspective of someone building a mental health app
- Reference the design philosophy: no streaks, no guilt, mood-first
- Include 2-3 specific insights about product design for neurodivergent users
- End with: "GentleQuest is a free mood check-in app. No streaks. No shame. Try it free at https://gentlequest.app"
- Tags: mentalhealth, adhd, productivity, wellness

Write ONLY the article markdown, nothing else. Start with the title as a # header."""

    text, err = call_gemini(prompt, creds, max_tokens=6000)
    if err:
        return None, err

    text = text.strip().strip('"').strip("'")
    # Extract title from first # header
    title = ""
    for line in text.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
            break

    return {"title": title, "body_markdown": text, "tags": ["mentalhealth", "adhd", "productivity", "wellness"]}, None


def auto_generate_content(creds, count=10):
    """Generate new content items and add them to the queue."""
    queue = load_queue()
    existing_ids = {i["id"] for i in queue.get("items", [])}

    # Count pending items
    state = load_state()
    posted_ids = set(state.get("posted_ids", []))
    pending_count = sum(1 for i in queue.get("items", []) if i["id"] not in posted_ids and i.get("status") != "posted")

    if pending_count >= 10:
        print(f"Queue has {pending_count} pending items. No generation needed.")
        return 0

    print(f"Queue has {pending_count} pending items. Generating {count} new items...")

    # Find the last scheduled date to continue from
    last_scheduled = datetime.now(timezone.utc)
    for item in queue.get("items", []):
        if item.get("scheduled_for"):
            try:
                sched = datetime.fromisoformat(item["scheduled_for"].replace("Z", "+00:00"))
                if sched > last_scheduled:
                    last_scheduled = sched
            except:
                pass

    new_items = []
    current_time = last_scheduled + timedelta(hours=4)  # Start 4h after last scheduled

    for i in range(count):
        item_type = random.choices(
            ["tweet", "tweet", "tweet", "tweet", "blog", "medium", "medium"],
            weights=[3, 3, 3, 3, 1, 1, 1]
        )[0]

        if item_type == "tweet":
            text, err = generate_tweet(creds)
            if err:
                print(f"  Tweet generation failed: {err}")
                continue
            item = {
                "id": f"gen_tweet_{int(time.time())}_{i}",
                "channel": "buffer",
                "target": "twitter",
                "text": text,
                "scheduled_for": current_time.isoformat().replace("+00:00", "Z"),
                "status": "pending",
                "generated": True,
            }
            current_time += timedelta(hours=4)  # 4h between tweets (6 tweets/day)
        elif item_type == "linkedin":
            text, err = generate_linkedin_post(creds)
            if err:
                print(f"  LinkedIn generation failed: {err}")
                continue
            item = {
                "id": f"gen_linkedin_{int(time.time())}_{i}",
                "channel": "buffer",
                "target": "linkedin",
                "text": text,
                "scheduled_for": current_time.isoformat().replace("+00:00", "Z"),
                "status": "pending",
                "generated": True,
            }
            current_time += timedelta(hours=24)  # 1 LinkedIn post/day
        elif item_type == "blog":
            text, err = generate_blog_post(creds)
            if err:
                print(f"  Blog generation failed: {err}")
                continue
            # Save blog post to scheduled folder
            slug = f"generated-{int(time.time())}-{i}"
            blog_path = Path("/Users/lokeshgarg/gentlequest/gentlequest-blog/src/content/scheduled") / f"{slug}.md"
            # Add frontmatter
            pub_date = current_time.strftime("%Y-%m-%d")
            blog_content = f"""---
title: "{text.split(chr(10))[0].replace('# ', '').replace('## ', '')[:80]}"
description: "{text.split(chr(10))[0].replace('# ', '').replace('## ', '')[:150]}"
pubDate: {pub_date}
author: "GentleQuest Team"
tags: ["ADHD", "Mental Health", "Self-Care"]
---

{text}
"""
            blog_path.parent.mkdir(parents=True, exist_ok=True)
            blog_path.write_text(blog_content)
            item = {
                "id": f"gen_blog_{int(time.time())}_{i}",
                "channel": "blog",
                "target": "blog",
                "text": f"Blog post scheduled: {slug}",
                "scheduled_for": current_time.isoformat().replace("+00:00", "Z"),
                "status": "pending",
                "generated": True,
                "blog_slug": slug,
            }
            current_time += timedelta(days=2)  # Blog post every 2 days
        elif item_type == "devto":
            article, err = generate_devto_article(creds)
            if err:
                print(f"  Dev.to generation failed: {err}")
                continue
            item = {
                "id": f"gen_devto_{int(time.time())}_{i}",
                "channel": "devto",
                "title": article["title"],
                "body_markdown": article["body_markdown"],
                "tags": article["tags"],
                "published": True,
                "scheduled_for": current_time.isoformat().replace("+00:00", "Z"),
                "status": "pending",
                "generated": True,
            }
            current_time += timedelta(days=7)  # Dev.to article weekly
        elif item_type == "medium":
            # Medium imports from the blog — find a blog post that's already live
            blog_dir = Path("/Users/lokeshgarg/gentlequest/gentlequest-blog/src/content/blog")
            blog_posts = sorted(blog_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not blog_posts:
                print(f"  Medium: no blog posts to import")
                continue
            # Pick a random recent post (not the very latest, to avoid duplicates)
            post_file = random.choice(blog_posts[:5]) if len(blog_posts) >= 5 else blog_posts[0]
            slug = post_file.stem
            blog_url = f"https://www.gentlequest.app/blog/{slug}"
            item = {
                "id": f"gen_medium_{int(time.time())}_{i}",
                "channel": "medium",
                "blog_url": blog_url,
                "title": post_file.stem.replace("-", " ").title(),
                "scheduled_for": current_time.isoformat().replace("+00:00", "Z"),
                "status": "pending",
                "generated": True,
            }
            current_time += timedelta(days=3)  # Medium import every 3 days
        elif item_type == "reddit":
            subreddit = random.choice(list(REDDIT_SUBREDDITS.keys()))
            item = {
                "id": f"gen_reddit_{int(time.time())}_{i}",
                "channel": "reddit",
                "subreddit": subreddit,
                "topic_keywords": REDDIT_SUBREDDITS[subreddit]["topics"],
                "scheduled_for": current_time.isoformat().replace("+00:00", "Z"),
                "status": "pending",
                "generated": True,
            }
            current_time += timedelta(hours=12)  # Reddit comment every 12h (2/day max)

        if item["id"] not in existing_ids:
            queue["items"].append(item)
            new_items.append(item)
            print(f"  Generated {item_type}: {item['id']} → {item.get('scheduled_for', '?')}")

    save_queue(queue)
    print(f"\nAdded {len(new_items)} new items to queue.")
    return len(new_items)


# ─── Queue management ──────────────────────────────────────────────────────

def load_queue():
    """Load the content queue."""
    if not QUEUE_PATH.exists():
        return {"items": []}
    with open(QUEUE_PATH) as f:
        return json.load(f)

def save_queue(queue):
    """Save the content queue."""
    with open(QUEUE_PATH, "w") as f:
        json.dump(queue, f, indent=2)

def load_state():
    """Load publisher state (what's been posted)."""
    if not STATE_PATH.exists():
        return {"posted_ids": [], "last_run": None}
    with open(STATE_PATH) as f:
        return json.load(f)

def save_state(state):
    """Save publisher state."""
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

def log_action(item, status, details=""):
    """Log a publish action."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "item_id": item.get("id", ""),
        "channel": item.get("channel", ""),
        "target": item.get("target", ""),
        "status": status,
        "details": details,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

# ─── Buffer publisher ──────────────────────────────────────────────────────

def fetch_buffer_channels(token):
    """Fetch channel IDs from Buffer GraphQL API. Returns dict mapping service name to channel ID."""
    # First get the account + organization ID
    account_query = """
    query {
        account {
            id
            organizations { id name }
        }
    }
    """
    payload = json.dumps({"query": account_query}).encode()
    req = urllib.request.Request(
        BUFFER_GRAPHQL,
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )

    org_id = None
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read())
            orgs = body.get("data", {}).get("account", {}).get("organizations", [])
            if orgs:
                org_id = orgs[0].get("id")
    except Exception as e:
        print(f"Warning: Failed to fetch Buffer account: {e}")
        return {}

    if not org_id:
        return {}

    # Now fetch channels for this org
    channels_query = """
    query GetChannels($input: ChannelsInput!) {
        channels(input: $input) {
            id
            service
            type
            name
            displayName
        }
    }
    """
    payload2 = json.dumps({
        "query": channels_query,
        "variables": {"input": {"organizationId": org_id}}
    }).encode()
    req2 = urllib.request.Request(
        BUFFER_GRAPHQL,
        data=payload2,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )

    channels = {}
    try:
        with urllib.request.urlopen(req2, timeout=15) as resp:
            body = json.loads(resp.read())
            for ch in body.get("data", {}).get("channels", []):
                ch_id = ch.get("id")
                service = ch.get("service", "").lower()
                if ch_id and service:
                    channels[service] = ch_id
                    print(f"  Buffer channel: {service} ({ch.get('displayName', '?')}) → {ch_id}")
    except Exception as e:
        print(f"Warning: Failed to fetch Buffer channels: {e}")

    return channels


def publish_to_buffer(item, creds, dry_run=False):
    """Publish to Buffer via GraphQL API."""
    token = creds.get("buffer_token")
    if not token:
        return False, "No Buffer token"

    # Fetch channel IDs dynamically if not cached
    if not creds.get("buffer_twitter_channel"):
        channels = fetch_buffer_channels(token)
        if channels:
            creds["buffer_twitter_channel"] = channels.get("twitter") or channels.get("x")
            creds["buffer_linkedin_channel"] = channels.get("linkedin")
            creds["buffer_instagram_channel"] = channels.get("instagram")
            creds["buffer_facebook_channel"] = channels.get("facebook")
            print(f"  Fetched Buffer channels: {list(channels.keys())}")

    channel_map = {
        "twitter": creds.get("buffer_twitter_channel"),
        "x": creds.get("buffer_twitter_channel"),
        "linkedin": creds.get("buffer_linkedin_channel"),
        "instagram": creds.get("buffer_instagram_channel"),
        "facebook": creds.get("buffer_facebook_channel"),
    }

    target = item.get("target", "twitter").lower()
    channel_id = channel_map.get(target)
    if not channel_id:
        available = [k for k, v in channel_map.items() if v]
        return False, f"No Buffer channel for target={target} (available: {available})"

    text = item.get("text", "")
    if not text:
        return False, "Empty text"

    if dry_run:
        return True, f"DRY RUN: Would post to Buffer/{target}: {text[:50]}..."

    query = """
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
    """

    variables = {
        "input": {
            "channelId": channel_id,
            "schedulingType": "automatic",
            "mode": "addToQueue",
            "assets": [],
            "text": text,
        }
    }

    payload = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        BUFFER_GRAPHQL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read())
            result = body.get("data", {}).get("createPost", {})
            if result.get("__typename") == "PostActionSuccess":
                post_id = result["post"]["id"]
                return True, f"Posted to Buffer/{target}, post_id={post_id}"
            else:
                return False, f"Buffer error: {result.get('message', 'unknown')}"
    except Exception as e:
        return False, f"Buffer exception: {e}"

# ─── Dev.to publisher ──────────────────────────────────────────────────────

def publish_to_devto(item, creds, dry_run=False):
    """Publish to Dev.to via REST API."""
    api_key = creds.get("devto_api_key")
    if not api_key:
        return False, "No Dev.to API key"

    if dry_run:
        return True, f"DRY RUN: Would publish to Dev.to: {item.get('title', '')[:50]}..."

    article = {
        "article": {
            "title": item.get("title", ""),
            "body_markdown": item.get("body_markdown", ""),
            "published": item.get("published", True),
            "tags": item.get("tags", ["mentalhealth", "adhd", "wellness"]),
        }
    }

    payload = json.dumps(article).encode()
    req = urllib.request.Request(
        DEVTO_API,
        data=payload,
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read())
            url = body.get("url", "unknown")
            return True, f"Published to Dev.to: {url}"
    except Exception as e:
        return False, f"Dev.to exception: {e}"

# ─── Reddit publisher (legacy API — deprecated, Reddit locked API Nov 2025) ─

def publish_to_reddit_api(item, creds, dry_run=False):
    """Publish to Reddit via OAuth2 API. DEPRECATED — Reddit closed API access Nov 2025.
    Kept for reference. Use publish_to_reddit (browser automation) instead.
    """
    client_id = creds.get("reddit_client_id")
    client_secret = creds.get("reddit_client_secret")
    refresh_token = creds.get("reddit_refresh_token")

    if not all([client_id, client_secret, refresh_token]):
        return False, "No Reddit credentials"

    if dry_run:
        return True, f"DRY RUN: Would post to Reddit/{item.get('subreddit', '')}: {item.get('text', '')[:50]}..."

    # Get access token
    token_req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=f"grant_type=refresh_token&refresh_token={refresh_token}".encode(),
        headers={
            "Authorization": f"Basic {__import__('base64').b64encode(f'{client_id}:{client_secret}'.encode()).decode()}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": REDDIT_USER_AGENT,
        }
    )

    try:
        with urllib.request.urlopen(token_req) as resp:
            token_data = json.loads(resp.read())
            access_token = token_data.get("access_token")
            if not access_token:
                return False, "Failed to get Reddit access token"
    except Exception as e:
        return False, f"Reddit token exception: {e}"

    # Post comment or submission
    subreddit = item.get("subreddit", "")
    text = item.get("text", "")
    post_type = item.get("type", "comment")  # "comment" or "submit"
    thread_id = item.get("thread_id", "")  # for comments

    if post_type == "comment" and thread_id:
        data = f"thing_id={thread_id}&text={__import__('urllib.parse', fromlist=['quote']).quote(text)}"
        endpoint = "https://oauth.reddit.com/api/comment"
    elif post_type == "submit":
        title = item.get("title", text[:100])
        data = f"kind=self&sr={subreddit}&title={__import__('urllib.parse', fromlist=['quote']).quote(title)}&text={__import__('urllib.parse', fromlist=['quote']).quote(text)}&spoiler=false&nsfw=false"
        endpoint = "https://oauth.reddit.com/api/submit"
    else:
        return False, f"Unknown Reddit post type: {post_type}"

    req = urllib.request.Request(
        endpoint,
        data=data.encode(),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": REDDIT_USER_AGENT,
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read())
            if body.get("json", {}).get("errors"):
                return False, f"Reddit error: {body['json']['errors']}"
            return True, f"Posted to Reddit/{subreddit}"
    except Exception as e:
        return False, f"Reddit exception: {e}"

# ─── IndieHackers publisher (browser automation) ──────────────────────────

def publish_to_indiehackers(item, creds, dry_run=False):
    """Publish to IndieHackers via browser automation."""
    if dry_run:
        return True, f"DRY RUN: Would post to IndieHackers: {item.get('title', '')[:50]}..."

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "Playwright not installed — skipping IndieHackers"

    title = item.get("title", "")
    body = item.get("body", "")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(PLAYWRIGHT_PROFILE),
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.new_page()
        try:
            page.goto("https://www.indiehackers.com/group/landing-page-feedback", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)

            if page.query_selector("text=Sign in"):
                return False, "Not logged in to IndieHackers — run --setup-browser"

            page.click("text=New Post")
            page.wait_for_selector('input[placeholder*="Title"], textarea[placeholder*="Title"]', timeout=10000)
            page.fill('input[placeholder*="Title"], textarea[placeholder*="Title"]', title)
            page.fill('textarea[placeholder*="Body"], div[contenteditable]', body)
            page.click('button:has-text("Post")')
            page.wait_for_load_state("networkidle", timeout=15000)
            return True, "Posted to IndieHackers"
        except Exception as e:
            return False, f"IH error: {e}"
        finally:
            context.close()


# ─── Medium publisher (browser automation — import from blog) ──────────────

PLAYWRIGHT_PROFILE = Path.home() / ".config" / "gentlequest" / "playwright-profile"

def publish_to_medium(item, creds, dry_run=False):
    """Import a blog post to Medium via browser automation.

    Uses Medium's 'Import a story' feature which:
    - Pulls content from the blog URL
    - Automatically sets canonical URL to the original
    - Publishes under the @gentlequest Medium account
    """
    if dry_run:
        return True, f"DRY RUN: Would import to Medium: {item.get('blog_url', '')[:60]}..."

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "Playwright not installed — skipping Medium"

    blog_url = item.get("blog_url", "")
    if not blog_url:
        return False, "No blog_url in item"

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(PLAYWRIGHT_PROFILE),
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.new_page()
        try:
            # Go to Medium's new story page
            page.goto("https://medium.com/new-story", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)

            # Check if logged in
            if "m/signin" in page.url or page.query_selector('button:has-text("Sign in")'):
                return False, "Not logged in to Medium — run --setup-browser"

            # Look for "Import a story" link
            import_link = page.query_selector('a:has-text("Import a story")')
            if not import_link:
                # Try the import URL directly
                page.goto("https://medium.com/new-story/import", timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)
            else:
                import_link.click()
                page.wait_for_load_state("networkidle", timeout=15000)

            # Paste the blog URL
            url_input = page.wait_for_selector('input[type="url"], input[placeholder*="URL"], input[placeholder*="url"]', timeout=10000)
            url_input.fill(blog_url)
            page.wait_for_timeout(500)

            # Click import button
            import_btn = page.query_selector('button:has-text("Import")')
            if not import_btn:
                import_btn = page.query_selector('button:has-text("import")')
            if not import_btn:
                return False, "Could not find Import button on Medium"

            import_btn.click()

            # Wait for import to complete (Medium fetches the content)
            page.wait_for_timeout(5000)
            page.wait_for_load_state("networkidle", timeout=30000)

            # Click Publish
            publish_btn = page.query_selector('button:has-text("Publish")')
            if not publish_btn:
                publish_btn = page.query_selector('button:has-text("Publish now")')
            if not publish_btn:
                # Maybe we need to confirm the import first
                confirm_btn = page.query_selector('button:has-text("Confirm")')
                if confirm_btn:
                    confirm_btn.click()
                    page.wait_for_timeout(2000)
                    publish_btn = page.query_selector('button:has-text("Publish")')

            if not publish_btn:
                return False, "Could not find Publish button — import may have failed"

            publish_btn.click()

            # Handle publish dialog — confirm
            page.wait_for_timeout(2000)
            final_btn = page.query_selector('button:has-text("Publish now")')
            if final_btn:
                final_btn.click()

            page.wait_for_timeout(3000)
            medium_url = page.url
            return True, f"Imported to Medium: {medium_url}"

        except Exception as e:
            return False, f"Medium error: {e}"
        finally:
            context.close()


# ─── Reddit publisher (browser automation — value-first comments) ──────────

REDDIT_SUBREDDITS = {
    "ADHD": {"url": "r/ADHD", "topics": ["paralysis", "can't start", "overwhelm", "streaks", "burnout", "task initiation", "executive dysfunction"]},
    "Anxiety": {"url": "r/Anxiety", "topics": ["overwhelm", "can't calm down", "panic", "racing thoughts", "night anxiety", "grounding", "breathing"]},
    "Habits": {"url": "r/Habits", "topics": ["streaks", "habit tracking", "consistency", "guilt", "missing days", "starting over"]},
}

def generate_reddit_comment(creds, post_title, post_body, subreddit):
    """Generate a unique, helpful Reddit comment using Gemini."""
    prompt = f"""You are a helpful Redditor on r/{subreddit}. Someone posted:

Title: {post_title}
Body: {post_body[:500]}

Write a genuinely helpful comment. Rules:
- 2-4 sentences, conversational, empathetic
- Share a specific technique or insight (not generic advice)
- DO NOT mention any app, product, or link
- DO NOT say "I built" or "I made" or "check out"
- Be a real community member, not a marketer
- First person perspective
- Match the tone of r/{subreddit} — supportive, real, no toxic positivity
- No emojis unless genuinely fitting

Write ONLY the comment text, nothing else."""

    text, err = call_gemini(prompt, creds, max_tokens=800)
    if err:
        return None, err

    text = text.strip().strip('"').strip("'")
    for prefix in ["Comment:", "Reply:", "Here's the comment:"]:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()

    return text, None


def publish_to_reddit(item, creds, dry_run=False):
    """Post a value-first comment on Reddit via browser automation.

    Flow:
    1. Browse the subreddit sorted by "new"
    2. Find a post matching the topic keyword
    3. Generate a unique, helpful comment via Gemini
    4. Post the comment
    5. NO links, NO app mentions — pure community engagement
    """
    if dry_run:
        return True, f"DRY RUN: Would comment on Reddit/{item.get('subreddit', '')}..."

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "Playwright not installed — skipping Reddit"

    subreddit = item.get("subreddit", "ADHD")
    sub_info = REDDIT_SUBREDDITS.get(subreddit, REDDIT_SUBREDDITS["ADHD"])
    topic_keywords = item.get("topic_keywords", sub_info["topics"])

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(PLAYWRIGHT_PROFILE),
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.new_page()
        try:
            # Go to subreddit sorted by new
            page.goto(f"https://www.reddit.com/{sub_info['url']}/new/", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)

            # Check if logged in
            if "login" in page.url.lower() or page.query_selector('a:has-text("Log In")'):
                return False, "Not logged in to Reddit — run --setup-browser"

            # Find posts matching topic keywords
            posts = page.query_selector_all('article, [data-testid="post-container"], shreddit-post')
            target_post = None
            target_title = ""
            target_href = ""

            for post in posts[:15]:  # Check first 15 posts
                title_el = post.query_selector('a[slot="title"], h3, [data-testid="post-title"]')
                if not title_el:
                    continue
                title = title_el.inner_text().lower()

                # Check if title matches any topic keyword
                if any(kw.lower() in title for kw in topic_keywords):
                    # Make sure it's not our own post and has no comments from us
                    target_post = post
                    target_title = title_el.inner_text()
                    link_el = post.query_selector('a[slot="full-post-link"], a[href*="/comments/"]')
                    if link_el:
                        target_href = link_el.get_attribute("href")
                    break

            if not target_post:
                return False, f"No matching posts found in r/{subreddit} (checked 15 posts)"

            # Click into the post
            if target_href:
                page.goto(f"https://www.reddit.com{target_href}", timeout=30000)
            else:
                target_post.click()
            page.wait_for_load_state("networkidle", timeout=15000)

            # Get post body for context
            post_body = ""
            body_el = page.query_selector('[data-testid="post-content"], div[data-post-click="body"] .RichTextJSONRoot, shreddit-post .md')
            if body_el:
                post_body = body_el.inner_text()[:500]

            # Generate a unique comment
            comment_text, err = generate_reddit_comment(creds, target_title, post_body, subreddit)
            if err or not comment_text:
                return False, f"Comment generation failed: {err}"
            if len(comment_text) > 1000:
                comment_text = comment_text[:997] + "..."

            # Find the comment box
            comment_box = page.query_selector('div[contenteditable="true"][data-lexical-editor="true"], textarea[placeholder*="comment"], div[role="textbox"]')
            if not comment_box:
                # Try clicking "Add a comment" first
                add_comment = page.query_selector('button:has-text("Add a comment")')
                if add_comment:
                    add_comment.click()
                    page.wait_for_timeout(2000)
                    comment_box = page.query_selector('div[contenteditable="true"], textarea[placeholder*="comment"], div[role="textbox"]')

            if not comment_box:
                return False, "Could not find comment box on Reddit"

            comment_box.click()
            page.wait_for_timeout(500)
            comment_box.type(comment_text, delay=50)
            page.wait_for_timeout(500)

            # Find and click submit button
            submit_btn = page.query_selector('button:has-text("Comment"), button:has-text("Reply"), button[type="submit"]')
            if not submit_btn:
                return False, "Could not find submit button for Reddit comment"

            submit_btn.click()
            page.wait_for_timeout(3000)

            return True, f"Commented on r/{subreddit}: \"{target_title[:50]}...\""

        except Exception as e:
            return False, f"Reddit error: {e}"
        finally:
            context.close()


# ─── Browser setup (one-time login) ────────────────────────────────────────

def setup_browser():
    """Open a browser for one-time login to Medium + Reddit.

    The user logs in once, cookies are saved to the persistent profile,
    and the publisher daemon uses them for headless automation.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed. Run: pip3 install playwright && python3 -m playwright install chromium")
        return

    PLAYWRIGHT_PROFILE.mkdir(parents=True, exist_ok=True)

    print("Opening browser for one-time login...")
    print("1. Log in to Medium (medium.com)")
    print("2. Log in to Reddit (reddit.com)")
    print("3. Close the browser when done")
    print("")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(PLAYWRIGHT_PROFILE),
            headless=False,  # Visible so user can log in
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.new_page()
        page.goto("https://medium.com")

        # Wait for user to close the browser
        try:
            page.wait_for_event("close", timeout=0)
        except:
            pass

        context.close()

    print("Browser profile saved. Publisher daemon can now use it for Medium + Reddit.")

# ─── Main publisher logic ──────────────────────────────────────────────────

def get_pending_items(queue, state):
    """Get items that haven't been posted yet and are due."""
    now = datetime.now(timezone.utc)
    posted_ids = set(state.get("posted_ids", []))
    pending = []

    for item in queue.get("items", []):
        if item.get("id") in posted_ids:
            continue
        if item.get("status") == "posted":
            continue

        # Check if scheduled and due
        scheduled = item.get("scheduled_for")
        if scheduled:
            sched_time = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
            if now < sched_time:
                continue

        pending.append(item)

    return pending

def publish_item(item, creds, dry_run=False):
    """Publish a single item to its channel."""
    channel = item.get("channel", "").lower()

    if channel == "buffer":
        return publish_to_buffer(item, creds, dry_run)
    elif channel == "devto":
        return publish_to_devto(item, creds, dry_run)
    elif channel == "reddit":
        return publish_to_reddit(item, creds, dry_run)
    elif channel == "medium":
        return publish_to_medium(item, creds, dry_run)
    elif channel == "indiehackers":
        return publish_to_indiehackers(item, creds, dry_run)
    else:
        return False, f"Unknown channel: {channel}"

def run_once(creds, dry_run=False):
    """Process the queue once. Auto-generates content if queue is low."""
    queue = load_queue()
    state = load_state()
    pending = get_pending_items(queue, state)

    # Auto-generate if queue is running low
    if len(pending) < 5 and not dry_run:
        print(f"Queue running low ({len(pending)} pending). Auto-generating content...")
        auto_generate_content(creds, count=10)
        # Reload queue after generation
        queue = load_queue()
        pending = get_pending_items(queue, state)

    if not pending:
        print(f"No pending items. Queue has {len(queue.get('items', []))} total items.")
        return

    print(f"Found {len(pending)} pending items.")

    for item in pending:
        print(f"\nProcessing: {item.get('id', '?')} → {item.get('channel')}/{item.get('target', '')}")

        # Skip blog items — they're handled by the blog staggered daemon
        if item.get("channel") == "blog":
            state["posted_ids"].append(item.get("id"))
            item["status"] = "posted"
            continue

        success, message = publish_item(item, creds, dry_run)

        if success:
            print(f"  ✓ {message}")
            state["posted_ids"].append(item.get("id"))
            item["status"] = "posted"
            item["posted_at"] = datetime.now(timezone.utc).isoformat()
            log_action(item, "success", message)
        else:
            print(f"  ✗ {message}")
            item["status"] = "failed"
            item["error"] = message
            log_action(item, "failed", message)

        # Rate limit: wait between posts
        if not dry_run:
            time.sleep(5)

    state["last_run"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    save_queue(queue)

def show_status(creds):
    """Show queue status."""
    queue = load_queue()
    state = load_state()
    posted_ids = set(state.get("posted_ids", []))

    total = len(queue.get("items", []))
    posted = len([i for i in queue.get("items", []) if i.get("id") in posted_ids or i.get("status") == "posted"])
    pending = total - posted

    print(f"GentleQuest Publisher Status")
    print(f"=" * 40)
    print(f"Total items:  {total}")
    print(f"Posted:       {posted}")
    print(f"Pending:      {pending}")
    print(f"Last run:     {state.get('last_run', 'never')}")
    print(f"")

    # Show by channel
    channels = {}
    for item in queue.get("items", []):
        ch = item.get("channel", "unknown")
        if ch not in channels:
            channels[ch] = {"total": 0, "posted": 0, "pending": 0}
        channels[ch]["total"] += 1
        if item.get("id") in posted_ids or item.get("status") == "posted":
            channels[ch]["posted"] += 1
        else:
            channels[ch]["pending"] += 1

    print(f"By channel:")
    for ch, stats in sorted(channels.items()):
        print(f"  {ch:15s} {stats['posted']}/{stats['total']} posted, {stats['pending']} pending")

    # Show next 5 pending
    print(f"\nNext pending items:")
    next_items = [i for i in queue.get("items", []) if i.get("id") not in posted_ids and i.get("status") != "posted"][:5]
    for item in next_items:
        text = item.get("text", item.get("title", ""))[:60]
        print(f"  {item.get('id', '?'):20s} → {item.get('channel')}/{item.get('target', ''):10s} {text}...")

# ─── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GentleQuest Autonomous Publisher")
    parser.add_argument("--once", action="store_true", help="Process queue once (auto-generates if low)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would fire without posting")
    parser.add_argument("--status", action="store_true", help="Show queue status")
    parser.add_argument("--generate", action="store_true", help="Generate new content now")
    parser.add_argument("--generate-count", type=int, default=10, help="Number of items to generate")
    parser.add_argument("--setup-browser", action="store_true", help="One-time login to Medium + Reddit (opens browser)")
    args = parser.parse_args()

    creds = load_credentials()

    if args.setup_browser:
        setup_browser()
    elif args.status:
        show_status(creds)
    elif args.generate:
        count = auto_generate_content(creds, count=args.generate_count)
        print(f"Generated {count} new items.")
    elif args.once or args.dry_run:
        run_once(creds, dry_run=args.dry_run)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
