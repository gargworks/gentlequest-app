"""Stress test the system with concurrent requests"""
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from statistics import mean, median

BASE_URL = "http://localhost:5055"

def send_request(session_id):
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Hello, how are you?"},
            headers={"X-Session-ID": session_id},
            timeout=10
        )
        duration = time.time() - start
        return {"success": response.status_code == 200, "duration": duration}
    except Exception as e:
        return {"success": False, "duration": time.time() - start, "error": str(e)}

def stress_test(num_users=100, requests_per_user=10):
    print(f"🔥 STRESS TEST")
    print("=" * 80)
    print(f"Users: {num_users}, Requests per user: {requests_per_user}")
    print(f"Total requests: {num_users * requests_per_user}")
    print()
    
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = []
        for user_id in range(num_users):
            session_id = f"stress_test_user_{user_id}"
            for _ in range(requests_per_user):
                futures.append(executor.submit(send_request, session_id))
        
        for future in futures:
            results.append(future.result())
    
    total_time = time.time() - start_time
    
    # Analysis
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    durations = [r["duration"] for r in successful]
    
    print(f"RESULTS:")
    print(f"  Total requests: {len(results)}")
    print(f"  Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"  Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Requests/second: {len(results)/total_time:.2f}")
    print()
    
    if durations:
        sorted_durations = sorted(durations)
        p50 = sorted_durations[len(sorted_durations)//2]
        p95 = sorted_durations[int(len(sorted_durations)*0.95)]
        p99 = sorted_durations[int(len(sorted_durations)*0.99)]
        
        print(f"RESPONSE TIMES:")
        print(f"  Average: {mean(durations):.2f}s")
        print(f"  Median (p50): {p50:.2f}s")
        print(f"  p95: {p95:.2f}s {'✅' if p95 < 3.0 else '⚠️'}")
        print(f"  p99: {p99:.2f}s")
        print(f"  Min: {min(durations):.2f}s")
        print(f"  Max: {max(durations):.2f}s")
    
    print()
    print("=" * 80)
    print(f"{'✅ PASS' if len(successful)/len(results) > 0.95 and (p95 < 3.0 if durations else False) else '⚠️  NEEDS OPTIMIZATION'}")

if __name__ == '__main__':
    import sys
    num_users = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    requests_per_user = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    stress_test(num_users, requests_per_user)
