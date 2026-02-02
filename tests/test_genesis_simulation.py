
import os
import sys
import unittest
from pathlib import Path

# Add src to path (repo-relative)
sys.path.append(str(Path(__file__).resolve().parents[1] / "mcp-server-nucleus" / "src"))

from mcp_server_nucleus.runtime.orchestrator import SwarmsOrchestrator

@unittest.skipIf(os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI"), "requires local brain fixture")
class TestGenesisSimulation(unittest.TestCase):
    def test_squad_injection(self):
        """Test that Genesis Swarm injection includes the Squad Context."""
        
        # Point to the actual Brain context
        brain_path = Path("/Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1")
        orchestrator = SwarmsOrchestrator(brain_path=brain_path)
        
        mission = "Build a Time Machine"
        result = orchestrator.start_mission(mission, swarm_type="genesis")
        
        context = result["kickoff_context"]
        
        print("\n--- Genesis Kickoff Context ---")
        print(context[:1000] + "...") # Print first 1000 chars
        
        # Verify Squad Members are present
        self.assertIn("--- SQUAD MEMBER: PRODUCT_OWNER ---", context)
        self.assertIn("--- SQUAD MEMBER: STRATEGIST ---", context)
        # Verify content from personas
        self.assertIn("You are **The Product Owner**", context)
        self.assertIn("You are **The Strategist**", context)

if __name__ == "__main__":
    unittest.main()
