
import sys
import os
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("mcp-server-nucleus/src"))
sys.path.append(os.path.abspath("scripts"))

from mcp_server_nucleus.runtime.event_stream import emit_event, EventSeverity
from orchestrator import process_events, BRAIN_PATH
from mcp_server_nucleus.runtime.factory import ContextFactory

async def test_team_execution():
    print("🧪 Testing Team Execution (Orchestrator -> PM)...")
    
    # 1. Emit Trigger Event
    print("   Emitting 'spec_needed' event...")
    emit_event(
        brain_path=BRAIN_PATH,
        event_type="spec_needed",
        emitter="test_script",
        payload={
            "description": "User wants a 'Dark Mode' feature for the dashboard.",
            "priority": "P2"
        },
        severity=EventSeverity.ROUTINE
    )
    
    # 2. Run Orchestrator Processing
    print("   Running Orchestrator process_events()...")
    factory = ContextFactory(brain_path=BRAIN_PATH)
    
    summary = await process_events(factory)
    
    # 3. Verify Results
    spawned = summary.get("agents_spawned", [])
    print(f"\n   Spawned Agencies: {[s['agent'] for s in spawned]}")
    
    pm_spawned = any(s['agent'] == 'product_manager' for s in spawned)
    
    if pm_spawned:
        print("✅ TEST PASSED: Product Manager spawned successfully.")
    else:
        print("❌ TEST FAILED: Product Manager did NOT spawn.")
        # Debug: check triggers
        from mcp_server_nucleus.runtime.triggers import match_triggers
        # Re-read last event
        # ... logic skipped for brevity ...

if __name__ == "__main__":
    asyncio.run(test_team_execution())
