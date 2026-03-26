#!/usr/bin/env python3
"""Track and report organic growth metrics from social_log + GA4.

Usage:
    python scripts/growth_tracker.py --status     # One-line summary
    python scripts/growth_tracker.py --report     # Full weekly report → .brain/growth/weekly_report.md
    python scripts/growth_tracker.py --goals      # Compare against targets in goals.json
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GROWTH_DIR = PROJECT_ROOT / ".brain" / "growth"
SOCIAL_LOG = GROWTH_DIR / "social_log.jsonl"
CONTENT_BANK = GROWTH_DIR / "content_bank.jsonl"
GOALS_FILE = GROWTH_DIR / "goals.json"
REPORT_OUT = GROWTH_DIR / "weekly_report.md"
GA4_JSON = PROJECT_ROOT / "metrics" / "analytics_latest.json"


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _parse_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.fromisoformat(raw)
        except (ValueError, TypeError):
            pass
    return None


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------

def compute_metrics() -> dict:
    posts = _load_jsonl(SOCIAL_LOG)
    bank = _load_jsonl(CONTENT_BANK)
    ga4 = _load_json(GA4_JSON)

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # Parse timestamps on successful posts
    successful = []
    for p in posts:
        if not p.get("success"):
            continue
        ts = _parse_ts(p.get("timestamp"))
        successful.append({**p, "_ts": ts})

    # --- Post metrics ---
    total_posts = len(successful)
    this_week = [p for p in successful if p["_ts"] and p["_ts"] >= week_ago]
    posts_this_week = len(this_week)

    # Posts per week (over all history)
    if successful and successful[0].get("_ts"):
        first_ts = min(p["_ts"] for p in successful if p["_ts"])
        span_weeks = max(1, (now - first_ts).days / 7)
        posts_per_week = round(total_posts / span_weeks, 1)
    else:
        posts_per_week = 0

    # Platforms active
    platforms = set(p.get("platform", "unknown") for p in successful)

    # Content bank remaining
    posted_content = set(p.get("content", "") for p in successful)
    bank_remaining = sum(1 for b in bank if b.get("content", "") not in posted_content)

    # Posting streak (consecutive days with ≥1 post, counting back from today)
    if successful:
        post_dates = sorted(set(
            p["_ts"].date() for p in successful if p["_ts"]
        ), reverse=True)
        streak = 0
        check_date = now.date()
        for d in post_dates:
            if d == check_date or d == check_date - timedelta(days=1):
                streak += 1
                check_date = d
            else:
                break
    else:
        streak = 0

    # Best performing category (approximate: keyword bucket)
    categories = Counter()
    category_keywords = {
        "product": ["shipped", "launch", "release", "v0.", "v1.", "feature"],
        "thought-leadership": ["why", "how", "lesson", "built", "approach"],
        "community": ["community", "open", "contributor", "pr", "feedback"],
        "technical": ["api", "local", "memory", "agent", "rag", "model"],
    }
    for p in successful:
        content_lower = (p.get("content") or "").lower()
        matched = False
        for cat, kws in category_keywords.items():
            if any(kw in content_lower for kw in kws):
                categories[cat] += 1
                matched = True
                break
        if not matched:
            categories["general"] += 1

    best_category = categories.most_common(1)[0][0] if categories else "none"

    # --- GA4 metrics (if available) ---
    ga4_summary = None
    if ga4:
        ga4_summary = {
            "users_7d": ga4.get("users_7d") or ga4.get("activeUsers"),
            "sessions_7d": ga4.get("sessions_7d") or ga4.get("sessions"),
            "pageviews_7d": ga4.get("pageviews_7d") or ga4.get("screenPageViews"),
            "top_pages": ga4.get("top_pages", [])[:5],
        }

    return {
        "generated_at": now.isoformat(),
        "total_posts": total_posts,
        "posts_this_week": posts_this_week,
        "posts_per_week": posts_per_week,
        "platforms": sorted(platforms),
        "content_bank_remaining": bank_remaining,
        "posting_streak_days": streak,
        "best_category": best_category,
        "category_breakdown": dict(categories.most_common()),
        "ga4": ga4_summary,
    }


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def one_line_status(m: dict) -> str:
    ga = ""
    if m["ga4"] and m["ga4"].get("users_7d"):
        ga = f" | GA4 {m['ga4']['users_7d']} users/7d"
    return (
        f"Posts: {m['total_posts']} total, {m['posts_this_week']} this week "
        f"({m['posts_per_week']}/wk avg) | "
        f"Streak: {m['posting_streak_days']}d | "
        f"Bank: {m['content_bank_remaining']} remaining | "
        f"Platforms: {', '.join(m['platforms']) or 'none'}"
        f"{ga}"
    )


def full_report(m: dict) -> str:
    lines = [
        f"# Weekly Growth Report",
        f"Generated: {m['generated_at'][:10]}",
        "",
        "## Posting Activity",
        f"- **Total posts:** {m['total_posts']}",
        f"- **This week:** {m['posts_this_week']}",
        f"- **Average:** {m['posts_per_week']} posts/week",
        f"- **Streak:** {m['posting_streak_days']} consecutive days",
        "",
        "## Content Pipeline",
        f"- **Content bank remaining:** {m['content_bank_remaining']} entries",
        f"- **Platforms active:** {', '.join(m['platforms']) or 'none'}",
        "",
        "## Content Categories",
    ]
    for cat, count in m["category_breakdown"].items():
        marker = " (best)" if cat == m["best_category"] else ""
        lines.append(f"- {cat}: {count}{marker}")

    if m["ga4"]:
        ga = m["ga4"]
        lines += [
            "",
            "## Website (GA4)",
            f"- Users (7d): {ga.get('users_7d', 'n/a')}",
            f"- Sessions (7d): {ga.get('sessions_7d', 'n/a')}",
            f"- Pageviews (7d): {ga.get('pageviews_7d', 'n/a')}",
        ]
        if ga.get("top_pages"):
            lines.append("- Top pages:")
            for p in ga["top_pages"]:
                if isinstance(p, dict):
                    lines.append(f"  - {p.get('page', p.get('path', '?'))}: {p.get('views', '?')}")
                else:
                    lines.append(f"  - {p}")
    else:
        lines += ["", "## Website (GA4)", "- No GA4 data found (run `scripts/analytics_dashboard.py` first)"]

    return "\n".join(lines) + "\n"


def goals_comparison(m: dict) -> str:
    goals = _load_json(GOALS_FILE)
    if not goals:
        return f"No goals file found. Create one at {GOALS_FILE}"

    lines = ["# Growth: Actual vs Goals", ""]
    targets = goals.get("weekly_targets", {})

    checks = [
        ("posts_per_week", m["posts_per_week"], targets.get("posts_per_week")),
        ("posting_streak_days", m["posting_streak_days"], targets.get("min_streak_days")),
        ("content_bank_remaining", m["content_bank_remaining"], targets.get("min_content_bank")),
        ("platforms_active", len(m["platforms"]), targets.get("platforms_active")),
    ]
    if m["ga4"] and m["ga4"].get("users_7d"):
        checks.append(("ga4_users_7d", m["ga4"]["users_7d"], targets.get("ga4_users_7d")))

    for name, actual, target in checks:
        if target is None:
            continue
        hit = actual >= target
        icon = "PASS" if hit else "MISS"
        lines.append(f"- [{icon}] {name}: {actual} (target: {target})")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Organic growth metrics tracker")
    parser.add_argument("--status", action="store_true", help="One-line summary")
    parser.add_argument("--report", action="store_true", help="Full weekly report")
    parser.add_argument("--goals", action="store_true", help="Compare against targets")
    args = parser.parse_args()

    if not any([args.status, args.report, args.goals]):
        parser.print_help()
        sys.exit(0)

    m = compute_metrics()

    if args.status:
        print(one_line_status(m))

    if args.report:
        report = full_report(m)
        os.makedirs(GROWTH_DIR, exist_ok=True)
        with open(REPORT_OUT, "w") as f:
            f.write(report)
        print(report)
        print(f"\nSaved to {REPORT_OUT}")

    if args.goals:
        print(goals_comparison(m))


if __name__ == "__main__":
    main()
