import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path("/Users/lokeshgarg/ai-mvp-backend")
sys.path.append(str(project_root / "mcp-server-nucleus" / "src"))

# Set environment variable
os.environ["NUCLEUS_BRAIN_PATH"] = str(project_root / ".brain")
os.environ["NUCLEAR_BRAIN_PATH"] = str(project_root / ".brain")

from mcp_server_nucleus.runtime.swarm import _orchestrate_swarm

async def main():
    mission = (
        "Research the implementation patterns for 'Decision Systems of Record' and 'Context Graphs' "
        "within an event-sourced agentic architecture, specifically referencing the Jaya Gupta/Foundation Capital "
        "'Trillion Dollar Elephant' thesis. Propose how to modify the Nucleus-MCP v0.5.0 runtime to capture "
        "structured decision traces (the 'why' links) and build a queryable record of how decisions turned into action."
    )
    agents = ["researcher", "synthesizer", "architect"]
    
    print(f"🚀 Spawning research swarm for mission: {mission}")
    result = _orchestrate_swarm(mission, agents)
    print(f"✅ Swarm initiated: {result}")
    
    if result.get("success"):
        mission_id = result["mission_id"]
        print(f"⏳ Waiting for mission {mission_id} to complete...")
        
        from mcp_server_nucleus.runtime.swarm import _get_swarm_status
        
        while True:
            status_res = _get_swarm_status(mission_id)
            if not status_res.get("success"):
                print(f"❌ Could not get status: {status_res.get('error')}")
                break
                
            status = status_res.get("status")
            print(f"📊 Status: {status} (Step: {status_res.get('step_count')})")
            
            if status in ["completed", "failed", "halted_steps", "halted_budget"]:
                print(f"🏁 Mission terminated with status: {status}")
                if status == "completed":
                    print(f"📄 Results should be at: {result.get('check_results')}")
                break
                
            await asyncio.sleep(10)
    else:
        print(f"❌ Failed to start swarm: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
