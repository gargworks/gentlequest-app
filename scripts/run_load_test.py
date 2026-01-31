import concurrent.futures
import requests
import time
import statistics
import argparse
import uuid
import json
import random

# Configuration
BASE_URL = "https://app.gentlequest.app"
API_BASE = f"{BASE_URL}/api"

def get_session():
    """Get a new session ID consistently."""
    # In a real scenario, we might want unique sessions per simulated user
    # or reuse them. Let's create a new one for each simulated user run
    # to test session creation load, or reuse if provided.
    try:
        # Check if we can just generate one client-side or need server roundtrip
        # The backend accepts X-Session-ID.
        session_id = f"load_test_{uuid.uuid4().hex[:8]}"
        response = requests.get(f"{API_BASE}/get_or_create_session", headers={"X-Session-ID": session_id}, timeout=10)
        if response.status_code == 200:
            return session_id
        return None
    except Exception as e:
        print(f"Session Error: {e}")
        return None

def simulate_user_flow(user_id):
    """
    Simulates a typical user session:
    1. App Open (Resources, Quests, Profile)
    2. Daily Check-in (Mood Entry)
    3. History Check (Mood History)
    """
    session_id = get_session()
    if not session_id:
        return {"error": 1, "latencies": []}

    headers = {"X-Session-ID": session_id, "Content-Type": "application/json"}
    latencies = []
    errors = 0

    # 1. Dashboard Load (Parallel-ish in real app, sequential here)
    endpoints = [
        ("GET", "/quests"),
        ("GET", "/resources"),
        ("GET", "/user/profile"),
        ("GET", "/assessment/history")
    ]

    for method, endpoint in endpoints:
        start_time = time.time()
        try:
            if method == "GET":
                resp = requests.get(f"{API_BASE}{endpoint}", headers=headers, timeout=5)
            
            if resp.status_code != 200:
                print(f"❌ Error {endpoint}: Status {resp.status_code}")
                errors += 1
            else:
                latencies.append(time.time() - start_time)
        except Exception as e:
            print(f"❌ Exception {endpoint}: {e}")
            errors += 1

    # 2. Mood Entry (Write)
    try:
        start_time = time.time()
        mood_data = {
            "mood_level": random.randint(1, 5),  # App expects 1-5
            "note": "Load test auto-generated note."
        }
        resp = requests.post(f"{API_BASE}/mood_entry", headers=headers, json=mood_data, timeout=5)
        if resp.status_code == 200:
            latencies.append(time.time() - start_time)
        else:
            print(f"❌ Error Mood Entry: Status {resp.status_code}")
            errors += 1
    except Exception as e:
        print(f"❌ Exception Mood Entry: {e}")
        errors += 1

    # 3. Read Mood History (Read after Write)
    try:
        start_time = time.time()
        resp = requests.get(f"{API_BASE}/mood_history", headers=headers, timeout=5)
        if resp.status_code == 200:
            latencies.append(time.time() - start_time)
        else:
            print(f"❌ Error Mood History: Status {resp.status_code}")
            errors += 1
    except Exception as e:
        print(f"❌ Exception Mood History: {e}")
        errors += 1

    return {"error": errors, "latencies": latencies}

def run_load_test(num_users=10, max_workers=5):
    print(f"🚀 Starting Load Test via {BASE_URL}")
    print(f"👥 Users: {num_users} | 🧵 Workers: {max_workers}")
    
    start_global = time.time()
    all_latencies = []
    total_errors = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(simulate_user_flow, i) for i in range(num_users)]
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            total_errors += result['error']
            all_latencies.extend(result['latencies'])
            
    end_global = time.time()
    duration = end_global - start_global
    
    print("\n📊 Results:")
    print(f"Total Duration: {duration:.2f}s")
    print(f"Total Requests: {len(all_latencies) + total_errors}")
    print(f"Total Errors: {total_errors}")
    
    if all_latencies:
        avg_latency = statistics.mean(all_latencies)
        p95 = statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) >= 20 else max(all_latencies)
        print(f"Avg Latency: {avg_latency*1000:.2f}ms")
        print(f"P95 Latency: {p95*1000:.2f}ms")
        print(f"Requests/Sec: {len(all_latencies)/duration:.2f}")
    else:
        print("No successful requests.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GentleQuest Load Tester")
    parser.add_argument("--users", type=int, default=10, help="Number of simulated user sessions")
    parser.add_argument("--concurrency", type=int, default=5, help="Max concurrent threads")
    args = parser.parse_args()
    
    run_load_test(args.users, args.concurrency)
