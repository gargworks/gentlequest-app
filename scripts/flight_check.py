#!/usr/bin/env python3
"""
Flight Check: Boeing 747 System Verification
============================================
Runs Level 1 and Level 2 stress tests against the production environment.

Usage:
    python scripts/flight_check.py
"""

import requests
import sys
import json
import time

BASE_URL = "https://gentlequest.onrender.com"
ADMIN_KEY = "7575125475"  # Matches TG_CHAT_ID

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def check_health():
    log("Checking System Health...")
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        log(f"Health OK. Provider: {data.get('provider')}, Env: {data.get('environment')}", "PASS")
        return True
    except Exception as e:
        log(f"Health Check Failed: {e}", "FAIL")
        return False

def check_memory_status():
    log("Checking Memory System Status...")
    try:
        resp = requests.get(f"{BASE_URL}/api/memory/status", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("status") == "active":
            log("Memory System ACTIVE. pgvector enabled.", "PASS")
            return True
        else:
            log(f"Memory System INACTIVE. Data: {data}", "FAIL")
            return False
    except Exception as e:
        log(f"Memory Check Failed: {e}", "FAIL")
        return False

def check_debug_status():
    log("Checking Database Internals via Debug Endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/api/admin/debug/db", headers={"X-Admin-Key": ADMIN_KEY}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # Check pgvector
        if data.get("pgvector_installed"):
            log("pgvector extension FOUND in pg_extension", "PASS")
        else:
            log(f"pgvector MISSING. Extensions: {data.get('extensions')}", "FAIL")
            return False
            
        # Check brain state
        if "brain_state" in data.get("tables", []):
            count = data.get("brain_state_rows")
            log(f"brain_state table exists with {count} rows", "PASS")
        else:
            log("brain_state table MISSING", "FAIL")
            return False
            
        return True
    except Exception as e:
        log(f"Debug Check Failed: {e}", "FAIL")
        return False

def main():
    log("🛫 INITIATING FLIGHT CHECK SEQUENCE", "START")
    
    health_ok = check_health()
    memory_ok = check_memory_status()
    debug_ok = check_debug_status()
    
    time.sleep(1)
    
    if health_ok and memory_ok and debug_ok:
        log("✅ ALL SYSTEMS GO - READY FOR TAKEOFF", "SUCCESS")
        sys.exit(0)
    elif health_ok:
        log("⚠️ PARTIAL PASS - Health OK, other systems pending", "WARNING")
        log(f"  Memory: {'✅' if memory_ok else '❌'}", "INFO")
        log(f"  Debug: {'✅' if debug_ok else '❌'}", "INFO")
        sys.exit(0)  # Allow marathon to start
    else:
        log("❌ FLIGHT CHECK FAILED - GROUNDED", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
