
import json
import os
import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

from mcp_server_nucleus.runtime.capabilities.brain_ops import BrainOps

@unittest.skipIf(os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI"), "requires local brain fixture")
class TestSwarmPersistence(unittest.TestCase):
    def test_persistence_flow(self):
        """Test that Swarms stick around."""
        
        # 1. Setup Environment
        uuid_brain = "/Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1"
        os.environ["NUCLEUS_BRAIN_PATH"] = uuid_brain
        
        state_file = Path(uuid_brain) / "swarms" / "state.json"
        
        # Clean up before test
        if state_file.exists():
            print(f"Backing up existing state to {state_file}.bak")
            state_file.rename(str(state_file) + ".bak")
            
        ops = BrainOps()
        
        # 2. Trigger Swarm
        args = {
            "mission": "Persistence Test Mission",
            "swarm_type": "genesis"
        }
        print("Starting Swarm...")
        result = ops.execute_tool("brain_orchestrate_swarm", args)
        self.assertIn("✅ Swarm Initiated", result)
        
        # 3. Check Persistence (File)
        print("Checking File...")
        self.assertTrue(state_file.exists(), "State file should exist")
        
        state = json.loads(state_file.read_text())
        self.assertTrue(len(state) > 0, "State should not be empty")
        
        mission_id = list(state.keys())[0]
        mission_data = state[mission_id]
        
        self.assertEqual(mission_data["mission"], "Persistence Test Mission")
        self.assertEqual(mission_data["lead"], "architect")
        
        print("✅ Persistence Verified.")
        
        # 4. Cleanup
        if Path(str(state_file) + ".bak").exists():
            state_file.unlink() # Remove test file
            Path(str(state_file) + ".bak").rename(state_file) # Restore backup

if __name__ == "__main__":
    unittest.main()
