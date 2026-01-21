import requests
import json
import time

BASE_URL = "http://localhost:5055"
SESSION_ID = f"test-variety-{int(time.time())}"

def send_chat(message):
    print(f"\nUser: {message}")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        headers={"X-Session-ID": SESSION_ID},
        json={"message": message}
    )
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    ai_response = data.get("response", "")
    interactive = data.get("interactive", False)
    exercise_type = data.get("exercise_type", "none")
    
    print(f"Luna: {ai_response[:100]}...")
    print(f"Interactive: {interactive} | Type: {exercise_type}")
    return data

def run_test():
    print(f"Starting variety test for session: {SESSION_ID}")
    
    # 1. First anxiety message -> Breathing
    # Use "nervous" to avoid strict "anxiety" trigger if it's sensitive
    send_chat("I'm feeling a bit nervous about school")
    
    # Report completed for turn 1
    print("\n[Reporting Completed for turn 1]")
    requests.post(
        f"{BASE_URL}/api/intervention/outcome",
        headers={"X-Session-ID": SESSION_ID},
        json={"intervention_id": "calm_478", "outcome": "completed"}
    )
    
    # 2. Second anxiety message -> Grounding
    send_chat("I'm still so stressed")
    
    # 3. Third anxiety message -> Journaling
    send_chat("I'm really overwhelmed now")
    
    # 4. Fourth anxiety message -> Talk mode
    send_chat("I just want to talk")

if __name__ == "__main__":
    run_test()
