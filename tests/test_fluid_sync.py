
import sys
import os
import asyncio
import json
from pathlib import Path
from typing import Any

# Add src to path
sys.path.append(os.path.abspath("mcp-server-nucleus/src"))
sys.path.append(os.path.abspath("scripts"))

# --------------------------------------------------------------------------------
# MOCK LLM to bypass missing API Keys in Test Output
# --------------------------------------------------------------------------------

class MockLLM:
    def __init__(self, *args, **kwargs):
        pass
        
    def generate_content(self, prompt: str, **kwargs) -> Any:
        # Simple heuristic to simulate agent decisions based on prompt keywords
        
        # 1. Synthesizer Response (User Intent -> Delegate)
        if "Synthesizer" in prompt:
            return type('Response', (), {
                'text': '''I see a user intent for research. I will delegate this to the Researcher.
```json
{
  "tool": "brain_delegate_task",
  "args": {
    "persona": "researcher",
    "intent": "Research the latest Agentic AI Frameworks."
  }
}
```'''
            })
            
        # 2. Researcher Response (Research -> Web Search)
        elif "Researcher" in prompt:
             return type('Response', (), {
                'text': '''I will search for the latest frameworks.
```json
{
  "tool": "web_search",
  "args": {
    "query": "latest agentic ai frameworks 2025"
  }
}
```'''
            })
        
        return type('Response', (), {'text': 'Mock Response'})

class MockDualEngineLLM(MockLLM): # Alias
    pass

# Patch the orchestrator's import to use MockLLM
import mcp_server_nucleus.runtime.llm_client
mcp_server_nucleus.runtime.llm_client.DualEngineLLM = MockDualEngineLLM

# Imports after Patching (order matters if they import llm_client at top level)?
# Actually, llm_client is imported inside process_events in orchestrator.py (as per my modification),
# so patching the module here is safe.
from mcp_server_nucleus.runtime.event_stream import emit_event, EventSeverity
from orchestrator import process_events, BRAIN_PATH
from mcp_server_nucleus.runtime.factory import ContextFactory

async def test_fluid_sync():
    print("🧪 Testing Fluid Sync (User -> Orchestrator -> Agent) [MOCK MODE]...")
    
    # 1. Emit User Intent
    print("   Emitting 'user_intent' event: 'Research the latest Agentic AI Frameworks'")
    emit_event(
        brain_path=BRAIN_PATH,
        event_type="user_intent",
        emitter="user_via_cli",
        payload={
            "description": "Research the latest Agentic AI Frameworks.", 
            "priority": "P2"
        },
        severity=EventSeverity.ROUTINE
    )
    
    # 2. Run Orchestrator (Pass 1 - Spawns Synthesizer)
    print("   Running Orchestrator (Pass 1)...")
    factory = ContextFactory(brain_path=BRAIN_PATH)
    
    # We expect Synthesizer to run and call 'brain_delegate_task'
    summary1 = await process_events(factory)
    
    print(f"   Pass 1 Spawned: {[s['agent'] for s in summary1['agents_spawned']]}")
    
    # Check logs for delegation
    # With MockLLM, Synthesizer should have called 'brain_delegate_task'.
    # This tool executes the SUB-AGENT (Researcher) synchronously via `nest_asyncio` (if enabled in brain_ops).
    # So we should see Researcher logs inside Synthesizer logs?
    
    # Let's inspect logs
    synth_logs = [s.get('log', '') for s in summary1['agents_spawned'] if 'ynthesizer' in s['agent']]
    full_log = "\n".join(synth_logs)
    
    if "Delegation Complete" in full_log:
        print("✅ Synthesizer Delegated Successfully.")
    else:
        print("❌ Synthesizer did not delegate.")
        print("--- Log Content ---")
        print(full_log[:1000])

    if "web_search" in full_log:
         print("✅ Researcher executed web_search (via Delegation).")
         print("🚀 FLUID SYNC VERIFIED (Mocked)!")
    else:
         print("⚠️ Researcher execution not found in logs.")

if __name__ == "__main__":
    asyncio.run(test_fluid_sync())
