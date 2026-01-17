"""Verify crisis detection accuracy with comprehensive test cases"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crisis_detection_enhanced import detect_crisis_level

# Test cases with expected results
TEST_CASES = [
    # Suicide - should detect as crisis
    ("I want to kill myself", "crisis"),
    ("thinking about suicide", "crisis"),
    ("I want to die", "crisis"),
    ("better off dead", "crisis"),
    ("end my life", "crisis"),
    ("permanent solution", "crisis"),
    ("won't be here much longer", "crisis"),
    ("saying goodbye", "crisis"),
    ("everyone would be better without me", "high"),
    ("can't go on anymore", "high"),
    
    # Self-harm - should detect as high
    ("I've been cutting myself", "high"),
    ("burning myself", "high"),
    ("self-harm", "high"),
    ("hurting myself", "high"),
    ("deserve the pain", "high"),
    ("punishing myself", "high"),
    
    # Harm to others - should detect as crisis
    ("I want to hurt someone", "crisis"),
    ("planning to shoot", "crisis"),
    ("kill someone", "crisis"),
    ("violent thoughts", "high"),
    
    # False positives - should NOT detect as crisis
    ("I'm dying to see that movie", "low"),
    ("this exam is killing me", "low"),
    ("dead tired", "low"),
    ("killing time", "low"),
    ("cutting class", "low"),
]

def verify_detection():
    print("🔍 CRISIS DETECTION VERIFICATION")
    print("=" * 80)
    
    passed = 0
    failed = 0
    errors = []
    
    for message, expected in TEST_CASES:
        result = detect_crisis_level(message)
        
        # Allow escalation to crisis (high → crisis is acceptable)
        if result == expected or (expected == "high" and result == "crisis"):
            passed += 1
            print(f"✅ {message[:50]:<50} → {result}")
        else:
            failed += 1
            errors.append(f"{message} → Expected {expected}, got {result}")
            print(f"❌ {message[:50]:<50} → {result} (expected {expected})")
    
    print()
    print("=" * 80)
    print(f"RESULTS: {passed}/{len(TEST_CASES)} passed ({passed/len(TEST_CASES)*100:.1f}%)")
    print(f"TARGET: 95%+ detection rate")
    
    if passed/len(TEST_CASES) >= 0.95:
        print("✅ DETECTION RATE ACCEPTABLE")
    else:
        print("⚠️  DETECTION RATE BELOW TARGET")
        print("\nFAILED CASES:")
        for error in errors:
            print(f"  - {error}")
    
    return passed/len(TEST_CASES)

if __name__ == '__main__':
    accuracy = verify_detection()
    sys.exit(0 if accuracy >= 0.95 else 1)
