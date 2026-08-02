#!/usr/bin/env python3
"""
GentleQuest Traffic & Growth Report — queries production Neon DB + sends Telegram.

Usage:
    python3 gq_traffic_report.py --mode daily    # yesterday's stats
    python3 gq_traffic_report.py --mode weekly   # last 7 days + week-over-week
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

try:
    import psycopg2
except ImportError:
    sys.path.insert(0, "/Users/lokeshgarg/ai-mvp-backend/.venv/lib/python3.12/site-packages")
    import psycopg2

# --- Config ---
NEON_API_KEY = os.environ.get("NEON_API_KEY", "")
NEON_PROJECT_ID = "quiet-poetry-21495159"
NEON_BRANCH_ID = "br-summer-queen-aockr9yn"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Lokesh's session (ved) — excluded from "real users" count
OWNER_SESSION = "30455ab2-5799-4798-9501-58e58bde96d7"

# Test sessions from agent API checks (Aug 2)
TEST_SESSIONS = {
    "b8977ef0-189d-4356-a90c-bef9a23342fd",
    "4130d9e7-cf24-47be-92cc-2aa321d30816",
    "381429ef-3c02-4889-a045-488a2db01f8e",
    "d8470dae-3a4f-4819-8946-0a52afa564a5",
}


def get_neon_uri():
    """Get Neon connection URI via API."""
    if NEON_API_KEY:
        url = (f"https://console.neon.tech/api/v2/projects/{NEON_PROJECT_ID}"
               f"/connection_uri?branch_id={NEON_BRANCH_ID}"
               f"&database_name=neondb&role_name=neondb_owner")
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {NEON_API_KEY}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("connection_uri", data.get("uri", ""))
    # Fallback: try to read from ai-mvp-backend .env DATABASE_URL
    return None


def send_telegram(text):
    """Send a message to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("WARNING: Telegram credentials not set, skipping alert", file=sys.stderr)
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
    except Exception as e:
        print(f"Telegram send failed: {e}", file=sys.stderr)
        return False


def query_db(uri, sql, params=None):
    """Execute a query and return rows."""
    conn = psycopg2.connect(uri)
    cursor = conn.cursor()
    cursor.execute(sql, params or ())
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description] if cursor.description else []
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


def get_funnel_from_api():
    """Get funnel metrics from the production API."""
    try:
        url = "https://gentlequest.onrender.com/api/metrics/funnel?days=7"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return {}


