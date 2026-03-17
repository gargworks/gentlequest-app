#!/usr/bin/env python3
"""
Task Source Migration Script
Unifies /ledger/tasks.json and .brain/ledger/tasks.json into a single source of truth.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

# Paths
BRAIN_TASKS = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/ledger/tasks.json")
LEDGER_TASKS = Path("/Users/lokeshgarg/ai-mvp-backend/ledger/tasks.json")
BACKUP_DIR = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/backups/task_migration")

def load_tasks(path: Path) -> List[Dict[str, Any]]:
    """Load tasks from JSON file."""
    if not path.exists():
        return []
    return json.loads(path.read_text())

def save_tasks(path: Path, tasks: List[Dict[str, Any]]):
    """Save tasks to JSON file with atomic write."""
    temp_path = path.with_suffix('.json.tmp')
    temp_path.write_text(json.dumps(tasks, indent=2, ensure_ascii=False))
    temp_path.replace(path)

def create_backup():
    """Create timestamped backup of both task files."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    if BRAIN_TASKS.exists():
        backup_brain = BACKUP_DIR / f"brain_tasks_{timestamp}.json"
        shutil.copy2(BRAIN_TASKS, backup_brain)
        print(f"✅ Backed up brain tasks to: {backup_brain}")
    
    if LEDGER_TASKS.exists():
        backup_ledger = BACKUP_DIR / f"ledger_tasks_{timestamp}.json"
        shutil.copy2(LEDGER_TASKS, backup_ledger)
        print(f"✅ Backed up ledger tasks to: {backup_ledger}")
    
    return timestamp

def merge_tasks(brain_tasks: List[Dict], ledger_tasks: List[Dict]) -> List[Dict]:
    """Merge tasks from both sources, preserving brain tasks and adding ledger tasks."""
    # Brain tasks take precedence (they're the canonical source)
    merged = brain_tasks.copy()
    
    # Get existing IDs
    existing_ids = {t['id'] for t in brain_tasks}
    
    # Add ledger tasks that don't exist in brain
    added_count = 0
    for task in ledger_tasks:
        if task['id'] not in existing_ids:
            # Tag the source for tracking
            if 'source' not in task or not task['source']:
                task['source'] = 'migrated_from_ledger'
            elif task['source'] != 'migrated_from_ledger':
                task['source'] = f"{task['source']}_migrated"
            
            merged.append(task)
            added_count += 1
    
    print(f"📊 Merged {len(brain_tasks)} brain tasks + {added_count} ledger tasks = {len(merged)} total")
    return merged

def analyze_migration(brain_tasks: List[Dict], ledger_tasks: List[Dict], merged: List[Dict]):
    """Print migration analysis."""
    from collections import Counter
    
    print("\n" + "=" * 60)
    print("MIGRATION ANALYSIS")
    print("=" * 60)
    
    print(f"\nBefore:")
    print(f"  Brain tasks:  {len(brain_tasks)}")
    print(f"  Ledger tasks: {len(ledger_tasks)}")
    
    print(f"\nAfter:")
    print(f"  Unified tasks: {len(merged)}")
    
    # Status distribution
    status_dist = Counter(t['status'] for t in merged)
    print(f"\nStatus distribution:")
    for status, count in sorted(status_dist.items()):
        print(f"  {status}: {count}")
    
    # Source distribution
    source_dist = Counter(t.get('source', 'unknown') for t in merged)
    print(f"\nSource distribution:")
    for source, count in sorted(source_dist.items(), key=lambda x: -x[1]):
        print(f"  {source}: {count}")
    
    # Priority distribution
    priority_dist = Counter(t.get('priority', 0) for t in merged)
    print(f"\nPriority distribution:")
    for priority, count in sorted(priority_dist.items()):
        print(f"  Priority {priority}: {count}")

def main():
    print("🔄 Task Source Migration")
    print("=" * 60)
    
    # Step 1: Create backups
    print("\n📦 Creating backups...")
    timestamp = create_backup()
    
    # Step 2: Load tasks
    print("\n📖 Loading tasks...")
    brain_tasks = load_tasks(BRAIN_TASKS)
    ledger_tasks = load_tasks(LEDGER_TASKS)
    print(f"  Brain: {len(brain_tasks)} tasks")
    print(f"  Ledger: {len(ledger_tasks)} tasks")
    
    # Step 3: Merge
    print("\n🔀 Merging tasks...")
    merged = merge_tasks(brain_tasks, ledger_tasks)
    
    # Step 4: Analysis
    analyze_migration(brain_tasks, ledger_tasks, merged)
    
    # Step 5: Confirm
    print("\n" + "=" * 60)
    print("⚠️  READY TO MIGRATE")
    print("=" * 60)
    print(f"\nThis will:")
    print(f"  1. Write {len(merged)} tasks to {BRAIN_TASKS}")
    print(f"  2. Archive {LEDGER_TASKS} to {LEDGER_TASKS}.archived_{timestamp}")
    print(f"  3. Create symlink: {LEDGER_TASKS} → {BRAIN_TASKS}")
    print(f"\nBackups saved to: {BACKUP_DIR}")
    
    response = input("\nProceed? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Migration aborted.")
        return
    
    # Step 6: Execute migration
    print("\n🚀 Executing migration...")
    
    # Write merged tasks to brain
    save_tasks(BRAIN_TASKS, merged)
    print(f"✅ Wrote {len(merged)} tasks to {BRAIN_TASKS}")
    
    # Archive old ledger
    archived_path = LEDGER_TASKS.with_suffix(f'.json.archived_{timestamp}')
    shutil.move(LEDGER_TASKS, archived_path)
    print(f"✅ Archived {LEDGER_TASKS} to {archived_path}")
    
    # Create symlink
    LEDGER_TASKS.symlink_to(BRAIN_TASKS)
    print(f"✅ Created symlink: {LEDGER_TASKS} → {BRAIN_TASKS}")
    
    print("\n" + "=" * 60)
    print("✅ MIGRATION COMPLETE")
    print("=" * 60)
    print(f"\nAll tasks now unified in: {BRAIN_TASKS}")
    print(f"Legacy path {LEDGER_TASKS} now points to brain tasks")
    print(f"\nBackups: {BACKUP_DIR}")
    
    # Verification
    print("\n🔍 Verification...")
    verify_tasks = load_tasks(BRAIN_TASKS)
    print(f"  Brain tasks: {len(verify_tasks)} ✅")
    
    symlink_tasks = load_tasks(LEDGER_TASKS)
    print(f"  Symlink tasks: {len(symlink_tasks)} ✅")
    
    if len(verify_tasks) == len(symlink_tasks) == len(merged):
        print("\n✅ All verification checks passed!")
    else:
        print("\n⚠️  Verification mismatch detected!")

if __name__ == "__main__":
    main()
