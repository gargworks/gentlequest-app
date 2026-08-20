#!/usr/bin/env python3
"""D14 retention from GA4/Firebase cohorts — the WORKING instrument for the Stage-1 gate.

Replaces metrics/d14_cohort.sql + d14_cohort_read.py for gate purposes.

WHY THIS EXISTS
---------------
The SQL cohort reads `analytics_events`, whose population is ~78% landing-page
traffic: of 265 session_ids, 206 exist solely from a `cta_impression` (a marketing
event fired on page view), and only 33 carry any real app-usage event. Native app
telemetry barely reaches that table at all (10 days to 2026-08-20: first_chat_message=1,
chat_message=1, against 209 lifetime native installs). d14_cohort.sql filters by neither
event type nor platform, so its denominator is mostly people who read a web page and
left — it measures something closer to landing-page bounce than app retention, and no
amount of accumulated data fixes that.

GA4/Firebase holds genuine per-user first_open/session data across web + native and
supports cohort retention natively. Verified working 2026-08-20 against the live
property (see the numbers in
docs/NOTIFICATION_AND_RETENTION_FINDINGS_2026-08-20.md).

USAGE
-----
    GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json python3 metrics/d14_cohort_ga4.py \
        --start 2026-08-15 --end 2026-09-24

Gate defaults match BILLION_DOLLAR_ROADMAP.md Stage 1: D14 >= 15%, n >= 40.

VERDICTS
--------
  INSUFFICIENT : n < min-cohort, OR the cohort has not fully matured past D14 yet.
                 A cohort whose members have not reached their own day 14 CANNOT be
                 scored — reporting FAIL there manufactures churn out of people who
                 simply have not had the chance to return. (This exact bug was found
                 and fixed twice in the SQL reader; do not reintroduce it here.)
  PASS / FAIL  : only once eligible n >= min-cohort AND the window has matured.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta, timezone

MIN_COHORT = 40
D14_PASS_THRESHOLD = 0.15
D14_KILL_THRESHOLD = 0.07  # roadmap: D14 < 7% with n>=40 => freeze ADR
PROPERTY_ID = os.getenv("GQ_GA4_PROPERTY_ID", "516568186")


def fetch(start: str, end: str, end_offset: int = 16):
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        Cohort, CohortSpec, CohortsRange, DateRange, Dimension, Metric, RunReportRequest,
    )

    client = BetaAnalyticsDataClient()
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        # NOTE: GA4 rejects cohort requests that omit the "cohort" dimension,
        # even when you only care about cohortNthDay. Keep it.
        dimensions=[Dimension(name="cohort"), Dimension(name="cohortNthDay"),
                    Dimension(name="platform")],
        metrics=[Metric(name="cohortActiveUsers"), Metric(name="cohortTotalUsers")],
        cohort_spec=CohortSpec(
            cohorts=[Cohort(name="gate", dimension="firstSessionDate",
                            date_range=DateRange(start_date=start, end_date=end))],
            cohorts_range=CohortsRange(granularity="DAILY", start_offset=0,
                                       end_offset=end_offset),
        ),
    )
    resp = client.run_report(req)
    by_platform: dict[str, dict[int, tuple[int, int]]] = {}
    for row in resp.rows:
        day = int(row.dimension_values[1].value)
        platform = row.dimension_values[2].value
        active = int(row.metric_values[0].value)
        total = int(row.metric_values[1].value)
        by_platform.setdefault(platform, {})[day] = (active, total)
    return by_platform


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="D14 retention from GA4 cohorts")
    p.add_argument("--start", required=True, help="cohort first-session start (YYYY-MM-DD)")
    p.add_argument("--end", required=True, help="cohort first-session end (YYYY-MM-DD)")
    p.add_argument("--min-cohort", type=int, default=MIN_COHORT)
    p.add_argument("--pass-threshold", type=float, default=D14_PASS_THRESHOLD)
    args = p.parse_args(argv)

    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("ERROR: set GOOGLE_APPLICATION_CREDENTIALS to a GA4-readable service account.",
              file=sys.stderr)
        return 1

    try:
        end_d = datetime.strptime(args.end, "%Y-%m-%d").date()
    except ValueError:
        print(f"ERROR: --end must be YYYY-MM-DD, got {args.end!r}", file=sys.stderr)
        return 1

    by_platform = fetch(args.start, args.end)
    if not by_platform:
        print("No cohort data returned.")
        return 0

    print(f"GA4 cohort {args.start} → {args.end}   (property {PROPERTY_ID})\n")
    print(f"{'platform':<10} {'n':>5} {'D1':>8} {'D7':>8} {'D14':>8}")
    print("-" * 44)

    tot_n = tot_d14 = 0
    for platform, days in sorted(by_platform.items()):
        n = days.get(0, (0, 0))[1]
        d1 = days.get(1, (0, 0))[0]
        d7 = days.get(7, (0, 0))[0]
        d14 = days.get(14, (0, 0))[0]
        tot_n += n
        tot_d14 += d14
        f = lambda a: f"{a/n*100:6.1f}%" if n else "   n/a"
        print(f"{platform:<10} {n:>5} {f(d1):>8} {f(d7):>8} {f(d14):>8}")

    # Maturity: the LAST first-session day in the window must be >= 14 days old,
    # else part of the cohort simply cannot have reached its own D14 yet.
    matured = (datetime.now(timezone.utc).date() - end_d).days >= 14
    rate = (tot_d14 / tot_n) if tot_n else None

    print("-" * 44)
    print(f"{'ALL':<10} {tot_n:>5} {'':>8} {'':>8} "
          f"{(f'{rate*100:6.1f}%' if rate is not None else '   n/a'):>8}")

    if not matured:
        days_left = 14 - (datetime.now(timezone.utc).date() - end_d).days
        print(f"\nVERDICT: INSUFFICIENT — cohort has not matured past D14 "
              f"({days_left} more day(s) needed). Any PASS/FAIL now would be fiction.")
    elif tot_n < args.min_cohort:
        print(f"\nVERDICT: INSUFFICIENT — n={tot_n} below floor {args.min_cohort}.")
    elif rate is not None and rate >= args.pass_threshold:
        print(f"\nVERDICT: PASS — D14 {rate*100:.1f}% >= {args.pass_threshold*100:.0f}%")
    else:
        kill = rate is not None and rate < D14_KILL_THRESHOLD
        print(f"\nVERDICT: FAIL — D14 {rate*100:.1f}% < {args.pass_threshold*100:.0f}%"
              + (f"  (BELOW KILL LINE {D14_KILL_THRESHOLD*100:.0f}% — roadmap freeze condition)"
                 if kill else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
