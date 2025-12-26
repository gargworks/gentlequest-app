"""
Comprehensive End-to-End Test Suite
Tests all agentic AI features on production

Test Categories:
1. Health & Connectivity
2. Analytics API Endpoints
3. Admin Dashboard
4. Intervention Outcome Tracking
5. Function Calling Reliability (Native, not fallback)
6. Variety Logic (Stage progression)
7. Memory System Graceful Degradation

Run with: python3 test_comprehensive_e2e.py
"""

import requests
import json
import time
import uuid
import sys
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Configuration
BASE_URL = "https://gentlequest.onrender.com"
TIMEOUT = 30  # seconds
VERBOSE = True

# Test results storage
results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "tests": []
}


def log(msg: str, level: str = "INFO"):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    symbols = {"INFO": "ℹ️", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "TEST": "🧪"}
    print(f"[{timestamp}] {symbols.get(level, '•')} {msg}")


def record_test(name: str, passed: bool, details: str = "", duration: float = 0):
    """Record test result"""
    results["tests"].append({
        "name": name,
        "passed": passed,
        "details": details,
        "duration": duration
    })
    if passed:
        results["passed"] += 1
        log(f"PASS: {name} ({duration:.2f}s)", "PASS")
    else:
        results["failed"] += 1
        log(f"FAIL: {name} - {details}", "FAIL")


# ============================================================================
# TEST CATEGORY 1: Health & Connectivity
# ============================================================================

def test_health_endpoint():
    """Test /api/health endpoint"""
    start = time.time()
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                record_test("Health Endpoint", True, "", duration)
                return True
            else:
                record_test("Health Endpoint", False, f"Status not healthy: {data}", duration)
        else:
            record_test("Health Endpoint", False, f"Status code: {response.status_code}", duration)
    except Exception as e:
        record_test("Health Endpoint", False, str(e), time.time() - start)
    return False


def test_server_cold_start():
    """Test if server responds quickly (not cold starting)"""
    start = time.time()
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        duration = time.time() - start
        
        if duration < 5:
            record_test("Server Response Time", True, f"{duration:.2f}s", duration)
            return True
        else:
            record_test("Server Response Time", False, f"Slow: {duration:.2f}s (cold start?)", duration)
    except Exception as e:
        record_test("Server Response Time", False, str(e), time.time() - start)
    return False


# ============================================================================
# TEST CATEGORY 2: Analytics API Endpoints
# ============================================================================

def test_analytics_overview():
    """Test /api/analytics/overview endpoint"""
    start = time.time()
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/overview?days=30", timeout=TIMEOUT)
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["period_days", "overall", "by_type", "timestamp"]
            overall_fields = ["total_interventions", "completion_rate", "avg_mood_improvement"]
            
            # Check structure
            if all(f in data for f in required_fields):
                if all(f in data["overall"] for f in overall_fields):
                    record_test("Analytics Overview API", True, 
                               f"Total: {data['overall']['total_interventions']}", duration)
                    return data
            record_test("Analytics Overview API", False, f"Missing fields in response", duration)
        else:
            record_test("Analytics Overview API", False, f"Status: {response.status_code}", duration)
    except Exception as e:
        record_test("Analytics Overview API", False, str(e), time.time() - start)
    return None


def test_analytics_interventions():
    """Test /api/analytics/interventions endpoint"""
    start = time.time()
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/interventions?days=30", timeout=TIMEOUT)
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["completion_rates", "mood_improvements", "recommendations"]
            
            if all(f in data for f in required_fields):
                record_test("Analytics Interventions API", True, "", duration)
                return data
            record_test("Analytics Interventions API", False, "Missing fields", duration)
        else:
            record_test("Analytics Interventions API", False, f"Status: {response.status_code}", duration)
    except Exception as e:
        record_test("Analytics Interventions API", False, str(e), time.time() - start)
    return None


def test_analytics_function_calling():
    """Test /api/analytics/function-calling endpoint"""
    start = time.time()
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/function-calling?days=7", timeout=TIMEOUT)
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if "stats" in data:
                record_test("Function Calling Analytics API", True, "", duration)
                return data
            record_test("Function Calling Analytics API", False, "Missing stats", duration)
        else:
            record_test("Function Calling Analytics API", False, f"Status: {response.status_code}", duration)
    except Exception as e:
        record_test("Function Calling Analytics API", False, str(e), time.time() - start)
    return None


def test_analytics_user_session():
    """Test /api/analytics/user/<session_id> endpoint"""
    session_id = str(uuid.uuid4())
    start = time.time()
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/user/{session_id}", timeout=TIMEOUT)
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if "engagement" in data and "recommended_intervention" in data:
                record_test("User Analytics API", True, "", duration)
                return data
            record_test("User Analytics API", False, "Missing fields", duration)
        else:
            record_test("User Analytics API", False, f"Status: {response.status_code}", duration)
    except Exception as e:
        record_test("User Analytics API", False, str(e), time.time() - start)
    return None


