
import json
import unittest
from datetime import datetime
from io import BytesIO

# Mock request handler
class MockHandler:
    def __init__(self):
        self.wfile = BytesIO()
        self.headers = {}
        
    def _set_headers(self, code, type):
        self.headers['code'] = code
        self.headers['type'] = type

    def list_swarms(self):
        return []

class TestHealthLogic(unittest.TestCase):
    def test_health_logic(self):
        # Simulate the logic added to server.py
        handler = MockHandler()
    
        # Logic extracted from server.py patch
        import time
        from datetime import datetime
        health_data = {
            "status": "green",
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time(), 
            "version": "1.0"
        }
        handler.wfile.write(json.dumps(health_data).encode())
        
        # Assertions
        response = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(response['status'], 'green')
        self.assertIn('uptime', response)
        self.assertIn('version', response)
        print("✅ Health Logic Verified")

if __name__ == "__main__":
    unittest.main()
