#!/usr/bin/env python3
"""Enqueue strategically-timed GQ posts to X + FB via Buffer.

Strategy:
- YouTube: 10:00 IST (already scheduled) — morning consumption
- X (@GentleQuestApp): 18:30 IST same day — evening engagement, 8.5h offset
  - Only 8 strongest hooks (every 2-3 days, not daily)
- Facebook (GentleQuest page): 09:00 IST NEXT DAY — 23h offset, different demographic
  - Same 8 hooks as X — FB audience is different, no duplicate-content penalty
"""
import json, subprocess

WORKER_URL = "https://growth-scheduler.morning-lake-f944.workers.dev"
ADMIN_SECRET = "4a38bba572b8aeb754066e338895c16e8cdae45d6983343f1282d56bf7cb36af"

from datetime import datetime, timedelta

POSTS = [
    ("v2",  "2026-06-23", "0XRdun421Jw",
     "Your safety plan shouldn't be buried in Settings.\n\nIt's at the top of your profile. One tap.\n\nhttps://youtube.com/shorts/0XRdun421Jw\n\niOS — https://apps.apple.com/app/gentlequest/id6756537464\nAndroid — https://play.google.com/store/apps/details?id=com.gentlequest.app\n\nFree. 18+. No ads."),
    ("v5",  "2026-07-03", "N6C2BXQjWfo",
     "We're not an AI therapist.\n\nWe're a quiet chat that happens to be AI. Real disclosures happen here. We take that seriously.\n\nhttps://youtube.com/shorts/N6C2BXQjWfo\n\niOS — https://apps.apple.com/app/gentlequest/id6756537464\nAndroid — https://play.google.com/store/apps/details?id=com.gentlequest.app"),
    ("v7",  "2026-07-08", "RJzNVEa743o",
     "A journal that is just yours.\n\nNo AI reads it. No prompts. No streaks. Just a blank page.\n\nhttps://youtube.com/shorts/RJzNVEa743o\n\niOS — https://apps.apple.com/app/gentlequest/id6756537464\nAndroid — https://play.google.com/store/apps/details?id=com.gentlequest.app\n\nFree. 18+. No ads."),
    ("v8",  "2026-07-09", "AE6V33f9jLA",
     "Your data is yours.\n\nExport everything. Delete everything. Or go anonymous — no account, no email, no tracking.\n\nhttps://youtube.com/shorts/AE6V33f9jLA\n\niOS — https://apps.apple.com/app/gentlequest/id6756537464\nAndroid — https://play.google.com/store/apps/details?id=com.gentlequest.app"),
    ("v9",  "2026-07-10", "5Y286NeQgO4",
     "Anxious? Try this.\n\n5 things you see. 4 you can touch. 3 you can hear. 2 you can smell. 1 you can taste.\n\n60 seconds. Back to now.\n\nhttps://youtube.com/shorts/5Y286NeQgO4\n\nFree. 18+. No ads."),
    ("v12", "2026-07-13", "f-6DDMX2LGo",
     "Real PHQ-9 screening. Not just chat.\n\nA validated tool clinicians use. Honest results. And a safety plan if you need one.\n\nNot a diagnosis. A starting point.\n\nhttps://youtube.com/shorts/f-6DDMX2LGo\n\niOS — https://apps.apple.com/app/gentlequest/id6756537464"),
    ("v17", "2026-07-18", "38LRFHiKU9I",
     "Who do you call?\n\nAdd people you trust to your safety plan. One tap to call when you need them.\n\nFill it now. Find it later.\n\nhttps://youtube.com/shorts/38LRFHiKU9I\n\niOS — https://apps.apple.com/app/gentlequest/id6756537464\nAndroid — https://play.google.com/store/apps/details?id=com.gentlequest.app"),
    ("v18", "2026-07-19", "UlHNIbuFap4",
     "We are not a therapist.\n\nWe are a quiet chat. Real disclosures happen here. We take that seriously.\n\nNot a replacement. A bridge.\n\nhttps://youtube.com/shorts/UlHNIbuFap4\n\niOS — https://apps.apple.com/app/gentlequest/id6756537464\nAndroid — https://play.google.com/store/apps/details?id=com.gentlequest.app"),
]

def enqueue(target, text, scheduled_utc, label):
    payload = json.dumps({
        "channel": "buffer",
        "target": target,
        "text": text,
        "scheduled_for": scheduled_utc,
        "approval_status": "approved",
    })
    result = subprocess.run([
        "curl", "-s", "-X", "POST", WORKER_URL + "/queue",
        "-H", f"Authorization: Bearer {ADMIN_SECRET}",
        "-H", "Content-Type: application/json",
        "-d", payload,
    ], capture_output=True, text=True)
    try:
        resp = json.loads(result.stdout)
        if resp.get("ok"):
            print(f"    {label}: {resp['entry']['id']}")
            return True
        else:
            print(f"    {label}: ERROR -> {resp}")
    except:
        print(f"    {label}: ERROR -> {result.stdout[:80]}")
    return False

x_count = 0
fb_count = 0
for vname, date, vid_id, text in POSTS:
    yt_date = datetime.strptime(date, "%Y-%m-%d")
    print(f"\n  {vname} ({date}):")

    # X: same day 18:30 IST = 13:00 UTC
    x_time = f"{date}T13:00:00Z"
    if enqueue("gq_x", text, x_time, f"X 18:30 IST"):
        x_count += 1

    # FB: next day 09:00 IST = 03:30 UTC
    fb_date = (yt_date + timedelta(days=1)).strftime("%Y-%m-%d")
    fb_time = f"{fb_date}T03:30:00Z"
    if enqueue("gq_fb", text, fb_time, f"FB 09:00 IST +1d"):
        fb_count += 1

print(f"\n=== Summary ===")
print(f"  X posts:  {x_count} (evening IST, same day as YT)")
print(f"  FB posts: {fb_count} (morning IST, day after YT)")
print(f"\nStrategy:")
print(f"  YouTube 10:00 IST — morning consumption")
print(f"  X       18:30 IST — evening engagement (8.5h offset)")
print(f"  FB      09:00 IST next day — different demographic (23h offset)")