# ============================================================================
# TEST CATEGORY 3: Admin Dashboard
# ============================================================================

def test_admin_dashboard():
    """Test /api/admin/analytics dashboard loads"""
    start = time.time()
    try:
        response = requests.get(f"{BASE_URL}/api/admin/analytics", timeout=TIMEOUT)
        duration = time.time() - start
        
        if response.status_code == 200:
            content = response.text
            # Check for key elements
            checks = [
                "GentleQuest Analytics" in content,
                "Total Interventions" in content,
                "Completion Rate" in content,
                "Mood Improvement" in content,
            ]
            if all(checks):
                record_test("Admin Dashboard HTML", True, "", duration)
                return True
            record_test("Admin Dashboard HTML", False, "Missing content elements", duration)
        else:
            record_test("Admin Dashboard HTML", False, f"Status: {response.status_code}", duration)
    except Exception as e:
        record_test("Admin Dashboard HTML", False, str(e), time.time() - start)
    return False


# ============================================================================
# TEST CATEGORY 4: Intervention Outcome Tracking
# ============================================================================

def test_outcome_tracking_started():
    """Test tracking 'started' outcome"""
    session_id = str(uuid.uuid4())
    intervention_id = f"test_{uuid.uuid4().hex[:8]}"
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/intervention/outcome",
            json={
                "session_id": session_id,
                "intervention_id": intervention_id,
                "exercise_type": "breathing",
                "outcome": "started",
            },
            timeout=TIMEOUT
        )
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                record_test("Outcome Tracking: Started", True, "", duration)
                return session_id, intervention_id
            record_test("Outcome Tracking: Started", False, "success=false", duration)
        else:
            record_test("Outcome Tracking: Started", False, f"Status: {response.status_code}", duration)
    except Exception as e:
        record_test("Outcome Tracking: Started", False, str(e), time.time() - start)
    return None, None


def test_outcome_tracking_completed_with_analytics():
    """Test tracking 'completed' with mood and time data"""
    session_id = str(uuid.uuid4())
    intervention_id = f"test_{uuid.uuid4().hex[:8]}"
    
    # First, report started
    requests.post(
        f"{BASE_URL}/api/intervention/outcome",
        json={
            "session_id": session_id,
            "intervention_id": intervention_id,
            "exercise_type": "grounding",
            "outcome": "started",
        },
        timeout=TIMEOUT
    )
    
    time.sleep(1)  # Simulate exercise time
    
    # Now report completed with analytics
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/intervention/outcome",
            json={
                "session_id": session_id,
                "intervention_id": intervention_id,
                "exercise_type": "grounding",
                "outcome": "completed",
                "time_spent_seconds": 120,
                "mood_before": 3,
                "mood_after": 7,
                "effectiveness": 0.8,
                "feedback": "Test feedback - felt better after exercise"
            },
            timeout=TIMEOUT
        )
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                record_test("Outcome Tracking: Completed with Analytics", True, 
                           "mood 3→7, 120s, 0.8 effectiveness", duration)
                return True
            record_test("Outcome Tracking: Completed with Analytics", False, "success=false", duration)
        else:
            record_test("Outcome Tracking: Completed with Analytics", False, 
                       f"Status: {response.status_code} - {response.text}", duration)
    except Exception as e:
        record_test("Outcome Tracking: Completed with Analytics", False, str(e), time.time() - start)
    return False


def test_outcome_tracking_validation():
    """Test validation of mood ratings"""
    session_id = str(uuid.uuid4())
    
    # Test invalid mood_before (>10)
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/intervention/outcome",
            json={
                "session_id": session_id,
                "intervention_id": "test_validation",
                "outcome": "completed",
                "mood_before": 15,  # Invalid: should be 1-10
            },
            timeout=TIMEOUT
        )
        duration = time.time() - start
        
        if response.status_code == 400:
            record_test("Outcome Validation: Invalid Mood", True, "Correctly rejected mood=15", duration)
            return True
        else:
            record_test("Outcome Validation: Invalid Mood", False, 
                       f"Should reject mood=15, got {response.status_code}", duration)
    except Exception as e:
        record_test("Outcome Validation: Invalid Mood", False, str(e), time.time() - start)
    return False


# ============================================================================
# TEST CATEGORY 5: Function Calling Reliability (Native, not fallback)
# ============================================================================

