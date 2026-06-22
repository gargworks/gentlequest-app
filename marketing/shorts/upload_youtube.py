#!/usr/bin/env python3
"""Upload GQ YT Shorts to YouTube via Data API v3.

First run: opens browser for OAuth consent, saves token to youtube_token.json.
Subsequent runs: uses saved token (refreshes automatically).

Usage:
  python3 upload_youtube.py                    # upload all v7-v12
  python3 upload_youtube.py v7_journal         # upload one
  python3 upload_youtube.py --privacy unlisted # upload as unlisted (default)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# ── Config ──────────────────────────────────────────────────────────────────
CLIENT_SECRET = Path("/Users/lokeshgarg/Downloads/client_secret_680543456536-pssc73p4dgiij83f88gb682v2fh47n29.apps.googleusercontent.com.json")
TOKEN_FILE = Path(__file__).resolve().parent / "youtube_token.json"
SHORTS_DIR = Path(__file__).resolve().parent / "out" / "final"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Video metadata — title, description, tags per short
VIDEO_META = {
    "v7_journal": {
        "title": "GentleQuest — a journal that is just yours",
        "description": "A journal that is just yours. No AI reads it. No prompts. Just a blank page.\n\niOS — https://apps.apple.com/app/gentlequest/id6756537464\nAndroid — https://play.google.com/store/apps/details?id=com.gentlequest.app\nWeb — https://gentlequest.app\n\nFree. 18+. No ads.",
        "tags": ["mental health", "journaling", "privacy", "wellness app", "gentlequest"],
    },
    "v8_privacy": {
        "title": "GentleQuest — your data is yours",
        "description": "Export everything. Delete everything. Or go anonymous. Your call.\n\niOS — https://apps.apple.com/app/gentlequest/id6756537464\nAndroid — https://play.google.com/store/apps/details?id=com.gentlequest.app\nWeb — https://gentlequest.app\n\nNo account needed. No tracking. No ads.",
        "tags": ["privacy", "data privacy", "mental health app", "anonymous", "gentlequest"],
    },
    "v9_grounding": {
        "title": "GentleQuest — grounding 5-4-3-2-1 exercise",
        "description": "Anxious? Try the 5-4-3-2-1 grounding exercise. 60 seconds, back to now.\n\niOS — https://apps.apple.com/app/gentlequest/id6756537464\nAndroid — https://play.google.com/store/apps/details?id=com.gentlequest.app\nWeb — https://gentlequest.app\n\nFree. 18+.",
        "tags": ["anxiety relief", "grounding exercise", "5-4-3-2-1", "CBT", "wellness app"],
    },
    "v10_community": {
        "title": "GentleQuest — this is not social media",
        "description": "No feed. No likes. No follower count. No algorithm. Just you and your mood.\n\niOS — https://apps.apple.com/app/gentlequest/id6756537464\nAndroid — https://play.google.com/store/apps/details?id=com.gentlequest.app\nWeb — https://gentlequest.app\n\nFree. 18+. No ads.",
        "tags": ["not social media", "mental health", "no algorithm", "wellness", "gentlequest"],
    },
    "v11_onboarding": {
        "title": "GentleQuest — first 30 seconds in the app",
        "description": "First 30 seconds in the app: open, 18+ check, say hi, log your mood. That is it.\n\niOS — https://apps.apple.com/app/gentlequest/id6756537464\nAndroid — https://play.google.com/store/apps/details?id=com.gentlequest.app\nWeb — https://gentlequest.app\n\nFree. 18+.",
        "tags": ["app demo", "onboarding", "mental health app", "gentlequest", "how to"],
    },
    "v12_screening": {
        "title": "GentleQuest — real PHQ-9 clinical screening",
        "description": "Real PHQ-9 screening, not just chat. Honest results, and a safety plan if needed.\n\niOS — https://apps.apple.com/app/gentlequest/id6756537464\nAndroid — https://play.google.com/store/apps/details?id=com.gentlequest.app\nWeb — https://gentlequest.app\n\nNot a diagnosis. A starting point. Free. 18+.",
        "tags": ["PHQ-9", "clinical screening", "depression test", "mental health", "gentlequest"],
    },
}


def get_credentials() -> Credentials:
    """Load saved token or run OAuth flow."""
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


def upload_video(youtube, file_path: Path, meta: dict, privacy: str = "unlisted") -> str:
    """Upload a single video. Returns video ID."""
    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": "26",  # Howto & Style
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(file_path), mimetype="video/mp4", resumable=True, chunksize=10 * 1024 * 1024)

    print(f"  Uploading {file_path.name} ({file_path.stat().st_size / (1024*1024):.1f} MB)...")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"    {int(status.progress() * 100)}% uploaded")

    video_id = response["id"]
    video_url = f"https://youtube.com/shorts/{video_id}"
    print(f"  Done: {video_url}")
    return video_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="*", help="short name(s) to upload (default: all v7-v12)")
    ap.add_argument("--privacy", default="unlisted", choices=["public", "unlisted", "private"])
    args = ap.parse_args()

    if args.name:
        names = args.name
    else:
        names = list(VIDEO_META.keys())

    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    results = []
    for name in names:
        if name not in VIDEO_META:
            print(f"  SKIP {name} — no metadata")
            continue

        file_path = SHORTS_DIR / f"gq_short_{name}_final.mp4"
        if not file_path.exists():
            print(f"  SKIP {name} — file not found: {file_path}")
            continue

        print(f"\n=== {name} ===")
        try:
            video_id = upload_video(youtube, file_path, VIDEO_META[name], args.privacy)
            results.append({"name": name, "video_id": video_id, "url": f"https://youtube.com/shorts/{video_id}"})
        except HttpError as e:
            print(f"  ERROR: {e}")
            results.append({"name": name, "error": str(e)})

        # Rate limit: wait between uploads
        if name != names[-1]:
            print("  Waiting 5s before next upload...")
            time.sleep(5)

    print("\n=== Upload Summary ===")
    for r in results:
        if "url" in r:
            print(f"  {r['name']:20s} -> {r['url']}")
        else:
            print(f"  {r['name']:20s} -> ERROR: {r['error'][:80]}")

    # Save results
    results_file = SHORTS_DIR / "upload_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_file}")


if __name__ == "__main__":
    main()
