#!/usr/bin/env python3
"""
The Digital Twin Lifecycle Daemon
Executes the Morning (Awakening) and Evening (Consolidation) routines.
"""
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
import shutil

NUCLEUS_ROOT = Path("/Users/lokeshgarg/ai-mvp-backend")
BRAIN_PATH = NUCLEUS_ROOT / ".brain"

def notify(title, message):
    """Send a native macOS notification."""
    apple_script = f'display notification "{message}" with title "{title}"'
    subprocess.run(["osascript", "-e", apple_script])
    print(f"[{title}] {message}")

def run_morning_routine():
    """Brushing, Showering, Suiting Up & Breakfast"""
    print("🌅 Initiating Morning Routine...")
    
    # 1. Clean the environment (Shower)
    log_file = NUCLEUS_ROOT / "nucleus" / "logs" / "coordinator.log"
    if log_file.exists():
        rotated_log = log_file.with_name(f"coordinator_{datetime.now().strftime('%Y%m%d')}.log")
        shutil.copy(log_file, rotated_log)
        open(log_file, 'w').close() # Clear current log
        print("✅ Logs rotated and environment cleaned.")

    # 2. Ingest Data (Breakfast)
    # Check git diffs to see what Boss did last night
    try:
        diff = subprocess.check_output(["git", "diff", "--stat", "HEAD@{1.day.ago}"], cwd=NUCLEUS_ROOT, stderr=subprocess.DEVNULL)
        diff_str = diff.decode('utf-8').strip()
    except:
        diff_str = "No major changes or git history unavailable."
    
    context_file = BRAIN_PATH / "meta" / "morning_context.txt"
    context_file.parent.mkdir(exist_ok=True, parents=True)
    with open(context_file, "w") as f:
        f.write(f"Morning Context - {datetime.now().isoformat()}\n\nRecent Code Changes:\n{diff_str}\n")
    print("✅ Morning context ingested.")

    # 3. Say Hi (Sensory Activation)
    notify("🧠 Twin Online", "Good morning Boss. Logs cleaned, context ingested. I am ready for the day.")

def run_evening_routine():
    """Winding Down & Sleeping (Consolidation)"""
    print("🌙 Initiating Evening Routine...")
    
    # 1. Consolidate Memory
    try:
        subprocess.run(["nucleus", "consolidate"], env={**os.environ, "NUCLEUS_BRAIN_PATH": str(BRAIN_PATH)}, check=False)
        print("✅ Brain consolidated.")
    except Exception as e:
        print(f"⚠️ Consolidation notice: {e}")

    # 2. Backup Brain
    backup_name = f".brain-backup-nightly-{datetime.now().strftime('%Y%m%d')}"
    backup_path = NUCLEUS_ROOT / backup_name
    if not backup_path.exists():
        shutil.copytree(BRAIN_PATH, backup_path)
    print(f"✅ Brain backed up to {backup_name}.")

    # 3. Prune old backups (keep last 2)
    backups = sorted(NUCLEUS_ROOT.glob(".brain-backup-nightly-*"))
    if len(backups) > 2:
        for old in backups[:-2]:
            try:
                shutil.rmtree(old)
                print(f"🗑️ Pruned old backup: {old.name}")
            except Exception as e:
                print(f"⚠️ Could not prune {old.name}: {e}")

    # 3. Power Down Signal
    notify("🧠 Twin Sleeping", "Memory consolidated and backed up. Goodnight Boss.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: twin_routine.py [morning|evening]")
        sys.exit(1)
        
    action = sys.argv[1].lower()
    if action == "morning":
        run_morning_routine()
    elif action == "evening":
        run_evening_routine()
    else:
        print("Unknown routine. Use 'morning' or 'evening'.")
