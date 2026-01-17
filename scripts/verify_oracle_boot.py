#!/usr/bin/env python3
"""
verify_oracle_boot.py

Verification script for Phase 61: Chat 35 - The Oracle Identity.
Bootstraps the Oracle Agent and tests its ability to read/evolve strategy.

Process:
1. Define Source (Manifest + Strategy Tool).
2. Publish .nuke Artifact.
3. Trust & Install.
4. Verify Strategy Read/Write Access.
"""

import os
import sys
import logging
import json
import shutil
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.publisher import Publisher
from mcp_server_nucleus.runtime.installer import Installer
from mcp_server_nucleus.runtime.identity.keygen import KeyManager
from mcp_server_nucleus.runtime.lifecycle import LifecycleManager, AgentState
from mcp_server_nucleus.runtime.plugin_loader import PluginLoader
from mcp_server_nucleus.runtime.budget import BudgetAuditor

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_ORACLE")

TEST_ORACLE_ROOT = Path("test_oracle_boot")
TEST_BRAIN_STRATEGY = TEST_ORACLE_ROOT / "strategy"

def setup_env():
    if TEST_ORACLE_ROOT.exists():
        shutil.rmtree(TEST_ORACLE_ROOT)
    TEST_ORACLE_ROOT.mkdir()
    (TEST_ORACLE_ROOT / "config").mkdir()
    (TEST_ORACLE_ROOT / "ledger").mkdir()
    (TEST_ORACLE_ROOT / "decisions").mkdir()
    TEST_BRAIN_STRATEGY.mkdir()
    
    # Create a dummy strategy file to read
    (TEST_BRAIN_STRATEGY / "DUMMY_PROTOCOL.md").write_text("# Dummy Protocol\nThis is a test.")
    
    # Init lifecycle
    (TEST_ORACLE_ROOT / "ledger" / "lifecycle.json").write_text("{}")
    
    return TEST_ORACLE_ROOT

def create_oracle_source(root: Path):
    src = root / "src"
    src.mkdir()
    
    # 1. Manifest
    # Note: Using ${BRAIN_PATH} substitution which strategy.py supports
    manifest = {
        "manifest_version": "1.0.0",
        "agent": {
            "id": "nucleus.core.oracle",
            "name": "The Oracle",
            "version": "1.0.0",
            "description": "Antifragile Co-Founder.",
            "author": "Nucleus Genesis",
            "license": "MIT"
        },
        "capabilities": [
            {
                "scope": "strategy",
                "reason": "Evolution",
                "paths": ["${BRAIN_PATH}/strategy"],
                "mode": "read_write"
            }
        ],
        "lifecycle": {
            "persistence": "immortal",
            "cleanup": "none"
        }
    }
    (src / "manifest.json").write_text(json.dumps(manifest, indent=2))
    
    # 2. Tool: Strategy Ops
    tool_code = """
import sys
from pathlib import Path
from mcp_server_nucleus.runtime.capabilities.strategy import StrategyTool

def get_capability():
    # We need to inject the config from somewhere. 
    # For now, we simulate the factory passing 'paths' via ENV or similar?
    # Actually, in this test, we construct it manually since PluginLoader v2 
    # instantiates the module but doesn't pass args to 'get_capability' usually.
    # But wait, StrategyTool needs 'brain_path' and 'allowed_paths'.
    
    # HACK for MVP/Test: We hardcode the test path or rely on an environment var injection
    # In a real system, PluginLoader would pass context.
    
    # Let's assume the test sets an env var "NUCLEUS_BRAIN_PATH"
    import os
    brain_path = Path(os.environ.get("NUCLEUS_BRAIN_PATH", "."))
    
    # And allowed paths from Manifest? 
    # The tool code "should" know what it allows, OR the runtime enforces it.
    # Here we just pass the strategy dir.
    allowed = ["${BRAIN_PATH}/strategy"]
    
    return StrategyTool(brain_path, allowed)
"""
    (src / "strategy_ops.py").write_text(tool_code)
    
    return src

def verify_oracle_boot():
    brain = setup_env()
    
    # Set Env Var for the tool to find the brain
    os.environ["NUCLEUS_BRAIN_PATH"] = str(brain.absolute())
    
    logger.info("--- Phase 1: Identity ---")
    km = KeyManager(brain)
    key_id = km.generate_key("nucleus_core")
    key_pair = km.get_key_pair(key_id)
    
    # Configure Trust
    team_config = {
        "team_id": "nucleus.core",
        "name": "Nucleus Core Team",
        "trusted_keys": [key_pair.public_key_pem]
    }
    (brain / "config" / "team.json").write_text(json.dumps(team_config))
    
    logger.info("--- Phase 2: Build & Publish ---")
    publisher = Publisher(brain)
    src_dir = create_oracle_source(brain)
    dist_dir = brain / "dist"
    dist_dir.mkdir()
    
    artifact = publisher.publish(src_dir, dist_dir, key_id)
    
    logger.info("--- Phase 3: Install ---")
    installer = Installer(brain)
    manifest = installer.install_from_file(artifact)
    
    if not manifest or manifest.agent.id != "nucleus.core.oracle":
        logger.error("❌ Installation failed")
        return False
        
    logger.info("✅ Installed @nucleus/oracle")
    
    logger.info("--- Phase 4: Strategy Capability Verification ---")
    auditor = BudgetAuditor(brain)
    loader = PluginLoader(brain, auditor=auditor)
    
    # Load the tool
    tools = loader.load_agent_tools(manifest.agent.id, ["strategy_ops"])
    
    if not tools:
        logger.error("❌ Failed to load strategy_ops")
        return False
        
    tool = tools[0] # BudgetGuard wrapped
    tool.max_budget_usd = 1000.0 # Unlimited budget for Oracle
    
    logger.info(f"Loaded tool: {tool.name}")
    
    # 1. Test READ
    logger.info("Testing READ...")
    result_read = tool.execute({
        "filename": "strategy/DUMMY_PROTOCOL.md"
    })
    
    if "This is a test." not in result_read:
        logger.error(f"❌ READ failed: {result_read}")
        return False
    logger.info("✅ READ Successful")
    
    # 2. Test EVOLVE (WRITE)
    logger.info("Testing EVOLVE...")
    new_content = "# Dummy Protocol v2\nEvolved."
    result_write = tool.execute({
        "filename": "strategy/DUMMY_PROTOCOL.md",
        "content": new_content,
        "reason": "Evolution Test"
    })
    
    if "evolved" not in result_write:
        logger.error(f"❌ EVOLVE failed: {result_write}")
        return False
        
    # Verify file changed
    if (TEST_BRAIN_STRATEGY / "DUMMY_PROTOCOL.md").read_text() != new_content:
        logger.error("❌ File content verification failed")
        return False
        
    logger.info("✅ EVOLVE Successful")
    
    return True

def main():
    try:
        if not verify_oracle_boot():
            sys.exit(1)
            
        logger.info("✨ ORACLE BOOT COMPLETE ✨")
        if TEST_ORACLE_ROOT.exists():
            shutil.rmtree(TEST_ORACLE_ROOT)
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if TEST_ORACLE_ROOT.exists():
            shutil.rmtree(TEST_ORACLE_ROOT)
        sys.exit(1)

if __name__ == "__main__":
    main()
