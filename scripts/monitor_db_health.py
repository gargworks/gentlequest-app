#!/usr/bin/env python3
"""
DB Health Monitor - Checks database connectivity and alerts via Telegram.
Part of Phase 67: Infrastructure Hardening
"""

import os
import sys
import json
import urllib.request
from datetime import datetime
from mcp_server_nucleus.runtime.secrets import get_telegram_token, get_telegram_chat_id
BACKEND_URL = os.getenv("BACKEND_URL", "https://app.gentlequest.app")

def check_db_health() -> dict:
    """Check database health via backend API."""
    try:
        req = urllib.request.Request(f"{BACKEND_URL}/api/health", method="GET")
        req.add_header("User-Agent", "NucleusMonitor/1.0")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return {
                "status": "healthy" if data.get("database") == "healthy" else "unhealthy",
                "details": data,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

def send_telegram_alert(message: str) -> bool:
    """Send alert to Telegram."""
    token, chat_id = get_telegram_token(), get_telegram_chat_id()
    if not token or not chat_id:
        print("Telegram credentials not configured")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Telegram alert failed: {e}")
        return False

def main():
    result = check_db_health()
    
    if result["status"] != "healthy":
        alert_msg = f"""🚨 *DB Health Alert*

Status: `{result['status']}`
Time: `{result['timestamp']}`
Details: ```{json.dumps(result.get('details', result.get('error', 'Unknown')), indent=2)}```

Action Required: Check Cloud SQL connection."""
        
        send_telegram_alert(alert_msg)
        print(f"ALERT: {result}")
        sys.exit(1)
    else:
        print(f"OK: DB healthy at {result['timestamp']}")
        sys.exit(0)

if __name__ == "__main__":
    main()
