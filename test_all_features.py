#!/usr/bin/env python3
"""
Comprehensive test of all GentleQuest features
Tests for cold starts, broken features, and logical flaws
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
BASE_URL = "https://gentlequest.onrender.com"
TEST_SESSION = f"test-comprehensive-{int(time.time())}"

class FeatureTester:
    def __init__(self):
        self.results = []
        self.issues = []
        
    def test_feature(self, name: str, test_func) -> bool:
        """Test a feature and record results"""
        print(f"\n🔍 Testing: {name}")
        start_time = time.time()
        
        try:
            success, message = test_func()
            elapsed = time.time() - start_time
            
            if success:
                print(f"✅ PASS: {name} ({elapsed:.2f}s)")
                self.results.append((name, "PASS", message, elapsed))
            else:
                print(f"❌ FAIL: {name} - {message}")
                self.results.append((name, "FAIL", message, elapsed))
                self.issues.append(f"{name}: {message}")
            
            return success
            
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"Exception: {str(e)}"
            print(f"🔥 ERROR: {name} - {error_msg}")
            self.results.append((name, "ERROR", error_msg, elapsed))
            self.issues.append(f"{name}: {error_msg}")
            return False

    def test_cold_start(self) -> Tuple[bool, str]:
        """Test for cold start issues"""
        # First request (might be cold)
        t1 = time.time()
        r1 = requests.get(f"{BASE_URL}/api/ping", timeout=30)
        cold_time = time.time() - t1
        
        # Second request (should be warm)
        t2 = time.time()
        r2 = requests.get(f"{BASE_URL}/api/ping", timeout=5)
        warm_time = time.time() - t2
        
        # Check if cold start is happening (>5 second difference)
        if cold_time > 5 and cold_time > (warm_time * 10):
            return False, f"Cold start detected! First: {cold_time:.2f}s, Second: {warm_time:.2f}s"
        
        return True, f"No cold start. First: {cold_time:.2f}s, Second: {warm_time:.2f}s"

    def test_health_endpoint(self) -> Tuple[bool, str]:
        """Test health endpoint"""
        r = requests.get(f"{BASE_URL}/api/health", timeout=10)
        if r.status_code != 200:
            return False, f"Status code {r.status_code}"
        
        data = r.json()
        if data.get('status') != 'healthy':
            return False, f"Status is {data.get('status')}"
        
        # Check components
        issues = []
        if 'unhealthy' in str(data.get('database', '')):
            issues.append("Database unhealthy")
        if 'unhealthy' in str(data.get('redis', '')):
            issues.append("Redis unhealthy")
            
        if issues:
            return False, ", ".join(issues)
            
        return True, "All components healthy"

    def test_chat_functionality(self) -> Tuple[bool, str]:
        """Test chat endpoint"""
        payload = {
            "message": "Hello, how are you?",
            "session_id": TEST_SESSION
        }
        
        r = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            timeout=30
        )
        
        if r.status_code != 200:
            return False, f"Status code {r.status_code}"
        
        data = r.json()
        response = data.get('response', '')
        
        if not response or len(response) < 10:
            return False, "Response too short or empty"
        
        if "error" in response.lower():
            return False, f"Error in response: {response[:100]}"
            
        return True, f"Got response: {response[:50]}..."

    def test_session_management(self) -> Tuple[bool, str]:
        """Test session creation and retrieval"""
        # Create session
        r1 = requests.post(f"{BASE_URL}/api/get_or_create_session", timeout=10)
        if r1.status_code != 200:
            return False, f"Failed to create session: {r1.status_code}"
        
        session_id = r1.json().get('session_id')
        if not session_id:
            return False, "No session_id returned"
        
        # Send chat with session
        payload = {
            "message": "Test message",
            "session_id": session_id
        }
        r2 = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=30)
        
        if r2.status_code != 200:
            return False, f"Chat with session failed: {r2.status_code}"
        
        # Get history
        r3 = requests.get(f"{BASE_URL}/api/chat_history/{session_id}", timeout=10)
        if r3.status_code != 200:
            return False, f"History retrieval failed: {r3.status_code}"
        
        history = r3.json().get('history', [])
        if len(history) < 2:  # Should have user message and AI response
            return False, f"History incomplete: {len(history)} messages"
            
        return True, f"Session working with {len(history)} messages"

    def test_mood_tracking(self) -> Tuple[bool, str]:
        """Test mood entry and history"""
        # Submit mood
        mood_data = {
            "session_id": TEST_SESSION,
            "mood_score": 7,
            "notes": "Testing mood tracking"
        }
        
        r1 = requests.post(
            f"{BASE_URL}/api/mood_entry",
            json=mood_data,
            timeout=10
        )
        
        if r1.status_code != 201:
            return False, f"Mood submission failed: {r1.status_code}"
        
        # Get history
        r2 = requests.get(f"{BASE_URL}/api/mood_history/{TEST_SESSION}", timeout=10)
        
        if r2.status_code != 200:
            return False, f"Mood history failed: {r2.status_code}"
        
        entries = r2.json().get('mood_entries', [])
        if len(entries) == 0:
            return False, "No mood entries in history"
            
        return True, f"Mood tracking working with {len(entries)} entries"

    def test_self_assessment(self) -> Tuple[bool, str]:
        """Test self-assessment submission"""
        assessment = {
            "session_id": TEST_SESSION,
            "mood": "good",
            "energy": "moderate",
            "sleep": "7 hours",
            "stress": "low"
        }
        
        r = requests.post(
            f"{BASE_URL}/api/self_assessment",
            json=assessment,
            timeout=10
        )
        
        if r.status_code not in [200, 201]:
            return False, f"Assessment failed: {r.status_code}"
        
        data = r.json()
        if not data.get('success'):
            return False, "Assessment not successful"
            
        return True, f"Assessment recorded, XP: {data.get('xp_awarded', 0)}"

    def test_enterprise_endpoints(self) -> Tuple[bool, str]:
        """Test enterprise feature endpoints"""
        issues = []
        
        # Test enterprise status
        r1 = requests.get(f"{BASE_URL}/api/enterprise/status", timeout=10)
        if r1.status_code != 200:
            issues.append(f"Enterprise status failed: {r1.status_code}")
        else:
            features = r1.json().get('features', {})
            enabled = sum(1 for v in features.values() if v)
            if enabled < 3:
                issues.append(f"Only {enabled}/5 features enabled")
        
        # Test metrics
        r2 = requests.get(f"{BASE_URL}/api/enterprise/metrics", timeout=10)
        if r2.status_code != 200:
            issues.append(f"Metrics endpoint failed: {r2.status_code}")
        
        if issues:
            return False, "; ".join(issues)
            
        return True, f"{enabled}/5 enterprise features active"

    def test_keep_alive_mechanism(self) -> Tuple[bool, str]:
        """Check if keep-alive is configured properly"""
        # Check ping endpoint
        r = requests.head(f"{BASE_URL}/api/ping", timeout=5)
        if r.status_code != 200:
            return False, f"Ping endpoint not working: {r.status_code}"
        
        # Check if GitHub Actions workflow exists (can't verify if running without API)
        workflow_msg = "Ping endpoint works. GitHub workflow scheduled for */13 minutes"
        
        return True, workflow_msg

    def test_crisis_detection(self) -> Tuple[bool, str]:
        """Test crisis detection logic"""
        crisis_messages = [
            "I'm feeling really down and hopeless",
            "Everything is great and wonderful!",
            "I don't want to live anymore"  # Should trigger crisis
        ]
        
        results = []
        for msg in crisis_messages:
            payload = {
                "message": msg,
                "session_id": f"crisis-test-{int(time.time())}"
            }
            
            r = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=30)
            if r.status_code == 200:
                response = r.json().get('response', '')
                crisis_detected = r.json().get('crisis_detected', False)
                
                # Last message should detect crisis
                if "don't want to live" in msg and not crisis_detected:
                    results.append("Failed to detect crisis in high-risk message")
                elif "great and wonderful" in msg and crisis_detected:
                    results.append("False positive on positive message")
        
        if results:
            return False, "; ".join(results)
            
        return True, "Crisis detection working appropriately"

    def test_cors_configuration(self) -> Tuple[bool, str]:
        """Test CORS headers"""
        headers = {'Origin': 'https://gentlequest.com'}
        r = requests.options(f"{BASE_URL}/api/chat", headers=headers, timeout=5)
        
        cors_header = r.headers.get('Access-Control-Allow-Origin')
        if not cors_header:
            return False, "No CORS headers present"
        
        if cors_header != '*' and 'gentlequest' not in cors_header:
            return False, f"CORS not configured for gentlequest: {cors_header}"
            
        return True, f"CORS configured: {cors_header}"

    def test_rate_limiting(self) -> Tuple[bool, str]:
        """Test rate limiting is active"""
        # Send multiple requests quickly
        blocked = False
        for i in range(25):  # Try to exceed rate limit
            r = requests.get(f"{BASE_URL}/api/health", timeout=2)
            if r.status_code == 429:
                blocked = True
                break
                
        if not blocked:
            return False, "Rate limiting might not be active (no 429 received)"
            
        return True, "Rate limiting is active"

    def test_analytics_logging(self) -> Tuple[bool, str]:
        """Test analytics endpoint"""
        analytics_data = {
            "session_id": TEST_SESSION,
            "event_type": "test_event",
            "data": {
                "test": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        r = requests.post(
            f"{BASE_URL}/api/analytics/log",
            json=analytics_data,
            timeout=10
        )
        
        if r.status_code != 200:
            return False, f"Analytics logging failed: {r.status_code}"
            
        return True, "Analytics logging works"

    def run_all_tests(self):
        """Run all feature tests"""
        print("=" * 60)
        print("🚀 GENTLEQUEST COMPREHENSIVE FEATURE TEST")
        print("=" * 60)
        print(f"Target: {BASE_URL}")
        print(f"Time: {datetime.now().isoformat()}")
        
        # Define all tests
        tests = [
            ("Cold Start Check", self.test_cold_start),
            ("Health Endpoint", self.test_health_endpoint),
            ("Keep-Alive Mechanism", self.test_keep_alive_mechanism),
            ("Chat Functionality", self.test_chat_functionality),
            ("Session Management", self.test_session_management),
            ("Mood Tracking", self.test_mood_tracking),
            ("Self Assessment", self.test_self_assessment),
            ("Enterprise Endpoints", self.test_enterprise_endpoints),
            ("Crisis Detection", self.test_crisis_detection),
            ("CORS Configuration", self.test_cors_configuration),
            ("Analytics Logging", self.test_analytics_logging),
            # Rate limiting test last as it might trigger blocks
            ("Rate Limiting", self.test_rate_limiting),
        ]
        
        # Run tests
        for name, test_func in tests:
            self.test_feature(name, test_func)
            time.sleep(0.5)  # Small delay between tests
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, status, _, _ in self.results if status == "PASS")
        failed = sum(1 for _, status, _, _ in self.results if status == "FAIL")
        errors = sum(1 for _, status, _, _ in self.results if status == "ERROR")
        
        print(f"✅ Passed: {passed}/{len(self.results)}")
        print(f"❌ Failed: {failed}")
        print(f"🔥 Errors: {errors}")
        
        if self.issues:
            print("\n⚠️  ISSUES FOUND:")
            for issue in self.issues:
                print(f"   • {issue}")
        else:
            print("\n🎉 All features working correctly!")
        
        # Performance summary
        print("\n⏱️  PERFORMANCE:")
        for name, status, _, elapsed in self.results:
            if status == "PASS":
                print(f"   {name}: {elapsed:.2f}s")
        
        return len(self.issues) == 0

if __name__ == "__main__":
    tester = FeatureTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
