"""
MINIMAL Function Calling Test - Correct SDK Format
Run with: GEMINI_API_KEY=your_key python3 test_minimal_function.py
"""

import os
import google.generativeai as genai

api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    print("❌ Set GEMINI_API_KEY first")
    exit(1)

genai.configure(api_key=api_key)

# Correct format: list of function declarations wrapped in dict
tools = [
    {
        "function_declarations": [
            {
                "name": "get_weather",
                "description": "Get weather for a city. Call this when user asks about weather.",
                "parameters": {
                    "type": "OBJECT",  # Must be uppercase
                    "properties": {
                        "location": {
                            "type": "STRING",  # Must be uppercase
                            "description": "City name"
                        }
                    },
                    "required": ["location"]
                }
            }
        ]
    }
]

models_to_test = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]

message = "What's the weather in New York?"

print("=" * 60)
print("Minimal Function Calling Test")
print("=" * 60)

for model_name in models_to_test:
    print(f"\n🔧 Testing: {model_name}")
    print("-" * 40)
    
    try:
        model = genai.GenerativeModel(model_name, tools=tools)
        response = model.generate_content(message)
        
        found_function = False
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    fc = part.function_call
                    print(f"✅ FUNCTION CALLED: {fc.name}")
                    print(f"   Args: {dict(fc.args) if fc.args else {}}")
                    found_function = True
                elif hasattr(part, 'text') and part.text:
                    print(f"📝 Text: {part.text[:80]}...")
        
        if not found_function:
            print("❌ No function called")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 60)