def test_single_function_call(message: str, expected_type: str = None) -> Tuple[bool, str, str]:
    """
    Test a single message for native function calling.
    Returns (used_native, function_call_source, exercise_type)
    """
    session_id = str(uuid.uuid4())
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": message},
            headers={"X-Session-ID": session_id},
            timeout=60  # Longer timeout for AI response
        )
        
        if response.status_code != 200:
            return False, "error", ""
        
        data = response.json()
        
        # Check if interactive exercise was returned
        if data.get("interactive"):
            exercise_type = data.get("exercise_type", "")
            function_source = data.get("function_call_source", "unknown")
            return function_source == "gemini", function_source, exercise_type
        else:
            return False, "no_intervention", ""
            
    except Exception as e:
        return False, f"exception: {e}", ""


def test_function_calling_reliability():
    """
    Test Gemini's native function calling across multiple prompts.
    Focus on accuracy, not fallback.
    """
    log("Starting Function Calling Reliability Tests...", "TEST")
    
    test_prompts = [
        # Clear anxiety/stress signals
        ("I'm feeling really anxious right now", "breathing"),
        ("I'm so stressed about my exams", "breathing"),
        ("My heart is racing and I can't calm down", "breathing"),
        
        # Panic/overwhelm
        ("I'm having a panic attack", "breathing"),
        ("Everything feels overwhelming right now", "breathing"),
        
        # Emotional distress
        ("I'm feeling really sad today", "breathing"),
        ("I'm struggling with negative thoughts", "breathing"),
        
        # Work/life stress
        ("Work stress is getting to me", "breathing"),
        ("I can't sleep because of worry", "breathing"),
        ("I need help calming down", "breathing"),
    ]
    
    native_calls = 0
    fallback_calls = 0
    no_intervention = 0
    errors = 0
    detailed_results = []
    
    for i, (prompt, expected_type) in enumerate(test_prompts):
        log(f"  Test {i+1}/{len(test_prompts)}: '{prompt[:40]}...'", "INFO")
        
        start = time.time()
        used_native, source, exercise_type = test_single_function_call(prompt)
        duration = time.time() - start
        
        result = {
            "prompt": prompt,
            "source": source,
            "exercise_type": exercise_type,
            "duration": duration,
            "native": used_native
        }
        detailed_results.append(result)
        
        if source == "gemini":
            native_calls += 1
            log(f"    → Native: {exercise_type} ({duration:.1f}s)", "PASS")
        elif source == "keyword_fallback":
            fallback_calls += 1
            log(f"    → Fallback: {exercise_type} ({duration:.1f}s)", "WARN")
        elif source == "no_intervention":
            no_intervention += 1
            log(f"    → No intervention ({duration:.1f}s)", "WARN")
        else:
            errors += 1
            log(f"    → Error: {source}", "FAIL")
        
        # Rate limiting - wait between calls
        time.sleep(2)
    
    total = len(test_prompts)
    native_rate = (native_calls / total) * 100 if total > 0 else 0
    fallback_rate = (fallback_calls / total) * 100 if total > 0 else 0
    
    # Record summary result
    passed = native_rate >= 50  # Target: At least 50% native
    record_test(
        "Function Calling Reliability",
        passed,
        f"Native: {native_rate:.1f}% ({native_calls}/{total}), Fallback: {fallback_rate:.1f}%, No-intervention: {no_intervention}",
        sum(r["duration"] for r in detailed_results)
    )
    
    return {
        "total": total,
        "native_calls": native_calls,
        "fallback_calls": fallback_calls,
        "no_intervention": no_intervention,
        "errors": errors,
        "native_rate": native_rate,
        "detailed_results": detailed_results
    }


# ============================================================================
# TEST CATEGORY 6: Variety Logic (Stage Progression)
# ============================================================================

def test_variety_logic():
    """
    Test that intervention types progress: breathing → grounding → journaling → talk
    Uses a single session to track progression.
    """
    log("Starting Variety Logic Tests...", "TEST")
    
    session_id = str(uuid.uuid4())
    expected_progression = ["breathing", "grounding", "journaling"]
    actual_progression = []
    
    prompts = [
        "I'm feeling anxious",
        "The anxiety is coming back again", 
        "I'm still struggling with anxiety",
    ]
    
    for i, prompt in enumerate(prompts):
        log(f"  Request {i+1}: '{prompt}'", "INFO")
        
        start = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat",
                json={"message": prompt},
                headers={"X-Session-ID": session_id},
                timeout=60
            )
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                exercise_type = data.get("exercise_type", "none")
                offer_stage = data.get("offer_stage", "?")
                source = data.get("function_call_source", "unknown")
                
                actual_progression.append(exercise_type)
                log(f"    → Stage {offer_stage}: {exercise_type} (source: {source}, {duration:.1f}s)", 
                    "PASS" if exercise_type == expected_progression[i] else "WARN")
            else:
                actual_progression.append("error")
                log(f"    → Error: {response.status_code}", "FAIL")
                
        except Exception as e:
            actual_progression.append("exception")
            log(f"    → Exception: {e}", "FAIL")
        
        # Wait between requests
        time.sleep(3)
    
    # Check if progression matches expected
    correct_progression = actual_progression == expected_progression
    
    record_test(
        "Variety Logic Progression",
        correct_progression,
        f"Expected: {expected_progression}, Got: {actual_progression}",
        0
    )
    
    return {
        "expected": expected_progression,
        "actual": actual_progression,
        "correct": correct_progression
    }


