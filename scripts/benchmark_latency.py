
import time
import statistics
import sys
import os
from flask import json

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db

def run_benchmark(iterations=10):
    print(f"🚀 Starting Latency Benchmark ({iterations} runs)...")
    
    with app.test_client() as client:
        latencies = []
        
        # 1. Get Session
        print("🔑 Authenticating...")
        session_resp = client.get('/api/get_or_create_session')
        if session_resp.status_code != 200:
            print(f"❌ Failed to create session: {session_resp.status_code}")
            return
            
        session_data = json.loads(session_resp.data)
        session_id = session_data.get('session_id')
        headers = {'X-Session-ID': session_id}
        print(f"✅ Session Key: {session_id[:8]}...")

        # 2. Warmup
        print("🔥 Warmup request...")
        client.post('/api/chat', json={'message': 'warmup'}, headers=headers)
        
        # 3. Benchmark
        for i in range(iterations):
            start = time.time()
            response = client.post('/api/chat', json={'message': 'Hello, system check.'}, headers=headers)
            end = time.time()
            
            if response.status_code != 200:
                print(f"⚠️ Error {response.status_code}: {response.data}")
            
            duration = (end - start) * 1000 # ms
            latencies.append(duration)
            print(f"Run {i+1}: {duration:.2f}ms (Status: {response.status_code})")
            
        avg = statistics.mean(latencies)
        median = statistics.median(latencies)
        stdev = statistics.stdev(latencies)
        
        print("\n📊 Benchmark Results:")
        print(f"Samples: {iterations}")
        print(f"Average: {avg:.2f}ms")
        print(f"Median:  {median:.2f}ms")
        print(f"StdDev:  {stdev:.2f}ms")
        
        return avg, median, stdev

if __name__ == "__main__":
    run_benchmark()
