
import unittest
import requests
import os
import json

# PRE-CONFIGURED URLS (From previous tool outputs)
BACKEND_URL = "https://gentlequest-backend-7an2ps6yna-uc.a.run.app"
HUD_URL_PREDICTED = "https://nucleus-hud-7an2ps6yna-uc.a.run.app" 
# Note: Cloud Run URLs are usually predictable [SERVICE_NAME]-[HASH]-[REGION].a.run.app
# The hash '7an2ps6yna' seems stable for the project/region combo.

@unittest.skipIf(os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI"), "requires live deployment")
class TestNucleusDeployment(unittest.TestCase):
    
    def test_backend_health(self):
        """Verify the Backend serves API endpoints"""
        print(f"Checking Backend: {BACKEND_URL}/api/tasks?format=json")
        try:
            resp = requests.get(f"{BACKEND_URL}/api/tasks?format=json", timeout=10)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            if "tasks" not in data:
                print(f"❌ UNEXPECTED RESPONSE: {json.dumps(data, indent=2)}")
            self.assertTrue("tasks" in data, "Backend response missing 'tasks' key")
            print("✅ Backend API is reachable and returning JSON tasks.")
        except Exception as e:
            self.fail(f"Backend Health Check Failed: {e}")

    def test_hud_availability(self):
        """Verify the HUD Frontend is served"""
        print(f"Checking HUD: {HUD_URL_PREDICTED}")
        try:
            resp = requests.get(HUD_URL_PREDICTED, timeout=10)
            self.assertEqual(resp.status_code, 200)
            self.assertTrue("<!DOCTYPE html>" in resp.text, "HUD response is not HTML")
            print("✅ HUD Frontend is reachable.")
            
            # Optional: Check if the config is active
            # Since Next.js inlines vars, we might see the URL string in the minified JS or HTML
            # This is hard to robustly regex, but we can check basic connectivity.
        except Exception as e:
            self.fail(f"HUD Availability Check Failed: {e}")

if __name__ == "__main__":
    unittest.main()