def daily_report(uri):
    """Generate yesterday's traffic report."""
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    y_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    y_end = y_start + timedelta(days=1)

    # Sessions
    sessions = query_db(uri, """
        SELECT COUNT(*) as count FROM user_sessions
        WHERE created_at >= %s AND created_at < %s
    """, (y_start, y_end))[0]["count"]

    # Real sessions (exclude owner + test)
    real_sessions = query_db(uri, """
        SELECT COUNT(*) as count FROM user_sessions
        WHERE created_at >= %s AND created_at < %s
        AND id != %s AND id NOT IN %s
    """, (y_start, y_end, OWNER_SESSION, tuple(TEST_SESSIONS)))[0]["count"]

    # Chat messages
    chat = query_db(uri, """
        SELECT COUNT(*) as count, COUNT(DISTINCT session_id) as unique_sessions
        FROM chat_messages WHERE timestamp >= %s AND timestamp < %s
    """, (y_start, y_end))[0]

    # Real chat (exclude owner)
    real_chat = query_db(uri, """
        SELECT COUNT(*) as count FROM chat_messages
        WHERE timestamp >= %s AND timestamp < %s AND session_id != %s
    """, (y_start, y_end, OWNER_SESSION))[0]["count"]

    # Mood entries
    mood = query_db(uri, """
        SELECT COUNT(*) as count FROM mood_entries
        WHERE timestamp >= %s AND timestamp < %s
    """, (y_start, y_end))[0]["count"]

    # Newsletter subscribers
    try:
        newsletter = query_db(uri, """
            SELECT COUNT(*) as count FROM newsletter_subscribers
            WHERE subscribed_at >= %s AND subscribed_at < %s AND active = true
        """, (y_start, y_end))[0]["count"]
    except Exception:
        newsletter = "?"

    # Total active newsletter subscribers
    try:
        newsletter_total = query_db(uri, """
            SELECT COUNT(*) as count FROM newsletter_subscribers WHERE active = true
        """)[0]["count"]
    except Exception:
        newsletter_total = "?"

    # Funnel from API
    funnel = get_funnel_from_api()
    f_counts = funnel.get("counts", {})

    # Blog posts published yesterday
    blog_dir = "/Users/lokeshgarg/gentlequest/gentlequest-blog/src/content/blog"
    blog_count = 0
    if os.path.isdir(blog_dir):
        for fname in os.listdir(blog_dir):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(blog_dir, fname)
            try:
                with open(fpath) as f:
                    for line in f:
                        if line.startswith("pubDate:"):
                            pub = line.split(":", 1)[1].strip()[:10]
                            if pub == y_start.strftime("%Y-%m-%d"):
                                blog_count += 1
                            break
            except Exception:
                pass

    date_str = y_start.strftime("%Y-%m-%d")
    lines = [
        f"GentleQuest Daily Report — {date_str}",
        "",
        f"Sessions: {sessions} total ({real_sessions} real)",
        f"Chat messages: {chat['count']} ({chat['unique_sessions']} unique sessions)",
        f"Real user chat: {real_chat}",
        f"Mood entries: {mood}",
        f"Newsletter: {newsletter} new ({newsletter_total} total active)",
        f"Blog posts published: {blog_count}",
        "",
        f"Funnel (last 7d): {f_counts.get('landing_sessions', 0)} sessions, "
        f"{f_counts.get('cta_clicks', 0)} CTA clicks, "
        f"{f_counts.get('first_value_actions', 0)} first value actions",
        f"CTA CTR: {funnel.get('cta_ctr', 0)*100:.1f}%",
    ]

    # Alert flags
    alerts = []
    if real_chat == 0 and real_sessions == 0:
        days_since = days_since_last_real_user(uri)
        alerts.append(f"NO REAL USERS ({days_since} days since last real user)")
    if f_counts.get("cta_clicks", 0) == 0 and f_counts.get("landing_sessions", 0) > 0:
        alerts.append("CTA still at 0% CTR")
    if mood == 0:
        days_since_mood = days_since_last_mood(uri)
        if days_since_mood > 7:
            alerts.append(f"Mood tracking dead ({days_since_mood} days since last entry)")

    if alerts:
        lines.append("")
        lines.append("ALERTS:")
        for a in alerts:
            lines.append(f"  - {a}")

    return "\n".join(lines)


