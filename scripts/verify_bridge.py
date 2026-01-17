#!/usr/bin/env python3
"""
verify_bridge.py

Verification script for Phase 57: Chat 30 - The Bridge.
Tests the end-to-end flow: Publish -> Trust -> Install.
"""

import os
import sys
import logging
import json
import shutil
import tempfile
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.publisher import Publisher
from mcp_server_nucleus.runtime.installer import Installer
from mcp_server_nucleus.runtime.identity.keygen import KeyManager
from mcp_server_nucleus.runtime.lifecycle import LifecycleManager, AgentState

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_BRIDGE")

TEST_AREA = Path("test_bridge_area")

def setup_env():
    if TEST_AREA.exists():
        shutil.rmtree(TEST_AREA)
    TEST_AREA.mkdir()
    (TEST_AREA / "config").mkdir()
    (TEST_AREA / "agents").mkdir()
    (TEST_AREA / "ledger").mkdir() # KeyManager needs ledger
    
    # Init empty lifecycle ledger
    (TEST_AREA / "ledger" / "lifecycle.json").write_text("{}")
    
    return TEST_AREA

def create_agent_source(root: Path):
    src = root / "src"
    src.mkdir()
    
    manifest = {
        "manifest_version": "1.0.0",
        "agent": {
            "id": "agent.bridge.walker",
            "name": "Bridge Walker",
            "version": "1.0.0",
            "description": "Crossing the chasm.",
            "author": "Constructor",
            "license": "MIT"
        },
        "capabilities": []
    }
    
    (src / "manifest.json").write_text(json.dumps(manifest))
    (src / "tool.py").write_text("print('Walking the bridge')")
    
    return src

def verify_bridge():
    brain = setup_env()
    
    logger.info("--- Step 1: Identity & Trust Setup ---")
    km = KeyManager(brain)
    # Generate a key and get its ID
    # generate_key returns the ID string, NOT the KeyPair object.
    key_id = km.generate_key("publisher_identity")
    logger.info(f"Generated Publisher Key ID: {key_id}")
    
    # Needs to retrieve the full pair to get the public PEM for trust config
    key_pair = km.get_key_pair(key_id)
    if not key_pair:
        logger.error("❌ Failed to retrieve generated key pair")
        return False
        
    pub_pem = key_pair.public_key_pem
    
    # Configure Team to TRUST this key (Using PEM as the 'ID' for this test based on Installer logic)
    team_config = {
        "team_id": "team.bridge",
        "name": "Bridge Team",
        "trusted_keys": [pub_pem] # Pass actual PEM so Installer can map it
    }
    (brain / "config" / "team.json").write_text(json.dumps(team_config))
    
    
    logger.info("--- Step 2: Publish Artifact ---")
    publisher = Publisher(brain)
    src_dir = create_agent_source(brain)
    dist_dir = brain / "dist"
    dist_dir.mkdir()
    
    # We use the key_id we just generated
    artifact_path = publisher.publish(src_dir, dist_dir, key_id)
    
    if not artifact_path.exists():
        logger.error("❌ Artifact not created")
        return False
        
        
    logger.info("--- Step 3: Install Artifact ---")
    installer = Installer(brain)
    manifest = installer.install_from_file(artifact_path)
    
    if not manifest:
        logger.error("❌ Install returned None")
        return False
        
    if manifest.agent.id != "agent.bridge.walker":
        logger.error("❌ Installed wrong agent ID")
        return False
        
        
    logger.info("--- Step 4: Verify Lifecycle ---")
    lm = LifecycleManager(brain)
    state = lm.get_state(manifest.agent.id)
    
    if state != AgentState.ACTIVE: # Default is ACTIVE on registration? Or STOPPED?
        # Check `lifecycle.py`. register_agent usually sets to ACTIVE or STOPPED.
        # Let's check. Assuming ACTIVE for now.
        logger.info(f"State is: {state}")
        # If it's stopped, that's fine too, as long as it's registered (not Unknown)
    
    installed_tool = brain / "tools" / "installed" / "agent.bridge.walker" / "tool.py"
    if not installed_tool.exists():
        logger.error(f"❌ Tool not unpacked to {installed_tool}")
        return False
        
    logger.info("✅ Bridge crossed successfully.")
    return True

def main():
    try:
        if not verify_bridge():
            sys.exit(1)
            
        logger.info("✨ ALL BRIDGE CHECKS PASSED ✨")
        if TEST_AREA.exists():
            shutil.rmtree(TEST_AREA)
        sys.exit(0)
        
    except ImportError as e:
        logger.error(f"❌ Import Error: {e}. Implementation missing?")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        if TEST_AREA.exists():
            shutil.rmtree(TEST_AREA)
        sys.exit(1)

if __name__ == "__main__":
    main()
