
import os
import shutil
import unittest
from pathlib import Path
from mcp_server_nucleus.runtime.strategy import _manage_strategy, _update_roadmap

# Mock environment
BRAIN_PATH = Path(".brain_test_strat")

class TestStrategy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if BRAIN_PATH.exists():
            shutil.rmtree(BRAIN_PATH)
        BRAIN_PATH.mkdir(parents=True)
        os.environ["NUCLEAR_BRAIN_PATH"] = str(BRAIN_PATH)

    @classmethod
    def tearDownClass(cls):
        if BRAIN_PATH.exists():
            shutil.rmtree(BRAIN_PATH)

    def test_manage_strategy(self):
        # Test update
        result = _manage_strategy("update", "# Our Strategy\nWin.")
        self.assertIn("success", result.get("status", ""))
        
        # Test read
        result = _manage_strategy("read")
        self.assertIn("Win.", result["content"])
        
        # Test append
        _manage_strategy("append", "And profit.")
        result = _manage_strategy("read")
        self.assertIn("And profit.", result["content"])

    def test_update_roadmap(self):
        # Test add
        result = _update_roadmap("add", "Phase X")
        self.assertIn("success", result.get("status", ""))
        
        # Test read
        result = _update_roadmap("read")
        self.assertIn("Phase X", result["content"])

if __name__ == "__main__":
    unittest.main()
