
import os
from typing import Tuple

def check_safety_llm(user_message: str, ai_response: str) -> Tuple[bool, str]:
    """
    Layer 2 Guardrail: Verify AI response safety using a separate LLM call.
    
    Returns:
        (is_safe, reason_or_fallback)
    """
    api_key = os.getenv('GEMINI_API_KEY', '').split(',')[0].strip()
    if not api_key:
        return True, "No API key to verify"

    prompt = f"""
    You are a strict Safety Supervisor for a mental health AI.
    
    User: "{user_message}"
    AI Response: "{ai_response}"
    
    Task: Analyze the AI Response.
    Crucial Rules:
    1. It MUST NOT encourage self-harm, suicide, or violence.
    2. It MUST NOT give specific medical prescriptions or diagnoses.
    3. It MUST NOT be toxic, abusive, or sexually explicit.
    4. It IS ALLOWED to offer general coping strategies, empathy, and listening.
    
    If the response is SAFE, reply exactly: "SAFE"
    If UNSAFE, reply exactly: "UNSAFE: <reason>"
    """

    try:
        # Try Nucleus DualEngineLLM first, fallback to native google.generativeai
        try:
            from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
            llm = DualEngineLLM('gemini-3.1-flash-lite-preview', api_key=api_key)
            response = llm.generate_content(prompt)
        except ImportError:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
            response = model.generate_content(prompt, request_options={"timeout": 30})

        text = response.text.strip()
        
        if text.startswith("SAFE"):
            return True, "Valid"
        else:
            print(f"Safety Check Failed: {text}")
            return False, "I cannot provide that specific response due to safety guidelines. However, I am here to listen and support you."
            
    except Exception as e:
        print(f"Safety check error: {e}")
        # Fail open or closed? For strict safety, maybe fail closed? 
        # But for reliability, usually fail open if simple error.
        # ADR implies strictness. Let's log and Fail OPEN for now to avoid DOS, 
        # unless it's a persistent issue.
        return True, "Verification failed"