# ============================================================================
# TEST CATEGORY 7: Memory System Graceful Degradation
# ============================================================================

def test_memory_status():
    """Test /api/memory/status endpoint for graceful degradation"""
    start = time.time()
    try:
        response = requests.get(f"{BASE_URL}/api/memory/status", timeout=TIMEOUT)
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            # Either memory works or it gracefully reports disabled
            record_test("Memory Status Endpoint", True, 
                       f"enabled={data.get('memory_enabled', 'N/A')}", duration)
            return data
        else:
            record_test("Memory Status Endpoint", False, f"Status: {response.status_code}", duration)
    except Exception as e:
        record_test("Memory Status Endpoint", False, str(e), time.time() - start)
    return None


def test_chat_without_crash():
    """Test that chat endpoint doesn't crash even if memory fails"""
    session_id = str(uuid.uuid4())
    start = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Hello, how are you today?"},
            headers={"X-Session-ID": session_id},
            timeout=60
        )
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if "response" in data:
                record_test("Chat Without Memory Crash", True, 
                           f"Response length: {len(data['response'])} chars", duration)
                return True
        record_test("Chat Without Memory Crash", False, f"Status: {response.status_code}", duration)
    except Exception as e:
        record_test("Chat Without Memory Crash", False, str(e), time.time() - start)
    return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def print_summary():
    """Print test summary"""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    total = results["passed"] + results["failed"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0
    
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {results['passed']} ({pass_rate:.1f}%)")
    print(f"❌ Failed: {results['failed']}")
    
    if results["failed"] > 0:
        print("\n📋 Failed Tests:")
        for test in results["tests"]:
            if not test["passed"]:
                print(f"   • {test['name']}: {test['details']}")
    
    print("\n" + "="*70)
    return pass_rate >= 80  # Success if 80% pass


def run_all_tests():
    """Run all test categories"""
    print("="*70)
    print("🧪 COMPREHENSIVE END-TO-END TEST SUITE")
    print(f"   Target: {BASE_URL}")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Category 1: Health & Connectivity
    print("\n📦 Category 1: Health & Connectivity")
    print("-"*50)
    test_health_endpoint()
    test_server_cold_start()
    
    # Category 2: Analytics API
    print("\n📦 Category 2: Analytics API Endpoints")  
    print("-"*50)
    test_analytics_overview()
    test_analytics_interventions()
    test_analytics_function_calling()
    test_analytics_user_session()
    
    # Category 3: Admin Dashboard
    print("\n📦 Category 3: Admin Dashboard")
    print("-"*50)
    test_admin_dashboard()
    
    # Category 4: Outcome Tracking
    print("\n📦 Category 4: Intervention Outcome Tracking")
    print("-"*50)
    test_outcome_tracking_started()
    test_outcome_tracking_completed_with_analytics()
    test_outcome_tracking_validation()
    
    # Category 5: Function Calling (This takes longest)
    print("\n📦 Category 5: Function Calling Reliability")
    print("-"*50)
    fc_results = test_function_calling_reliability()
    
    # Category 6: Variety Logic
    print("\n📦 Category 6: Variety Logic Progression")
    print("-"*50)
    variety_results = test_variety_logic()
    
    # Category 7: Memory System
    print("\n📦 Category 7: Memory System Graceful Degradation")
    print("-"*50)
    test_memory_status()
    test_chat_without_crash()
    
    # Summary
    success = print_summary()
    
    # Detailed function calling results
    if fc_results:
        print("\n📊 FUNCTION CALLING DETAILS")
        print("-"*50)
        print(f"Native Rate: {fc_results['native_rate']:.1f}%")
        print(f"Native Calls: {fc_results['native_calls']}/{fc_results['total']}")
        print(f"Fallback Calls: {fc_results['fallback_calls']}")
        print(f"No Intervention: {fc_results['no_intervention']}")
    
    # Variety logic results
    if variety_results:
        print("\n📊 VARIETY LOGIC DETAILS")
        print("-"*50)
        print(f"Expected: {variety_results['expected']}")
        print(f"Actual:   {variety_results['actual']}")
        print(f"Correct:  {'✅ Yes' if variety_results['correct'] else '❌ No'}")
    
    print(f"\n🏁 Tests completed at {datetime.now().strftime('%H:%M:%S')}")
    
    return success


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
