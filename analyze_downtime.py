#!/usr/bin/env python3
"""
Analyze why the app goes down despite keep-alive
"""

import requests
import time
from datetime import datetime, timedelta

print("🔍 ANALYZING DOWNTIME ISSUES")
print("=" * 60)

print("\n⚠️  PROBLEMS FOUND WITH CURRENT KEEP-ALIVE:\n")

print("1. **TIMING ISSUE**:")
print("   - GitHub Actions runs every 13 minutes")
print("   - BUT adds 0-59 second random jitter (line 15)")
print("   - Worst case: 13 min + 59 sec = 13:59")
print("   - Render sleeps after 15 minutes")
print("   - ⚠️  Gap is only 1 minute - TOO RISKY!\n")

print("2. **GITHUB ACTIONS LIMITATIONS**:")
print("   - Can skip runs during GitHub outages")
print("   - May fail silently (has '|| true' fallback)")
print("   - Free tier has execution limits")
print("   - Workflows pause after 60 days of repo inactivity\n")

print("3. **SINGLE POINT OF FAILURE**:")
print("   - Only GitHub Actions keeping it alive")
print("   - No backup if Actions fails")
print("   - No monitoring/alerting when it goes down\n")

print("4. **RENDER FREE TIER REALITY**:")
print("   - Sleeps after 15 minutes NO MATTER WHAT")
print("   - Cold starts take 30-60 seconds")
print("   - Database also spins down")
print("   - Redis connection may timeout\n")

print("=" * 60)
print("🔧 SOLUTIONS:\n")

print("IMMEDIATE FIXES:")
print("1. Reduce interval to */10 (10 minutes)")
print("2. Remove or reduce jitter (max 30 seconds)")
print("3. Add multiple keep-alive sources")
print("4. Add monitoring/alerts\n")

print("BETTER SOLUTION:")
print("✨ Upgrade to Render Paid Tier ($7/month)")
print("   - No sleep/cold starts")
print("   - Always on")
print("   - Better performance")
print("   - Worth it for production\n")

# Test current response time
print("Testing current status...")
times = []
for i in range(5):
    try:
        start = time.time()
        r = requests.get("https://gentlequest.onrender.com/api/health", timeout=30)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Test {i+1}: {elapsed:.2f}s - {r.status_code}")
        time.sleep(2)
    except Exception as e:
        print(f"  Test {i+1}: FAILED - {e}")

if times:
    avg = sum(times) / len(times)
    if avg > 5:
        print(f"\n🔴 HIGH LATENCY: {avg:.2f}s average")
        print("   App is likely cold starting frequently!")
    elif avg > 2:
        print(f"\n🟡 MODERATE LATENCY: {avg:.2f}s average")
        print("   Some cold starts happening")
    else:
        print(f"\n🟢 GOOD LATENCY: {avg:.2f}s average")
        print("   App is currently warm")
