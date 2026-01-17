#!/usr/bin/env python3
"""
verify_researcher.py

Verification script for Phase 57: Chat 33 - The Second Agent.
Bootstraps @nucleus/researcher and tests Economy Integration.

Process:
1. Define Source (Manifest + Tools).
2. Publish .nuke Artifact.
3. Trust & Install.
4. Verify Runtime & Broker Integration.
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
from mcp_server_nucleus.runtime.broker import ContextBroker

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_RESEARCH")

TEST_RES_ROOT = Path("test_research_boot")

def setup_env():
    if TEST_RES_ROOT.exists():
        shutil.rmtree(TEST_RES_ROOT)
    TEST_RES_ROOT.mkdir()
    (TEST_RES_ROOT / "config").mkdir()
    (TEST_RES_ROOT / "ledger").mkdir()
    
    # Init lifecycle
    (TEST_RES_ROOT / "ledger" / "lifecycle.json").write_text("{}")
    
    return TEST_RES_ROOT

def create_researcher_source(root: Path):
    src = root / "src"
    src.mkdir()
    
    # 1. Manifest
    manifest = {
        "manifest_version": "1.0.0",
        "agent": {
            "id": "nucleus.core.researcher",
            "name": "Nucleus Researcher",
            "version": "1.0.0",
            "description": "Deep research specialist. Can browse the web and sell insights.",
            "author": "Nucleus Core Team",
            "license": "MIT"
        },
        "capabilities": [
            {
                "scope": "network",
                "reason": "Access to google.com for research",
                "domains": ["google.com", "wikipedia.org"]
            }
        ],
        "lifecycle": {
            "persistence": "persistent",
            "cleanup": "strict"
        }
    }
    (src / "manifest.json").write_text(json.dumps(manifest, indent=2))
    
    # 2. Tool: Market Publisher
    # We simulate a tool that knows how to talk to the Broker.
    # In reality, this might be injected, but here we import relative to runtime.
    tool_code = """
import sys
from pathlib import Path

# Hack to find the runtime for this test
# In prod, the runtime is in path
try:
    from mcp_server_nucleus.runtime.broker import ContextBroker
    from mcp_server_nucleus.runtime.capabilities.base import Capability
except ImportError:
    # Just a mock for syntax check if environment fails, but verify script puts it in path
    pass

class MarketTool(Capability):
    def __init__(self):
        self._name = "publish_insight"
        self._desc = "Publishes research to the market"
        
    @property
    def name(self): return self._name
    
    @property
    def description(self): return self._desc
    
    def get_tools(self):
        return [{"name": "publish_insight", "schema": {}}]

    def execute(self, params):
        # We need the brain path. For this MVP tool, we assume we know it or it's passed.
        # Let's assume the params contain 'brain_path' injected by the test, 
        # or we just assume a hardcoded test path for this verification script context.
        # To make it robust: The Tool shouldn't know internal paths. 
        # It should call a 'service'.
        # But for this simulation, we will instantiate a broker on the specific TEST path.
        
        brain_path_str = params.get("brain_path")
        topic = params.get("topic")
        content = params.get("content")
        
        broker = ContextBroker(Path(brain_path_str))
        listing_id = broker.publish_listing(
            provider_id="nucleus.core.researcher",
            topic=topic,
            description=f"Research on {topic}",
            content=content,
            price=15.0
        )
        return f"Published {listing_id}"

def get_capability():
    return MarketTool()
"""
    (src / "market_tool.py").write_text(tool_code)
    
    return src

def verify_researcher_boot():
    brain = setup_env()
    
    logger.info("--- Phase 1: Identity ---")
    km = KeyManager(brain)
    key_id = km.generate_key("nucleus_core") # Reusing core key identity concept
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
    src_dir = create_researcher_source(brain)
    dist_dir = brain / "dist"
    dist_dir.mkdir()
    
    artifact = publisher.publish(src_dir, dist_dir, key_id)
    
    logger.info("--- Phase 3: Install ---")
    installer = Installer(brain)
    manifest = installer.install_from_file(artifact)
    
    if not manifest or manifest.agent.id != "nucleus.core.researcher":
        logger.error("❌ Installation failed")
        return False
        
    logger.info("✅ Installed @nucleus/researcher")
    
    logger.info("--- Phase 4: Economy Integration ---")
    # Verify we can load the tool and use it to publish context
    auditor = BudgetAuditor(brain)
    loader = PluginLoader(brain, auditor=auditor)
    
    # Load the specific tool
    tools = loader.load_agent_tools(manifest.agent.id, ["market_tool"])
    
    if not tools:
        logger.error("❌ Failed to load market_tool")
        return False
        
    tool = tools[0] # This is the BudgetGuard wrapped tool
    logger.info(f"Loaded tool: {tool.name}")
    
    # GRANT BUDGET (Simulation of User Approval)
    tool.max_budget_usd = 1.0
    
    # Execute it
    # We inject brain_path so the tool can find the broker (Mocking Service Injection)
    result = tool.execute({
        "brain_path": str(brain),
        "topic": "quantum_encryption",
        "content": "Q-Day is coming. Buy gold."
    })
    
    logger.info(f"Tool Result: {result}")
    
    if "Published list-" not in result:
        logger.error("❌ Tool failed to publish listing")
        return False
        
    # Verify Broker State
    broker = ContextBroker(brain)
    listings = broker.search_listings("quantum")
    
    if len(listings) == 0:
        logger.error("❌ Listing not found in Broker")
        return False
        
    logger.info(f"✅ Found listing in Market: {listings[0].topic}")
    return True

def main():
    try:
        if not verify_researcher_boot():
            sys.exit(1)
            
        logger.info("✨ RESEARCHER BOOT COMPLETE ✨")
        if TEST_RES_ROOT.exists():
            shutil.rmtree(TEST_RES_ROOT)
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if TEST_RES_ROOT.exists():
            shutil.rmtree(TEST_RES_ROOT)
        sys.exit(1)

if __name__ == "__main__":
    main()
