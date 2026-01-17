#!/usr/bin/env python3
"""
Genesis Swarm Runner (Phase 5.2)
================================
CLI tool to spawn the Genesis Swarm (Architect/Product Owner) for planning.
Injects a local 'PlanWriterOps' capability to allow the agent to save the plan.

Usage:
    python scripts/genesis_swarm.py --mission "Add Dark Mode"
    python scripts/genesis_swarm.py --mission "Refactor Auth" --persona "product_owner"
"""

import os
import sys
import json
import argparse
import asyncio
import nest_asyncio
from pathlib import Path
from typing import List, Dict, Any

# Apply nest_asyncio for smooth async execution in scripts
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
# LOCAL CAPABILITY: PlanWriterOps
# ============================================================
class PlanWriterOps(Capability):
    """
    Local capability to allow Genesis Swarm to write the Implementation Plan.
    """
    @property
    def name(self) -> str:
        return "plan_writer_ops"

    @property
    def description(self) -> str:
        return "Tools for saving the architecture/implementation plan."

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "save_implementation_plan",
                "description": "Save the generated implementation plan to IMPLEMENTATION_PLAN.md.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The full markdown content of the plan."
                        },
                        "filename": {
                            "type": "string",
                            "description": "Optional filename (default: IMPLEMENTATION_PLAN.md)"
                        }
                    },
                    "required": ["content"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, args: Dict) -> str:
        if tool_name == "save_implementation_plan":
            content = args.get("content")
            filename = args.get("filename", "IMPLEMENTATION_PLAN.md")
            
            # Determine path (In .brain or root? Usually root for active plan)
            # Defaulting to .brain artifacts for safety, but user might want root.
            # Let's put it in the Brain artifacts folder under current conversation if possible,
            # or just project root if not specifying conversation.
            
            # For this script, let's save to PROJECT_ROOT for immediate visibility involved in the task.
            # Or better: Save to PROJECT_ROOT so it overwrites the active plan.
            file_path = PROJECT_ROOT / filename
            
            try:
                # Add header if missing
                if not content.startswith("#"):
                    content = f"# Implementation Plan: {filename}\n\n{content}"
                
                with open(file_path, "w") as f:
                    f.write(content)
                    
                return f"✅ Plan saved successfully to {file_path}"
            except Exception as e:
                return f"❌ Error saving plan: {e}"
                
        return f"Tool {tool_name} not found."

# ============================================================
# MOCK LLM (For Testing)
# ============================================================
class MockLLM:
    def __init__(self, *args, **kwargs):
        pass
    
    def generate_content(self, prompt: str) -> Any:
        # Simulate a refined plan response
        print(">> [MockLLM] Generating outcome...")
        
        tool_call = {
            "tool": "save_implementation_plan",
            "args": {
                "content": "# Mock Plan\n\n## Goal\nTest the Genesis Protocol.\n\n## Changes\n- None.",
                "filename": "IMPLEMENTATION_PLAN_MOCK.md"
            }
        }
        
        json_str = json.dumps(tool_call, indent=2)
        response_text = f"I have analyzed the mission and created the plan.\n```json\n{json_str}\n```"
        
        return type('Response', (), {
            'text': response_text
        })

# ============================================================
# MAIN
# ============================================================
async def run_swarm(mission: str, persona: str, test_mode: bool = False):
    print(f"🚀 Genesis Swarm Initiated")
    print(f"   Mission: {mission}")
    print(f"   Lead: {persona}")
    print(f"   Test Mode: {test_mode}")
    
    # 1. Initialize Factory and Brain
    brain_path = PROJECT_ROOT / ".brain"
    factory = ContextFactory(brain_path=brain_path)
    
    # 2. Register Local Capability
    factory.register(PlanWriterOps())
    
    # 3. Create Context
    # We want to force the 'genesis' protocol usage.
    # The 'architect' agent has a .brain/agents/architect.md file.
    # We also want to inject the mission as the INTENT.
    
    # Load the specific swarm protocol to append to system prompt?
    # Or rely on 'Architect' loading its own prompt and receiving the mission?
    # Using 'create_context_for_persona' which respects agent.md
    
    context = factory.create_context_for_persona(
        session_id="genesis-cli-run",
        persona_name=persona,
        intent=f"MISSION: {mission}\n\nExecute the Genesis Swarm Protocol to create an IMPLEMENTATION_PLAN.md."
    )
    
    # MANUAL INJECTION of PlanWriterOps (since Architect doesn't have it by default)
    plan_ops = PlanWriterOps()
    # Check if not already running (factory might have added it if we modified persona, but we didn't)
    if plan_ops.name not in context["capabilities"]:
        context["capabilities"].append(plan_ops.name)
        context["capability_instances"].append(plan_ops)
        context["tools"].extend(plan_ops.get_tools())
        print(f"   + Injected {plan_ops.name} into context")
    
    # 4. Initialize LLM
    if test_mode:
        llm = MockLLM()
    else:
        try:
            llm = DualEngineLLM() 
        except Exception as e:
            print(f"⚠️ Failed to init LLM: {e}")
            return

    # 5. Run Agent
    agent = EphemeralAgent(context, model=llm)
    log = await agent.run()
    
    print("\n--- Mission Report ---")
    # Check if tool was called in the log?
    # Simple debug print
    print(log)
    print("----------------------")

def main():
    parser = argparse.ArgumentParser(description="Run the Genesis Swarm")
    parser.add_argument("--mission", required=True, help="The mission description")
    parser.add_argument("--persona", default="architect", help="The persona to lead (architect/product_owner)")
    parser.add_argument("--test", action="store_true", help="Run in test mode (Mock LLM)")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_swarm(args.mission, args.persona, args.test))
    except KeyboardInterrupt:
        print("\n🛑 Swarm halted by user.")

if __name__ == "__main__":
    main()
