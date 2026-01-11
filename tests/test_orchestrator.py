
import json
import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

from mcp_server_nucleus.runtime.orchestrator import SwarmsOrchestrator

class TestOrchestrator(unittest.TestCase):
    def test_spawn_genesis_swarm(self):
        """Test spawning a Genesis Swarm for a Planning Mission."""
        
        # Point to the actual Brain context where we created the file
        brain_path = Path("/Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1")
        orchestrator = SwarmsOrchestrator(brain_path=brain_path)
        
        mission = "Deconstruct the monolith into microservices"
        result = orchestrator.start_mission(mission, swarm_type="genesis")
        
        print("\n--- Orchestrator Result ---")
        print(json.dumps(result, indent=2))
        
        self.assertEqual(result["status"], "success")
        self.assertIn("mission-", result["mission_id"])
        self.assertEqual(result["lead_agent"], "architect")
        
        context = result["kickoff_context"]
        self.assertIn(f"OBJECTIVE: {mission}", context)
        self.assertIn("ROLE: architect (Swarm Lead)", context)
        self.assertIn("Genesis Swarm Protocol", context)
        
    def test_invalid_swarm(self):
        orchestrator = SwarmsOrchestrator()
        result = orchestrator.start_mission("Foo", swarm_type="invalid")
        self.assertEqual(result["status"], "error")

if __name__ == "__main__":
    unittest.main()
