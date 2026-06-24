#!/usr/bin/env python3
"""GentleQuest funnel CLI — prints the current funnel + trend.

Usage:
    python scripts/gq_funnel.py              # current funnel
    python scripts/gq_funnel.py --trend      # + 30-snapshot trend
    python scripts/gq_funnel.py --json       # raw JSON output

No dependencies beyond requests (or curl fallback).
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime

API_BASE = "https://gentlequest.onrender.com"


def fetch(path):
    """Fetch JSON from the API."""
    try:
        import requests
        r = requests.get(f"{API_BASE}{path}", timeout=30)
        r.raise_for_status()
        return r.json()
    except ImportError:
        # Fallback to curl
        result = subprocess.run(
            ["curl", "-s", "--max-time", "30", f"{API_BASE}{path}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        return json.loads(result.stdout)


def print_funnel(data):
    """Print the funnel in a clean terminal format."""
    f = data.get("funnel", {})
    all_time = data.get("all_time", {})
    active = data.get("active_users_90d", {})

    installs = f.get("stage_2_installs", {})
    total_installs = (installs.get("iOS", 0) + installs.get("Android", 0))
    all_installs = all_time.get("installs", {})
    all_total = all_time.get("total_users", {})
    all_total_sum = sum(all_total.values())
    active_sum = sum(active.values())

    print()
    print("  GentleQuest Funnel")
    print("  ─────────────────────────────────────────────")
    print(f"  Last 90 days · simulator-filtered · {data.get('blocked_test_sessions', 0)} test sessions excluded")
    print()
    print("  Stage          Value     Detail")
    print("  ─────────────  ────────  ──────────────────────────────")
    print(f"  1. Web visits  {str(f.get('stage_1_web_visits', '—')).rjust(8)}  gentlequest.app + /blog")
    print(f"  2. Installs    {str(total_installs).rjust(8)}  iOS {installs.get('iOS',0)} · Android {installs.get('Android',0)}")
    print(f"  3. App opens   {str(f.get('stage_3_app_opens', 0)).rjust(8)}  last 90 days")
    print(f"  4. First chat  {str(f.get('stage_4_first_chat', 0)).rjust(8)}  real users only")
    print()
    print("  All-time       Value     Detail")
    print("  ─────────────  ────────  ──────────────────────────────")
    print(f"  Installs       {str(sum(all_installs.values())).rjust(8)}  iOS {all_installs.get('iOS',0)} · Android {all_installs.get('Android',0)}")
    print(f"  Total users    {str(all_total_sum).rjust(8)}  iOS {all_total.get('iOS',0)} · Android {all_total.get('Android',0)}")
    print(f"  Active (90d)   {str(active_sum).rjust(8)}  iOS {active.get('iOS',0)} · Android {active.get('Android',0)}")
    print()
    cached = "cached" if data.get("cached") else "fresh"
    ts = data.get("timestamp", "")[:19]
    print(f"  Source: GA4 property {data.get('ga4_property', '?')} · {cached} · {ts}")
    print()


def print_trend(history):
    """Print the trend table from snapshot history."""
    snapshots = history.get("snapshots", [])
    if not snapshots:
        print("  No historical snapshots yet.")
        print()
        return

    print("  Trend (last 30 snapshots)")
    print("  ──────────────  ──────────  ──────────  ──────────  ──────────")
    print("  Date            iOS (90d)   Android    Opens      First chat")
    print("  ──────────────  ──────────  ──────────  ──────────  ──────────")
    for s in reversed(snapshots):
        d = s.get("data", {})
        inst = d.get("installs_90d", {})
        opens = d.get("app_opens_90d", 0)
        ts = s.get("created_at", "")[:10]
        print(f"  {ts}  {str(inst.get('iOS',0)).rjust(9)}  {str(inst.get('Android',0)).rjust(9)}  {str(opens).rjust(9)}  {'—'.rjust(9)}")
    print()


def main():
    parser = argparse.ArgumentParser(description="GentleQuest funnel metrics")
    parser.add_argument("--trend", action="store_true", help="Show 30-snapshot trend")
    parser.add_argument("--json", action="store_true", help="Raw JSON output")
    args = parser.parse_args()

    if args.json:
        data = fetch("/api/metrics/funnel")
        print(json.dumps(data, indent=2))
        return

    data = fetch("/api/metrics/funnel")
    print_funnel(data)

    if args.trend:
        history = fetch("/api/metrics/funnel/history?limit=30")
        print_trend(history)


if __name__ == "__main__":
    main()
