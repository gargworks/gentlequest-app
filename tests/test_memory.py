
import os
import shutil
import unittest
from pathlib import Path
from mcp_server_nucleus.runtime.memory import _search_memory, _read_memory

# Mock environment
BRAIN_PATH = Path(".brain_test")
MEMORY_DIR = BRAIN_PATH / "memory"

class TestMemory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if BRAIN_PATH.exists():
            shutil.rmtree(BRAIN_PATH)
        MEMORY_DIR.mkdir(parents=True)
        os.environ["NUCLEAR_BRAIN_PATH"] = str(BRAIN_PATH)
        
        # Create dummy content
        (MEMORY_DIR / "context.md").write_text("# Context\nProject: Nucleus\nVision: Autonomous AI")
        (MEMORY_DIR / "patterns.md").write_text("# Patterns\n- Use Factory Pattern\n- Avoid Global State")

    @classmethod
    def tearDownClass(cls):
        if BRAIN_PATH.exists():
            shutil.rmtree(BRAIN_PATH)

    def test_search_memory(self):
        # Test valid search
        result = _search_memory("Nucleus")
        self.assertIn("count", result)
        self.assertGreater(result["count"], 0)
        self.assertIn("Nucleus", result["results"][0])

        # Test no match
        result = _search_memory("Banana")
        self.assertEqual(result["count"], 0)

    def test_read_memory(self):
        # Test valid read
        result = _read_memory("context")
        self.assertIn("content", result)
        self.assertIn("Vision: Autonomous AI", result["content"])

        # Test invalid category
        result = _read_memory("invalid_category")
        self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main()
