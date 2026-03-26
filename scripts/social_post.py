#!/usr/bin/env python3
"""Post Nucleus updates to Twitter/X via v2 API.

Usage:
    python scripts/social_post.py --message "Hello world"
    python scripts/social_post.py --message "Hello world" --dry-run
    python scripts/social_post.py --thread thread.json
    python scripts/social_post.py --generate
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from hashlib import sha256
from hmac import new as hmac_new
from base64 import b64encode
from urllib.parse import quote as urlquote
import uuid

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library required. Install with: pip install requests")
    sys.exit(1)

# --- Constants ---
TWITTER_API_URL = "https://api.twitter.com/2/tweets"
MAX_TWEET_LENGTH = 280
SOCIAL_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", ".brain", "growth", "social_log.jsonl")
CONTENT_BANK_PATH = os.path.join(os.path.dirname(__file__), "..", ".brain", "growth", "content_bank.jsonl")

REQUIRED_ENV_VARS = [
    "TWITTER_API_KEY",
    "TWITTER_API_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_SECRET",
]


def load_credentials():
    """Load Twitter API credentials from environment variables."""
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Set them before running:\n")
        for v in missing:
            print(f"  export {v}=your_value")
        sys.exit(1)
    return {
        "api_key": os.environ["TWITTER_API_KEY"],
        "api_secret": os.environ["TWITTER_API_SECRET"],
        "access_token": os.environ["TWITTER_ACCESS_TOKEN"],
        "access_secret": os.environ["TWITTER_ACCESS_SECRET"],
    }


def _percent_encode(s):
    return urlquote(str(s), safe="")


def _generate_oauth_signature(method, url, params, consumer_secret, token_secret):
    """Generate OAuth 1.0a HMAC-SHA1 signature."""
    sorted_params = "&".join(
        f"{_percent_encode(k)}={_percent_encode(v)}" for k, v in sorted(params.items())
    )
    base_string = f"{method.upper()}&{_percent_encode(url)}&{_percent_encode(sorted_params)}"
    signing_key = f"{_percent_encode(consumer_secret)}&{_percent_encode(token_secret)}"
    signature = hmac_new(
        signing_key.encode(), base_string.encode(), sha256
    ).digest()
    return b64encode(signature).decode()


def build_oauth_header(method, url, creds, body_params=None):
    """Build OAuth 1.0a Authorization header for Twitter API v2."""
    oauth_params = {
        "oauth_consumer_key": creds["api_key"],
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA256",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": creds["access_token"],
        "oauth_version": "1.0",
    }
    # For JSON body requests, only OAuth params go into signature base
    sig_params = dict(oauth_params)
    if body_params:
        sig_params.update(body_params)

    signature = _generate_oauth_signature(
        method, url, sig_params, creds["api_secret"], creds["access_secret"]
    )
    oauth_params["oauth_signature"] = signature

    header_parts = ", ".join(
        f'{_percent_encode(k)}="{_percent_encode(v)}"'
        for k, v in sorted(oauth_params.items())
    )
    return f"OAuth {header_parts}"


def handle_rate_limit(response):
    """Check rate limit headers and sleep if needed. Returns True if caller should retry."""
    remaining = response.headers.get("x-rate-limit-remaining")
    reset_at = response.headers.get("x-rate-limit-reset")

    if response.status_code == 429:
        if reset_at:
            wait = max(int(reset_at) - int(time.time()), 1)
            print(f"Rate limited. Waiting {wait}s until reset...")
            time.sleep(wait)
        else:
            print("Rate limited. Waiting 60s (no reset header)...")
            time.sleep(60)
        return True

    if remaining and int(remaining) <= 1 and reset_at:
        wait = max(int(reset_at) - int(time.time()), 1)
        print(f"Rate limit nearly exhausted ({remaining} left). Waiting {wait}s...")
        time.sleep(wait)

    return False


def log_post(content, tweet_id, success, platform="twitter"):
    """Append post record to social_log.jsonl."""
    log_path = os.path.normpath(SOCIAL_LOG_PATH)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": platform,
        "content": content,
        "tweet_id": tweet_id,
        "success": success,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def post_tweet(creds, text, reply_to=None, dry_run=False):
    """Post a single tweet. Returns (tweet_id, success)."""
    if len(text) > MAX_TWEET_LENGTH:
        print(f"ERROR: Tweet exceeds {MAX_TWEET_LENGTH} chars ({len(text)} chars):\n  {text[:100]}...")
        return None, False

    if dry_run:
        reply_info = f" (reply to {reply_to})" if reply_to else ""
        print(f"[DRY RUN] Would post{reply_info}:\n  {text}")
        log_post(text, "dry_run", True)
        return "dry_run", True

    payload = {"text": text}
    if reply_to:
        payload["reply"] = {"in_reply_to_tweet_id": reply_to}

    auth_header = build_oauth_header("POST", TWITTER_API_URL, creds)
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
    }

    for attempt in range(3):
        try:
            resp = requests.post(TWITTER_API_URL, headers=headers, json=payload, timeout=30)
        except requests.RequestException as e:
            print(f"ERROR: Request failed: {e}")
            log_post(text, None, False)
            return None, False

        if handle_rate_limit(resp):
            # Rebuild auth header with fresh timestamp/nonce for retry
            auth_header = build_oauth_header("POST", TWITTER_API_URL, creds)
            headers["Authorization"] = auth_header
            continue

        if resp.status_code in (200, 201):
            data = resp.json()
            tweet_id = data.get("data", {}).get("id")
            print(f"Posted (id={tweet_id}): {text[:80]}...")
            log_post(text, tweet_id, True)
            return tweet_id, True

        print(f"ERROR: Twitter API returned {resp.status_code}: {resp.text}")
        log_post(text, None, False)
        return None, False

    print("ERROR: Exhausted retries after rate limiting.")
    log_post(text, None, False)
    return None, False


def post_thread(creds, tweets, dry_run=False):
    """Post a thread (array of tweet texts). Each replies to the previous."""
    if not tweets:
        print("ERROR: Thread is empty.")
        return

    print(f"Posting thread ({len(tweets)} tweets)...")
    reply_to = None
    for i, text in enumerate(tweets, 1):
        print(f"\n--- Tweet {i}/{len(tweets)} ---")
        tweet_id, success = post_tweet(creds, text, reply_to=reply_to, dry_run=dry_run)
        if not success:
            print(f"Thread aborted at tweet {i}.")
            return
        reply_to = tweet_id
        if not dry_run and i < len(tweets):
            time.sleep(2)  # small delay between thread tweets
    print(f"\nThread complete ({len(tweets)} tweets).")


def pick_next_from_content_bank():
    """Read content_bank.jsonl, cross-reference social_log.jsonl, return first unposted entry."""
    bank_path = os.path.normpath(CONTENT_BANK_PATH)
    log_path = os.path.normpath(SOCIAL_LOG_PATH)

    if not os.path.exists(bank_path):
        print(f"ERROR: Content bank not found at {bank_path}")
        print("Create it with one JSON object per line, each having a 'content' field.")
        sys.exit(1)

    # Load already-posted content
    posted = set()
    if os.path.exists(log_path):
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("success"):
                        posted.add(entry.get("content", ""))
                except json.JSONDecodeError:
                    continue

    # Find first unposted
    with open(bank_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            content = entry.get("content", "")
            if content and content not in posted:
                return content

    print("All content bank entries have been posted. Add more to content_bank.jsonl.")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Post Nucleus updates to Twitter/X")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--message", "-m", help="Tweet text (max 280 chars)")
    group.add_argument("--thread", "-t", help="Path to JSON file with array of tweet texts")
    group.add_argument("--generate", "-g", action="store_true",
                       help="Pick next unposted entry from content_bank.jsonl")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be posted without posting")
    args = parser.parse_args()

    # Resolve the tweet text
    if args.generate:
        text = pick_next_from_content_bank()
        print(f"Selected from content bank:\n  {text}\n")
        if not args.dry_run:
            creds = load_credentials()
        else:
            creds = None
        tweet_id, success = post_tweet(creds or {}, text, dry_run=args.dry_run)
        sys.exit(0 if success else 1)

    if args.thread:
        thread_path = args.thread
        if not os.path.exists(thread_path):
            print(f"ERROR: Thread file not found: {thread_path}")
            sys.exit(1)
        with open(thread_path) as f:
            tweets = json.load(f)
        if not isinstance(tweets, list) or not all(isinstance(t, str) for t in tweets):
            print("ERROR: Thread file must contain a JSON array of strings.")
            sys.exit(1)
        if not args.dry_run:
            creds = load_credentials()
        else:
            creds = {}
        post_thread(creds, tweets, dry_run=args.dry_run)
        sys.exit(0)

    # --message
    text = args.message
    if not args.dry_run:
        creds = load_credentials()
    else:
        creds = {}
    tweet_id, success = post_tweet(creds, text, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
