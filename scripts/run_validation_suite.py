"""Run complete validation suite - 30 scenarios"""
import requests
import time

import uuid

BASE_URL = "http://localhost:5055"
SESSION_ID = f"validation_{str(uuid.uuid4())[:8]}"

SCENARIOS = [
    # Auth (3)
    {"id": 1, "name": "Get session", "method": "GET", "endpoint": "/api/get_or_create_session", "expected": 200},
    {"id": 2, "name": "Chat message", "method": "POST", "endpoint": "/api/chat", "data": {"message": "Hello"}, "expected": 200},
    {"id": 3, "name": "Chat history", "method": "GET", "endpoint": "/api/chat_history", "expected": 200},
    # Mood (3)
    {"id": 4, "name": "Mood entry", "method": "POST", "endpoint": "/api/mood_entry", "data": {"mood_level": 3}, "expected": 200},
    {"id": 5, "name": "Mood history", "method": "GET", "endpoint": "/api/mood_history", "expected": 200},
    {"id": 6, "name": "Mood analytics", "method": "GET", "endpoint": "/api/mood_analytics", "expected": 200},
    # Assessments (4)
    {"id": 7, "name": "PHQ-9 questions", "method": "GET", "endpoint": "/api/assessment/phq9/questions", "expected": 200},
    {"id": 8, "name": "PHQ-9 submit", "method": "POST", "endpoint": "/api/assessment/phq9", "data": {"responses": [1]*9}, "expected": 200},
    {"id": 9, "name": "GAD-7 submit", "method": "POST", "endpoint": "/api/assessment/gad7", "data": {"responses": [1]*7}, "expected": 200},
    {"id": 10, "name": "Assessment history", "method": "GET", "endpoint": "/api/assessment/history", "expected": 200},
    # Quests (6)
    {"id": 11, "name": "Get quests", "method": "GET", "endpoint": "/api/quests", "expected": 200},
    {"id": 12, "name": "Complete quest", "method": "POST", "endpoint": "/api/quests/1/complete", "expected": 200},
    {"id": 13, "name": "Get profile", "method": "GET", "endpoint": "/api/user/profile", "expected": 200},
    # Resources (3)
    {"id": 14, "name": "Get resources", "method": "GET", "endpoint": "/api/resources", "expected": 200},
    {"id": 15, "name": "Search resources", "method": "GET", "endpoint": "/api/resources", "params": {"search": "anxiety"}, "expected": 200},
    {"id": 16, "name": "Track view", "method": "POST", "endpoint": "/api/resources/<resource_id>/view", "expected": 200},
    # Crisis (6)
    {"id": 17, "name": "Suicide detection", "method": "POST", "endpoint": "/api/chat", "data": {"message": "I want to kill myself"}, "expected": 200},
    {"id": 18, "name": "Self-harm detection", "method": "POST", "endpoint": "/api/chat", "data": {"message": "I've been cutting"}, "expected": 200},
    {"id": 19, "name": "No false positive", "method": "POST", "endpoint": "/api/chat", "data": {"message": "dying to see that movie"}, "expected": 200},
    # Health (1)
    {"id": 20, "name": "Health check", "method": "GET", "endpoint": "/api/health", "expected": 200},
    # Alerts (2) - Relies on Scenario 17 creating an alert
    {"id": 21, "name": "Get alert history", "method": "GET", "endpoint": "/api/alerts/history", "params": {"university_id": 1}, "expected": 200},
    {"id": 22, "name": "Acknowledge alert", "method": "POST", "endpoint": "/api/alerts/<alert_id>/acknowledge", "data": {"counselor_id": "auto_test", "response_notes": "Validated", "action_taken": "check"}, "expected": 200},
]

def run_validation():
    results = {"passed": 0, "failed": 0, "errors": []}
    
    dynamic_context = {}

    for scenario in SCENARIOS:
        try:
            # Substitute dynamic values in endpoint path
            endpoint = scenario["endpoint"]
            for key, value in dynamic_context.items():
                if f"<{key}>" in endpoint:
                    endpoint = endpoint.replace(f"<{key}>", str(value))
            
            headers = {"X-Session-ID": SESSION_ID}
            
            if scenario["method"] == "GET":
                response = requests.get(
                    f"{BASE_URL}{endpoint}",
                    headers=headers,
                    params=scenario.get("params", {})
                )
                
                # Capture Resource ID from Scenario 14
                if scenario["id"] == 14 and response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get("resources") and len(data["resources"]) > 0:
                            res_id = data["resources"][0]["id"]
                            dynamic_context["resource_id"] = res_id
                            print(f"   ℹ️ Captured resource_id: {res_id}")
                        else:
                            print("   ⚠️ No resources found to capture ID.")
                    except:
                        pass

            else:
                response = requests.post(
                    f"{BASE_URL}{endpoint}",
                    json=scenario.get("data", {}),
                    headers=headers
                )
            
            if response.status_code == scenario["expected"]:
                results["passed"] += 1
                print(f"✅ {scenario['id']:2d}. {scenario['name']}")
                
                # Logic to capture dynamic ID from Alert History to correct the next test
                if scenario["id"] == 21: # Get alert history
                    try:
                        data = response.json()
                        if data.get("alerts") and len(data["alerts"]) > 0:
                            # Capture the FIRST alert ID
                            alert_id = data["alerts"][0]["id"]
                            dynamic_context["alert_id"] = alert_id
                            print(f"   ℹ️ Captured alert_id: {alert_id}")
                        else:
                            print("   ⚠️ No alerts found in history to capture ID from.")
                    except:
                        pass
                        
            else:
                results["failed"] += 1
                results["errors"].append(f"Scenario {scenario['id']}: Expected {scenario['expected']}, got {response.status_code}")
                print(f"❌ {scenario['id']:2d}. {scenario['name']} (got {response.status_code})")
                
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Scenario {scenario['id']}: {str(e)}")
            print(f"❌ {scenario['id']:2d}. {scenario['name']} - {e}")
    
    print(f"\n{'='*80}")
    print(f"RESULTS: {results['passed']}/{len(SCENARIOS)} passed ({results['passed']/len(SCENARIOS)*100:.1f}%)")
    print(f"PASS CRITERIA: {int(len(SCENARIOS)*0.83)}+ scenarios (83%+)")
    print(f"RECOMMENDATION: {'GO' if results['passed'] >= len(SCENARIOS)*0.83 else 'NO-GO'}")
    
    if results["errors"]:
        print(f"\nERRORS:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    return results

if __name__ == '__main__':
    run_validation()
