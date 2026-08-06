#!/usr/bin/env python3
"""
GentleQuest Playwright Pre-flight Check

Verifies the full Playwright stack before any browser automation runs:
  1. Python playwright package importable
  2. Chromium browser binary installed
  3. Playwright profile directory exists
  4. Reddit session still authenticated
  5. Medium session still authenticated

Writes auth status to ~/.local/share/gentlequest/playwright_auth_status.json
Sends Telegram alert if anything is broken.

Usage:
  python3 scripts/gq_playwright_preflight.py           # Full check + report
  python3 scripts/gq_playwright_preflight.py --quiet    # Only alert on failure
  python3 scripts/gq_playwright_preflight.py --check-only  # Exit code only, no alert
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PLAYWRIGHT_PROFILE = Path.home() / ".config/gentlequest/playwright-profile"
STATUS_PATH = Path.home() / ".local/share/gentlequest/playwright_auth_status.json"

# Load Telegram creds
ENV_PATH = Path("/Users/lokeshgarg/ai-mvp-backend/.env")
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            TELEGRAM_BOT_TOKEN = line.split("=", 1)[1].strip()
        elif line.startswith("TELEGRAM_CHAT_ID="):
            TELEGRAM_CHAT_ID = line.split("=", 1)[1].strip()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        subprocess.run(
            ["curl", "-s", "-X", "POST",
             f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
             "--data-urlencode", f"chat_id={TELEGRAM_CHAT_ID}",
             "--data-urlencode", f"text={message}",
             "-d", "parse_mode=Markdown"],
            timeout=10, capture_output=True,
        )
    except Exception:
        pass


def check_package():
    """Check if playwright Python package is importable."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return {"status": "ok"}
    except ImportError:
        return {"status": "fail", "error": "Playwright Python package not installed. Run: /usr/bin/python3 -m pip install playwright"}


def check_browser_binary():
    """Check if Chromium browser binary is installed."""
    cache_dir = Path.home() / "Library/Caches/ms-playwright"
    if not cache_dir.exists():
        return {"status": "fail", "error": "Playwright browser cache doesn't exist. Run: /usr/bin/python3 -m playwright install chromium"}
    chromium_dirs = list(cache_dir.glob("chromium-*"))
    if not chromium_dirs:
        return {"status": "fail", "error": "No Chromium binary found. Run: /usr/bin/python3 -m playwright install chromium"}
    return {"status": "ok", "path": str(chromium_dirs[0])}


def check_profile():
    """Check if Playwright profile directory exists with cookies."""
    if not PLAYWRIGHT_PROFILE.exists():
        return {"status": "fail", "error": "Playwright profile doesn't exist. Run: python3 gq_autonomous_publisher.py --setup-browser"}
    # Check for cookie/session files
    cookie_files = list(PLAYWRIGHT_PROFILE.glob("Default/Cookies"))
    if not cookie_files:
        return {"status": "fail", "error": "Profile exists but no cookies found. Run: --setup-browser to log in"}
    return {"status": "ok", "path": str(PLAYWRIGHT_PROFILE)}


def check_reddit_auth():
    """Verify Reddit session is still valid by loading old.reddit.com."""
    pkg = check_package()
    if pkg["status"] != "ok":
        return {"status": "skip", "error": "Playwright not installed"}

    browser = check_browser_binary()
    if browser["status"] != "ok":
        return {"status": "skip", "error": "Browser binary missing"}

    profile = check_profile()
    if profile["status"] != "ok":
        return {"status": "skip", "error": "Profile missing"}

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                str(PLAYWRIGHT_PROFILE),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = context.new_page()
            page.goto("https://old.reddit.com/r/ADHD/new/", timeout=20000)
            page.wait_for_timeout(3000)

            url = page.url
            body_text = page.inner_text("body")[:200] if page.query_selector("body") else ""

            # Check for blocked/login indicators
            if "blocked" in body_text.lower():
                context.close()
                return {"status": "fail", "error": "Reddit blocked the browser (anti-bot). May need to re-login or wait."}
            if "login" in url.lower() or "sign in" in body_text.lower():
                context.close()
                return {"status": "fail", "error": "Reddit session expired. Run: python3 gq_autonomous_publisher.py --setup-browser"}

            # Check if we see posts (means we're logged in and not blocked)
            things = page.query_selector_all(".thing")
            context.close()

            if len(things) > 0:
                return {"status": "ok", "posts_visible": len(things)}
            return {"status": "fail", "error": "No posts visible — session may be invalid or Reddit is blocking"}
    except Exception as e:
        return {"status": "fail", "error": str(e)}


def check_medium_auth():
    """Verify Medium session is still valid."""
    pkg = check_package()
    if pkg["status"] != "ok":
        return {"status": "skip", "error": "Playwright not installed"}

    browser = check_browser_binary()
    if browser["status"] != "ok":
        return {"status": "skip", "error": "Browser binary missing"}

    profile = check_profile()
    if profile["status"] != "ok":
        return {"status": "skip", "error": "Profile missing"}

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                str(PLAYWRIGHT_PROFILE),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = context.new_page()
            page.goto("https://medium.com/me/stories", timeout=20000)
            page.wait_for_timeout(3000)

            url = page.url
            body_text = page.inner_text("body")[:200] if page.query_selector("body") else ""

            context.close()

            if "m/signin" in url or "sign in" in body_text.lower():
                return {"status": "fail", "error": "Medium session expired. Run: python3 gq_autonomous_publisher.py --setup-browser"}
            if "stories" in url.lower():
                return {"status": "ok"}
            return {"status": "warn", "error": f"Unexpected URL: {url[:60]}"}
    except Exception as e:
        return {"status": "fail", "error": str(e)}


def main():
    quiet = "--quiet" in sys.argv
    check_only = "--check-only" in sys.argv

    checks = {
        "playwright_package": check_package(),
        "browser_binary": check_browser_binary(),
        "profile_dir": check_profile(),
        "reddit_auth": check_reddit_auth(),
        "medium_auth": check_medium_auth(),
    }

    # Aggregate
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

    # Print report
    if not quiet or overall == "fail":
        print(f"Playwright Pre-flight: {overall.upper()}")
        for name, result in checks.items():
            icon = {"ok": "✓", "fail": "✗", "warn": "⚠", "skip": "⊘"}.get(result["status"], "?")
            print(f"  {icon} {name}: {result['status']}", end="")
            if "error" in result:
                print(f" — {result['error']}", end="")
            print()

    # Telegram alert on failure (unless --check-only)
    if overall == "fail" and not check_only:
        failing = [k for k, v in checks.items() if v["status"] == "fail"]
        msg = f"⚠️ *Playwright Pre-flight: FAIL*\n\nBroken checks:\n"
        for check in failing:
            err = checks[check].get("error", "unknown")
            msg += f"  ✗ {check}: {err}\n"
        msg += f"\nFix: python3 ~/gentlequest/scripts/gq_autonomous_publisher.py --setup-browser"
        send_telegram(msg)

    sys.exit(0 if overall == "ok" else 1 if overall == "warn" else 2)


if __name__ == "__main__":
    main()
