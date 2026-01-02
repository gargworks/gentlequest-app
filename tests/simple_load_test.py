import threading
import time
import uuid
import random
import requests
import sys

# Configuration
BASE_URL = "https://gentlequest.onrender.com"
NUM_USERS = 100
DURATION_SECONDS = 60
HATCH_RATE = 10  # Users per second

# Statistics
stats = {
    "requests": 0,
    "errors": 0,
    "latencies": []
}
lock = threading.Lock()

def user_behavior(user_id):
    session_id = f"load-test-{str(uuid.uuid4())[:8]}"
    headers = {
        "Content-Type": "application/json",
        "X-User-ID": user_id,
        "X-Session-ID": session_id
    }
    
    start_time = time.time()
    while time.time() - start_time < DURATION_SECONDS:
        try:
            # 1. Chat Interaction (Weight 3)
            if random.random() < 0.6:
                payload = {
                    "message": random.choice([
                        "I'm feeling anxious today",
                        "Can you help me breathe?",
                        "I had a bad dream",
                        "Just checking in",
                        "What can you do?"
                    ]),
                    "session_id": session_id
                }
                req_start = time.time()
                resp = requests.post(f"{BASE_URL}/api/chat", json=payload, headers=headers, timeout=10)
                latency = time.time() - req_start
                
                with lock:
                    stats["requests"] += 1
                    stats["latencies"].append(latency)
                    if resp.status_code >= 400:
                        stats["errors"] += 1
                        print(f"Error {resp.status_code}: {resp.text[:100]}")

            # 2. Health Check (Weight 1)
            elif random.random() < 0.8:
                req_start = time.time()
                resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
                # Don't track latency for health check effectively
                pass

            # 3. Assessment Questions (Weight 1)
            else:
                req_start = time.time()
                requests.get(f"{BASE_URL}/api/assessment/phq9/questions", timeout=5)

            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            with lock:
                stats["errors"] += 1
            # print(f"Exception: {e}")

def run_load_test():
    print(f"🚀 Starting Load Test: {NUM_USERS} users, {DURATION_SECONDS}s duration")
    threads = []
    
    for i in range(NUM_USERS):
        t = threading.Thread(target=user_behavior, args=(str(uuid.uuid4()),))
        threads.append(t)
        t.start()
        time.sleep(1/HATCH_RATE) # Ramp up
        if i % 10 == 0:
            print(f"Spawned {i} users...")

    print("All users spawned. Waiting for completion...")
    
    for t in threads:
        t.join()
        
    print("\n📊 Load Test Results:")
    print(f"Total Requests: {stats['requests']}")
    print(f"Total Errors: {stats['errors']}")
    if stats['latencies']:
        avg_latency = sum(stats['latencies']) / len(stats['latencies'])
        max_latency = max(stats['latencies'])
        print(f"Avg Latency: {avg_latency:.2f}s")
        print(f"Max Latency: {max_latency:.2f}s")
    
    if stats['errors'] > 0:
        print("❌ Test Failed (Errors Detected)")
        sys.exit(1)
    else:
        print("✅ Test Passed")

if __name__ == "__main__":
    run_load_test()
