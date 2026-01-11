
import json
import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

from mcp_server_nucleus.runtime.orchestrator import SwarmsOrchestrator

class TestExecutionSimulation(unittest.TestCase):
    def test_execution_squad_injection(self):
        """Test that Execution Swarm injection includes the Squad Context."""
        
        # Point to the actual Brain context
        brain_path = Path("/Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1")
        orchestrator = SwarmsOrchestrator(brain_path=brain_path)
        
        mission = "Build the Login Page"
        result = orchestrator.start_mission(mission, swarm_type="execution")
        
        context = result["kickoff_context"]
        
        print("\n--- Execution Kickoff Context ---")
        print(context[:1000] + "...") 
        
        # Verify Squad Members
        self.assertIn("--- SQUAD MEMBER: DEVELOPER ---", context)
        self.assertIn("--- SQUAD MEMBER: FIXER ---", context)
        
        # Verify Content
        self.assertIn("You are **The Developer**", context)
        # Fixer might match "You are **The Fixer**" or similar, checking partial
        self.assertIn("The Fixer", context) 

if __name__ == "__main__":
    unittest.main()
