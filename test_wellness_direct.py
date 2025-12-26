"""
Test wellness function with EXACT same structure as working weather test
"""

import os
import google.generativeai as genai

api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    print("❌ Set GEMINI_API_KEY first")
    exit(1)

genai.configure(api_key=api_key)

# EXACT format that worked - just wellness function
tools = [
    {
        "function_declarations": [
            {
                "name": "get_wellness_intervention",
                "description": "Get a wellness exercise. MUST be called when user mentions anxiety, stress, panic, or feeling overwhelmed.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "issue": {
                            "type": "STRING",
                            "description": "The issue: anxiety, stress, panic, sleep, sadness",
                            "enum": ["anxiety", "stress", "panic", "sleep", "sadness"]
                        },
                        "intensity": {
                            "type": "STRING",
                            "description": "Severity level",
                            "enum": ["mild", "moderate", "severe"]
                        }
                    },
                    "required": ["issue", "intensity"]
                }
            }
        ]
    }
]

model_name = "gemini-2.5-flash"
messages = [
    "I'm feeling very anxious right now",
    "I am stressed",
    "I'm having a panic attack"
]

print("=" * 60)
print(f"Testing Wellness Function with {model_name}")
print("=" * 60)

for msg in messages:
    print(f"\n📝 Message: \"{msg}\"")
    print("-" * 40)
    
    try:
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
