#!/usr/bin/env python3
"""
Phase 2: Consolidation - Archive stale files, update indexes
============================================================
"""

import json
import shutil
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
STATE_FILE = ROOT / "autonomous_state.json"
ARCHIVE_DIR = ROOT / "docs" / "archive"
ARCHIVE_LOG = ROOT / "docs" / "ARCHIVE.md"

# Files to archive (relative to ROOT)
STALE_FILES = [
    "BEFORE_AFTER_COMPARISON.md",
    "COMPREHENSIVE_CRISIS_TESTING.md",
    "COMPREHENSIVE_FIXES.md",
    "COMPREHENSIVE_TESTING_PLAN.md",
    "CRISIS_DETECTION_ANALYSIS.md",
    "CRISIS_DETECTION_TEST_CASES.md",
    "CRISIS_WIDGET_DEBUG.md",
    "TEST_RESULTS_SUMMARY.md",
    "GEOGRAPHY_CRISIS_DETECTION_IMPLEMENTATION_SUMMARY.md",
    "GEOGRAPHY_CRISIS_DETECTION_TEST_REPORT.md",
]

def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def archive_files():
    """Move stale files to archive."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    archived = []
    for filename in STALE_FILES:
        src = ROOT / filename
        if src.exists():
            dst = ARCHIVE_DIR / filename
            shutil.move(str(src), str(dst))
            archived.append(filename)
            print(f"  Archived: {filename}")
    
    return archived

def update_archive_log(archived):
    """Append to ARCHIVE.md."""
    if not archived:
        return
    
    with open(ARCHIVE_LOG, "a") as f:
        f.write(f"\n## Archived {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        for filename in archived:
            f.write(f"- `{filename}` (auto-archived by Phase 2)\n")

def main():
    print("📦 Phase 2: Consolidation Starting...")
    
    archived = archive_files()
    print(f"\n✅ Archived {len(archived)} files")
    
    update_archive_log(archived)
    print("✅ Updated ARCHIVE.md")
    
    # Update state
    state = load_state()
    state["phases"]["2"]["status"] = "COMPLETE"
    state["phases"]["2"]["result"] = {"archived_count": len(archived), "files": archived}
    save_state(state)
    
    print("\n✅ Phase 2 Complete")

if __name__ == "__main__":
    main()
