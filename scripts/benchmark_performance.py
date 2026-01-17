"""Benchmark system performance"""
import sys
import os
import time
import requests
from statistics import mean
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:5055"

def benchmark_endpoint(endpoint, method="GET", data=None, iterations=100):
    times = []
    errors = 0
    
    for _ in range(iterations):
        start = time.time()
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers={"X-Session-ID": "benchmark"}, timeout=10)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers={"X-Session-ID": "benchmark"}, timeout=10)
            
            if response.status_code == 200:
                times.append(time.time() - start)
            else:
                errors += 1
        except Exception:
            errors += 1
    
    if times:
        sorted_times = sorted(times)
        return {
            "avg": mean(times),
            "p50": sorted_times[len(sorted_times)//2],
            "p95": sorted_times[int(len(sorted_times)*0.95)],
            "p99": sorted_times[int(len(sorted_times)*0.99)],
            "min": min(times),
            "max": max(times),
            "errors": errors
        }
    return None

def main():
    print("⚡ PERFORMANCE BENCHMARK")
    print("=" * 80)
    
    endpoints = [
        ("/api/health", "GET", None, "Health Check"),
        ("/api/chat", "POST", {"message": "Hello"}, "Chat Message"),
        ("/api/quests", "GET", None, "Get Quests"),
        ("/api/resources", "GET", None, "Get Resources"),
        ("/api/profile", "GET", None, "Get Profile"),
    ]
    
    for endpoint, method, data, name in endpoints:
        print(f"\n{name}:")
        result = benchmark_endpoint(endpoint, method, data, iterations=100)
        
        if result:
            print(f"  Average: {result['avg']*1000:.0f}ms")
            print(f"  p95: {result['p95']*1000:.0f}ms {'✅' if result['p95'] < 0.5 else '⚠️'}")
            print(f"  p99: {result['p99']*1000:.0f}ms")
            print(f"  Errors: {result['errors']}")
        else:
            print(f"  ❌ All requests failed")
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()
