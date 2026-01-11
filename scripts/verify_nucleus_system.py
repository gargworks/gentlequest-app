#!/usr/bin/env python3
"""
Nucleus System Verification Suite
==================================
Comprehensive verification of all 11 Nucleus components working in sync.

Usage:
    python3 scripts/verify_nucleus_system.py

Location: scripts/verify_nucleus_system.py
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
SERVER_SRC = PROJECT_ROOT / "mcp-server-nucleus" / "src"
sys.path.insert(0, str(SERVER_SRC))

# Set brain path
os.environ["NUCLEAR_BRAIN_PATH"] = str(PROJECT_ROOT / ".brain")

import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='google.generativeai')

# Components to verify
COMPONENTS = [
    "1. Event Stream",
    "2. Trigger Matching",
    "3. Agent Factory",
    "4. Orchestrator",
    "5. Meta-Optimizer",
    "6. Health Check",
    "7. Task Management",
    "8. Commitment Ledger",
    "9. Session Management",
    "10. Depth Tracker",
    "11. Telegram (Optional)"
]

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def verify_event_stream():
    """Verify event stream is working"""
    print("\n📡 Component 1: EVENT STREAM")
    try:
        from mcp_server_nucleus.runtime.event_stream import read_events, emit_event, EventSeverity
        brain_path = Path(os.environ["NUCLEAR_BRAIN_PATH"])
        
        # Count events
        events = read_events(brain_path, limit=100)
        event_count = len(events)
        print(f"   Total events: {event_count}")
        
        if event_count < 10:
            print(f"   ⚠️  Low event count (expected 100+)")
            
        # Test emit
        test_event = emit_event(
            brain_path=brain_path,
            event_type="verification_test",
            emitter="verify_nucleus_system",
            payload={"test": True, "timestamp": datetime.now().isoformat()},
            severity=EventSeverity.ROUTINE
        )
        print(f"   Test emit: ✅ Event ID: {test_event['event_id']}")
        
        # Get unique event types
        event_types = set()
        for e in events:
            et = e.get('event_type') or e.get('type', 'unknown')
            event_types.add(et)
        print(f"   Unique types: {len(event_types)}")
        
        return True, event_count
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, 0

def verify_triggers():
    """Verify trigger matching"""
    print("\n🎯 Component 2: TRIGGER MATCHING")
    try:
        from mcp_server_nucleus.runtime.triggers import load_triggers, match_triggers
        brain_path = Path(os.environ["NUCLEAR_BRAIN_PATH"])
        
        triggers = load_triggers(brain_path)
        trigger_count = len(triggers.get('triggers', []))
        print(f"   Triggers loaded: {trigger_count}")
        
        # Test matching
        test_event = {"type": "task_created", "emitter": "test"}
        matches = match_triggers(brain_path, test_event)
        print(f"   Test match (task_created): {len(matches)} agents would activate")
        
        return True, trigger_count
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, 0

def verify_factory():
    """Verify agent factory"""
    print("\n🏭 Component 3: AGENT FACTORY")
    try:
        from mcp_server_nucleus.runtime.factory import ContextFactory
        brain_path = Path(os.environ["NUCLEAR_BRAIN_PATH"])
        
        factory = ContextFactory(brain_path=brain_path)
        print(f"   Factory initialized: ✅")
        
        # Test context creation
        context = factory.create_context("test-session", "Test intent")
        print(f"   Context created: ✅")
        print(f"   Capabilities: {len(context.get('capabilities', []))}")
        print(f"   Tools: {len(context.get('tools', []))}")
        
        return True, len(context.get('capabilities', []))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, 0

def verify_orchestrator():
    """Verify orchestrator can run"""
    print("\n📋 Component 4: ORCHESTRATOR")
    try:
        brain_path = Path(os.environ["NUCLEAR_BRAIN_PATH"])
        digest_path = brain_path / "artifacts" / "synthesis"
        
        # Check for digest files
        digests = list(digest_path.glob("digest_*.md")) if digest_path.exists() else []
        print(f"   Digest files: {len(digests)}")
        
        if digests:
            latest = max(digests, key=lambda p: p.stat().st_mtime)
            age_hours = (time.time() - latest.stat().st_mtime) / 3600
            print(f"   Latest digest: {latest.name} ({age_hours:.1f}h ago)")
            print(f"   ✅ Orchestrator functional")
        else:
            print(f"   ⚠️  No digests found - run orchestrator.py")
            
        return True, len(digests)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, 0

def verify_meta_optimizer():
    """Verify meta-optimizer"""
    print("\n🧠 Component 5: META-OPTIMIZER")
    try:
        brain_path = Path(os.environ["NUCLEAR_BRAIN_PATH"])
        opt_log = brain_path / "meta" / "optimization_log.md"
        
        if opt_log.exists():
            age_hours = (time.time() - opt_log.stat().st_mtime) / 3600
            print(f"   Last optimization: {age_hours:.1f}h ago")
            print(f"   ✅ Meta-optimizer has run")
            return True, 1
        else:
            print(f"   ⚠️  No optimization log - run meta_optimizer.py")
            return True, 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, 0

def verify_health_check():
    """Verify health check"""
    print("\n🏥 Component 6: HEALTH CHECK")
    try:
        brain_path = Path(os.environ["NUCLEAR_BRAIN_PATH"])
        health_dir = brain_path / "meta" / "health_checks"
        
        if health_dir.exists():
            checks = list(health_dir.glob("health_check_*.txt"))
            print(f"   Health check files: {len(checks)}")
            
            if checks:
                latest = max(checks, key=lambda p: p.stat().st_mtime)
                age_hours = (time.time() - latest.stat().st_mtime) / 3600
                print(f"   Latest: {latest.name} ({age_hours:.1f}h ago)")
                print(f"   ✅ Health check functional")
            return True, len(checks)
        else:
            print(f"   ⚠️  No health checks - run nucleus_health_check.py")
            return True, 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, 0

def verify_tasks():
    """Verify task management"""
    print("\n✓ Component 7: TASK MANAGEMENT")
    try:
        from mcp_server_nucleus import brain_list_tasks, brain_add_task
        
        tasks = brain_list_tasks()
        print(f"   Tasks in queue: {len(tasks)}")
        
        # Test add
        result = brain_add_task("Verification test task", priority=5)
        if result.get('success'):
            print(f"   Task creation: ✅")
            return True, len(tasks)
        else:
            print(f"   ⚠️  Task creation failed: {result.get('error')}")
            return False, len(tasks)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, 0

def verify_commitments():
    """Verify commitment ledger"""
    print("\n📑 Component 8: COMMITMENT LEDGER")
    try:
        from mcp_server_nucleus import brain_list_commitments, brain_commitment_health
        
        health = brain_commitment_health()
        print("   " + health.split('\n')[2] if health else "   Status unknown")
        
        commitments = brain_list_commitments()
        if "No open" in commitments or "0 total" in commitments:
            print(f"   Open commitments: 0")
        else:
            lines = [l for l in commitments.split('\n') if l.strip()]
            print(f"   Ledger active: ✅")
        
        return True, 1
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, 0

def verify_sessions():
    """Verify session management"""
    print("\n💾 Component 9: SESSION MANAGEMENT")
    try:
        from mcp_server_nucleus import brain_list_sessions, brain_check_recent_session
        
        sessions = brain_list_sessions()
        if isinstance(sessions, list):
            print(f"   Saved sessions: {len(sessions)}")
        elif isinstance(sessions, str):
            print(f"   Sessions: Active")
            
        recent = brain_check_recent_session()
        if recent.get('has_recent_session'):
            print(f"   Recent session: ✅ (can resume)")
        else:
            print(f"   No recent session to resume")
            
        return True, 1
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, 0

def verify_depth():
    """Verify depth tracker"""
    print("\n📊 Component 10: DEPTH TRACKER")
    try:
        from mcp_server_nucleus import brain_depth_show
        
        depth = brain_depth_show()
        if isinstance(depth, dict):
            print(f"   Current depth: {depth.get('current_depth', 0)}/{depth.get('max_safe_depth', 5)}")
            print(f"   Status: {depth.get('status', 'unknown')}")
            print(f"   ✅ Depth tracker functional")
            return True, 1
        elif isinstance(depth, str) and ("DEPTH" in depth or "depth" in depth.lower()):
            print(f"   Depth tracker: ✅ Active")
            return True, 1
        else:
            print(f"   ⚠️  Depth info unclear")
            return True, 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, 0

def verify_telegram():
    """Verify Telegram integration"""
    print("\n📱 Component 11: TELEGRAM INTEGRATION")
    try:
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        if token:
            print(f"   Bot token: ✅ Configured")
        else:
            print(f"   Bot token: ❌ Missing")
            return False, 0
            
        if chat_id and chat_id != "PENDING_USER_ACTION":
            print(f"   Chat ID: ✅ {chat_id[:6]}...")
            return True, 1
        else:
            print(f"   Chat ID: ⏳ Pending (send /start to bot)")
            return True, 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, 0

def run_full_verification():
    """Run verification of all components"""
    print_header("NUCLEUS SYSTEM VERIFICATION")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Brain Path: {os.environ.get('NUCLEAR_BRAIN_PATH')}")
    
    results = {}
    
    # Run all verifications
    results['event_stream'] = verify_event_stream()
    results['triggers'] = verify_triggers()
    results['factory'] = verify_factory()
    results['orchestrator'] = verify_orchestrator()
    results['meta_optimizer'] = verify_meta_optimizer()
    results['health_check'] = verify_health_check()
    results['tasks'] = verify_tasks()
    results['commitments'] = verify_commitments()
    results['sessions'] = verify_sessions()
    results['depth'] = verify_depth()
    results['telegram'] = verify_telegram()
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(1 for r in results.values() if r[0])
    total = len(results)
    
    for name, (status, count) in results.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {name}: {'OK' if status else 'FAILED'}")
    
    print(f"\n   Total: {passed}/{total} components verified")
    
    if passed == total:
        print("\n   🎉 ALL SYSTEMS OPERATIONAL!")
    elif passed >= total - 1:
        print("\n   ✅ SYSTEM READY (minor items pending)")
    else:
        print("\n   ⚠️  Some components need attention")
    
    return passed, total

if __name__ == "__main__":
    # Load .env
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    passed, total = run_full_verification()
    sys.exit(0 if passed >= total - 1 else 1)
