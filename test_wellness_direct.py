"""
Test wellness function with EXACT same structure as working weather test
"""

import os
import sys

# Add path for DualEngineLLM
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mcp-server-nucleus", "src"))

try:
    from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
except ImportError:
    print("❌ DualEngineLLM module not found")
    sys.exit(1)

api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    print("❌ Set GEMINI_API_KEY first")
    sys.exit(1)

# EXACT format that worked - wrapping function declarations in a dict (Tool)
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
        model = DualEngineLLM(model_name, api_key=api_key)
        # Note: DualEngine/V1 expects tools as a list of tools or function declarations
        # Our updated client handles this.
        response = model.generate_content(msg, tools=tools)
        
        found = False
        
        # V1 Response Parsing
        # Check function calls
        if hasattr(response, 'function_calls') and response.function_calls:
             for fc in response.function_calls:
                 print(f"✅ FUNCTION CALLED: {fc.name}")
                 print(f"   Args: {fc.args}")
                 found = True
        # Check text
        elif hasattr(response, 'text') and response.text:
             print(f"📝 Text: {response.text[:80]}...")
        
        # Fallback/Manual check if attribute access varies
        if not found and response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    fc = part.function_call
                    print(f"✅ FUNCTION CALLED: {fc.name}")
                    print(f"   Args: {dict(fc.args) if fc.args else {}}")
                    found = True
        
        if not found:
            print("❌ No function called")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 60)
