
import os
import sys
import json
import time
import requests
import uuid

# Configuration
BASE_URL = "https://gentlequest.onrender.com/api"
HEADERS = {"Content-Type": "application/json"}

# Utility to print colored status
def print_step(step, msg):
    print(f"\n🔵 [STEP {step}] {msg}")

def print_result(msg, success=True):
    icon = "✅" if success else "❌"
    print(f"{icon} {msg}")

def run_simulation():
    print(f"🚀 Starting User Journey Simulation on {BASE_URL}")
    
    # 1. Start Session
    print_step(1, "User opens app (Start Session)")
    try:
        # Note: /get_or_create_session is GET in some versions, POST in others. 
        # Based on previous cURL, GET works.
        resp = requests.get(f"{BASE_URL}/get_or_create_session")
        if resp.status_code == 405: # Fallback if POST required
            resp = requests.post(f"{BASE_URL}/get_or_create_session", json={})
            
        if resp.status_code != 200:
            print_result(f"Failed to create session: {resp.text}", False)
            return
            
        session_data = resp.json()
        session_id = session_data.get("session_id")
        print_result(f"Session Active: {session_id}")
    except Exception as e:
        print_result(f"Session Error: {e}", False)
        return

    # 2. Chat - User expresses depression
    print_step(2, "User chats: 'I've been feeling really down lately, nothing interests me.'")
    try:
        chat_payload = {
            "session_id": session_id,
            "message": "I've been feeling really down lately, nothing interests me. I think I might be depressed."
        }
        start_time = time.time()
        resp = requests.post(f"{BASE_URL}/chat", json=chat_payload)
        latency = time.time() - start_time
        
        if resp.status_code == 200:
            chat_data = resp.json()
            reply = chat_data.get("reply", "")
            print_result(f"Luna Replied ({latency:.2f}s):\n   \"{reply[:100]}...\"")
            
            # Check if Luna suggested assessment (heuristic check)
            if "assessment" in reply.lower() or "phq-9" in reply.lower() or "check-in" in reply.lower():
                 print_result("Luna suggested an assessment/check-in")
        else:
            print_result(f"Chat failed: {resp.status_code}", False)
    except Exception as e:
        print_result(f"Chat Error: {e}", False)

    # 3. User takes PHQ-9 Assessment
    print_step(3, "User takes PHQ-9 Assessment (Simulation)")
    try:
        # Fetch questions first
        q_resp = requests.get(f"{BASE_URL}/assessment/phq9/questions")
        if q_resp.status_code == 200:
            print_result(f"User viewed {q_resp.json().get('total_questions')} PHQ-9 questions")
        
        # Submit responses (Simulating moderate depression)
        # 1-1-2-1-0-2-1-1-0
        assessment_payload = {
            "session_id": session_id,
            "responses": [1, 1, 2, 1, 0, 2, 1, 1, 0] 
        }
        resp = requests.post(f"{BASE_URL}/assessment/phq9", json=assessment_payload)
        
        if resp.status_code == 200:
            result = resp.json()
            print_result(f"Assessment Submitted: Score {result.get('total_score')} ({result.get('severity')})")
            print_result(f"Recommendations: {result.get('recommendations')[:2]}...")
        else:
            print_result(f"Assessment faulty: {resp.text}", False)
    except Exception as e:
        print_result(f"Assessment Error: {e}", False)

    # 4. Chat - User asks for help with anxiety
    print_step(4, "User chats: 'I also feel super anxious right now. Help.'")
    try:
        chat_payload = {
            "session_id": session_id,
            "message": "I also feel super anxious right now. My heart is racing. Can you help me relax?"
        }
        resp = requests.post(f"{BASE_URL}/chat", json=chat_payload)
        
        exercise_triggered = False
        intervention_id = "manual_test"
        
        if resp.status_code == 200:
            chat_data = resp.json()
            reply = chat_data.get("reply", "")
            print_result(f"Luna Replied:\n   \"{reply[:100]}...\"")
            
            # Check for exercise trigger in response metadata/content
            if chat_data.get("exercise"):
                 exercise = chat_data["exercise"]
                 print_result(f"Luna Triggered Exercise: {exercise.get('type')} - {exercise.get('name')}")
                 exercise_triggered = True
                 intervention_id = f"{exercise.get('type')}_{exercise.get('name')}"
            elif "breathe" in reply.lower():
                 print_result("Luna suggested breathing (text only)")
                 exercise_triggered = True # Assume user follows text
        else:
            print_result(f"Chat failed: {resp.status_code}", False)
    except Exception as e:
        print_result(f"Chat Error: {e}", False)

    # 5. User does Breathing Exercise
    print_step(5, "User completes Breathing Exercise")
    try:
        # reportExerciseOutcome / api/intervention/outcome
        outcome_payload = {
            "session_id": session_id,
            "exercise_type": "breathing",
            "outcome": "completed",
            "intervention_id": intervention_id,
            "time_spent_seconds": 45,
            "mood_before": 3,
            "mood_after": 6,
            "feedback": "Felt a bit better thanks"
        }
        resp = requests.post(f"{BASE_URL}/intervention/outcome", json=outcome_payload)
        
        if resp.status_code == 200:
             print_result("Exercise Completion Tracked Successfully")
        else:
             print_result(f"Tracking failed: {resp.text}", False)
    except Exception as e:
        print_result(f"Tracking Error: {e}", False)

    print("\n🚀 Simulation Complete!")

if __name__ == "__main__":
    run_simulation()
