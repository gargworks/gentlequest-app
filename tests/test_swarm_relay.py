
import json
import os
import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

from mcp_server_nucleus.runtime.capabilities.brain_ops import BrainOps

@unittest.skipIf(os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI"), "requires local brain fixture")
class TestSwarmRelay(unittest.TestCase):
    def test_relay_execution(self):
        """Test that BrainOps can trigger the Orchestrator (Relay)."""
        
        # Set Env Var to UUID Brain
        uuid_brain = "/Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1"
        os.environ["NUCLEUS_BRAIN_PATH"] = uuid_brain
        
        ops = BrainOps()
        
        # Simulate call
        # We use 'execution' swarm which we know exists
        args = {
            "mission": "Relay Test Mission",
            "swarm_type": "execution", 
            "agents": []
        }
        
        # This calls Orchestrator -> loads .brain/swarms/execution.md -> loads Personas
        result = ops.execute_tool("brain_orchestrate_swarm", args)
        
        print("\n--- Relay Result ---")
        print(result)
        
        self.assertIn("✅ Swarm Initiated", result)
        self.assertIn("Mission ID:", result)
        self.assertIn("Role: tech_lead", result)
        self.assertIn("Execution Swarm Protocol", result) 

if __name__ == "__main__":
    unittest.main()
