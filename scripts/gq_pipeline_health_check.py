#!/usr/bin/env python3
"""
GentleQuest Pipeline Health Check

Runs after each pipeline job (or independently) to verify:
  1. Blog is live and serving the latest published post
  2. Scheduled post queue is not exhausted
  3. Autonomous publisher channels are functional
  4. Credentials are valid

Writes structured JSON status to ~/.local/share/gentlequest/pipeline_status.json
Sends Telegram alert on any failure (if TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID set).

Usage:
  python3 scripts/gq_pipeline_health_check.py           # Full check
  python3 scripts/gq_pipeline_health_check.py --quiet    # Only alert on failure
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────

BLOG_URL = "https://gentlequest-blog.onrender.com"
BACKEND_URL = "https://gentlequest.onrender.com"
STATUS_PATH = Path.home() / ".local/share/gentlequest/pipeline_status.json"
GENTLEQUEST_DIR = Path("/Users/lokeshgarg/gentlequest")
SCHEDULED_DIR = GENTLEQUEST_DIR / "gentlequest-blog/src/content/scheduled"
BLOG_DIR = GENTLEQUEST_DIR / "gentlequest-blog/src/content/blog"
PUBLISHER_LOG = Path.home() / "Library/Logs/gq_autonomous_publisher.log"
BLOG_STAGGERED_LOG = Path.home() / "Library/Logs/gq_blog_staggered.log"

# Load Telegram creds from ai-mvp-backend/.env
ENV_PATH = Path("/Users/lokeshgarg/ai-mvp-backend/.env")
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            TELEGRAM_BOT_TOKEN = line.split("=", 1)[1].strip()
        elif line.startswith("TELEGRAM_CHAT_ID="):
            TELEGRAM_CHAT_ID = line.split("=", 1)[1].strip()

# ── Helpers ──────────────────────────────────────────────────────────────────


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def send_telegram(message):
    """Send alert via Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        subprocess.run(
            [
                "curl", "-s", "-X", "POST",
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                "--data-urlencode", f"chat_id={TELEGRAM_CHAT_ID}",
                "--data-urlencode", f"text={message}",
                "-d", "parse_mode=Markdown",
            ],
            timeout=10,
            capture_output=True,
        )
    except Exception:
        pass


def check_blog_live():
    """Check if blog is reachable and serving content."""
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--max-time", "15", BLOG_URL],
            capture_output=True, text=True, timeout=20,
        )
        code = result.stdout.strip()
        if code == "200":
            return {"status": "ok", "http_code": code}
        return {"status": "fail", "http_code": code, "error": f"Blog returned {code}"}
    except Exception as e:
        return {"status": "fail", "error": str(e)}


def check_scheduled_queue():
    """Check if there are scheduled posts remaining."""
    try:
        if not SCHEDULED_DIR.exists():
            return {"status": "warn", "count": 0, "error": "Scheduled dir does not exist"}
        posts = list(SCHEDULED_DIR.glob("*.md"))
        count = len(posts)
        if count == 0:
            return {"status": "fail", "count": 0, "error": "No scheduled posts remaining — queue exhausted"}
        if count < 5:
            return {"status": "warn", "count": count, "error": f"Only {count} scheduled posts remaining"}
        return {"status": "ok", "count": count}
    except Exception as e:
        return {"status": "fail", "error": str(e)}


def check_published_count():
    """Count published blog posts."""
    try:
        if not BLOG_DIR.exists():
            return {"status": "fail", "count": 0, "error": "Blog dir does not exist"}
        posts = list(BLOG_DIR.glob("*.md"))
        return {"status": "ok", "count": len(posts)}
    except Exception as e:
        return {"status": "fail", "error": str(e)}


def check_blog_staggered_recent():
    """Check if blog-staggered ran recently and succeeded."""
    try:
        if not BLOG_STAGGERED_LOG.exists():
            return {"status": "fail", "error": "No blog-staggered log"}
        lines = BLOG_STAGGERED_LOG.read_text().splitlines()
        if not lines:
            return {"status": "fail", "error": "Empty blog-staggered log"}

        # Find last meaningful entry
        last_entries = [l for l in lines[-20:] if l.strip()]
        if not last_entries:
            return {"status": "fail", "error": "No recent log entries"}

        # Check for npm failure in recent entries
        recent = "\n".join(last_entries[-10:])
        has_npm_fail = "npm: command not found" in recent
        has_no_posts = "No scheduled posts found" in last_entries[-1] if last_entries else False
        has_done = "Done. Published" in recent

        if has_npm_fail:
            return {"status": "fail", "error": "npm not found in PATH — blog rebuild failing"}
        if has_no_posts:
            return {"status": "warn", "error": "Queue exhausted — no posts to publish", "last_line": last_entries[-1]}
        if has_done:
            return {"status": "ok", "last_line": last_entries[-1]}
        return {"status": "warn", "last_line": last_entries[-1] if last_entries else "?"}
    except Exception as e:
        return {"status": "fail", "error": str(e)}


