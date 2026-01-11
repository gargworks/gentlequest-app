
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

from mcp_server_nucleus.runtime.loops.fixer import FixerLoop

class TestFixerLoop(unittest.TestCase):
    def setUp(self):
        self.test_file = Path("test_artifact.txt")
        self.test_file.write_text("FAIL")

    def tearDown(self):
        if self.test_file.exists():
            self.test_file.unlink()

    def test_loop_success(self):
        """Test that loop retries and succeeds when fix works."""
        
        # Mock verification: Fail first, then Pass
        # We use a command that checks for "PASS" in the file
        verify_cmd = f"grep 'PASS' {self.test_file.name}"
        
        # Mock Fixer: replaces FAIL with PASS
        def mock_fixer(path, context):
            Path(path).write_text("PASS")
            return json.dumps({"status": "success", "message": "Fixed"})

        loop = FixerLoop(
            target_file=str(self.test_file),
            verification_command=verify_cmd,
            fixer_func=mock_fixer,
            max_retries=3
        )

        result = loop.run()
        
        self.assertEqual(result["status"], "success")
        self.assertIn("Fixed in 1 attempts", result["message"])
        self.assertEqual(self.test_file.read_text(), "PASS")

    def test_loop_failure(self):
        """Test that loop gives up after max retries."""
        
        verify_cmd = f"grep 'PASS' {self.test_file.name}"
        
        # Mock Fixer: Does nothing active (or fails to fix)
        def mock_fixer(path, context):
            return json.dumps({"status": "success", "message": "Tried to fix"})

        loop = FixerLoop(
            target_file=str(self.test_file),
            verification_command=verify_cmd,
            fixer_func=mock_fixer,
            max_retries=2
        )

        result = loop.run()
        
        self.assertEqual(result["status"], "failure")
        self.assertIn("Failed to fix after 2 attempts", result["message"])

if __name__ == "__main__":
    unittest.main()
