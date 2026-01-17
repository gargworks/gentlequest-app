import sys
from pathlib import Path

import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))
# Mock fastmcp logic again or reuse robust init
# For now, we rely on the robust init we added earlier

from mcp_server_nucleus.runtime.factory import ContextFactory
from mcp_server_nucleus.runtime.agent import EphemeralAgent

def run_intent(intent):
    print(f"\n>> Intent: {intent}")
    factory = ContextFactory()
    context = factory.create_context(intent)
    
    # We need to manually inject the tool call logic into the agent for this verification
    # because the agent's run() method currently has hardcoded heuristics for "brain" and "render".
    # We need to update Agent to be generic or update the heuristic.
    # Let's update the Agent heuristic first in the Agent class, 
    # but for now I will just call the capability directly to verify the Logic.
    
    # Actually, let's trust the Factory produced the capability instance
    # and call it.
    
    cap = next((c for c in context['capability_instances'] if c.name == 'depth_tracker'), None)
    if not cap:
        print("❌ Depth capability not found in context")
        return

    # Mock Agent execution of the tool matching the intent
    if "push" in intent:
        print(cap.execute_tool("brain_depth_push", {"topic": "Refining Verification Strategy"}))
    elif "show" in intent:
         print(cap.execute_tool("brain_depth_show", {}))
    elif "pop" in intent:
         print(cap.execute_tool("brain_depth_pop", {}))
    elif "reset" in intent:
         print(cap.execute_tool("brain_depth_reset", {}))

def main():
    print("=== Depth Tracker Verification ===")
    
    # 1. Reset
    run_intent("reset depth")
    
    # 2. Push Level 1
    run_intent("track depth: push topic 'Phase 5 Specs'")
    
    # 3. Push Level 2
    run_intent("track depth: push topic 'Implementing Depth Tracker'")
    
    # 4. Show
    run_intent("show depth map")
    
    # 5. Pop
    run_intent("pop depth")
    
if __name__ == "__main__":
    main()
