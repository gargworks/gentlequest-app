#!/usr/bin/env python3
"""
Real-time Terminal Sync Monitor
Watches /tmp/nucleus-terminal-sync.log and displays new content as it arrives.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

SYNC_LOG = Path("/tmp/nucleus-terminal-sync.log")
POLL_INTERVAL = 0.5  # seconds

def monitor_log():
    """Monitor the sync log file and display new content."""
    print(f"🔍 Monitoring: {SYNC_LOG}")
    print(f"⏱️  Poll interval: {POLL_INTERVAL}s")
    print("=" * 60)
    
    # Create log file if it doesn't exist
    if not SYNC_LOG.exists():
        SYNC_LOG.touch()
        print(f"📝 Created new log file: {SYNC_LOG}")
    
    # Start from the end of the file
    with open(SYNC_LOG, 'r') as f:
        f.seek(0, 2)  # Seek to end
        
        try:
            while True:
                line = f.readline()
                if line:
                    # Print new content immediately
                    print(line, end='')
                    sys.stdout.flush()
                else:
                    # No new content, wait and retry
                    time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped.")
            return

def tail_log(lines: int = 50):
    """Display the last N lines of the sync log."""
    if not SYNC_LOG.exists():
        print(f"⚠️  Log file not found: {SYNC_LOG}")
        return
    
    with open(SYNC_LOG, 'r') as f:
        all_lines = f.readlines()
        tail_lines = all_lines[-lines:]
        
        print(f"📜 Last {len(tail_lines)} lines from {SYNC_LOG}:")
        print("=" * 60)
        for line in tail_lines:
            print(line, end='')

def clear_log():
    """Clear the sync log file."""
    if SYNC_LOG.exists():
        SYNC_LOG.unlink()
        print(f"🗑️  Cleared: {SYNC_LOG}")
    SYNC_LOG.touch()
    print(f"📝 Created fresh log: {SYNC_LOG}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "tail":
            lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            tail_log(lines)
        elif cmd == "clear":
            clear_log()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage:")
            print("  monitor_terminal_sync.py          # Monitor in real-time")
            print("  monitor_terminal_sync.py tail [N] # Show last N lines")
            print("  monitor_terminal_sync.py clear    # Clear log file")
    else:
        monitor_log()
