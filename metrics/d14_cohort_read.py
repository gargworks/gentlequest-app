#!/usr/bin/env python3
"""D14 retention cohort reader for GentleQuest.

Runs the parameterized SQL in d14_cohort.sql against the production
PostgreSQL database for a given date range and prints one row per cohort
date with: cohort_date, cohort_size, d14_returned, d14_rate, verdict.

verdict is PASS / FAIL / INSUFFICIENT:
  - INSUFFICIENT : cohort_size < 40 (small-n retention is noise, not signal)
  - PASS         : d14_rate >= D14_PASS_THRESHOLD (default 0.20)
  - FAIL         : d14_rate <  D14_PASS_THRESHOLD

Database URL resolution order:
  1. $DATABASE_URL (env var — the same one the Flask app reads in
     setup/db_url.py:configure_database_url)
  2. $RENDER_DB_URL (Render's secondary var, occasionally set)

Exit codes:
  0  — ran successfully (regardless of verdicts; check stdout for results)
  1  — could not resolve a database URL
  2  — database connection failed
  3  — analytics_events table missing or not queryable
  4  — SQL file missing / unreadable
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    import psycopg2  # type: ignore
except ImportError:
    psycopg2 = None  # type: ignore

SQL_FILE = Path(__file__).resolve().parent / "d14_cohort.sql"
MIN_COHORT = 40
D14_PASS_THRESHOLD = 0.20  # 20% D14 retention = PASS


def resolve_db_url() -> Optional[str]:
    """Return the database URL from the environment, or None."""
    for var in ("DATABASE_URL", "RENDER_DB_URL"):
        url = os.getenv(var)
        if url:
            return url
    return None


def normalize_url(url: str) -> str:
    """Normalize Render-style postgres:// to a form psycopg2 accepts."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # psycopg2 does not understand the +psycopg SQLAlchemy driver suffix.
    if url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql+psycopg://", "postgresql://", 1)
    return url


def load_sql() -> str:
    if not SQL_FILE.exists():
        print(f"ERROR: SQL file not found at {SQL_FILE}", file=sys.stderr)
        sys.exit(4)
    return SQL_FILE.read_text()


def table_exists(cur, table_name: str) -> bool:
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
        )
        """,
        (table_name,),
    )
    return bool(cur.fetchone()[0])


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def run_cohort(
    conn,
    sql: str,
    cohort_start: date,
    min_cohort: int = MIN_COHORT,
    pass_threshold: float = D14_PASS_THRESHOLD,
) -> dict:
    """Run the SQL for a single cohort date and return a result dict.

    The SQL file uses the SQLAlchemy/text-style :cohort_start placeholder so it
    stays readable as documentation. psycopg2 speaks %s, so we translate the
    single named parameter here rather than maintaining two copies of the SQL.
    """
    # Replace only the WHERE-clause parameter, not any :cohort_start mention
    # in the SQL file's header comments (which would create extra %s slots).
    psycopg_sql = sql.replace("= :cohort_start", "= %s")
    with conn.cursor() as cur:
        cur.execute(psycopg_sql, (cohort_start,))
        row = cur.fetchone()
    if row is None:
        return {
            "cohort_date": cohort_start.isoformat(),
            "cohort_size": 0,
            "d14_returned": 0,
            "d14_rate": None,
            "verdict": "INSUFFICIENT",
        }
    cohort_date, cohort_size, d14_returned, d14_rate = row
    cohort_size = int(cohort_size or 0)
    d14_returned = int(d14_returned or 0)
    # psycopg2 returns Decimal for numeric; coerce to float so the >=
    # comparison against a float threshold is exact, not Decimal-vs-float.
    d14_rate_f = float(d14_rate) if d14_rate is not None else None
    if cohort_size < min_cohort:
        verdict = "INSUFFICIENT"
    elif d14_rate_f is not None and d14_rate_f >= pass_threshold:
        verdict = "PASS"
    else:
        verdict = "FAIL"
    return {
        "cohort_date": cohort_date.isoformat() if hasattr(cohort_date, "isoformat") else str(cohort_date),
        "cohort_size": cohort_size,
        "d14_returned": d14_returned,
        "d14_rate": d14_rate_f,
        "verdict": verdict,
    }


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="D14 retention cohort reader")
    parser.add_argument(
        "--start",
        required=True,
        help="Cohort start date (YYYY-MM-DD, inclusive)",
    )
    parser.add_argument(
        "--end",
        default=None,
        help="Cohort end date (YYYY-MM-DD, inclusive). Defaults to --start.",
    )
    parser.add_argument(
        "--min-cohort",
        type=int,
        default=MIN_COHORT,
        help=f"Minimum cohort size for PASS/FAIL (default {MIN_COHORT})",
    )
    parser.add_argument(
        "--pass-threshold",
        type=float,
        default=D14_PASS_THRESHOLD,
        help=f"D14 rate threshold for PASS (default {D14_PASS_THRESHOLD})",
    )
    args = parser.parse_args(argv)

    min_cohort = args.min_cohort
    pass_threshold = args.pass_threshold

    try:
        start = datetime.strptime(args.start, "%Y-%m-%d").date()
    except ValueError:
        print(f"ERROR: --start must be YYYY-MM-DD, got {args.start!r}", file=sys.stderr)
        return 1
    end = (
        datetime.strptime(args.end, "%Y-%m-%d").date()
        if args.end
        else start
    )
    if end < start:
        print("ERROR: --end is before --start", file=sys.stderr)
        return 1

    db_url = resolve_db_url()
    if not db_url:
        print(
            "ERROR: no DATABASE_URL or RENDER_DB_URL in environment.",
            file=sys.stderr,
        )
        return 1

    if psycopg2 is None:
        print(
            "ERROR: psycopg2 not installed. Install with: pip install psycopg2-binary",
            file=sys.stderr,
        )
        return 2

    sql = load_sql()

    try:
        conn = psycopg2.connect(normalize_url(db_url))
    except Exception as e:
        print(f"ERROR: database connection failed: {e}", file=sys.stderr)
        return 2

    try:
        with conn.cursor() as cur:
            if not table_exists(cur, "analytics_events"):
                print(
                    "ERROR: table 'analytics_events' does not exist in the "
                    "public schema of the connected database.",
                    file=sys.stderr,
                )
                return 3
            # Quick empty-table check so we can report cleanly.
            cur.execute("SELECT COUNT(*) FROM analytics_events")
            total = cur.fetchone()[0]
            if total == 0:
                print(
                    "NOTE: analytics_events table exists but is empty. "
                    "All cohorts will be INSUFFICIENT.",
                    file=sys.stderr,
                )

        # Header
        print(
            f"{'cohort_date':<12} {'cohort_size':>11} {'d14_returned':>12} "
            f"{'d14_rate':>9} {'verdict':<13}"
        )
        print("-" * 60)

        any_rows = False
        for d in daterange(start, end):
            any_rows = True
            r = run_cohort(conn, sql, d, min_cohort, pass_threshold)
            rate_str = (
                f"{r['d14_rate']:.4f}" if r['d14_rate'] is not None else "  N/A"
            )
            print(
                f"{r['cohort_date']:<12} {r['cohort_size']:>11} "
                f"{r['d14_returned']:>12} {rate_str:>9} {r['verdict']:<13}"
            )
        if not any_rows:
            print("(no cohort dates in range)")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