def check_publisher_channels():
    """Check autonomous publisher channel status from recent log entries."""
    try:
        if not PUBLISHER_LOG.exists():
            return {"status": "fail", "error": "No publisher log"}

        lines = PUBLISHER_LOG.read_text().splitlines()
        if not lines:
            return {"status": "fail", "error": "Empty publisher log"}

        # Look at last 100 lines for channel status
        recent = "\n".join(lines[-100:])

        channels = {}

        # Buffer
        buffer_fail = "Scheduled posts limit reached" in recent
        buffer_success = "Posted to Buffer" in recent
        if buffer_fail and not buffer_success:
            channels["buffer"] = {"status": "fail", "error": "Buffer free-tier limit (10 max scheduled). Wait for posts to publish or upgrade Buffer plan."}
        elif buffer_success:
            channels["buffer"] = {"status": "ok"}
        elif "No Buffer token" in recent:
            channels["buffer"] = {"status": "fail", "error": "No Buffer token in keychain. Add: security add-generic-password -s buffer-gentlequest -a gentlequest -w TOKEN"}
        else:
            channels["buffer"] = {"status": "ok", "note": "No recent Buffer activity (no posts queued for Buffer)"}

        # Dev.to
        if "No Dev.to API key" in recent:
            channels["devto"] = {"status": "fail", "error": "No API key. Add: security add-generic-password -s devto-api-key -a gentlequest -w KEY"}
        elif "Posted to Dev.to" in recent or "Published to Dev.to" in recent:
            channels["devto"] = {"status": "ok"}
        else:
            channels["devto"] = {"status": "ok", "note": "No recent Dev.to activity"}

        # Medium (uses Playwright, checked by preflight)
        if "Playwright not installed" in recent:
            channels["medium"] = {"status": "fail", "error": "Playwright not installed. Run: /usr/bin/python3 -m pip install playwright && /usr/bin/python3 -m playwright install chromium"}
        else:
            channels["medium"] = {"status": "ok", "note": "Medium uses Playwright — see playwright_preflight check for auth status"}

        # Reddit (uses Playwright, checked by preflight)
        channels["reddit"] = {"status": "ok", "note": "Reddit uses Playwright — see playwright_preflight check for auth status"}

        # Aggregate
        failing = [k for k, v in channels.items() if v["status"] == "fail"]
        if failing:
            return {"status": "fail", "channels": channels, "failing": failing}
        return {"status": "ok", "channels": channels}
    except Exception as e:
        return {"status": "fail", "error": str(e)}


def check_credentials():
    """Probe keychain for required credentials."""
    creds = {}
    checks = {
        "buffer-gentlequest": "buffer",
        "devto-api-key": "devto",
    }
    for keychain_key, name in checks.items():
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-s", keychain_key, "-w"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                creds[name] = {"status": "ok"}
            else:
                creds[name] = {"status": "missing"}
        except Exception:
            creds[name] = {"status": "error"}

    # Playwright — check with /usr/bin/python3 (the launchd Python), not sys.executable
    try:
        result = subprocess.run(
            ["/usr/bin/python3", "-c", "from playwright.sync_api import sync_playwright"],
            capture_output=True, timeout=5,
        )
        if result.returncode == 0:
            creds["playwright"] = {"status": "ok"}
        else:
            creds["playwright"] = {"status": "missing"}
    except Exception:
        creds["playwright"] = {"status": "missing"}

    missing = [k for k, v in creds.items() if v["status"] != "ok"]
    if missing:
        return {"status": "fail", "creds": creds, "missing": missing}
    return {"status": "ok", "creds": creds}


