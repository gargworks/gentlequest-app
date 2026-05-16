#!/usr/bin/env python3
"""Install launchd daemon for brain_telegram.py webhook server.

Runs on boot, keeps alive on crash, logs to .brain/daemon/telegram_webhook*.log.
Required env (.env at repo root, gitignored):
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID
    WEBHOOK_PUBLIC_URL   (e.g. https://tg.nucleusos.dev — must be reachable from Telegram)

Usage:
    python3 scripts/install_telegram_webhook_daemon.py              # install + load
    python3 scripts/install_telegram_webhook_daemon.py --uninstall
    python3 scripts/install_telegram_webhook_daemon.py --status

---------------------------------------------------------------------------
ONE-TIME CLOUDFLARED + DNS SETUP (Lokesh keyboard, ~5 minutes)
---------------------------------------------------------------------------

Telegram webhooks require a public HTTPS URL. We reuse the existing
`nucleus-telemetry` cloudflared tunnel by adding a second ingress rule +
DNS route pointing to localhost:5001.

1) Edit ~/.cloudflared/config.yml — add the `tg.nucleusos.dev` ingress
   BEFORE the catch-all 404 line:

     ingress:
       - hostname: telemetry.nucleusos.dev
         service: http://localhost:4318
       - hostname: tg.nucleusos.dev          # ADD THIS
         service: http://localhost:5001      # ADD THIS
       - service: http_status:404

2) Route the DNS record to the tunnel (one-time, idempotent):

     cloudflared tunnel route dns nucleus-telemetry tg.nucleusos.dev

3) Restart the tunnel so the new ingress takes effect:

     launchctl unload ~/Library/LaunchAgents/com.cloudflare.cloudflared.plist
     launchctl load   ~/Library/LaunchAgents/com.cloudflare.cloudflared.plist

4) Add to .env (at repo root):

     WEBHOOK_PUBLIC_URL=https://tg.nucleusos.dev

5) Then run this installer. On daemon-start it will call Telegram's
   setWebhook API with https://tg.nucleusos.dev/telegram/webhook.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

LABEL = "dev.nucleusos.telegram-webhook"
LAUNCH_AGENT_DIR = Path.home() / "Library" / "LaunchAgents"
PLIST_PATH = LAUNCH_AGENT_DIR / f"{LABEL}.plist"

REPO_ROOT = Path(__file__).parent.parent.resolve()
SCRIPT_PATH = REPO_ROOT / "brain_telegram.py"
LOG_DIR = REPO_ROOT / ".brain" / "daemon"
LOG_PATH = LOG_DIR / "telegram_webhook.log"
ERR_PATH = LOG_DIR / "telegram_webhook.err.log"

PYTHON_EXE = sys.executable or "/opt/homebrew/bin/python3"

PLIST_TEMPLATE = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{PYTHON_EXE}</string>
        <string>{SCRIPT_PATH}</string>
        <string>serve</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{REPO_ROOT}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{LOG_PATH}</string>
    <key>StandardErrorPath</key>
    <string>{ERR_PATH}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
</dict>
</plist>
"""


def _load_dotenv() -> None:
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def preflight() -> int:
    """Verify Slice 1.1 prereqs before loading the daemon.

    Hard-fail if WEBHOOK_PUBLIC_URL is unset — without it Telegram has no
    route to localhost:5001 and callback_query taps never arrive. Prevents
    Lokesh from running the installer half-informed.
    """
    _load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    url = os.environ.get("WEBHOOK_PUBLIC_URL", "")
    missing = []
    if not token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not url:
        missing.append("WEBHOOK_PUBLIC_URL")
    if missing:
        print(f"Preflight FAIL — missing env vars: {', '.join(missing)}", file=sys.stderr)
        print("See scripts/install_telegram_webhook_daemon.py docstring for setup.", file=sys.stderr)
        return 1
    print(f"Preflight OK — WEBHOOK_PUBLIC_URL={url}")
    return 0


def install() -> int:
    rc = preflight()
    if rc != 0:
        return rc
    LAUNCH_AGENT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not SCRIPT_PATH.exists():
        print(f"brain_telegram.py not found at {SCRIPT_PATH}", file=sys.stderr)
        return 1
    PLIST_PATH.write_text(PLIST_TEMPLATE)
    subprocess.run(["launchctl", "unload", str(PLIST_PATH)], stderr=subprocess.DEVNULL)
    r = subprocess.run(
        ["launchctl", "load", str(PLIST_PATH)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"launchctl load failed: {r.stderr.strip()}", file=sys.stderr)
        return 1
    print(f"Installed: {PLIST_PATH}")
    print(f"Logs: {LOG_PATH}")
    print(f"Errors: {ERR_PATH}")
    print("Health check: curl http://localhost:5001/health")
    return 0


def uninstall() -> int:
    if not PLIST_PATH.exists():
        print(f"Nothing to uninstall at {PLIST_PATH}")
        return 0
    subprocess.run(["launchctl", "unload", str(PLIST_PATH)], stderr=subprocess.DEVNULL)
    PLIST_PATH.unlink()
    print(f"Uninstalled: {PLIST_PATH}")
    return 0


def status() -> int:
    if not PLIST_PATH.exists():
        print(f"Not installed: {PLIST_PATH} missing")
        return 1
    r = subprocess.run(
        ["launchctl", "list", LABEL],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"Installed but not loaded: {PLIST_PATH}")
        return 1
    print(r.stdout.strip() or f"Loaded: {LABEL}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group()
    g.add_argument("--uninstall", action="store_true")
    g.add_argument("--status", action="store_true")
    args = p.parse_args()
    if args.uninstall:
        sys.exit(uninstall())
    if args.status:
        sys.exit(status())
    sys.exit(install())
