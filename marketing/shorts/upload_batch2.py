#!/usr/bin/env python3
"""Upload v13-v18 shorts to YouTube."""
import json, time
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN = Path(__file__).resolve().parent / "youtube_token.json"
FINAL = Path(__file__).resolve().parent / "out" / "final"
META = Path(__file__).resolve().parent / "temp" / "v13_v18_meta.json"

creds = Credentials.from_authorized_user_file(str(TOKEN), [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
])
if not creds.valid:
    creds.refresh(Request())

yt = build("youtube", "v3", credentials=creds)
videos = json.loads(META.read_text())

results = []
for v in videos:
    name = v["name"]
    file_path = v["file"]
    print(f"\n=== {name} ===")
    body = {
        "snippet": {"title": v["title"], "description": v["description"], "tags": v["tags"], "categoryId": "26"},
        "status": {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(file_path, mimetype="video/mp4", resumable=True, chunksize=10*1024*1024)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"  {int(status.progress()*100)}%")
    vid = resp["id"]
    url = f"https://youtube.com/shorts/{vid}"
    print(f"  Done: {url}")
    results.append({"name": name, "video_id": vid, "url": url})
    time.sleep(5)

out = FINAL / "upload_results_v13_v18.json"
out.write_text(json.dumps(results, indent=2))
print(f"\n=== Summary ===")
for r in results:
    print(f"  {r['name']:20s} -> {r['url']}")
print(f"\nSaved to {out}")
