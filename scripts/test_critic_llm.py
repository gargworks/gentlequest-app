#!/usr/bin/env python3
"""
MDR_002 Critic Loop Test
========================
Verifies that the Critic correctly intercepts text output and forces tool usage.

Usage: GEMINI_API_KEY=... python3 test_critic_llm.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
SERVER_SRC = PROJECT_ROOT / "mcp-server-nucleus" / "src"
sys.path.insert(0, str(SERVER_SRC))

try:
    from google import genai
    from mcp_server_nucleus.runtime.factory import ContextFactory
    from mcp_server_nucleus.runtime.agent import EphemeralAgent
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_critic_loop():
    """Test that Critic enforces tool usage for Librarian persona"""
    
    print("=" * 60)
    print("MDR_002 CRITIC LOOP TEST")
    print("=" * 60)
    
    # 1. Configure Gemini with new Client API
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return False
    
    client = genai.Client(api_key=api_key)
    
    print(f"✅ Gemini configured")
    
    # 2. Create Factory and Context
    factory = ContextFactory()
    
    # Intent that should trigger Librarian persona
    intent = "Scan the brain artifacts and archive stale items"
    
    context = factory.create_context(
        session_id="critic-test-001",
        intent=intent
    )
    
    print(f"✅ Persona: {context['persona']}")
    print(f"✅ Tools: {[t['name'] for t in context['tools']]}")
    print(f"✅ System Prompt (excerpt):")
    print(context['system_prompt'][:300])
    print("...")
    
    # 3. Spawn Agent (Note: agent.py still uses old API internally - wait, Agent uses LLM Client now)
    # We should use DualEngineLLM to wrap the model for EphemeralAgent if it expects a model object.
    # EphemeralAgent likely expects a legacy model object if it hasn't been updated.
    # Let's check: EphemeralAgent usually takes a model. If we pass DualEngineLLM, it might work if duck-typed.
    
    from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
    model = DualEngineLLM("gemini-2.5-flash", api_key=api_key)
    
    # We need to make sure EphemeralAgent can handle DualEngineLLM.
    # If EphemeralAgent calls generate_content, it should match.
    agent = EphemeralAgent(model=model, context=context)
    
    print("\n" + "=" * 60)
    print("RUNNING AGENT (LLM MODE)")
    print("=" * 60 + "\n")
    
    result = await agent.run()
    
    print("\n" + "=" * 60)
    print("AGENT OUTPUT")
    print("=" * 60)
    print(result)
    
    # 4. Check if Critic was invoked
    if "[Critic]" in result:
        print("\n✅ PASS: Critic was invoked!")
        return True
    elif "Tool detected" in result or "Tool Result" in result:
        print("\n✅ PASS: Tool was called (Critic not needed)")
        return True
    else:
        print("\n⚠️ UNKNOWN: Check output manually")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_critic_loop())
    print("\n" + "=" * 60)
    print(f"TEST RESULT: {'PASS ✅' if success else 'FAIL ❌'}")
    print("=" * 60)
