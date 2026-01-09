import requests
import uuid
import json

BASE_URL = "http://localhost:5055"
SESSION_ID = str(uuid.uuid4())

def print_result(name, passed, detail=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name} {detail}")

def verify_assessments():
    print(f"🔍 Starting Device Verification (Simulated) for Session: {SESSION_ID}")
    
    headers = {"Content-Type": "application/json", "X-Session-ID": SESSION_ID}

    # 1. Get PHQ-9 Questions
    print("\n--- Testing PHQ-9 Questions ---")
    try:
        resp = requests.get(f"{BASE_URL}/api/assessment/phq9/questions", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if "questions" in data and len(data["questions"]) == 9:
                print_result("Get PHQ-9 Questions", True, f"(Found {len(data['questions'])} questions)")
            else:
                print_result("Get PHQ-9 Questions", False, "Invalid response structure")
        else:
            print_result("Get PHQ-9 Questions", False, f"Status: {resp.status_code}")
    except Exception as e:
        print_result("Get PHQ-9 Questions", False, str(e))

    # 2. Submit PHQ-9 (Moderate Depression Scenario)
    print("\n--- Testing PHQ-9 Submission ---")
    phq9_responses = [2, 1, 1, 2, 0, 0, 1, 3, 0] # Random but specific answers
    try:
        payload = {
            "session_id": SESSION_ID,
            "responses": phq9_responses
        }
        resp = requests.post(f"{BASE_URL}/api/assessment/phq9", 
                           headers=headers,
                           data=json.dumps(payload))
        
        if resp.status_code == 200:
            data = resp.json()
            # Expecting severity and recommendations
            if "severity" in data and "recommendations" in data:
                print_result("Submit PHQ-9", True, f"Severity: {data['severity']}, Recommendations: {len(data['recommendations'])}")
            else:
                print_result("Submit PHQ-9", False, f"Missing fields. Got: {data.keys()}")
        else:
            print_result("Submit PHQ-9", False, f"Status: {resp.status_code}, Body: {resp.text}")
    except Exception as e:
        print_result("Submit PHQ-9", False, str(e))

    # 3. Get History
    print("\n--- Testing Assessment History ---")
    try:
        resp = requests.get(f"{BASE_URL}/api/assessment/history", params={"session_id": SESSION_ID}, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            assessments = data.get("history", [])
            if len(assessments) >= 1:
                print_result("Get History", True, f"Found {len(assessments)} past assessments")
            else:
                print_result("Get History", False, "History empty (expected at least 1)")
        else:
            print_result("Get History", False, f"Status: {resp.status_code}")
    except Exception as e:
        print_result("Get History", False, str(e))

if __name__ == "__main__":
    verify_assessments()
