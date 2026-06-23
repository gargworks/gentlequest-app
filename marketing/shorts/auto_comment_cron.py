#!/usr/bin/env python3
"""Daily cron: post pinned comments on newly-published GQ YouTube shorts.

Run daily at 10:05 IST (5 min after videos publish at 10:00 IST).
Checks all scheduled videos — if any became public since last run, posts
the matching pinned comment.

Usage:
  python3 auto_comment_cron.py           # check + post
  python3 auto_comment_cron.py --dry-run # check only, no posting

Crontab entry (10:05 IST = 04:35 UTC):
  35 4 * * * python3 /Users/lokeshgarg/gentlequest/marketing/shorts/auto_comment_cron.py >> /Users/lokeshgarg/gentlequest/marketing/shorts/logs/auto_comment.log 2>&1
"""
import json, re, os, sys
from datetime import datetime
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE = Path(__file__).resolve().parent
CLIENT_SECRET = Path("/Users/lokeshgarg/Downloads/client_secret_680543456536-pssc73p4dgiij83f88gb682v2fh47n29.apps.googleusercontent.com.json")
TOKEN_FILE = BASE / "youtube_token.json"
PINNED_COMMENTS = BASE / "pinned_comments.md"
STATE_FILE = BASE / "comment_state.json"
LOG_DIR = BASE / "logs"
LOG_DIR.mkdir(exist_ok=True)

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

ALL_VIDEOS = {
    "hKeBrT7C3V4": "v1", "0XRdun421Jw": "v2", "xtdCaGJBeE0": "v3",
    "nFsl-EcLtfk": "v4", "N6C2BXQjWfo": "v5", "hNXwLzZUlkU": "v6",
    "RJzNVEa743o": "v7", "AE6V33f9jLA": "v8", "5Y286NeQgO4": "v9",
    "ABwSvbXpvwg": "v10", "N-Yv9YI2biA": "v11", "f-6DDMX2LGo": "v12",
    "5Cd3nK5J7Xk": "v13", "JgfgkrYWgIE": "v14", "d1aI5Gb5oWU": "v15",
    "gQZ7HrmU0eU": "v16", "38LRFHiKU9I": "v17", "UlHNIbuFap4": "v18",
}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def get_creds():
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())
        else:
            log("Token invalid — manual re-auth needed (run post_comments.py)")
            sys.exit(1)
    return creds

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def parse_pinned_comments():
    content = PINNED_COMMENTS.read_text()
    comments = {}
    blocks = re.split(r'\n## (v\d+)', content)
    for i in range(1, len(blocks), 2):
        name = blocks[i]
        block = blocks[i+1] if i+1 < len(blocks) else ""
        m = re.search(r'```\n(.+?)```', block, re.DOTALL)
        if m:
            comments[name] = m.group(1).strip()
    return comments

def main():
    dry_run = "--dry-run" in sys.argv
    log(f"Auto-comment cron starting{' (DRY RUN)' if dry_run else ''}...")

    creds = get_creds()
    yt = build("youtube", "v3", credentials=creds)
    comments = parse_pinned_comments()
    state = load_state()

    posted = 0
    skipped = 0

    for vid_id, vname in ALL_VIDEOS.items():
        # Skip if already commented
        if state.get(vid_id, {}).get("commented"):
            skipped += 1
            continue

        # Check if video is public
        resp = yt.videos().list(part="status", id=vid_id).execute()
        if not resp.get("items"):
            continue
        privacy = resp["items"][0]["status"].get("privacyStatus", "?")

        if privacy != "public":
            continue

        comment_text = comments.get(vname)
        if not comment_text:
            log(f"  {vname}: public but no comment found in pinned_comments.md")
            continue

        if dry_run:
            log(f"  {vname}: WOULD POST comment ({len(comment_text)} chars)")
            posted += 1
            continue

        try:
            resp = yt.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": vid_id,
                        "topLevelComment": {"snippet": {"textOriginal": comment_text}},
                    }
                },
            ).execute()
            comment_id = resp["id"]
            log(f"  {vname}: posted comment {comment_id}")
            state[vid_id] = {"commented": True, "comment_id": comment_id, "ts": datetime.now().isoformat()}
            posted += 1
        except Exception as e:
            log(f"  {vname}: ERROR — {e}")

    save_state(state)
    log(f"Done: {posted} posted, {skipped} already commented")

if __name__ == "__main__":
    main()
