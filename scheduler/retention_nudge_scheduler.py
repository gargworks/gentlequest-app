"""Background scheduler for the gentle D10 return nudge.

Runs a daemon thread that fires once per day at 09:00 UTC. Finds every
session whose first-open (earliest analytics_events row) was exactly 10
days ago and who has had no activity in the last 3 days, and sends them
one gentle push notification.

Why day 10, not day 14: this exists to lift the Stage-1 D14 retention gate
(BILLION_DOLLAR_ROADMAP.md), and a nudge sent ON day 14 is too late to
influence whether that session counts as "returned" in the D14 window. Day
10 gives up to 4 days for the nudge to land before the measurement window
(first_open + 14d to +15d) opens.

Why exactly 10 days, not a trailing window: each session has exactly one
first-open date, so matching on DATE(first_open) = today - 10 days sends
to a given session at most once by construction -- no separate "already
sent" tracking table needed. This mirrors the day-precision cohort match
in metrics/d14_cohort.sql. The known tradeoff (shared with
scheduler/funnel_scheduler.py): if the process is asleep on Render's free
tier exactly at 09:00 UTC on a given day, that day's cohort is skipped
with no catch-up. Accepted for the same reason the funnel scheduler
accepts it -- fixing it needs a paid tier or a Render Cron Job, not more
code here.

Uses threading.Timer (no extra dependency), same as funnel_scheduler.py.
"""

import atexit
import logging
import threading
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

_timer = None
_stop_event = threading.Event()


def _seconds_until_next_09_utc():
    """Calculate seconds until the next 09:00 UTC.

    Offset an hour from the funnel scheduler's 08:00 so the two daily jobs
    don't compete for the same wake tick on Render's free tier.
    """
    now = datetime.now(timezone.utc)
    target = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def _run_nudge(app):
    if _stop_event.is_set():
        return
    try:
        with app.app_context():
            from services.retention_nudge import send_d10_nudges

            result = send_d10_nudges()
            logger.info(
                f"[retention-nudge] cohort={result['cohort_size']} "
                f"sent={result['sent']} skipped={result['skipped']} "
                f"failed={result['failed']}"
            )
    except Exception as e:
        logger.error(f"[retention-nudge] Failed: {e}")
        try:
            from models import db
            db.session.rollback()
        except Exception:
            pass
    finally:
        _schedule_next(app)


def _schedule_next(app):
    if _stop_event.is_set():
        return
    delay = _seconds_until_next_09_utc()
    global _timer
    _timer = threading.Timer(delay, _run_nudge, args=[app])
    _timer.daemon = True
    _timer.start()
    next_time = (datetime.now(timezone.utc) + timedelta(seconds=delay)).strftime("%Y-%m-%d %H:%M UTC")
    logger.info(f"[retention-nudge] Next run at {next_time} (in {delay/3600:.1f}h)")


def start_retention_nudge_scheduler(app):
    """Start the daily D10 return-nudge scheduler."""
    _schedule_next(app)
    atexit.register(stop_retention_nudge_scheduler)


def stop_retention_nudge_scheduler():
    _stop_event.set()
    if _timer:
        _timer.cancel()
