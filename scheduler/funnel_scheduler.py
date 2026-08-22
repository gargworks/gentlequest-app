"""Background scheduler for daily funnel snapshots.

Runs a daemon thread that fires once per day at 08:00 UTC, hitting the
internal /api/metrics/funnel endpoint to persist a snapshot. This makes
the backend self-snapshotting — no external trigger needed.

Uses threading.Timer (no extra dependency). If the process restarts,
the timer recalculates the next 08:00 UTC and reschedules.
"""

import atexit
import logging
import threading
from datetime import datetime, timedelta, timezone

from metrics.d14_cohort_ga4 import collect_native_retention_gate

logger = logging.getLogger(__name__)

_timer = None
_stop_event = threading.Event()


def _seconds_until_next_08_utc():
    """Calculate seconds until the next 08:00 UTC."""
    now = datetime.now(timezone.utc)
    target = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def _run_snapshot(app, schedule_next=True):
    """Hit the funnel endpoint and persist the snapshot to the database."""
    if _stop_event.is_set():
        return
    try:
        with app.app_context(), app.test_client() as client:
            resp = client.get("/api/metrics/funnel",
                              headers={"User-Agent": "internal-scheduler"})
            if resp.status_code == 200:
                data = resp.get_json()

                # Attach the native D1/D7/D14 retention gate.  The collector
                # returns a structured error result on credential/API failure,
                # so a GA4 outage never prevents the funnel row from persisting.
                try:
                    data["retention_gate"] = collect_native_retention_gate()
                except Exception as exc:
                    logger.error(f"[funnel-scheduler] Retention gate collection failed: {exc}")
                    data["retention_gate"] = {
                        "schema_version": 1,
                        "population": "native",
                        "status": "error",
                        "reason": "unexpected_error",
                        "below_kill_line": False,
                    }

                rg = data.get("retention_gate", {})
                native = rg.get("native", {})
                d14 = native.get("d14", {})
                logger.info(
                    f"[funnel-scheduler] Snapshot persisted: "
                    f"landing={data.get('counts', {}).get('landing_sessions', 0)} "
                    f"cta_clicks={data.get('counts', {}).get('cta_clicks', 0)} "
                    f"first_value={data.get('counts', {}).get('first_value_actions', 0)} "
                    f"retention={rg.get('status')}/{rg.get('reason')} "
                    f"native_n={native.get('total_n', 0)} "
                    f"d14_rate={d14.get('rate', 0.0)}"
                )

                # Persist the full funnel + retention metrics blob as a snapshot row.
                # Previously this step was missing — the endpoint only
                # computed and returned JSON; nobody wrote a FunnelSnapshot
                # row, so /api/metrics/funnel/history always returned 0.
                from models import FunnelSnapshot, db
                snapshot = FunnelSnapshot(snapshot_data=data)
                db.session.add(snapshot)
                db.session.commit()
            else:
                logger.warning(f"[funnel-scheduler] Endpoint returned {resp.status_code}")
    except Exception as e:
        logger.error(f"[funnel-scheduler] Failed: {e}")
        try:
            from models import db
            db.session.rollback()
        except Exception:
            pass
    finally:
        if schedule_next:
            _schedule_next(app)


def _schedule_next(app):
    """Schedule the next snapshot."""
    if _stop_event.is_set():
        return
    delay = _seconds_until_next_08_utc()
    global _timer
    _timer = threading.Timer(delay, _run_snapshot, args=[app])
    _timer.daemon = True
    _timer.start()
    next_time = (datetime.now(timezone.utc) + timedelta(seconds=delay)).strftime("%Y-%m-%d %H:%M UTC")
    logger.info(f"[funnel-scheduler] Next snapshot at {next_time} (in {delay/3600:.1f}h)")


def start_funnel_scheduler(app):
    """Start the daily funnel snapshot scheduler."""
    _schedule_next(app)
    atexit.register(stop_funnel_scheduler)


def stop_funnel_scheduler():
    """Stop the scheduler on shutdown."""
    _stop_event.set()
    if _timer:
        _timer.cancel()
