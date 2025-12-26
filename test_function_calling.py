"""
Test that Gemini function calling actually works
Run with: python test_function_calling.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from providers.gemini import get_gemini_response_with_tools

def test_function_calling():
    """Test that Gemini calls wellness functions"""
    print("Testing Gemini function calling...")
    print("=" * 60)
    
    # Test messages that should trigger functions
    test_cases = [
        ("I'm feeling very anxious right now", "get_breathing_exercise"),
        ("I'm having a panic attack", "get_grounding_exercise"),  
        ("Can you give me a journaling prompt?", "get_journal_prompt"),
    ]
    
    for message, expected_tool in test_cases:
        print(f"\n📝 Message: \"{message}\"")
        print(f"🎯 Expected tool: {expected_tool}")
        
        response, tool_calls = get_gemini_response_with_tools(
            message,
            session_id="test_debug_session",
            risk_level="medium"
        )
        
        print(f"💬 Response: {response[:100]}...")
        print(f"🔧 Tool calls: {len(tool_calls)}")
        
        if tool_calls:
            for tc in tool_calls:
                tool_name = tc.get('name')
                result = tc.get('result', {})
                exercise_type = result.get('exercise_type', 'N/A')
                
                print(f"   ✅ Called: {tool_name}")
                print(f"   📦 Exercise type: {exercise_type}")
                
                if tool_name == expected_tool:
                    print(f"   ✨ SUCCESS: Correct tool called!")
                else:
                    print(f"   ⚠️  WARNING: Expected {expected_tool}, got {tool_name}")
        else:
            print(f"   ❌ FAILED: No tools called!")
            print(f"   🐛 This is the bug - Gemini should call {expected_tool}")
        
        print("-" * 60)
    
    print("\n" + "=" * 60)
    print("Test complete!")

if __name__ == '__main__':
    test_function_calling()
