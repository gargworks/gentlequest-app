#!/usr/bin/env python3
"""Daily data refresh daemon for the training flywheel.

Runs process_all_sources + export_raft + retrain-readiness check.
Designed to be called by cron daily (e.g., 2 AM).

Usage:
    python3 scripts/daily_data_refresh.py           # full refresh
    python3 scripts/daily_data_refresh.py --check   # just check readiness
    python3 scripts/daily_data_refresh.py --index   # also refresh brain_rag index

What it does:
    1. Refresh brain_rag index (if --index)
    2. Run process_all_sources.py (idempotent — deduplicates)
    3. Run export_raft_training.py --combined
    4. Check retrain readiness (100-task or 14-day threshold)
    5. Log results to .brain/training/refresh_log.jsonl
    6. Alert if retrain threshold hit
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRAIN_TRAINING = PROJECT_ROOT / ".brain" / "training"
DRIVER_DIR = PROJECT_ROOT / ".brain" / "driver"
EXPORTS_DIR = BRAIN_TRAINING / "exports"
REFRESH_LOG = BRAIN_TRAINING / "refresh_log.jsonl"
ALERTS_PATH = DRIVER_DIR / "alerts.jsonl"

RETRAIN_TASK_THRESHOLD = 100
RETRAIN_DAYS_THRESHOLD = 14


def send_telegram_alert(message: str) -> bool:
    """Send failure alert via Telegram. Returns True on success."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skipping alert")
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        logger.error("Telegram alert failed: %s", e)
        return False


def refresh_rag_index():
    """Re-index brain_rag knowledge base."""
    print("[1] Refreshing brain_rag index...")
    proc = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "providers" / "brain_rag.py"), "--index"],
        capture_output=True, text=True, timeout=300,
        cwd=str(PROJECT_ROOT),
    )
    if proc.returncode != 0:
        print(f"  WARNING: brain_rag index failed: {proc.stderr[:200]}")
        return False
    print("  Index refreshed.")
    return True


def run_pipeline():
    """Run process_all_sources.py."""
    print("[2] Running process_all_sources.py...")
    proc = subprocess.run(
        [sys.executable, str(BRAIN_TRAINING / "process_all_sources.py")],
        capture_output=True, text=True, timeout=2400,
        cwd=str(PROJECT_ROOT),
    )
    if proc.returncode != 0:
        print(f"  WARNING: pipeline failed: {proc.stderr[:200]}")
        return None

    # Parse counts from stats file
    stats_path = BRAIN_TRAINING / "unified_pipeline_stats.json"
    if stats_path.exists():
        with open(stats_path) as f:
            stats = json.load(f)
        sft = stats.get("total_sft", 0)
        dpo = stats.get("total_dpo", 0)
        print(f"  {sft:,} SFT + {dpo:,} DPO")
        return stats
    return {}


def run_export_combined():
    """Run export_raft_training.py --combined. Returns True on success."""
    print("[3] Running export_raft_training.py --combined...")
    export_script = PROJECT_ROOT / "scripts" / "export_raft_training.py"
    if not export_script.exists():
        print("  export_raft_training.py not found, skipping")
        return True  # not a failure, script just doesn't exist
    proc = subprocess.run(
        [sys.executable, str(export_script), "--combined"],
        capture_output=True, text=True, timeout=120,
        cwd=str(PROJECT_ROOT),
    )
    if proc.returncode != 0:
        print(f"  WARNING: export_raft failed")
        return False
    print("  Combined export done.")
    return True


def check_retrain_readiness():
    """Check if retrain threshold is hit."""
    print("[4] Checking retrain readiness...")

    # Load manifest from Drive (or local)
    drive_manifest = (
        Path.home() / "Library" / "CloudStorage"
        / "GoogleDrive-mailforlkgarg@gmail.com" / "My Drive"
        / "nucleus-training" / "data" / "manifest.json"
    )

    last_task_count = 0
    last_push_ts = None
    if drive_manifest.exists():
        with open(drive_manifest) as f:
            manifest = json.load(f)
        last_task_count = manifest.get("last_retrain_task_count", 0)
        last_push_ts = manifest.get("timestamp", "")

    # Current completed task count
    tasks_path = DRIVER_DIR / "tasks.json"
    current_tasks = 0
    if tasks_path.exists():
        with open(tasks_path) as f:
            data = json.load(f)
        current_tasks = sum(
            1 for t in data.get("tasks", [])
            if t.get("status") == "completed"
        )

    new_tasks = current_tasks - last_task_count

    # Days since last push
    days_since = 999
    if last_push_ts:
        try:
            last_dt = datetime.fromisoformat(last_push_ts[:19])  # strip any tz
            days_since = (datetime.now() - last_dt).days
        except Exception:
            pass

    ready = new_tasks >= RETRAIN_TASK_THRESHOLD or days_since >= RETRAIN_DAYS_THRESHOLD
    reason = []
    if new_tasks >= RETRAIN_TASK_THRESHOLD:
        reason.append(f"{new_tasks} new tasks (threshold: {RETRAIN_TASK_THRESHOLD})")
    if days_since >= RETRAIN_DAYS_THRESHOLD:
        reason.append(f"{days_since} days since last push (threshold: {RETRAIN_DAYS_THRESHOLD})")

    print(f"  New tasks since last push: {new_tasks}")
    print(f"  Days since last push: {days_since}")
    print(f"  Ready: {'YES' if ready else 'NO'}")

    return {
        "ready": ready,
        "new_tasks": new_tasks,
        "days_since_push": days_since,
        "reason": "; ".join(reason) if reason else "below threshold",
    }


