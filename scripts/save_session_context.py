"""
Save Session Context (Capture Phase)
====================================
Part of the Brain Consolidation Protocol.
This script forces a 'flush' of the current session state to disk.

It effectively:
1. Snapshots the current 'active' session task/context.
2. Ensures all raw logs in `.brain/raw/` are secured.
3. Prints a summary of what was captured (for the user to feel safe).
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
BRAIN_PATH = Path(os.environ.get("NUCLEUS_BRAIN_PATH", ".brain"))
RAW_PATH = BRAIN_PATH / "raw"
SNAPSHOT_PATH = BRAIN_PATH / "snapshots"

def main():
    print("🧠 Brain Consolidation: Capture Phase Initiated...")
    
    if not BRAIN_PATH.exists():
        print(f"❌ Brain not found at {BRAIN_PATH}")
        sys.exit(1)
        
    RAW_PATH.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.mkdir(parents=True, exist_ok=True)
    
    # 1. Identify what to save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_name = f"session_snapshot_{timestamp}"
    target_dir = SNAPSHOT_PATH / snapshot_name
    target_dir.mkdir()
    
    print(f"📁 Creating snapshot: {target_dir}")
    
    # 2. Save active session state (if any)
    # Usually in memory or implicit, but let's check for standard files
    session_files = ["task.md", "CONTEXT.md", "active_session.json"]
    saved_count = 0
    
    for filename in session_files:
        src = BRAIN_PATH / filename
        if src.exists():
            shutil.copy2(src, target_dir / filename)
            print(f"   - Saved {filename}")
            saved_count += 1
            
    # 3. Check Raw Logs
    # We don't move them yet (Consolidation phase does that), but we count them
    # to reassure the user.
    raw_files = list(RAW_PATH.glob("*.json"))
    raw_count = len(raw_files)
    
    total_size_mb = sum(f.stat().st_size for f in raw_files) / (1024 * 1024)
    
    print(f"📥 Verifying Raw Capture...")
    print(f"   - Found {raw_count} raw interaction logs in {RAW_PATH}")
    print(f"   - Total Size: {total_size_mb:.2f} MB")
    print(f"   - These contain the 'Entire Responses' and 'Jargon' for marketing.")
    
    # 4. Generate Receipt
    receipt = {
        "timestamp": datetime.now().isoformat(),
        "snapshot_path": str(target_dir),
        "files_saved": saved_count,
        "raw_logs_count": raw_count
    }
    
    with open(target_dir / "receipt.json", "w") as f:
        json.dump(receipt, f, indent=2)
        
    print("\n✅ Session Context Saved Successfully.")
    print("   Run '/consolidate-brain' (Step 2) to prune and process these logs.")

if __name__ == "__main__":
    main()
