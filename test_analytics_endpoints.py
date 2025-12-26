"""
Test Analytics Endpoints

Quick test to verify analytics API endpoints are working.
"""

import requests
import json

BASE_URL = "https://gentlequest.onrender.com"
# BASE_URL = "http://localhost:5055"

def test_analytics_endpoints():
    """Test all analytics endpoints"""
    
    print("Testing Analytics Endpoints")
    print("=" * 60)
    
    # Test 1: Overview
    print("\n1. Testing /api/analytics/overview")
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/overview?days=30", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   Total interventions: {data['overall']['total_interventions']}")
            print(f"   Completion rate: {data['overall']['completion_rate']:.1%}")
            print(f"   Avg mood improvement: {data['overall']['avg_mood_improvement']:.2f}")
        else:
            print(f"   ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Interventions
    print("\n2. Testing /api/analytics/interventions")
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/interventions?days=30", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   Completion rates by type:")
            for ex_type, stats in data['completion_rates'].items():
                print(f"      {ex_type}: {stats['completion_rate']:.1%} ({stats['total']} total)")
            if data['recommendations']:
                print(f"   Best mood improvement: {data['recommendations'].get('best_mood_improvement', 'N/A')}")
        else:
            print(f"   ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Function Calling
    print("\n3. Testing /api/analytics/function-calling")
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/function-calling?days=7", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   Stats: {data['stats']}")
        else:
            print(f"   ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Analytics endpoints test complete!")


if __name__ == "__main__":
    test_analytics_endpoints()
