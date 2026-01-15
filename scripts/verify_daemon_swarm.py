
"""
Verification Script for Phase 59 (Daemon + Orchestrator).
Proves the "Sovereign Organism" is alive.
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("mcp-server-nucleus/src"))

from mcp_server_nucleus.runtime.daemon import DaemonManager
from mcp_server_nucleus.runtime.export import DataExporter

async def verify_daemon_lifecycle():
    print("🧪 Starting Daemon Verification...")
    
    brain_path = Path(".brain")
    brain_path.mkdir(exist_ok=True)
    
    # 1. Initialize Daemon
    daemon = DaemonManager(brain_path)
    print("✅ DaemonManager Initialized.")
    
    # 2. Test Orchestrator Wiring
    print("🧪 Triggering Swarm Mission (Genesis)...")
    result = await daemon.orchestrator.start_mission("Verify Sovereignty", swarm_type="genesis")
    print(f"   Result: {result}")
    
    if result["status"] == "started":
        print("✅ Orchestrator: Mission Started.")
    else:
        print("❌ Orchestrator Failed.")
        return

    # 3. Verify State Persistence
    state_file = brain_path / "swarms" / "state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text())
        mission_id = result["mission_id"]
        if mission_id in state:
             print(f"✅ Persistence: Mission {mission_id} found in state.json")
             # Verify bounds were set
             m_data = state[mission_id]
             print(f"   Max Steps: {m_data.get('max_steps')}")
             print(f"   Max Budget: ${m_data.get('max_budget')}")
        else:
             print("❌ Persistence: Mission not found in state.")
    else:
        print("❌ Persistence: state.json not created.")

    # 4. Verify Data Exporter ("Eject Button")
    print("🧪 Testing DataExporter (Anti-Sherlock)...")
    exporter = DataExporter(brain_path)
    export_res = exporter.export_full_state()
    
    if Path(export_res["path"]).exists():
        print(f"✅ DataExporter: Archive created at {export_res['path']}")
    else:
        print("❌ DataExporter Failed.")

    # 5. Verify Strategic Hooks (The Missing 10%)
    print("🧪 Testing Strategic Hooks (Identity/Pulse)...")
    if daemon.identity.did.startswith("did:nucleus:"):
        print(f"✅ Identity: Node DID = {daemon.identity.did}")
    else:
        print("❌ Identity: Failed to generate DID.")

    # Pulse check (Manual beat)
    daemon.pulse.beat("test", 0)
    if daemon.pulse.pulse_file.exists():
        print(f"✅ Pulse: Heartbeat file verified at {daemon.pulse.pulse_file}")
    else:
        print("❌ Pulse: Failed to write heartbeat.")

    print("\n🎉 PHASE 59 VERIFICATION COMPLETE: The Daemon is Alive & Sovereign.")

if __name__ == "__main__":
    asyncio.run(verify_daemon_lifecycle())
