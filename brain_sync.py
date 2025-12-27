#!/usr/bin/env python3
"""
Brain Sync - Bridge God Mode to Event System
=============================================

Run this AFTER a God Mode session to:
1. Scan artifacts for new/modified files
2. Emit corresponding events to events.jsonl
3. Update state.json with completions
4. Send Telegram alerts for critical events

This bridges the gap between interactive sessions and the event-driven system.

Usage:
    python brain_sync.py              # Sync all recent artifacts
    python brain_sync.py --watch      # Watch and sync continuously
    python brain_sync.py --since 1h   # Sync artifacts from last hour

Author: Nuclear Brain System
"""

import os
import sys
import json
import hashlib
import argparse
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict

# Telegram config
TG_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7575125475")

def send_telegram_alert(message: str) -> bool:
    """Send alert to Telegram"""
    if not TG_BOT_TOKEN:
        return False
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "Markdown"},
            timeout=5
        )
        return True
    except:
        return False


# Paths
BRAIN_ROOT = Path(__file__).parent / ".brain"
ARTIFACTS_DIR = BRAIN_ROOT / "artifacts"
LEDGER_DIR = BRAIN_ROOT / "ledger"
EVENTS_FILE = LEDGER_DIR / "events.jsonl"
STATE_FILE = LEDGER_DIR / "state.json"
SYNC_STATE_FILE = BRAIN_ROOT / ".sync_state.json"

# Agent → Artifact folder mapping
AGENT_FOLDERS = {
    "researcher": "research",
    "strategist": "strategy",
    "architect": "architecture",
    "developer": "code",
    "critic": "reviews",
    "synthesizer": "synthesis",
}

def load_sync_state() -> dict:
    """Load last sync state (file hashes)"""
    if SYNC_STATE_FILE.exists():
        with open(SYNC_STATE_FILE, 'r') as f:
            return json.load(f)
    return {"hashes": {}, "last_sync": None}

def save_sync_state(state: dict):
    """Save current sync state"""
    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    with open(SYNC_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def file_hash(path: Path) -> str:
    """Get hash of file content"""
    return hashlib.md5(path.read_bytes()).hexdigest()[:12]

def infer_agent_from_path(path: Path) -> str:
    """Determine which agent produced an artifact"""
    path_str = str(path)
    for agent, folder in AGENT_FOLDERS.items():
        if f"artifacts/{folder}" in path_str:
            return agent
    return "unknown"

def extract_summary(path: Path) -> str:
    """Extract first meaningful line from artifact"""
    try:
        content = path.read_text()
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('>') and not line.startswith('---'):
                return line[:100]
        return path.stem
    except:
        return path.stem

def emit_event(emitter: str, event_type: str, payload: dict) -> str:
    """Emit an event to events.jsonl"""
    event = {
        "event_id": f"sync-{hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "emitter": emitter,
        "event_type": event_type,
        "severity": "NOTABLE",
        "payload": payload,
        "metadata": {"source": "brain_sync"}
    }
    with open(EVENTS_FILE, 'a') as f:
        f.write(json.dumps(event) + '\n')
    return event["event_id"]

def get_new_or_modified_artifacts(since: timedelta = None) -> List[Path]:
    """Find artifacts that are new or modified since last sync"""
    sync_state = load_sync_state()
    old_hashes = sync_state.get("hashes", {})
    
    cutoff_time = None
    if since:
        cutoff_time = datetime.now() - since
    
    new_files = []
    current_hashes = {}
    
    for folder in AGENT_FOLDERS.values():
        folder_path = ARTIFACTS_DIR / folder
        if not folder_path.exists():
            continue
        
        for artifact in folder_path.glob("*.md"):
            # Check modification time
            if cutoff_time:
                mtime = datetime.fromtimestamp(artifact.stat().st_mtime)
                if mtime < cutoff_time:
                    continue
            
            # Check hash
            current_hash = file_hash(artifact)
            current_hashes[str(artifact)] = current_hash
            
            old_hash = old_hashes.get(str(artifact))
            if old_hash != current_hash:
                new_files.append(artifact)
    
    # Update sync state with new hashes
    sync_state["hashes"].update(current_hashes)
    save_sync_state(sync_state)
    
    return new_files

def sync_artifacts(since: timedelta = None, verbose: bool = True):
    """Main sync function"""
    new_artifacts = get_new_or_modified_artifacts(since)
    
    if not new_artifacts:
        if verbose:
            print("✅ No new artifacts to sync")
        return 0
    
    print(f"Found {len(new_artifacts)} new/modified artifacts")
    
    synced = 0
    for artifact in new_artifacts:
        agent = infer_agent_from_path(artifact)
        summary = extract_summary(artifact)
        
        # Emit task_completed event
        event_id = emit_event(
            emitter=agent,
            event_type="task_completed",
            payload={
                "task_description": summary,
                "output_path": str(artifact.relative_to(Path(__file__).parent)),
                "success": True,
                "synced_from": "god_mode"
            }
        )
        
        print(f"  📤 {agent}: {artifact.name} → {event_id}")
        synced += 1
    
    # Update state.json counters
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        counters = state.setdefault("counters", {})
        counters["total_events"] = counters.get("total_events", 0) + synced
        counters["tasks_completed"] = counters.get("tasks_completed", 0) + synced
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=4)
    
    print(f"\n✅ Synced {synced} artifacts to event stream")
    return synced

def watch_and_sync(interval: int = 30):
    """Watch for new artifacts and sync continuously"""
    import time
    
    print(f"👀 Watching for new artifacts (checking every {interval}s)")
    print("   Press Ctrl+C to stop\n")
    
    while True:
        try:
            synced = sync_artifacts(since=timedelta(minutes=5), verbose=False)
            if synced > 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Synced {synced} artifacts")
                # Alert to Telegram
                send_telegram_alert(f"📤 *Brain Sync*\n\n{synced} artifact(s) synced to event stream.")
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n👋 Stopped watching")
            break

def sync_to_production():
    """Push local state.json to Production"""
    print("🚀 Pushing state to Production...")
    
    if not STATE_FILE.exists():
        print("❌ No state.json found locally.")
        return

    with open(STATE_FILE, 'r') as f:
        state_data = json.load(f)
    
    prod_url = "https://gentlequest.onrender.com/api/brain/sync"
    
    try:
        response = requests.post(prod_url, json=state_data, timeout=10)
        if response.status_code == 200:
            print("✅ Successfully synced state to Production!")
        else:
            print(f"❌ Failed to sync: {response.text}")
    except Exception as e:
        print(f"❌ Error syncing to prod: {e}")

def main():
    parser = argparse.ArgumentParser(description="Sync God Mode artifacts to event stream")
    parser.add_argument("--watch", action="store_true", help="Watch and sync continuously")
    parser.add_argument("--since", type=str, help="Time window (e.g., 1h, 30m, 2d)")
    parser.add_argument("--interval", type=int, default=30, help="Watch interval in seconds")
    parser.add_argument("--push-to-prod", action="store_true", help="Push local state.json to Production")
    
    args = parser.parse_args()
    
    if args.push_to_prod:
        sync_to_production()
        return

    # Parse --since
    since = None
    if args.since:
        unit = args.since[-1]
        value = int(args.since[:-1])
        if unit == 'h':
            since = timedelta(hours=value)
        elif unit == 'm':
            since = timedelta(minutes=value)
        elif unit == 'd':
            since = timedelta(days=value)
    
    if args.watch:
        watch_and_sync(args.interval)
    else:
        sync_artifacts(since)

if __name__ == "__main__":
    main()
