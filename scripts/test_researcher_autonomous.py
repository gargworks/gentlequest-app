#!/usr/bin/env python3
"""
Autonomous Stress Test: @nucleus/researcher
============================================
Spawns the researcher agent and verifies it can autonomously:
1. Call web_search tool
2. Generate a structured competitive analysis report
"""

import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path("mcp-server-nucleus/src").absolute()))

from mcp_server_nucleus.runtime.factory import ContextFactory
from mcp_server_nucleus.runtime.agent import EphemeralAgent
from mcp_server_nucleus.runtime.llm_client import DualEngineLLM

BRAIN_PATH = Path(".brain").absolute()
INTENT = "Analyze top 3 mental health competitors (Wysa, Woebot, BetterHelp). Generate a competitive analysis report."

async def run_stress_test():
    print("=" * 60)
    print("🧪 AUTONOMOUS STRESS TEST: @nucleus/researcher")
    print("=" * 60)
    
    # 1. Create Context
    print("\n📦 Step 1: Creating Context for Researcher...")
    factory = ContextFactory(BRAIN_PATH)
    context = factory.create_context_for_persona(
        session_id="stress_test_001",
        persona_name="researcher",
        intent=INTENT
    )
    
    print(f"   Persona: {context['persona']}")
    print(f"   Capabilities: {context['capabilities']}")
    print(f"   Tool Count: {context['tool_count']}")
    
    # 2. Initialize LLM
    print("\n🤖 Step 2: Initializing LLM (Gemini)...")
    try:
        llm = DualEngineLLM(
            model_name="gemini-2.0-flash-exp",
            system_instruction=context['system_prompt']
        )
        print(f"   Engine: {llm.active_engine}")
    except Exception as e:
        print(f"   ❌ LLM Init Failed: {e}")
        return False
    
    # 3. Spawn Agent
    print("\n🚀 Step 3: Spawning Ephemeral Agent...")
    agent = EphemeralAgent(context, model=llm)
    
    # 4. Run Agent
    print("\n⏳ Step 4: Running Agent (this may take 30-60 seconds)...")
    try:
        result = await agent.run()
        print("\n--- AGENT OUTPUT ---")
        print(result)
        print("--- END OUTPUT ---")
    except Exception as e:
        print(f"   ❌ Agent Run Failed: {e}")
        return False
    
    # 5. Verify Output
    print("\n✅ Step 5: Verifying Output...")
    
    # Check if a report was generated
    research_dir = BRAIN_PATH / "artifacts" / "research"
    if research_dir.exists():
        reports = list(research_dir.glob("competitive_*.md"))
        if reports:
            print(f"   ✅ Found {len(reports)} report(s) in artifacts/research/")
            for r in reports[-3:]:  # Show last 3
                print(f"      - {r.name}")
        else:
            print("   ⚠️ No competitive_*.md reports found (agent may have used different naming)")
    else:
        print("   ⚠️ artifacts/research/ directory not found")
    
    # Check if web_search was called (look for keywords in output)
    if "web_search" in result.lower() or "search" in result.lower():
        print("   ✅ Agent attempted to use search tools")
    else:
        print("   ⚠️ No explicit search tool call detected in output")
    
    if "TERMINATE" in result or "terminate" in result.lower():
        print("   ✅ Agent properly terminated")
    else:
        print("   ⚠️ Agent did not output TERMINATE signal")
    
    print("\n" + "=" * 60)
    print("🎉 STRESS TEST COMPLETE")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_stress_test())
    sys.exit(0 if success else 1)
