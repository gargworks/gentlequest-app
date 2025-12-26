"""
Test using WELLNESS_TOOLS_CONFIG directly (bypassing get_gemini_response_with_tools)
This will help identify if the issue is in our function or the config
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import google.generativeai as genai
from providers.gemini import WELLNESS_TOOLS_CONFIG

api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    print("❌ Set GEMINI_API_KEY first")
    exit(1)

genai.configure(api_key=api_key)

# Use WELLNESS_TOOLS_CONFIG from our actual code
tools = [WELLNESS_TOOLS_CONFIG]

model_name = "gemini-2.5-flash"
messages = [
    "I'm feeling very anxious right now",
    "I am stressed",
    "I'm having a panic attack"
]

print("=" * 60)
print(f"Testing WELLNESS_TOOLS_CONFIG with {model_name}")
print("=" * 60)

for msg in messages:
    print(f"\n📝 Message: \"{msg}\"")
    print("-" * 40)
    
    try:
        # EXACT same call as working test
        model = genai.GenerativeModel(model_name, tools=tools)
        response = model.generate_content(msg)
        
        found = False
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    fc = part.function_call
                    print(f"✅ FUNCTION CALLED: {fc.name}")
                    print(f"   Args: {dict(fc.args) if fc.args else {}}")
                    found = True
                elif hasattr(part, 'text') and part.text:
                    print(f"📝 Text: {part.text[:80]}...")
        
        if not found:
            print("❌ No function called")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("If this works but test_agentic_live.py fails,")
print("the issue is in get_gemini_response_with_tools function")
print("=" * 60)
