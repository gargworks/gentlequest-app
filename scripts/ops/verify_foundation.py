#!/usr/bin/env python3
"""
Phase 1: Foundation Fix - Verify Production Health
===================================================
Polls production endpoints with retries. Sets fallback mode if needed.
"""

import requests
import json
import time
import sys
from pathlib import Path

BASE_URL = "https://gentlequest.onrender.com"
STATE_FILE = Path(__file__).parent.parent.parent / "autonomous_state.json"
MAX_RETRIES = 30  # 30 retries * 60s = 30 minutes max wait
RETRY_INTERVAL = 60  # seconds

def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def check_health():
    """Check /api/health endpoint."""
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=10)
        return resp.status_code == 200
    except:
        return False

def check_memory():
    """Check /api/memory/status endpoint."""
    try:
        resp = requests.get(f"{BASE_URL}/api/memory/status", timeout=10)
        data = resp.json()
        return data.get("status") == "active"
    except:
        return False

def check_debug_db():
    """Check /api/admin/debug/db endpoint."""
    try:
        resp = requests.get(
            f"{BASE_URL}/api/admin/debug/db",
            headers={"X-Admin-Key": "7575125475"},
            timeout=10
        )
        data = resp.json()
        return data.get("pgvector_installed", False)
    except:
        return False

def run_verification():
    """Main verification loop with retries."""
    print("🔧 Phase 1: Foundation Verification Starting...")
    
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n[Attempt {attempt}/{MAX_RETRIES}]")
        
        health_ok = check_health()
        print(f"  Health: {'✅' if health_ok else '❌'}")
        
        memory_ok = check_memory()
        print(f"  Memory: {'✅' if memory_ok else '❌'}")
        
        debug_ok = check_debug_db()
        print(f"  Debug DB: {'✅' if debug_ok else '❌'}")
        
        if health_ok and memory_ok and debug_ok:
            print("\n✅ All checks PASSED. Production ready.")
            return {"success": True, "mode": "PRODUCTION"}
        
        if attempt < MAX_RETRIES:
            print(f"  Waiting {RETRY_INTERVAL}s before retry...")
            time.sleep(RETRY_INTERVAL)
    
    # Fallback mode
    print("\n⚠️ Max retries reached. Switching to LOCAL_FALLBACK mode.")
    return {"success": False, "mode": "LOCAL_FALLBACK"}

def main():
    result = run_verification()
    
    # Update state
    state = load_state()
    state["mode"] = result["mode"]
    state["phases"]["1"]["status"] = "COMPLETE" if result["success"] else "FALLBACK"
    state["phases"]["1"]["result"] = result
    save_state(state)
    
    sys.exit(0 if result["success"] else 1)

if __name__ == "__main__":
    main()
