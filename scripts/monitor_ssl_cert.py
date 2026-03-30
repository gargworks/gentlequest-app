#!/usr/bin/env python3
"""
SSL Certificate Monitor - Checks certificate expiry and alerts.
Part of Phase 67: Infrastructure Hardening
"""

import os
import ssl
import socket
import json
import urllib.request
from datetime import datetime, timezone
from mcp_server_nucleus.runtime.secrets import get_telegram_token, get_telegram_chat_id
DOMAINS = ["nucleus.gentlequest.app", "app.gentlequest.app"]  # hud.gentlequest.app DNS not configured
WARN_DAYS = 30

def check_cert(hostname: str, port: int = 443) -> dict:
    """Check SSL certificate for a domain."""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                not_after = not_after.replace(tzinfo=timezone.utc)
                days_left = (not_after - datetime.now(timezone.utc)).days
                return {
                    "domain": hostname,
                    "valid": True,
                    "expires": not_after.isoformat(),
                    "days_left": days_left,
                    "subject": dict(x[0] for x in cert['subject'])
                }
    except Exception as e:
        return {"domain": hostname, "valid": False, "error": str(e)}

def send_telegram_alert(message: str) -> bool:
    token, chat_id = get_telegram_token(), get_telegram_chat_id()
    if not token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False

def main():
    alerts = []
    for domain in DOMAINS:
        result = check_cert(domain)
        if not result.get("valid"):
            alerts.append(f"❌ {domain}: {result.get('error', 'Invalid')}")
        elif result.get("days_left", 0) < WARN_DAYS:
            alerts.append(f"⚠️ {domain}: Expires in {result['days_left']} days")
        else:
            print(f"✅ {domain}: {result['days_left']} days remaining")
    
    if alerts:
        msg = "🔐 *SSL Certificate Alert*\n\n" + "\n".join(alerts)
        send_telegram_alert(msg)
        print("\n".join(alerts))
        exit(1)

if __name__ == "__main__":
    main()
