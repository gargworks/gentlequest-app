#!/usr/bin/env python3
"""Post + pin comments on all live GQ YouTube shorts.

Re-auths with full youtube scope (includes comments). Posts the matching
pinned comment from pinned_comments.md on each public video.
"""
import json, re
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CLIENT_SECRET = Path("/Users/lokeshgarg/Downloads/client_secret_680543456536-pssc73p4dgiij83f88gb682v2fh47n29.apps.googleusercontent.com.json")
TOKEN_FILE = Path(__file__).resolve().parent / "youtube_token.json"
PINNED_COMMENTS = Path(__file__).resolve().parent / "pinned_comments.md"

# Full scope — includes comment posting
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

# All video IDs and their names
ALL_VIDEOS = {
    "hKeBrT7C3V4": "v1",
    "0XRdun421Jw": "v2",
    "xtdCaGJBeE0": "v3",
    "nFsl-EcLtfk": "v4",
    "N6C2BXQjWfo": "v5",
    "hNXwLzZUlkU": "v6",
    "RJzNVEa743o": "v7",
    "AE6V33f9jLA": "v8",
    "5Y286NeQgO4": "v9",
    "ABwSvbXpvwg": "v10",
    "N-Yv9YI2biA": "v11",
    "f-6DDMX2LGo": "v12",
    "5Cd3nK5J7Xk": "v13",
    "JgfgkrYWgIE": "v14",
    "d1aI5Gb5oWU": "v15",
    "gQZ7HrmU0eU": "v16",
    "38LRFHiKU9I": "v17",
    "UlHNIbuFap4": "v18",
}

def get_creds():
    # Force re-auth with full scope
    TOKEN_FILE.unlink(missing_ok=True)
    print("Re-authenticating with full YouTube scope (includes comments)...")
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    TOKEN_FILE.write_text(creds.to_json())
    print(f"Token saved to {TOKEN_FILE}")
    return creds

def parse_pinned_comments():
    """Parse pinned_comments.md into {video_name: comment_text}"""
    content = PINNED_COMMENTS.read_text()
    comments = {}
    # Match ## vN — ... blocks
    blocks = re.split(r'\n## (v\d+)', content)
    for i in range(1, len(blocks), 2):
        name = blocks[i]
        block = blocks[i+1] if i+1 < len(blocks) else ""
        # Extract comment from code block
        m = re.search(r'```\n(.+?)```', block, re.DOTALL)
        if m:
            comments[name] = m.group(1).strip()
    return comments

def main():
    creds = get_creds()
    yt = build("youtube", "v3", credentials=creds)
    comments = parse_pinned_comments()
    print(f"\nParsed {len(comments)} pinned comments")

    # Get all videos and their privacy status
    video_ids = list(ALL_VIDEOS.keys())
    posted = []
    for vid_id, vname in ALL_VIDEOS.items():
        # Check if video is public
        resp = yt.videos().list(part="status,snippet", id=vid_id).execute()
        if not resp.get("items"):
            print(f"  {vname}: video not found")
            continue
        status = resp["items"][0]["status"]
        privacy = status.get("privacyStatus", "?")
        title = resp["items"][0]["snippet"]["title"][:40]

        if privacy != "public":
            print(f"  {vname} ({privacy}): skipped — not public yet")
            continue

        comment_text = comments.get(vname)
        if not comment_text:
            print(f"  {vname}: no pinned comment found")
            continue

        print(f"  {vname} (public): posting comment...")
        try:
            resp = yt.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": vid_id,
                        "topLevelComment": {
                            "snippet": {"textOriginal": comment_text}
                        }
                    }
                }
            ).execute()
            comment_id = resp["id"]
            print(f"    Posted: {comment_id}")
            posted.append({"video": vname, "video_id": vid_id, "comment_id": comment_id})
        except Exception as e:
            print(f"    ERROR: {e}")

    print(f"\n=== Posted {len(posted)} comments ===")
    for p in posted:
        print(f"  {p['video']} -> {p['comment_id']}")

if __name__ == "__main__":
    main()
