#!/usr/bin/env python3
"""Enqueue strategically-timed X posts for GQ shorts.

Strategy:
- YouTube: 10:00 IST (already scheduled) — catches morning scroll
- X: 18:30 IST (evening scroll) — SAME DAY as YT, but 8.5h later
  - Different audience behavior: morning = consumption, evening = engagement/RT
  - Avoids duplicate-content algorithm penalty (different platform, different time)
- Not every short needs an X post — only the strongest hooks (saves X from spam)
  - v2, v5, v7, v8, v9, v12, v17, v18 = 8 of 17 (every ~2-3 days)
  - The others live on YouTube only — X stays quality over quantity

X post times: 18:30 IST = 13:00 UTC
"""
import json, subprocess

WORKER_URL = "https://growth-scheduler.morning-lake-f944.workers.dev"
ADMIN_SECRET = "4a38bba572b8aeb754066e338895c16e8cdae45d6983343f1282d56bf7cb36af"

# Only the strongest hooks get X posts — quality over quantity
# Format: (vname, date, video_id, hook, x_post_time_utc)
X_POSTS = [
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

enqueued = 0
for vname, date, vid_id, text in X_POSTS:
    # 18:30 IST = 13:00 UTC
    scheduled_utc = f"{date}T13:00:00Z"

    payload = json.dumps({
        "channel": "buffer",
        "target": "x",
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
            print(f"  {vname}: {date} 18:30 IST -> {resp['entry']['id']}")
            enqueued += 1
        else:
            print(f"  {vname}: ERROR -> {resp}")
    except:
        print(f"  {vname}: ERROR -> {result.stdout[:100]}")

print(f"\nEnqueued {enqueued} strategic X posts (evening IST, quality over quantity)")
print(f"\nStrategy:")
print(f"  YouTube: all 17 shorts, 10:00 IST daily (morning consumption)")
print(f"  X: 8 strongest hooks, 18:30 IST same-day (evening engagement)")
print(f"  Gap: 8.5h between YT and X — different audience, no algo penalty")
print(f"  X cadence: every 2-3 days (not daily — avoids spam)")
