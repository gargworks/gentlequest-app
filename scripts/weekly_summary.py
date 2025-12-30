#!/usr/bin/env python3
"""
Weekly Summary Generator
Aggregates the last 7 daily digests into a weekly summary.
Run via cron on Sundays: 0 9 * * 0 python3 scripts/weekly_summary.py
"""
import os
import re
import json
import datetime
import requests
from pathlib import Path
from google import genai

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent

# Load .env file if it exists (for cron jobs)
ENV_FILE = PROJECT_ROOT / ".env"
if ENV_FILE.exists():
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if key not in os.environ:
                    os.environ[key] = value

BRAIN_PATH = PROJECT_ROOT / ".brain"
LEDGER_PATH = BRAIN_PATH / "ledger"
DIGEST_PATH = LEDGER_PATH / "daily_digest.md"
WEEKLY_PATH = LEDGER_PATH / "weekly_summary.md"
EVENTS_FILE = LEDGER_PATH / "events.jsonl"
MODEL_ID = "gemini-2.0-flash-exp"

# Telegram config (loaded from .env or environment)
TG_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7575125475")


def get_timestamp():
    return datetime.datetime.now().isoformat()


def emit_event(event_type: str, severity: str, payload: dict):
    """Emit an event to events.jsonl."""
    event = {
        "timestamp": get_timestamp(),
        "event_type": event_type,
        "emitter": "weekly_summary",
        "severity": severity,
        "payload": payload
    }
    with open(EVENTS_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")


def send_telegram_notification(message: str) -> bool:
    """Send notification to Telegram."""
    if not TG_BOT_TOKEN:
        return False
    
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TG_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
        return resp.status_code == 200
    except Exception:
        return False


def extract_last_7_days_digests() -> list:
    """Extract the last 7 daily report sections from daily_digest.md"""
    if not DIGEST_PATH.exists():
        return []
    
    content = DIGEST_PATH.read_text(encoding='utf-8')
    
    # Split by report headers
    reports = re.split(r'\n---\n\n## 🌙 Nightly Report: ', content)
    
    # Get last 7 (skip first empty element)
    recent_reports = reports[-7:] if len(reports) > 7 else reports[1:]
    
    return recent_reports


def get_events_summary() -> dict:
    """Get summary of events from the last 7 days."""
    if not EVENTS_FILE.exists():
        return {"total": 0, "by_type": {}}
    
    seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    
    events = []
    with open(EVENTS_FILE, 'r') as f:
        for line in f:
            try:
                event = json.loads(line)
                event_time = datetime.datetime.fromisoformat(event['timestamp'].replace('+0530', '+05:30'))
                if event_time > seven_days_ago:
                    events.append(event)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    
    # Group by type
    by_type = {}
    for e in events:
        t = e.get('event_type', 'unknown')
        by_type[t] = by_type.get(t, 0) + 1
    
    return {"total": len(events), "by_type": by_type}


def generate_weekly_summary(client, digests: list, events_summary: dict) -> str:
    """Generate a weekly summary using Gemini."""
    
    # Combine recent digests
    digest_text = "\n\n---\n\n".join(digests)[:4000]
    
    prompt = f"""
Analyze the last 7 days of nightly reports and create a weekly summary.

NIGHTLY REPORTS:
{digest_text}

EVENTS THIS WEEK:
Total: {events_summary['total']}
By type: {json.dumps(events_summary['by_type'], indent=2)}

OUTPUT FORMAT:
# 📊 Weekly Summary

## Week of [date range]

### Highlights
- [Key accomplishment 1]
- [Key accomplishment 2]
- [Key accomplishment 3]

### Patterns Noticed
- [Recurring theme from daily reports]
- [Area of improvement]

### Tests & Code Health
- Test pass rate this week
- Any recurring issues

### Strategic Alignment
- Were we building the right things?
- Musk Method verdict

### Next Week Focus
- [Priority 1]
- [Priority 2]

Keep it under 200 words. Be actionable.
"""
    
    response = client.models.generate_content(model=MODEL_ID, contents=prompt)
    return response.text


def main():
    print("📊 Weekly Summary Generator Starting...")
    print(f"   Time: {get_timestamp()}")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        return

    client = genai.Client(api_key=api_key)
    
    emit_event("weekly_summary_started", "ROUTINE", {"time": get_timestamp()})
    
    # Get last 7 days of digests
    print("📖 Extracting last 7 days of digests...")
    digests = extract_last_7_days_digests()
    print(f"   Found {len(digests)} daily reports")
    
    # Get events summary
    print("📈 Analyzing events...")
    events_summary = get_events_summary()
    print(f"   {events_summary['total']} events this week")
    
    # Generate summary
    print("✍️ Generating weekly summary...")
    summary = generate_weekly_summary(client, digests, events_summary)
    
    # Save to file
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    header = f"\n\n---\n\n# Week Ending: {today}\n"
    
    with open(WEEKLY_PATH, "a") as f:
        f.write(header + summary)
    
    print(f"   ✅ Saved to {WEEKLY_PATH}")
    
    # Send Telegram notification
    print("📱 Sending Telegram notification...")
    tg_message = f"""📊 *Weekly Summary Ready*

_{today}_

{summary[:500]}...

_Full report in weekly\\_summary.md_"""
    
    if send_telegram_notification(tg_message):
        print("   ✅ Telegram sent!")
    else:
        print("   ⚠️ Telegram skipped (no token)")
    
    emit_event("weekly_summary_completed", "NOTABLE", {
        "digests_analyzed": len(digests),
        "events_count": events_summary['total']
    })
    
    print("✅ Weekly summary complete!")


if __name__ == "__main__":
    main()
