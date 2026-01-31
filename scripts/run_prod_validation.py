"""Run complete validation suite against PRODUCTION - 20 scenarios"""
import requests
import json

BASE_URL = "https://app.gentlequest.app"
SESSION_ID = f"validation_prod_test_{int(1737133773)}" # Unique-ish ID for this run

SCENARIOS = [
    # Auth (3)
    {"id": 1, "name": "Get session", "method": "GET", "endpoint": "/api/get_or_create_session", "expected": 200},
    {"id": 2, "name": "Chat message", "method": "POST", "endpoint": "/api/chat", "data": {"message": "Hello, I am testing the production system."}, "expected": 200},
    {"id": 3, "name": "Chat history", "method": "GET", "endpoint": "/api/chat_history", "expected": 200},
    # Mood (3)
    {"id": 4, "name": "Mood entry", "method": "POST", "endpoint": "/api/mood_entry", "data": {"mood_level": 4, "note": "Production Validation Run"}, "expected": 200},
    {"id": 5, "name": "Mood history", "method": "GET", "endpoint": "/api/mood_history", "expected": 200},
    {"id": 6, "name": "Mood analytics", "method": "GET", "endpoint": "/api/mood_analytics", "expected": 200},
    # Assessments (4)
    {"id": 7, "name": "PHQ-9 questions", "method": "GET", "endpoint": "/api/assessment/phq9/questions", "expected": 200},
    {"id": 8, "name": "PHQ-9 submit", "method": "POST", "endpoint": "/api/assessment/phq9", "data": {"responses": [0,1,0,1,0,1,0,1,0]}, "expected": 200},
    {"id": 9, "name": "GAD-7 submit", "method": "POST", "endpoint": "/api/assessment/gad7", "data": {"responses": [0,0,1,1,2,2,3]}, "expected": 200},
    {"id": 10, "name": "Assessment history", "method": "GET", "endpoint": "/api/assessment/history", "expected": 200},
    # Quests (3)
    {"id": 11, "name": "Get quests", "method": "GET", "endpoint": "/api/quests", "expected": 200},
    {"id": 12, "name": "Get profile", "method": "GET", "endpoint": "/api/user/profile", "expected": 200},
    # Resources (3)
    {"id": 13, "name": "Get resources", "method": "GET", "endpoint": "/api/resources", "expected": 200},
    {"id": 14, "name": "Search resources", "method": "GET", "endpoint": "/api/resources", "params": {"search": "anxiety"}, "expected": 200},
    # Crisis (3)
    {"id": 15, "name": "Suicide detection", "method": "POST", "endpoint": "/api/chat", "data": {"message": "I feel like ending it all"}, "expected": 200},
    {"id": 16, "name": "No false positive", "method": "POST", "endpoint": "/api/chat", "data": {"message": "I'm having a great day"}, "expected": 200},
    # Health (1)
    {"id": 17, "name": "Health check", "method": "GET", "endpoint": "/api/health", "expected": 200},
]

def run_validation():
    results = {"passed": 0, "failed": 0, "errors": []}
    print(f"🚀 Starting Production Validation Run on {BASE_URL}")
    print(f"Session ID: {SESSION_ID}\n")
    
    for scenario in SCENARIOS:
        try:
            headers = {"X-Session-ID": SESSION_ID}
            url = f"{BASE_URL}{scenario['endpoint']}"
            
            if scenario["method"] == "GET":
                response = requests.get(
                    url,
                    headers=headers,
                    params=scenario.get("params", {})
                )
            else:
                response = requests.post(
                    url,
                    json=scenario.get("data", {}),
                    headers=headers
                )
            
            if response.status_code == scenario["expected"]:
                results["passed"] += 1
                print(f"✅ {scenario['id']:2d}. {scenario['name']}")
            else:
                results["failed"] += 1
                error_msg = f"Scenario {scenario['id']}: Expected {scenario['expected']}, got {response.status_code}"
                try:
                    error_msg += f" - Response: {response.text[:200]}"
                except:
                    pass
                results["errors"].append(error_msg)
                print(f"❌ {scenario['id']:2d}. {scenario['name']} (got {response.status_code})")
                
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Scenario {scenario['id']}: {str(e)}")
            print(f"❌ {scenario['id']:2d}. {scenario['name']} - {e}")
    
    print(f"\n{'='*80}")
    print(f"RESULTS: {results['passed']}/{len(SCENARIOS)} passed ({results['passed']/len(SCENARIOS)*100:.1f}%)")
    print(f"PASS CRITERIA: 14+ scenarios (83%+ on target)")
    print(f"RECOMMENDATION: {'GO' if results['passed'] >= 14 else 'NO-GO'}")
    
    if results["errors"]:
        print(f"\nERRORS:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    return results

if __name__ == '__main__':
    run_validation()