def log_alert(message: str, level: str = "INFO"):
    """Write alert to driver alerts log."""
    entry = {
        "ts": datetime.now().isoformat(),
        "source": "daily_data_refresh",
        "level": level,
        "message": message,
    }
    with open(ALERTS_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def log_refresh(stats: dict, readiness: dict, indexed: bool):
    """Log this refresh run."""
    entry = {
        "ts": datetime.now().isoformat(),
        "indexed": indexed,
        "sft_count": stats.get("total_sft", 0) if stats else 0,
        "dpo_count": stats.get("total_dpo", 0) if stats else 0,
        "retrain_ready": readiness.get("ready", False),
        "new_tasks": readiness.get("new_tasks", 0),
        "days_since_push": readiness.get("days_since_push", 0),
    }
    with open(REFRESH_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Daily data refresh for training flywheel")
    parser.add_argument("--check", action="store_true", help="Only check readiness")
    parser.add_argument("--index", action="store_true", help="Also refresh brain_rag index")
    args = parser.parse_args()

    print("=" * 50)
    print(f"DAILY DATA REFRESH — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    # Lock file to prevent overlapping runs
    lock_path = BRAIN_TRAINING / ".refresh_lock"
    if lock_path.exists():
        # Stale lock check: if older than 60 min, remove it
        import os, time
        age_min = (time.time() - os.path.getmtime(lock_path)) / 60
        if age_min < 60:
            print(f"Another refresh is running (lock age: {age_min:.0f} min). Exiting.")
            return
        print(f"Removing stale lock ({age_min:.0f} min old)")
        lock_path.unlink()
    lock_path.write_text(str(datetime.now().isoformat()))
    try:
        _run_refresh(args)
    except Exception as exc:
        msg = (
            f"🚨 *daily\\_data\\_refresh FAILED*\n\n"
            f"⏰ `{datetime.now().strftime('%Y-%m-%d %H:%M')}`\n"
            f"❌ `{type(exc).__name__}: {exc}`"
        )
        send_telegram_alert(msg)
        log_alert(f"Refresh failed: {exc}", "ERROR")
        raise
    finally:
        lock_path.unlink(missing_ok=True)


def _run_refresh(args):
    if args.check:
        readiness = check_retrain_readiness()
        if readiness["ready"]:
            print(f"\n>>> RETRAIN RECOMMENDED: {readiness['reason']}")
        return

    # Full refresh — track step failures for alerting
    failures = []
    indexed = False
    if args.index:
        indexed = refresh_rag_index()
        if not indexed:
            failures.append("brain_rag index refresh failed")

    stats = run_pipeline()
    if stats is None:
        failures.append("process_all_sources pipeline failed")

    if not run_export_combined():
        failures.append("export_raft_training failed")
    readiness = check_retrain_readiness()

    # Log
    log_refresh(stats, readiness, indexed)

    # Alert on step failures
    if failures:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M')
        msg = (
            f"⚠️ *daily\\_data\\_refresh partial failure*\n\n"
            f"⏰ `{ts}`\n"
            + "\n".join(f"• {f}" for f in failures)
        )
        send_telegram_alert(msg)
        for f in failures:
            log_alert(f, "ERROR")

    if readiness["ready"]:
        msg = f"Retrain threshold hit: {readiness['reason']}"
        log_alert(msg, "WARNING")
        print(f"\n>>> RETRAIN RECOMMENDED: {readiness['reason']}")
        print("    Run: python3 .brain/training/colab_push_data.py")

    print("\nDone.")


if __name__ == "__main__":
    main()
