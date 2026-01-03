
import sys
import time
import requests
import concurrent.futures
from statistics import mean, median

# Configuration
TARGET_URL = "https://gentlequest.onrender.com/api/brain/status"
WORKER_COUNT = 10
REQUESTS_PER_WORKER = 5
TOTAL_REQUESTS = WORKER_COUNT * REQUESTS_PER_WORKER

def make_request(request_id):
    start_time = time.time()
    try:
        response = requests.get(TARGET_URL, timeout=10)
        status_code = response.status_code
        # For /api/brain/status, we expect 200
        success = (status_code == 200)
    except Exception as e:
        status_code = 0
        success = False
        print(f"Request {request_id} failed: {e}")
    
    latency = time.time() - start_time
    return {
        "id": request_id,
        "status": status_code,
        "latency": latency,
        "success": success
    }

def main():
    print(f"🚀 Starting Load Test against {TARGET_URL}")
    print(f"Workers: {WORKER_COUNT}")
    print(f"Total Requests: {TOTAL_REQUESTS}")
    print("-" * 40)
    
    start_time = time.time()
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKER_COUNT) as executor:
        futures = [executor.submit(make_request, i) for i in range(TOTAL_REQUESTS)]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            print(".", end="", flush=True)
            
    total_time = time.time() - start_time
    print("\n" + "-" * 40)
    
    # Analysis
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    latencies = [r["latency"] for r in successful]
    
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    print(f"⏱️  Total Time: {total_time:.2f}s")
    print(f"⚡ RPS: {len(results) / total_time:.2f}")
    
    if latencies:
        print(f"📊 AVG Latency: {mean(latencies):.4f}s")
        print(f"📉 MED Latency: {median(latencies):.4f}s")
        print(f"🐢 MAX Latency: {max(latencies):.4f}s")
    
    if len(failed) > 0:
        print("⚠️  Failures detected!")
        sys.exit(1)
    else:
        print("🎉 Load Test Passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
