#!/usr/bin/env python3
"""
Execution Swarm Runner (Phase 5.3)
==================================
CLI tool to spawn the Execution Swarm (Tech Lead + Developer) to build features.
Takes an IMPLEMENTATION_PLAN.md and executes it.

Usage:
    python scripts/execution_swarm.py --plan IMPLEMENTATION_PLAN.md
    python scripts/execution_swarm.py --plan IMPLEMENTATION_PLAN_MOCK.md --test
"""

import os
import sys
import json
import argparse
import asyncio
import nest_asyncio
from pathlib import Path
from typing import List, Dict, Any

# Apply nest_asyncio
nest_asyncio.apply()

# Add Nucleus Source to Path
PROJECT_ROOT = Path(__file__).parent.parent
NUCLEUS_SRC = PROJECT_ROOT / "mcp-server-nucleus" / "src"
sys.path.append(str(NUCLEUS_SRC))

try:
    from mcp_server_nucleus.runtime.factory import ContextFactory
    from mcp_server_nucleus.runtime.agent import EphemeralAgent
    from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
    from mcp_server_nucleus.runtime.capabilities.base import Capability
except ImportError as e:
    print(f"❌ Error importing Nucleus: {e}")
    sys.exit(1)

# ============================================================
# MOCK LLM (For Testing)
# ============================================================
class MockLLM:
    def __init__(self, role: str = "generic"):
        self.role = role
    
    def generate_content(self, prompt: str) -> Any:
        print(f">> [MockLLM:{self.role}] Generating response...")
        
        if self.role == "tech_lead":
            response_text = "I have reviewed the plan. It looks solid. I have updated task.md.\nTERMINATE"
        elif self.role == "developer":
            # Simulate code editing tool call
            tool_call = {
                "tool": "code_write_file",
                "args": {
                 "path": "test_output.py",
                 "content": "print('Hello Swarm')"
                }
            }
            json_str = json.dumps(tool_call, indent=2)
            response_text = f"I am implementing the feature.\n```json\n{json_str}\n```"
        else:
            response_text = "Acknowledged. TERMINATE"

        return type('Response', (), {
            'text': response_text
        })

# ============================================================
# MAIN
# ============================================================
async def run_swarm(plan_path: str, test_mode: bool = False):
    print(f"🚀 Execution Swarm Initiated")
    print(f"   Plan: {plan_path}")
    print(f"   Test Mode: {test_mode}")
    
    # 1. Read Plan
    try:
        if test_mode and not os.path.exists(plan_path):
             plan_content = "# Mock Plan\n## Proposed Changes\n- Create test_output.py"
        else:
            with open(plan_path, "r") as f:
                plan_content = f.read()
    except Exception as e:
        print(f"❌ Error reading plan: {e}")
        return

    # 2. Initialize Factory
    brain_path = PROJECT_ROOT / ".brain"
    factory = ContextFactory(brain_path=brain_path)
    
    # ============================================================
    # STEP 1: TECH LEAD (Planning & Breakdown)
    # ============================================================
    print("\n🔹 Step 1: Tech Lead is processing the plan...")
    
    context_tl = factory.create_context_for_persona(
        session_id="exec-swarm-tl",
        persona_name="tech_lead",
        intent=f"Implementation Plan:\n{plan_content}\n\nReview this plan and break it down into tasks in task.md."
    )
    
    # Initialize LLM
    if test_mode:
        llm_tl = MockLLM("tech_lead")
    else:
        llm_tl = DualEngineLLM()

    agent_tl = EphemeralAgent(context_tl, model=llm_tl)
    log_tl = await agent_tl.run()
    print(log_tl)

    # ============================================================
    # STEP 2: DEVELOPER (Execution)
    # ============================================================
    print("\n🔹 Step 2: Developer is executing the verified tasks...")
    
    # In a real loop, we would parse task.md. 
    # For now, we pass the plan as the context and ask to execute "Proposed Changes".
    
    context_dev = factory.create_context_for_persona(
        session_id="exec-swarm-dev",
        persona_name="developer",
        intent=f"The Tech Lead has approved this plan:\n{plan_content}\n\nExecute the 'Proposed Changes' section. Write code."
    )
    
    # Developer needs CodeOps (should be in persona default, but let's verify/inject if needed)
    # Factory loads capabilities from persona definition. Developer has CodeOps.
    
    if test_mode:
        llm_dev = MockLLM("developer")
    else:
        llm_dev = DualEngineLLM()

    agent_dev = EphemeralAgent(context_dev, model=llm_dev)
    log_dev = await agent_dev.run()
    print(log_dev)

    print("\n✅ Execution Swarm Sequence Complete.")

def main():
    parser = argparse.ArgumentParser(description="Run the Execution Swarm")
    parser.add_argument("--plan", default="IMPLEMENTATION_PLAN_MOCK.md", help="Path to IMPLEMENTATION_PLAN.md (Default: Mock)")
    parser.add_argument("--test", action="store_true", help="Run in test mode (Mock LLM)")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_swarm(args.plan, args.test))
    except KeyboardInterrupt:
        print("\n🛑 Swarm halted by user.")

if __name__ == "__main__":
    main()
