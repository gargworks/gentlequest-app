#!/usr/bin/env python3
"""
GentleQuest Analytics Dashboard
Pulls GA4 data, saves JSON + human-readable report.

Usage:
  python3 scripts/analytics_dashboard.py              # Full report
  python3 scripts/analytics_dashboard.py --json-only  # JSON only (for cron)

Output:
  metrics/analytics_latest.json   — Machine-readable snapshot
  metrics/analytics_report.md     — Human-readable report
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# NOTE: the google.* GA4 client imports are wrapped in try/except so this
# module is importable (and `is_qualified_human` is usable) without the GA4
# client libraries installed. The GA4-dependent functions (get_client,
# run_report, pull_*, main) raise on use when google isn't available; the
# bot-filter rule set is side-effect free on import — required by the
# Qualified Activation Proof (Task 5).
try:  # pragma: no cover - import guard
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        RunReportRequest, DateRange, Dimension, Metric, OrderBy,
        FilterExpression, Filter,
    )
    from google.oauth2 import service_account
except ImportError:  # GA4 client libs not installed in this environment.
    BetaAnalyticsDataClient = None  # type: ignore[assignment]
    RunReportRequest = None  # type: ignore[assignment]
    DateRange = None  # type: ignore[assignment]
    Dimension = None  # type: ignore[assignment]
    Metric = None  # type: ignore[assignment]
    OrderBy = None  # type: ignore[assignment]
    FilterExpression = None  # type: ignore[assignment]
    Filter = None  # type: ignore[assignment]
    service_account = None  # type: ignore[assignment]

# ── Config ──
PROPERTY_ID = "516568186"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CREDS_PATH = PROJECT_ROOT / "secret" / "gentlequest-prod-sa.json"
METRICS_DIR = PROJECT_ROOT / "metrics"
JSON_OUT = METRICS_DIR / "analytics_latest.json"
REPORT_OUT = METRICS_DIR / "analytics_report.md"
HISTORY_DIR = METRICS_DIR / "history"


# ── Bot / crawler filter (Qualified Activation Proof, Task 5) ──

# Substrings matched case-insensitively against the User-Agent string. Any
# match disqualifies the session from the qualified-human funnel counts.
_BOT_UA_SUBSTRINGS = (
    "googlebot", "bingbot", "yandex", "baiduspider", "duckduckbot", "slirp",
    "semrush", "ahrefs", "petalbot", "applebot", "facebookexternalhit",
    "twitterbot", "linkedinbot", "telegrambot", "whatsapp",
    "python-requests", "curl", "wget", "selenium", "puppeteer", "playwright",
    "headlesschrome", "phantomjs", "okhttp", "go-http-client", "apachebench",
    "jmeter", "gtmhub", "googlestackdriver", "uptimerobot", "site24x7",
    "newrelicpinger", "dotcommonitor", "statuscake",
)


def is_qualified_human(session_metadata, user_agent, duration_seconds, pageviews):
    """Return True only if the session is likely a real human.

    Used by the activation funnel (Task 6) to exclude crawlers, agents, and
    headless automation from the qualified-human gate counts. Returns False
    if ANY of the bot rules match; otherwise True.

    Args:
        session_metadata: opaque session metadata dict (currently unused by the
            rule set but accepted so callers can pass it through unchanged;
            kept in the signature for forward-compat — e.g. future rules may
            inspect IP/ASN/referrer fields without changing the call site).
        user_agent: raw User-Agent header string (or None).
        duration_seconds: session duration in seconds (float/int).
        pageviews: number of page views in the session (int).

    Returns:
        bool — True if the session passes the human filter, False otherwise.
    """
    # Rule: empty / None / too-short UA → not a real browser.
    if not user_agent or not isinstance(user_agent, str) or len(user_agent) < 20:
        return False

    ua_lower = user_agent.lower()

    # Rule: known crawler / bot / automation UA substrings.
    for needle in _BOT_UA_SUBSTRINGS:
        if needle in ua_lower:
            return False

    # Rule: desktop Linux (Linux present, Android absent) with a sub-2s
    # single-pageview session — classic headless/CI fingerprint. Mobile
    # Android UAs also contain "Linux" but are exempted by the Android check.
    is_linux_desktop = "linux" in ua_lower and "android" not in ua_lower
    try:
        dur = float(duration_seconds)
    except (TypeError, ValueError):
        dur = 0.0
    try:
        pv = int(pageviews)
    except (TypeError, ValueError):
        pv = 0
    if is_linux_desktop and dur < 2.0 and pv == 1:
        return False

    return True


def get_client():
    creds = service_account.Credentials.from_service_account_file(
        str(CREDS_PATH),
        scopes=["https://www.googleapis.com/auth/analytics.readonly"],
    )
    return BetaAnalyticsDataClient(credentials=creds)


def run_report(client, date_range, dimensions=None, metrics=None,
               order_bys=None, dim_filter=None, limit=0, max_retries=3):
    """Wrapper around GA4 runReport with retry + exponential backoff."""
    import time
    from google.api_core.exceptions import DeadlineExceeded

    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[date_range],
        dimensions=dimensions or [],
        metrics=metrics or [],
        order_bys=order_bys or [],
        dimension_filter=dim_filter,
        limit=limit,
    )
    for attempt in range(max_retries):
        try:
            return client.run_report(request=req)
        except DeadlineExceeded:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  GA4 timeout (attempt {attempt + 1}/{max_retries}), retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


def extract_rows(resp, dim_count=1):
    """Extract rows as list of dicts."""
    rows = []
    for row in resp.rows:
        dims = [d.value for d in row.dimension_values]
        vals = [v.value for v in row.metric_values]
        rows.append({"dimensions": dims, "metrics": vals})
    return rows


def pull_overview(client, range_key, date_range):
    resp = run_report(client, date_range, metrics=[
        Metric(name="activeUsers"),
        Metric(name="newUsers"),
        Metric(name="sessions"),
        Metric(name="screenPageViews"),
        Metric(name="engagedSessions"),
        Metric(name="averageSessionDuration"),
        Metric(name="eventCount"),
    ])
    if not resp.rows:
        return {}
    v = [m.value for m in resp.rows[0].metric_values]
    return {
        "active_users": int(v[0]),
        "new_users": int(v[1]),
        "sessions": int(v[2]),
        "screen_views": int(v[3]),
        "engaged_sessions": int(v[4]),
        "avg_session_sec": round(float(v[5]), 1),
        "total_events": int(v[6]),
    }


def pull_daily_users(client, date_range):
    resp = run_report(client, date_range,
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="activeUsers"), Metric(name="newUsers"), Metric(name="sessions")],
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))])
    days = []
    for row in resp.rows:
        d = row.dimension_values[0].value
        days.append({
            "date": f"{d[:4]}-{d[4:6]}-{d[6:]}",
            "active_users": int(row.metric_values[0].value),
            "new_users": int(row.metric_values[1].value),
            "sessions": int(row.metric_values[2].value),
        })
    return days


def pull_events(client, date_range):
    resp = run_report(client, date_range,
        dimensions=[Dimension(name="eventName")],
        metrics=[Metric(name="eventCount")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="eventCount"), desc=True)])
    return {row.dimension_values[0].value: int(row.metric_values[0].value) for row in resp.rows}


def pull_platforms(client, date_range):
    resp = run_report(client, date_range,
        dimensions=[Dimension(name="platform"), Dimension(name="operatingSystem")],
        metrics=[Metric(name="activeUsers"), Metric(name="sessions")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)])
    platforms = []
    for row in resp.rows:
        platforms.append({
            "platform": row.dimension_values[0].value,
            "os": row.dimension_values[1].value,
            "users": int(row.metric_values[0].value),
            "sessions": int(row.metric_values[1].value),
        })
    return platforms


def pull_countries(client, date_range):
    resp = run_report(client, date_range,
        dimensions=[Dimension(name="country")],
        metrics=[Metric(name="activeUsers"), Metric(name="sessions")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)])
    return [{
        "country": row.dimension_values[0].value,
        "users": int(row.metric_values[0].value),
        "sessions": int(row.metric_values[1].value),
    } for row in resp.rows]


def pull_versions(client, date_range):
    resp = run_report(client, date_range,
        dimensions=[Dimension(name="appVersion"), Dimension(name="platform")],
        metrics=[Metric(name="activeUsers"), Metric(name="sessions")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)])
    return [{
        "version": row.dimension_values[0].value,
        "platform": row.dimension_values[1].value,
        "users": int(row.metric_values[0].value),
        "sessions": int(row.metric_values[1].value),
    } for row in resp.rows]


def pull_acquisition(client, date_range):
    resp = run_report(client, date_range,
        dimensions=[Dimension(name="firstUserSource"), Dimension(name="firstUserMedium")],
        metrics=[Metric(name="activeUsers"), Metric(name="newUsers")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)])
    return [{
        "source": row.dimension_values[0].value,
        "medium": row.dimension_values[1].value,
        "users": int(row.metric_values[0].value),
        "new_users": int(row.metric_values[1].value),
    } for row in resp.rows]


def pull_compliance_events(client, date_range):
    dim_filter = FilterExpression(
        filter=Filter(
            field_name="eventName",
            string_filter=Filter.StringFilter(
                match_type=Filter.StringFilter.MatchType.CONTAINS,
                value="compliance"
            )
        )
    )
    resp = run_report(client, date_range,
        dimensions=[Dimension(name="eventName"), Dimension(name="date")],
        metrics=[Metric(name="eventCount")],
        dim_filter=dim_filter,
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))])
    events = []
    for row in resp.rows:
        d = row.dimension_values[1].value
        events.append({
            "event": row.dimension_values[0].value,
            "date": f"{d[:4]}-{d[4:6]}-{d[6:]}",
            "count": int(row.metric_values[0].value),
        })
    return events


def compute_insights(data):
    """Derive actionable insights from raw data."""
    insights = []
    o90 = data.get("overview_90d", {})
    o7 = data.get("overview_7d", {})

    # Retention
    if o90.get("active_users") and o90.get("new_users"):
        if o90["active_users"] == o90["new_users"]:
            insights.append({
                "severity": "critical",
                "category": "retention",
                "message": "Zero retention — every active user is a new user. Nobody is coming back.",
            })

    # Compliance block rate
    events = data.get("events_90d", {})
    checks = events.get("compliance_check_started", 0)
    blocks = events.get("compliance_blocked", 0)
    if checks > 0:
        block_rate = round(blocks / checks * 100, 1)
        if block_rate > 20:
            insights.append({
                "severity": "high",
                "category": "funnel",
                "message": f"Compliance blocks {block_rate}% of users ({blocks}/{checks} checks). Review if all blocks are necessary.",
            })

    # Engagement rate
    if o90.get("sessions") and o90.get("engaged_sessions"):
        eng_rate = round(o90["engaged_sessions"] / o90["sessions"] * 100, 1)
        insights.append({
            "severity": "info" if eng_rate >= 50 else "medium",
            "category": "engagement",
            "message": f"Engagement rate: {eng_rate}% ({o90['engaged_sessions']}/{o90['sessions']} sessions).",
        })

    # 7d vs prior 7d trend
    o7_prior = data.get("overview_7d_prior", {})
    if o7.get("active_users") and o7_prior.get("active_users"):
        curr = o7["active_users"]
        prev = o7_prior["active_users"]
        if prev > 0:
            change = round((curr - prev) / prev * 100, 1)
            direction = "up" if change > 0 else "down"
            insights.append({
                "severity": "info" if change >= 0 else "medium",
                "category": "trend",
                "message": f"Active users {direction} {abs(change)}% week-over-week ({prev} → {curr}).",
            })

    # Platform imbalance
    platforms = data.get("platforms_90d", [])
    android = sum(p["users"] for p in platforms if p["os"] == "Android")
    ios = sum(p["users"] for p in platforms if p["os"] == "iOS")
    if android > 0 and ios > 0:
        ratio = round(android / ios, 1)
        dominant = "Android" if android > ios else "iOS"
        insights.append({
            "severity": "info",
            "category": "platform",
            "message": f"Android:iOS ratio is {ratio}:1 ({android} vs {ios} users). {dominant} dominates.",
        })

    # No custom events
    auto_events = {"user_engagement", "screen_view", "session_start", "first_open",
                   "app_open", "app_remove", "app_clear_data", "os_update", "app_update",
                   "first_visit", "page_view"}
    custom = {k: v for k, v in events.items() if k not in auto_events and not k.startswith("compliance")}
    if not custom:
        insights.append({
            "severity": "medium",
            "category": "instrumentation",
            "message": "No custom behavioral events (chat_sent, exercise_started, etc). Add Firebase events in next app build.",
        })

    return insights


def generate_report(data):
    """Generate human-readable markdown report."""
    ts = data["pulled_at"]
    o90 = data.get("overview_90d", {})
    o7 = data.get("overview_7d", {})
    insights = data.get("insights", [])

    lines = [
        f"# GentleQuest Analytics Report",
        f"**Generated:** {ts}",
        f"**Property:** {PROPERTY_ID} (gentlequest-prod)",
        "",
        "---",
        "",
        "## Overview (90 Days)",
        "",
        "| Metric | Value |",
        "|--------|-------|",
    ]

    if o90:
        avg_min = round(o90.get("avg_session_sec", 0) / 60, 1)
        eng_rate = round(o90["engaged_sessions"] / o90["sessions"] * 100, 1) if o90.get("sessions") else 0
        lines += [
            f"| Active Users | **{o90.get('active_users', 0)}** |",
            f"| New Users | **{o90.get('new_users', 0)}** |",
            f"| Sessions | **{o90.get('sessions', 0)}** |",
            f"| Engaged Sessions | **{o90.get('engaged_sessions', 0)}** ({eng_rate}%) |",
            f"| Avg Session | **{avg_min} min** |",
            f"| Total Events | **{o90.get('total_events', 0)}** |",
        ]

    # 7-day snapshot
    if o7:
        lines += [
            "",
            "## This Week (7 Days)",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Active Users | **{o7.get('active_users', 0)}** |",
            f"| Sessions | **{o7.get('sessions', 0)}** |",
            f"| Events | **{o7.get('total_events', 0)}** |",
        ]

    # Insights
    if insights:
        lines += ["", "## Insights", ""]
        severity_icon = {"critical": "!!!", "high": "!!", "medium": "!", "info": ""}
        for i in insights:
            icon = severity_icon.get(i["severity"], "")
            prefix = f"[{i['severity'].upper()}]" if icon else f"[{i['severity'].upper()}]"
            lines.append(f"- **{prefix}** {i['message']}")

    # Platforms
    platforms = data.get("platforms_90d", [])
    if platforms:
        lines += ["", "## Platforms", "", "| Platform | OS | Users | Sessions |", "|----------|-----|-------|----------|"]
        for p in platforms:
            lines.append(f"| {p['platform']} | {p['os']} | {p['users']} | {p['sessions']} |")

    # Countries
    countries = data.get("countries_90d", [])
    if countries:
        lines += ["", "## Countries", "", "| Country | Users | Sessions |", "|---------|-------|----------|"]
        for c in countries:
            lines.append(f"| {c['country']} | {c['users']} | {c['sessions']} |")

    # App versions
    versions = data.get("versions_90d", [])
    if versions:
        lines += ["", "## App Versions", "", "| Version | Platform | Users | Sessions |", "|---------|----------|-------|----------|"]
        for v in versions:
            lines.append(f"| {v['version']} | {v['platform']} | {v['users']} | {v['sessions']} |")

    # Events
    events = data.get("events_90d", {})
    if events:
        lines += ["", "## Events (Top 15)", "", "| Event | Count |", "|-------|-------|"]
        for name, count in sorted(events.items(), key=lambda x: -x[1])[:15]:
            lines.append(f"| {name} | {count} |")

    # Compliance timeline
    compliance = data.get("compliance_events_90d", [])
    if compliance:
        lines += ["", "## Compliance Events Timeline", "", "| Date | Event | Count |", "|------|-------|-------|"]
        for e in compliance:
            lines.append(f"| {e['date']} | {e['event']} | {e['count']} |")

    # Daily users (last 14 days)
    daily = data.get("daily_users_30d", [])
    if daily:
        recent = daily[-14:]
        lines += ["", "## Daily Users (Last 14 Days)", "", "| Date | Active | New | Sessions |", "|------|--------|-----|----------|"]
        for d in recent:
            lines.append(f"| {d['date']} | {d['active_users']} | {d['new_users']} | {d['sessions']} |")

    # Acquisition
    acq = data.get("acquisition_90d", [])
    if acq:
        lines += ["", "## Acquisition Sources", "", "| Source | Medium | Users | New |", "|--------|--------|-------|-----|"]
        for a in acq:
            lines.append(f"| {a['source']} | {a['medium']} | {a['users']} | {a['new_users']} |")

    lines += ["", "---", f"*Auto-generated by `scripts/analytics_dashboard.py`*", ""]
    return "\n".join(lines)


def update_activation_proof_t0():
    """Auto-trigger t=0 measurement window start timestamp (Task 10)."""
    state_path = METRICS_DIR / "activation_proof_state.json"
    if not state_path.exists():
        return None

    try:
        with open(state_path, "r") as f:
            state = json.load(f)
    except Exception:
        return None

    if state.get("t0_timestamp") is not None:
        return state

    # Check production API for funnel data (was: local DB — issue #191)
    try:
        import urllib.request
        api_url = os.environ.get("GQ_API_URL", "https://app.gentlequest.app")
        funnel_url = f"{api_url}/api/metrics/funnel"
        req = urllib.request.Request(funnel_url, headers={"User-Agent": "gq-t0-check/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            funnel_data = json.loads(resp.read())

        # If there are landing sessions, set t0 to the window start
        counts = funnel_data.get("counts", {})
        landing_sessions = counts.get("landing_sessions", 0)
        if landing_sessions and landing_sessions > 0:
            window = funnel_data.get("window", {})
            t0 = window.get("start")
            if t0:
                state["t0_timestamp"] = t0
                state["status"] = "measuring"
                with open(state_path, "w") as f:
                    json.dump(state, f, indent=2)
                print(f"t0 set to {t0} (landing_sessions={landing_sessions})")
    except Exception as e:
        print(f"t0 check failed: {e}")

    return state


def main():
    json_only = "--json-only" in sys.argv

    # Ensure output dirs
    METRICS_DIR.mkdir(exist_ok=True)
    HISTORY_DIR.mkdir(exist_ok=True)

    if not CREDS_PATH.exists():
        print(f"Error: credentials not found at {CREDS_PATH}")
        sys.exit(1)

    client = get_client()
    now = datetime.now(timezone.utc)

    print(f"Pulling GA4 analytics at {now.isoformat()}Z ...")

    # Date ranges
    r90 = DateRange(start_date="90daysAgo", end_date="today")
    r30 = DateRange(start_date="30daysAgo", end_date="today")
    r7 = DateRange(start_date="7daysAgo", end_date="today")
    r7_prior = DateRange(start_date="14daysAgo", end_date="8daysAgo")

    data = {
        "pulled_at": now.isoformat() + "Z",
        "property_id": PROPERTY_ID,
    }

    print("  Overview (90d, 7d, 7d prior)...")
    data["overview_90d"] = pull_overview(client, "90d", r90)
    data["overview_7d"] = pull_overview(client, "7d", r7)
    data["overview_7d_prior"] = pull_overview(client, "7d_prior", r7_prior)

    print("  Daily users (30d)...")
    data["daily_users_30d"] = pull_daily_users(client, r30)

    print("  Events (90d)...")
    data["events_90d"] = pull_events(client, r90)

    print("  Platforms (90d)...")
    data["platforms_90d"] = pull_platforms(client, r90)

    print("  Countries (90d)...")
    data["countries_90d"] = pull_countries(client, r90)

    print("  App versions (90d)...")
    data["versions_90d"] = pull_versions(client, r90)

    print("  Acquisition (90d)...")
    data["acquisition_90d"] = pull_acquisition(client, r90)

    print("  Compliance events (90d)...")
    data["compliance_events_90d"] = pull_compliance_events(client, r90)

    # Compute insights
    data["insights"] = compute_insights(data)

    # Save JSON
    with open(JSON_OUT, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved: {JSON_OUT}")

    # Save timestamped history
    hist_file = HISTORY_DIR / f"analytics_{now.strftime('%Y%m%d_%H%M')}.json"
    with open(hist_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved: {hist_file}")

    if not json_only:
        # Generate markdown report
        report = generate_report(data)
        with open(REPORT_OUT, "w") as f:
            f.write(report)
        print(f"  Saved: {REPORT_OUT}")

        # Print insights to stdout
        insights = data.get("insights", [])
        if insights:
            print(f"\n{'='*50}")
            print("INSIGHTS")
            print(f"{'='*50}")
            for i in insights:
                sev = i["severity"].upper()
                print(f"  [{sev}] {i['message']}")
        print()

    # Prune old history (keep last 30)
    history_files = sorted(HISTORY_DIR.glob("analytics_*.json"))
    if len(history_files) > 30:
        for old in history_files[:-30]:
            old.unlink()
            print(f"  Pruned: {old.name}")

    # Update activation proof t0 timestamp if eligible (Task 10)
    update_activation_proof_t0()

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
