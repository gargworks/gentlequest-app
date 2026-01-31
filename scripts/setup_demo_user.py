
import requests
import sys
import uuid
import datetime

# Config
BASE_URL = "https://app.gentlequest.app/api"
DEMO_SESSION_ID = "caps_demo_user_2026"

def setup_demo_user():
    """
    Sets up a pristine demo user state.
    1. Clear existing session data (if possible/needed, or just use unique ID).
    2. Seed initial 'history' to show graphs (Mood).
    3. Ensure clean chat state.
    """
    print(f"🎤 Setting up Demo User: {DEMO_SESSION_ID}")
    
    headers = {"X-Session-ID": DEMO_SESSION_ID, "Content-Type": "application/json"}
    
    # 1. Ping to warm up
    try:
        requests.get(f"{BASE_URL}/ping", timeout=5)
        print("✅ Backend Online")
    except Exception:
        print("❌ Backend Offline. Deploy first.")
        sys.exit(1)

    # 2. Seed Mood History (Past 5 days)
    # This creates a "story" of improving mood for the charts
    print("🌱 Seeding Mood History...")
    past_moods = [
        {"days_ago": 4, "level": 2, "note": "Feeling overwhelmed with finals."},
        {"days_ago": 3, "level": 3, "note": "Talked to a friend, fell better."},
        {"days_ago": 2, "level": 2, "note": "Stress coming back."},
        {"days_ago": 1, "level": 4, "note": "Used breathing exercise, helped."},
        {"days_ago": 0, "level": 4, "note": "Ready for the demo."} # Today
    ]
    
    for m in past_moods:
        # Note: In a real app we might not be able to backdate easily via public API
        # unless the API supports it or we use a backdoor.
        # Check app.py: timestamp is accepted!
        ts = (datetime.datetime.utcnow() - datetime.timedelta(days=m["days_ago"])).isoformat()
        payload = {
            "mood_level": m["level"],
            "note": m["note"],
            "timestamp": ts
        }
        res = requests.post(f"{BASE_URL}/mood_entry", json=payload, headers=headers)
        if res.status_code == 200:
            print(f"  - Entry {m['days_ago']} days ago: OK")
        else:
            print(f"  - Entry {m['days_ago']} days ago: FAIL ({res.status_code})")

    # 3. Clear Chat History? 
    # The API doesn't usually allow clearing via public endpoint.
    # We rely on the session_id being unique or 'clean'.
    # If we reuse 'caps_demo_user_2026', it will accumulate.
    # Recommendation: Use a fresh suffix if cleaning is impossible.
    # For now, we assume this ID is reserved for this demo.
    
    print("\n✅ Demo User Setup Complete!")
    print(f"🔑 Session ID: {DEMO_SESSION_ID}")
    print("👉 Use this ID in your browser/client configuration.")

if __name__ == "__main__":
    setup_demo_user()
