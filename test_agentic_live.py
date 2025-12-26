"""
Test Agentic Architecture Locally
Verifies if Gemini actually calls get_wellness_intervention()

Run with Gemini API key set:
export GEMINI_API_KEY=your_key
python test_agentic_live.py
"""

import sys
import os

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from providers.gemini import get_gemini_response_with_tools

def test_anxiety_triggers_function():
    """Test if 'I'm anxious' triggers get_wellness_intervention"""
    print("=" * 70)
    print("Testing: Does Gemini call get_wellness_intervention()?")
    print("=" * 70)
    
    test_messages = [
        "I'm feeling very anxious right now",
        "I am stressed and anxious",
        "I'm having a panic attack",
    ]
    
    for msg in test_messages:
        print(f"\n📝 User: \"{msg}\"")
        print("-" * 70)
        
        try:
            response, tool_calls = get_gemini_response_with_tools(
                message=msg,
                session_id="test_local_session",
                risk_level="medium"
            )
            
            print(f"💬 Luna: {response[:150]}...")
            print(f"\n🔧 Tool calls: {len(tool_calls)}")
            
            if tool_calls:
                for tc in tool_calls:
                    tool_name = tc.get('name', 'unknown')
                    result = tc.get('result', {})
                    
                    print(f"\n✅ Function Called: {tool_name}")
                    print(f"   Args: {tc.get('args', {})}")
                    
                    if 'intervention_type' in result:
                        print(f"   ✨ Intervention: {result.get('intervention_type')}")
                        print(f"   📦 Exercise: {result.get('exercise', {}).get('name', 'N/A')}")
                    
                    print(f"\n   THIS WOULD SHOW WIDGET IN FLUTTER ✅")
            else:
                print(f"\n❌ NO FUNCTION CALLED - Widget won't appear")
                print(f"   Problem: Gemini responded with text only")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("=" * 70)
    
    print("\nSummary:")
    print("If you see '✅ Function Called: get_wellness_intervention' above,")
    print("the agentic architecture works!")
    print("\nIf you see '❌ NO FUNCTION CALLED', we need a fallback.")

if __name__ == '__main__':
    # Check for API key
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not set")
        print("Set it with: export GEMINI_API_KEY=your_key")
        sys.exit(1)
    
    test_anxiety_triggers_function()
