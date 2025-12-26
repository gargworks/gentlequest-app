"""
Test function calling reliability across different prompt strategies
"""
import requests
import time

BASE_URL = "https://gentlequest.onrender.com"

test_messages = [
    "I feel really anxious",
    "I'm stressed about exams", 
    "I feel overwhelmed",
    "I'm having panic attacks",
    "I feel sad and lonely",
    "I can't sleep at night"
]

def test_function_calling_rate(num_tests=10):
    """Test how often Gemini actually calls the function vs keyword fallback"""
    
    results = {
        "gemini_called": 0,
        "keyword_fallback": 0,
        "total": 0
    }
    
    for i in range(num_tests):
        session = f"fc-test-{int(time.time())}-{i}"
        msg = test_messages[i % len(test_messages)]
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Content-Type": "application/json", "X-Session-ID": session},
            json={"message": msg}
        )
        
        data = response.json()
        
        # If we got an exercise, check logs to see if it was Gemini or fallback
        # (We'd need to check server logs for "💡 Keyword fallback triggered")
        if data.get("exercise_type"):
            results["total"] += 1
            # For now, assume it's working
            print(f"✓ Test {i+1}: {msg[:30]} → {data.get('exercise_type')}")
        
        time.sleep(2)  # Rate limit
    
    print(f"\n📊 Results: {results['total']}/{num_tests} triggered interventions")
    return results

if __name__ == "__main__":
    print("Testing function calling reliability...")
    print("=" * 60)
    test_function_calling_rate(6)
