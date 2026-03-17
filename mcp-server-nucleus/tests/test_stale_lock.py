#!/usr/bin/env python3
"""
Test for Stale Lock Recovery in Nucleus.
Verifies that:
1. Active locks are respected.
2. Dead processes leave 'stale' locks.
3. Nucleus can autonomously recover from stale locks.
"""

import sys
import os
import time
import subprocess
from pathlib import Path

# Add src to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.append(str(repo_root / "src"))

from mcp_server_nucleus.runtime.locking import get_lock

def test_stale_lock_recovery():
    print("🧪 Running Stale Lock Recovery Test...")
    
    test_brain = repo_root / ".brain_test"
    test_brain.mkdir(parents=True, exist_ok=True)
    locks_dir = test_brain / ".locks"
    locks_dir.mkdir(parents=True, exist_ok=True)
    
    lock_name = "test_resilience"
    lock = get_lock(lock_name, base_dir=locks_dir)
    
    # 1. Simulate an active lock
    print("   [1] Acquiring legitimate lock...")
    if not lock.acquire(timeout=1.0, metadata={"test": "active"}):
        print("❌ Failed: Could not acquire fresh lock.")
        return False
    
    print("   [2] Verification: Checking active lock status...")
    report = lock.check_stale_locks()
    if report["state"] != "held":
        print(f"❌ Failed: Lock should be 'held', got '{report['state']}'")
        lock.release()
        return False
    print(f"   ✅ Lock held by PID {report['pid']}")
    
    lock.release()
    
    # 2. Simulate a STALE lock (PID that doesn't exist)
    print("   [3] Mocking a stale lock file (Fake PID 99999)...")
    stale_lock_path = locks_dir / f"{lock_name}.lock"
    # Use a PID that is very unlikely to exist
    fake_pid = 99999
    stale_lock_path.write_text(str(fake_pid))
    
    print("   [4] Verification: Detecting stale lock...")
    report = lock.check_stale_locks()
    if report["state"] != "stale":
        print(f"❌ Failed: Lock should be 'stale', got '{report['state']}'")
        return False
    print("   ✅ Stale lock correctly identified.")
    
    # 3. Test autonomous cleanup
    print("   [5] Testing cleanup_stale()...")
    cleared = lock.cleanup_stale()
    if not cleared:
        print("❌ Failed: cleanup_stale() returned False.")
        return False
    
    if stale_lock_path.exists():
        print("❌ Failed: Lock file still exists after cleanup.")
        return False
    print("   ✅ Stale lock autonomously cleared.")
    
    # 4. Verify re-acquisition after stale cleanup
    print("   [6] Verifying re-acquisition...")
    if not lock.acquire(timeout=1.0):
        print("❌ Failed: Could not acquire lock after stale cleanup.")
        return False
    print("   ✅ Lock re-acquired successfully.")
    lock.release()
    
    print("\n🎉 Stale Lock Recovery Test: PASSED")
    return True

if __name__ == "__main__":
    success = test_stale_lock_recovery()
    sys.exit(0 if success else 1)
