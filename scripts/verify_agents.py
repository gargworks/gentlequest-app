#!/usr/bin/env python3
"""
scripts/verify_agents.py

Verification harness for Phase 57 (Nucleus Marketplace).
Scans .brain/tools/ for Sovereign Agents and validates their integrity.
"""

import sys
import os
import importlib.util
import inspect
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "mcp-server-nucleus" / "src"))

def verify_agent_module(file_path: Path) -> dict:
    """
    Loads a python module and checks for SovereignAgent compliance.
    Returns a dict with 'status' (PASS/FAIL) and 'details'.
    """
    module_name = file_path.stem
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec or not spec.loader:
            return {"status": "FAIL", "details": "Could not create module spec"}
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Check for Agent class or instance
        # Standard: Look for a class inheriting from SovereignAgent or an instance named 'agent'
        
        if not hasattr(module, "agent"):
            return {"status": "FAIL", "details": "Module missing 'agent' instance export"}
            
        agent = module.agent
        
        # Validation Checks
        if not hasattr(agent, "name") or not agent.name.startswith("@nucleus/"):
            return {"status": "FAIL", "details": f"Invalid agent name: {getattr(agent, 'name', 'N/A')}"}
            
        if not hasattr(agent, "description") or len(agent.description) < 10:
            return {"status": "FAIL", "details": "Description too short or missing"}
            
        if not hasattr(agent, "tools") or not isinstance(agent.tools, list):
            return {"status": "FAIL", "details": "Missing 'tools' list"}
            
        return {
            "status": "PASS",
            "details": f"Tools: {len(agent.tools)} | {agent.description[:50]}..."
        }

    except Exception as e:
        return {"status": "FAIL", "details": f"Exception: {str(e)}"}

def main():
    tools_dir = PROJECT_ROOT / ".brain" / "tools"
    if not tools_dir.exists():
        print(f"❌ Tools directory not found: {tools_dir}")
        sys.exit(1)

    print(f"🔍 Verifying Sovereign Agents in {tools_dir}...\n")
    
    # Header
    print(f"{'File':<30} | {'Agent Name':<30} | {'Status':<10} | {'Details'}")
    print("-" * 100)

    passed = 0
    failed = 0
    
    # Files to ignore
    ignore_files = ["__init__.py", "echo_tool.py"]

    for file_path in tools_dir.glob("*.py"):
        if file_path.name in ignore_files:
            continue
            
        result = verify_agent_module(file_path)
        
        # Try to extract name purely for display if load failed
        agent_name = "Unknown"
        if result["status"] == "PASS":
            agent_name = sys.modules[file_path.stem].agent.name
        
        print(f"{file_path.name:<30} | {agent_name:<30} | {result['status']:<10} | {result['details']}")
        
        if result["status"] == "PASS":
            passed += 1
        else:
            failed += 1

    print("-" * 100)
    print(f"\nSummary: Passed: {passed} | Failed: {failed}")
    
    if failed > 0:
        sys.exit(1)
    
if __name__ == "__main__":
    main()