def check_playwright_preflight():
    """Run the Playwright pre-flight check and return status."""
    preflight = Path("/Users/lokeshgarg/gentlequest/scripts/gq_playwright_preflight.py")
    if not preflight.exists():
        return {"status": "skip", "error": "Preflight script not found"}

    # Read the last known status file (avoids launching a browser during health check)
    status_file = Path.home() / ".local/share/gentlequest/playwright_auth_status.json"
    if not status_file.exists():
        return {"status": "fail", "error": "No preflight status file — run preflight manually"}

    try:
        status = json.loads(status_file.read_text())
        # Check if status is stale (>24h old)
        timestamp = status.get("timestamp", "")
        if timestamp:
            from datetime import datetime, timezone, timedelta
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - ts
            if age > timedelta(hours=24):
                return {"status": "warn", "error": f"Preflight status is {age.total_seconds()/3600:.0f}h old — run preflight"}

        overall = status.get("overall", "unknown")
        if overall == "ok":
            return {"status": "ok"}
        elif overall == "warn":
            return {"status": "warn", "error": "Preflight has warnings"}
        else:
            failing = [k for k, v in status.get("checks", {}).items() if v.get("status") == "fail"]
            return {"status": "fail", "error": f"Preflight failing: {failing}", "failing": failing}
    except Exception as e:
        return {"status": "fail", "error": str(e)}


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    quiet = "--quiet" in sys.argv

    checks = {
        "blog_live": check_blog_live(),
        "scheduled_queue": check_scheduled_queue(),
        "published_count": check_published_count(),
        "blog_staggered_recent": check_blog_staggered_recent(),
        "publisher_channels": check_publisher_channels(),
        "credentials": check_credentials(),
        "playwright_preflight": check_playwright_preflight(),
    }

    # Aggregate status
    statuses = [v["status"] for v in checks.values()]
    overall = "ok"
    if "fail" in statuses:
        overall = "fail"
    elif "warn" in statuses:
        overall = "warn"

    report = {
        "timestamp": utc_now(),
        "overall": overall,
        "checks": checks,
    }

    # Write status file
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(report, indent=2))

    # Print report unless quiet
    if not quiet or overall == "fail":
        print(f"Pipeline Health: {overall.upper()}")
        for name, result in checks.items():
            status_icon = {"ok": "✓", "fail": "✗", "warn": "⚠"}.get(result["status"], "?")
            print(f"  {status_icon} {name}: {result['status']}", end="")
            if "error" in result:
                print(f" — {result['error']}", end="")
            if "count" in result:
                print(f" (count={result['count']})", end="")
            if "failing" in result:
                print(f" (failing={result['failing']})", end="")
            if "missing" in result:
                print(f" (missing={result['missing']})", end="")
            print()

    # Telegram alert on failure — includes fix commands an agent can execute directly
    if overall == "fail":
        failing_checks = [k for k, v in checks.items() if v["status"] == "fail"]
        msg = "⚠️ *GentleQuest Pipeline Health: FAIL*\n\nFailing checks:\n"
        for check in failing_checks:
            err = checks[check].get("error", "unknown")
            # For publisher_channels, include per-channel breakdown
            if check == "publisher_channels" and "channels" in checks[check]:
                ch_failures = checks[check].get("failing", [])
                ch_details = checks[check]["channels"]
                err = ", ".join(f"{c}: {ch_details[c].get('error', '?')}" for c in ch_failures)
            msg += f"  ✗ {check}: {err}\n"

        msg += "\n*Fix commands:*\n"
        fix_map = {
            "blog_live": "curl -s --max-time 15 https://gentlequest-blog.onrender.com — check if blog is down. If down, check Render dashboard: https://dashboard.render.com",
            "scheduled_queue": "No scheduled posts left. Generate more:\npython3 ~/gentlequest/scripts/gq_autonomous_publisher.py --generate --generate-count 20\nThen move some to gentlequest-blog/src/content/scheduled/",
            "blog_staggered_recent": "Blog staggered script failing. Check log:\ntail -20 ~/Library/Logs/gq_blog_staggered.log\nIf npm PATH issue, verify plist has PATH with nvm. Reload:\nlaunchctl unload ~/Library/LaunchAgents/com.gentlequest.blog-staggered.plist && launchctl load ~/Library/LaunchAgents/com.gentlequest.blog-staggered.plist",
            "publisher_channels": "Check which channels are failing (see above). Common fixes:\n• Buffer limit: wait for scheduled posts to publish\n• Dev.to: security add-generic-password -s devto-api-key -a gentlequest -w KEY\n• Medium/Reddit: python3 ~/gentlequest/scripts/gq_autonomous_publisher.py --setup-browser\n• Playwright: /usr/bin/python3 -m pip install playwright && /usr/bin/python3 -m playwright install chromium",
            "credentials": "Missing keychain credentials. Add with:\nsecurity add-generic-password -s SERVICE_NAME -a gentlequest -w KEY_VALUE\nCheck Apple Notes 'Tokens (new) and api keys' for available keys.",
            "playwright_preflight": "Playwright auth expired or broken. Re-authenticate:\npython3 ~/gentlequest/scripts/gq_autonomous_publisher.py --setup-browser\nLog in to Reddit + Medium in the browser, then close it.\nIf Playwright uninstalled: /usr/bin/python3 -m pip install playwright && /usr/bin/python3 -m playwright install chromium",
        }
        for check in failing_checks:
            if check in fix_map:
                msg += f"\n_{check}_:\n{fix_map[check]}\n"
            else:
                msg += f"\n_{check}_: See status file for details.\n"

        msg += f"\nFull status: {STATUS_PATH}"
        msg += f"\nRun full check: python3 ~/gentlequest/scripts/gq_pipeline_health_check.py"
        send_telegram(msg)

    # Exit code: 0=ok, 1=warn, 2=fail
    sys.exit(0 if overall == "ok" else 1 if overall == "warn" else 2)


if __name__ == "__main__":
    main()
