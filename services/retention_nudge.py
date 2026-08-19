"""Gentle D10 return-nudge: the one lever that can still move the Stage-1
D14 retention gate before its measurement window closes.

Finds sessions whose first-open was exactly 10 days ago, who have gone
quiet since (no analytics_events activity in the trailing 3 days), and
who still hold a valid (non-revoked) push token -- then sends one push
via services.push_delivery.send_push under the "gentle_return" category.

Called once a day by scheduler/retention_nudge_scheduler.py. Exposed as a
plain function (not a route) so it's also directly callable for a manual
or backfilled run, e.g. from a Flask shell:

    from services.retention_nudge import send_d10_nudges
    send_d10_nudges(target_date=date(2026, 8, 15))
"""

from datetime import date, datetime, timedelta

from sqlalchemy import func

from models import AnalyticsEvent, PushToken, db
from services.push_delivery import send_push

NUDGE_CATEGORY = "gentle_return"
NUDGE_DAY_OFFSET = 10
QUIET_WINDOW_DAYS = 3
NUDGE_TITLE = "Quest is still here"
NUDGE_BODY = "No streak to break, no catching up to do. Whenever you're ready."


def _d10_cohort_session_ids(target_date: date) -> list[str]:
    """Session ids whose first-open falls on target_date, restricted to
    sessions that have gone quiet in the trailing QUIET_WINDOW_DAYS days.
    """
    first_open = (
        db.session.query(
            AnalyticsEvent.session_id,
            func.min(AnalyticsEvent.timestamp).label("first_open_ts"),
        )
        .filter(AnalyticsEvent.session_id.isnot(None))
        .group_by(AnalyticsEvent.session_id)
        .subquery()
    )
    cohort = (
        db.session.query(first_open.c.session_id)
        .filter(func.date(first_open.c.first_open_ts) == target_date)
        .all()
    )
    session_ids = [row.session_id for row in cohort]
    if not session_ids:
        return []

    quiet_cutoff = datetime.utcnow() - timedelta(days=QUIET_WINDOW_DAYS)
    recently_active = {
        row.session_id
        for row in db.session.query(AnalyticsEvent.session_id)
        .filter(
            AnalyticsEvent.session_id.in_(session_ids),
            AnalyticsEvent.timestamp >= quiet_cutoff,
        )
        .distinct()
        .all()
    }
    return [sid for sid in session_ids if sid not in recently_active]


def send_d10_nudges(target_date: date | None = None) -> dict:
    """Send the gentle return nudge to today's D10 cohort. Returns counts.

    target_date defaults to (today - NUDGE_DAY_OFFSET days); pass an
    explicit date for a manual/backfilled run.
    """
    if target_date is None:
        # UTC, not date.today() (local server tz) -- every timestamp in
        # analytics_events is UTC (datetime.utcnow()), and local-vs-UTC
        # disagree for several hours a day on any non-UTC server, which
        # would silently target the wrong cohort day. Caught by a test
        # failing specifically on an IST (UTC+5:30) dev machine.
        target_date = datetime.utcnow().date() - timedelta(days=NUDGE_DAY_OFFSET)

    session_ids = _d10_cohort_session_ids(target_date)
    result = {"cohort_size": len(session_ids), "sent": 0, "skipped": 0, "failed": 0}
    if not session_ids:
        return result

    # .distinct(column) is Postgres-only DISTINCT ON syntax (silently
    # ignored on SQLite, deprecated even where it works) -- the set
    # comprehension already dedupes, so no DB-level DISTINCT is needed.
    has_token = {
        row.session_id
        for row in PushToken.query.filter(
            PushToken.session_id.in_(session_ids),
            PushToken.revoked_at.is_(None),
        ).all()
    }

    for session_id in session_ids:
        if session_id not in has_token:
            result["skipped"] += 1
            continue
        outcome = send_push(
            session_id,
            NUDGE_TITLE,
            NUDGE_BODY,
            category=NUDGE_CATEGORY,
            collapse_key="gentle_return",
        )
        if outcome["sent"] > 0:
            result["sent"] += 1
        else:
            result["failed"] += 1
    return result
