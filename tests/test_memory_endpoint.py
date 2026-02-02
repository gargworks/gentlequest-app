
import unittest
import requests
import os
import sys

# Ensure we can import modules if needed, though we are mostly testing the running server
sys.path.append(os.path.join(os.getcwd(), "tools/marketing-dashboard"))

API_URL = "http://localhost:9999/api/memory"

@unittest.skipIf(os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI"), "requires local server")
class TestMemoryEndpoint(unittest.TestCase):
    def test_memory_endpoint_structure(self):
        """Test that /api/memory returns a list of memory nodes with correct fields."""
        try:
            response = requests.get(API_URL)
        except requests.exceptions.ConnectionError:
            self.fail("Could not connect to server. Is it running on port 9999?")

        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list, "Response should be a list")
        
        if len(data) > 0:
            node = data[0]
            self.assertIn("id", node)
            self.assertIn("path", node)
            self.assertIn("type", node)
            self.assertIn("size", node)
            self.assertIn("last_modified", node)
            
            # Verify types
            self.assertIn(node["type"], ["strategy", "agent", "data", "memory", "other", "agent"])
            
            print(f"✅ Verified {len(data)} memory nodes.")
            print(f"   Sample: {node['path']} ({node['type']})")
        else:
            print("⚠️ No memory nodes found. Is .brain directory empty?")

if __name__ == '__main__':
    unittest.main()