def weekly_report(uri):
    """Generate last 7 days report with week-over-week comparison."""
    now = datetime.now(timezone.utc)
    this_week_start = now - timedelta(days=7)
    last_week_start = now - timedelta(days=14)

    # This week sessions
    this_sessions = query_db(uri, """
        SELECT COUNT(*) as count FROM user_sessions WHERE created_at >= %s
    """, (this_week_start,))[0]["count"]

    # Last week sessions
    last_sessions = query_db(uri, """
        SELECT COUNT(*) as count FROM user_sessions
        WHERE created_at >= %s AND created_at < %s
    """, (last_week_start, this_week_start))[0]["count"]

    # Real sessions this week
    this_real = query_db(uri, """
        SELECT COUNT(*) as count FROM user_sessions
        WHERE created_at >= %s AND id != %s AND id NOT IN %s
    """, (this_week_start, OWNER_SESSION, tuple(TEST_SESSIONS)))[0]["count"]

    last_real = query_db(uri, """
        SELECT COUNT(*) as count FROM user_sessions
        WHERE created_at >= %s AND created_at < %s AND id != %s
    """, (last_week_start, this_week_start, OWNER_SESSION))[0]["count"]

    # Chat this week
    this_chat = query_db(uri, """
        SELECT COUNT(*) as count, COUNT(DISTINCT session_id) as unique_sessions
        FROM chat_messages WHERE timestamp >= %s
    """, (this_week_start,))[0]

    last_chat = query_db(uri, """
        SELECT COUNT(*) as count, COUNT(DISTINCT session_id) as unique_sessions
        FROM chat_messages WHERE timestamp >= %s AND timestamp < %s
    """, (last_week_start, this_week_start))[0]

    # Real chat this week
    this_real_chat = query_db(uri, """
        SELECT COUNT(*) as count FROM chat_messages
        WHERE timestamp >= %s AND session_id != %s
    """, (this_week_start, OWNER_SESSION))[0]["count"]

    last_real_chat = query_db(uri, """
        SELECT COUNT(*) as count FROM chat_messages
        WHERE timestamp >= %s AND timestamp < %s AND session_id != %s
    """, (last_week_start, this_week_start, OWNER_SESSION))[0]["count"]

    # Mood entries
    this_mood = query_db(uri, """
        SELECT COUNT(*) as count FROM mood_entries WHERE timestamp >= %s
    """, (this_week_start,))[0]["count"]

    last_mood = query_db(uri, """
        SELECT COUNT(*) as count FROM mood_entries
        WHERE timestamp >= %s AND timestamp < %s
    """, (last_week_start, this_week_start))[0]["count"]

    # Funnel
    funnel = get_funnel_from_api()
    f_counts = funnel.get("counts", {})

    # Days since last real user
    days_since_user = days_since_last_real_user(uri)
    days_since_mood = days_since_last_mood(uri)

    # Sessions by day
    by_day = query_db(uri, """
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM user_sessions WHERE created_at >= %s
        GROUP BY DATE(created_at) ORDER BY date DESC
    """, (this_week_start,))

    def trend(curr, prev):
        if prev == 0:
            return "+NEW" if curr > 0 else "—"
        pct = ((curr - prev) / prev) * 100
        return f"+{pct:.0f}%" if pct >= 0 else f"{pct:.0f}%"

    lines = [
        f"GentleQuest Weekly Report — {this_week_start.strftime('%b %d')} to {now.strftime('%b %d')}",
        "",
        "WEEK OVER WEEK",
        f"  Sessions: {this_sessions} (last week: {last_sessions}) {trend(this_sessions, last_sessions)}",
        f"  Real sessions: {this_real} (last week: {last_real}) {trend(this_real, last_real)}",
        f"  Chat messages: {this_chat['count']} (last week: {last_chat['count']}) {trend(this_chat['count'], last_chat['count'])}",
        f"  Real user chat: {this_real_chat} (last week: {last_real_chat}) {trend(this_real_chat, last_real_chat)}",
        f"  Mood entries: {this_mood} (last week: {last_mood}) {trend(this_mood, last_mood)}",
        "",
        f"Funnel (last 7d): {f_counts.get('landing_sessions', 0)} sessions, "
        f"{f_counts.get('cta_clicks', 0)} CTA clicks (CTR: {funnel.get('cta_ctr', 0)*100:.1f}%)",
        "",
        "SESSIONS BY DAY:",
    ]

    for d in by_day:
        lines.append(f"  {d['date']}: {d['count']} sessions")

    lines.extend([
        "",
        f"Days since last real user: {days_since_user}",
        f"Days since last mood entry: {days_since_mood}",
    ])

    # Alerts
    alerts = []
    if this_real_chat == 0:
        alerts.append(f"NO REAL USER CHAT this week ({days_since_user} days since last)")
    if f_counts.get("cta_clicks", 0) == 0:
        alerts.append("CTA still at 0% CTR — broken")
    if this_mood == 0 and days_since_mood > 7:
        alerts.append(f"Mood tracking dead ({days_since_mood} days)")
    if this_real == 0 and this_sessions > 0:
        alerts.append(f"{this_sessions} sessions but 0 real users — all blog impressions")

    if alerts:
        lines.append("")
        lines.append("ALERTS:")
        for a in alerts:
            lines.append(f"  - {a}")

    return "\n".join(lines)


def days_since_last_real_user(uri):
    """Days since last real user (excluding owner + test sessions) chatted."""
    rows = query_db(uri, """
        SELECT MAX(timestamp) as last FROM chat_messages
        WHERE session_id != %s AND session_id NOT IN %s
        AND content NOT IN ('hello', 'hi', 'hey whats up')
    """, (OWNER_SESSION, tuple(TEST_SESSIONS)))
    last = rows[0].get("last") if rows else None
    if not last:
        return "N/A"
    if isinstance(last, str):
        last = datetime.fromisoformat(last)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - last
    return delta.days


def days_since_last_mood(uri):
    """Days since last mood entry."""
    rows = query_db(uri, "SELECT MAX(timestamp) as last FROM mood_entries")
    last = rows[0].get("last") if rows else None
    if not last:
        return "N/A"
    if isinstance(last, str):
        last = datetime.fromisoformat(last)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - last
    return delta.days


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["daily", "weekly"], required=True)
    args = parser.parse_args()

    uri = get_neon_uri()
    if not uri:
        print("ERROR: Could not get Neon URI", file=sys.stderr)
        sys.exit(1)

    if args.mode == "daily":
        report = daily_report(uri)
    else:
        report = weekly_report(uri)

    print(report)
    print()
    send_telegram(report)


if __name__ == "__main__":
    main()
