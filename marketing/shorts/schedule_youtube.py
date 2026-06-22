#!/usr/bin/env python3
"""Schedule GQ YT Shorts for daily publish at a fixed time.

Uses the saved OAuth token (with youtube scope) to set publishAt on each video.
Requires re-auth with broader scope — run upload_youtube.py first if token is stale.

Usage:
  python3 schedule_youtube.py                          # schedule v7-v12 daily at 10:00 IST
  python3 schedule_youtube.py --time 18:00             # schedule at 18:00 IST
  python3 schedule_youtube.py --start 2026-06-23       # start on specific date
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

CLIENT_SECRET = Path("/Users/lokeshgarg/Downloads/client_secret_680543456536-pssc73p4dgiij83f88gb682v2fh47n29.apps.googleusercontent.com.json")
TOKEN_FILE = Path(__file__).resolve().parent / "youtube_token.json"
RESULTS_FILE = Path(__file__).resolve().parent / "out" / "final" / "upload_results.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

# IST is UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))


def get_credentials() -> Credentials:
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing token...")
            creds.refresh(Request())
        else:
            print("Running OAuth flow — browser will open...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
        TOKEN_FILE.write_text(creds.to_json())
        print(f"Token saved to {TOKEN_FILE}")

    return creds


def schedule_videos(youtube, time_str: str, start_date: str):
    """Set publishAt on each video for consecutive days at the given IST time."""
    results = json.loads(RESULTS_FILE.read_text())

    # Parse start date and time
    hour, minute = map(int, time_str.split(":"))
    start = datetime.strptime(start_date, "%Y-%m-%d").replace(
        hour=hour, minute=minute, second=0, tzinfo=IST
    )

    print(f"\nScheduling {len(results)} videos daily at {time_str} IST starting {start_date}")
    print(f"  (publishAt times are in UTC: {(start - timedelta(hours=5, minutes=30)).strftime('%H:%M')}Z)\n")

    scheduled = []
    for i, r in enumerate(results):
        if "error" in r:
            print(f"  SKIP {r['name']} — upload had error")
            continue

        publish_at = start + timedelta(days=i)
        publish_utc = publish_at.astimezone(timezone.utc)
        publish_str = publish_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        video_id = r["video_id"]
        print(f"  {r['name']:20s} -> {publish_at.strftime('%Y-%m-%d %H:%M IST')} (UTC: {publish_str})")

        try:
            # Update video: set privacy to private with publishAt
            # First get current snippet
            resp = youtube.videos().list(part="snippet,status", id=video_id).execute()
            if not resp["items"]:
                print(f"    ERROR: video not found")
                continue

            video = resp["items"][0]
            snippet = video["snippet"]
            status = video["status"]

            # Set to private with scheduled publish
            status["privacyStatus"] = "private"
            status["publishAt"] = publish_str
            # Remove selfDeclaredMadeForKids if present (can't update)
            status.pop("selfDeclaredMadeForKids", None)

            # Update
            youtube.videos().update(
                part="status",
                body={
                    "id": video_id,
                    "status": status,
                }
            ).execute()

            scheduled.append({
                "name": r["name"],
                "video_id": video_id,
                "url": r["url"],
                "publish_at_ist": publish_at.strftime("%Y-%m-%d %H:%M IST"),
                "publish_at_utc": publish_str,
            })
            print(f"    Done")

        except HttpError as e:
            print(f"    ERROR: {e}")

    print(f"\n=== Schedule Summary ===")
    for s in scheduled:
        print(f"  {s['name']:20s} -> {s['publish_at_ist']} | {s['url']}")

    # Save schedule
    sched_file = Path(__file__).resolve().parent / "out" / "final" / "schedule_results.json"
    sched_file.write_text(json.dumps(scheduled, indent=2))
    print(f"\nSaved to {sched_file}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--time", default="10:00", help="publish time in IST (HH:MM, default 10:00)")
    ap.add_argument("--start", default=None, help="start date YYYY-MM-DD (default: tomorrow)")
    args = ap.parse_args()

    if args.start is None:
        tomorrow = datetime.now(IST) + timedelta(days=1)
        args.start = tomorrow.strftime("%Y-%m-%d")

    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)
    schedule_videos(youtube, args.time, args.start)


if __name__ == "__main__":
    main()
