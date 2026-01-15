#!/usr/bin/env python3
"""
verify_sandbox.py

Verification script for Phase 57: Chat 19 - The Sandbox.
Tests PluginLoader v2 (Air Gap by Default).
"""

import os
import sys
import logging
import shutil
import json
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.plugin_loader import PluginLoader
from mcp_server_nucleus.runtime.identity.manifest import AgentManifest, AgentIdentity, Capability, CapabilityScope
from mcp_server_nucleus.runtime.budget import BudgetAuditor

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_SANDBOX")

TEST_BRAIN = Path("test_sandbox_brain")

def setup_env():
    if TEST_BRAIN.exists():
        shutil.rmtree(TEST_BRAIN)
    
    # Create structure
    (TEST_BRAIN / "tools" / "installed" / "agent.valid").mkdir(parents=True)
    (TEST_BRAIN / "ledger").mkdir()

    # Create dummy tools
    tool_code = """
from mcp_server_nucleus.runtime.capabilities.base import Capability
from typing import List, Dict, Any

class MockTool(Capability):
    def __init__(self, name):
        self._name = name
    
    @property
    def name(self): return self._name
    
    @property
    def description(self): return "Mock"
    
    def get_tools(self): return []
    
    def execute(self, params): return "Executed"
    
def get_capability():
    return MockTool("mock_tool")
"""
    # 1. Valid Tool (Installed in right place)
    (TEST_BRAIN / "tools" / "installed" / "agent.valid" / "valid_tool.py").write_text(tool_code.replace("mock_tool", "valid_tool"))
    
    # 2. Checkmate Tool (Rogue file in same dir, but NOT in manifest)
    (TEST_BRAIN / "tools" / "installed" / "agent.valid" / "rogue_tool.py").write_text(tool_code.replace("mock_tool", "rogue_tool"))
    
    # 3. Global Tool (Outside agent dir - should be ignored)
    (TEST_BRAIN / "tools" / "global_tool.py").write_text(tool_code.replace("mock_tool", "global_tool"))

    return BudgetAuditor(TEST_BRAIN)

def verify_sandbox_isolation():
    logger.info("Step 1: Verify Air Gap (Manifest Whitelist)...")
    
    auditor = setup_env()
    loader = PluginLoader(TEST_BRAIN, auditor)
    
    # Define Manifest that ONLY allows 'valid_tool'
    manifest = AgentManifest(
        agent=AgentIdentity(id="agent.valid", name="Valid", version="1.0.0", description="V", author="A", license="MIT"),
        capabilities=[
            # We treat the 'name' of the capability as the tool filename stem or defined name
            # In Phase 57, the Mainfest maps capabilities to python modules.
            # Simplified: checks if module name is in list or derived from manifest.
            # Let's say we pass a list of *module names* to load.
        ]
    )
    
    # We need to tell the loader WHAT to load for this agent.
    # In Phase 57, NukeLoader unpacks tools. 
    # PluginLoader should take an Agent ID and a list of authorized tool modules.
    
    # Load ONLY 'valid_tool'
    loaded_caps = loader.load_agent_tools(
        agent_id="agent.valid",
        authorized_modules=["valid_tool"] 
    )
    
    loaded_names = [c.name for c in loaded_caps]
    logger.info(f"Loaded: {loaded_names}")
    
    if "valid_tool" not in loaded_names:
        logger.error("❌ Failed to load valid_tool")
        return False
        
    if "rogue_tool" in loaded_names:
        logger.error("❌ SECURITY BREACH: Loaded rogue_tool (not in whitelist)")
        return False
        
    if "global_tool" in loaded_names:
        logger.error("❌ SECURITY BREACH: Loaded global_tool (outside sandbox)")
        return False
        
    logger.info("✅ Air Gap Verified: Only whitelisted tools loaded.")
    
    # Verify BudgetGuard Wrapper
    if "Budget: $0.0" not in loaded_caps[0].description:
         logger.error("❌ BudgetGuard not applied (Description missing budget info)")
         return False
         
    logger.info("✅ BudgetGuard Verified: Tool wrapped with default $0.00 limit.")
    return True

def main():
    try:
        if not verify_sandbox_isolation():
            sys.exit(1)
            
        logger.info("✨ ALL SANDBOX CHECKS PASSED ✨")
        # Cleanup
        if TEST_BRAIN.exists():
            shutil.rmtree(TEST_BRAIN)
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        # Cleanup
        if TEST_BRAIN.exists():
            shutil.rmtree(TEST_BRAIN)
        sys.exit(1)

if __name__ == "__main__":
    main()
