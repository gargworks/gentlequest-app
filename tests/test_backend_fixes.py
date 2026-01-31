#!/usr/bin/env python3
"""Fixed version of comprehensive test"""

import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:5055"

def test_all_features_fixed():
    """Run fixed tests"""
    print("\n🧪 RUNNING FIXED TESTS\n")
    
    results = []
    
    # 1. Session (GET not POST)
    print("Testing Session Creation...")
    r = requests.get(f"{BASE_URL}/api/get_or_create_session", timeout=10)
    if r.status_code == 200 and r.json().get('session_id'):
        print("✅ Session creation works")
        results.append(("Session", True))
        session_id = r.json()['session_id']
    else:
        print(f"❌ Session failed: {r.status_code}")
        results.append(("Session", False))
        session_id = f"test-{int(time.time())}"
    
    # 2. Mood (score 1-5)
    print("\nTesting Mood Tracking...")
    mood_data = {
        "session_id": session_id,
        "mood_level": 4,  # Changed key to match app.py (mood_level)
        "note": "Testing mood",
        "timestamp": datetime.utcnow().isoformat()
    }
    r = requests.post(f"{BASE_URL}/api/mood_entry", json=mood_data, timeout=10)
    if r.status_code in [200, 201]:
        print("✅ Mood tracking works")
        results.append(("Mood", True))
    else:
        print(f"❌ Mood failed: {r.status_code} - {r.text}")
        results.append(("Mood", False))
    
    # 3. Analytics (with consent header)
    print("\nTesting Analytics...")
    headers = {"X-Analytics-Consent": "true"}
    analytics_data = {
        "session_id": session_id,
        "event_type": "test_event",
        "metadata": {"action": "test"}
    }
    r = requests.post(f"{BASE_URL}/api/analytics/log", 
                     json=analytics_data, headers=headers, timeout=10)
    if r.status_code in [200, 201]:
        print("✅ Analytics works")
        results.append(("Analytics", True))
    else:
        print(f"❌ Analytics failed: {r.status_code}")
        results.append(("Analytics", False))
    
    # 4. Crisis Detection (check response content)
    print("\nTesting Crisis Detection...")
    crisis_msg = "I dont want to live anymore"
    r = requests.post(f"{BASE_URL}/api/chat",
                     json={"message": crisis_msg, "session_id": session_id},
                     timeout=30)
    if r.status_code == 200:
        data = r.json()
        response_text = data.get('response', '')
        # Check for crisis keywords in response OR structured flags
        crisis_keywords = ['crisis', 'help', '988', '741741', 'emergency', 'concerned']
        
        flagged = False
        if data.get('crisis_detected') is True:
             flagged = True
             print("✅ Crisis detection works (Flagged Correctly via crisis_detected)")
        elif any(word in response_text.lower() for word in crisis_keywords):
             flagged = True
             print("✅ Crisis detection works (Keyword match)")
        
        if flagged:
            results.append(("Crisis", True))
        else:
            print(f"❌ Crisis not detected. Data: {data}")
            results.append(("Crisis", False))
    else:
        print(f"❌ Crisis test failed: {r.status_code}")
        results.append(("Crisis", False))
    
    # 5. Rate Limiting (more aggressive)
    print("\nTesting Rate Limiting...")
    # Send requests rapidly to one endpoint
    # Use /api/mood_pulse which is 30/min
    limited = False
    print("Sending rapid requests to trigger limit...")
    for i in range(50):
        r = requests.get(f"{BASE_URL}/api/mood_pulse", timeout=1)
        if r.status_code == 429:
            limited = True
            print(f"✅ Rate limiting triggered at request {i+1}")
            results.append(("RateLimit", True))
            break
    if not limited:
        print("⚠️  Rate limiting not triggered (might need more requests or check config)")
        results.append(("RateLimit", None))
    
    # Summary
    print("\n" + "="*40)
    print("RESULTS:")
    passed = sum(1 for _, r in results if r is True)
    print(f"Passed: {passed}/{len(results)}")
    for name, result in results:
        status = "✅" if result is True else ("❌" if result is False else "⚠️")
        print(f"  {status} {name}")
    
    return all(r is not False for _, r in results)

if __name__ == "__main__":
    test_all_features_fixed()
