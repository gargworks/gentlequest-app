#!/usr/bin/env python3
"""Enqueue X posts for all 17 scheduled GQ YouTube shorts via Buffer."""
import json, subprocess
from pathlib import Path

WORKER_URL = "https://growth-scheduler.morning-lake-f944.workers.dev"
ADMIN_SECRET = "4a38bba572b8aeb754066e338895c16e8cdae45d6983343f1282d56bf7cb36af"

# v2-v18 schedule (v1 already live)
SCHEDULE = {
    "v2":  ("2026-06-23", "0XRdun421Jw", "Safety plan — not buried in settings"),
    "v3":  ("2026-06-26", "xtdCaGJBeE0", "Mood tracking without streaks or guilt"),
    "v4":  ("2026-06-30", "nFsl-EcLtfk", "Tiny quests — no homework feel"),
    "v5":  ("2026-07-03", "N6C2BXQjWfo", "Not an AI therapist"),
    "v6":  ("2026-07-07", "hNXwLzZUlkU", "GentleQuest is in beta — free, no ads"),
    "v7":  ("2026-07-08", "RJzNVEa743o", "A journal that is just yours"),
    "v8":  ("2026-07-09", "AE6V33f9jLA", "Your data is yours — export, delete, or go anonymous"),
    "v9":  ("2026-07-10", "5Y286NeQgO4", "Grounding 5-4-3-2-1 — 60 seconds back to now"),
    "v10": ("2026-07-11", "ABwSvbXpvwg", "This is not social media"),
    "v11": ("2026-07-12", "N-Yv9YI2biA", "First 30 seconds in the app"),
    "v12": ("2026-07-13", "f-6DDMX2LGo", "Real PHQ-9 clinical screening — not just chat"),
    "v13": ("2026-07-14", "5Cd3nK5J7Xk", "A week of moods — patterns, not streaks"),
    "v14": ("2026-07-15", "JgfgkrYWgIE", "Journaling without pressure"),
    "v15": ("2026-07-16", "d1aI5Gb5oWU", "90 second box breathing"),
    "v16": ("2026-07-17", "gQZ7HrmU0eU", "This app is 18+ only — we mean it"),
    "v17": ("2026-07-18", "38LRFHiKU9I", "Safety contacts — one tap to call"),
    "v18": ("2026-07-19", "UlHNIbuFap4", "We are not a therapist — we are a bridge"),
}

enqueued = 0
for vname, (date_str, vid_id, hook) in SCHEDULE.items():
    yt_url = f"https://youtube.com/shorts/{vid_id}"
    post_text = f"{hook}\n\n{yt_url}\n\niOS — https://apps.apple.com/app/gentlequest/id6756537464\nAndroid — https://play.google.com/store/apps/details?id=com.gentlequest.app\n\nFree. 18+. No ads."

    # 10:05 IST = 04:35 UTC
    scheduled_utc = f"{date_str}T04:35:00Z"

    payload = json.dumps({
        "channel": "buffer",
        "target": "x",
        "text": post_text,
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
            print(f"  {vname}: enqueued for {date_str} 10:05 IST -> {resp['entry']['id']}")
            enqueued += 1
        else:
            print(f"  {vname}: ERROR -> {resp}")
    except:
        print(f"  {vname}: ERROR -> {result.stdout[:100]}")

print(f"\nEnqueued {enqueued} X posts via Buffer")
