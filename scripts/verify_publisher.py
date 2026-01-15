#!/usr/bin/env python3
"""
verify_publisher.py

Verification script for Phase 57: Chat 25 - The Publisher.
Tests Publisher orchestration (Validation -> Packing -> Distribution).
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
from mcp_server_nucleus.runtime.identity.trust import TrustProfile
from mcp_server_nucleus.runtime.identity.keygen import KeyManager

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_PUBLISHER")

TEST_ROOT = Path("test_publisher_area")

def setup_env():
    if TEST_ROOT.exists():
        shutil.rmtree(TEST_ROOT)
    TEST_ROOT.mkdir()
    
    # 1. Create Key/Profile
    key_mgr = KeyManager(TEST_ROOT)
    key_id = key_mgr.generate_key("test_publisher")
    
    # 2. Create Agent Source
    agent_dir = TEST_ROOT / "my_agent"
    agent_dir.mkdir()
    
    manifest = {
        "agent": {
            "id": "agent.test.published",
            "name": "Published Agent",
            "version": "1.0.0",
            "description": "Test Agent",
            "author": "Test Publisher",
            "license": "MIT"
        },
        "capabilities": [],
        "lifecycle": {}
    }
    
    (agent_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (agent_dir / "tool.py").write_text("print('hello')")
    
    return Publisher(TEST_ROOT, key_mgr), agent_dir, key_id

def verify_publish_flow():
    logger.info("Step 1: Test Publish Flow...")
    
    publisher, agent_dir, key_id = setup_env()
    
    # Output dir for artifacts
    dist_dir = TEST_ROOT / "dist"
    dist_dir.mkdir()
    
    try:
        artifact_path = publisher.publish(
            agent_source=agent_dir,
            output_dir=dist_dir,
            key_id=key_id,
            private=True
        )
        
        if not artifact_path.exists():
            logger.error("❌ Artifact file not created")
            return False
            
        if not str(artifact_path).endswith(".nuke"):
            logger.error(f"❌ Invalid extension: {artifact_path}")
            return False
            
        logger.info(f"✅ Successfully created artifact: {artifact_path.name}")
        
        # Verify Manifest update (if any) or check logs?
        # For Phase 57, ensure valid nuke file size > 0
        if artifact_path.stat().st_size == 0:
            logger.error("❌ Artifact is empty")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Publish failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    try:
        if not verify_publish_flow():
            sys.exit(1)
            
        logger.info("✨ ALL PUBLISHER CHECKS PASSED ✨")
        if TEST_ROOT.exists():
            shutil.rmtree(TEST_ROOT)
        sys.exit(0)
        
    except ImportError as e:
        logger.error(f"❌ Import Error: {e}. Implementation missing?")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        if TEST_ROOT.exists():
            shutil.rmtree(TEST_ROOT)
        sys.exit(1)

if __name__ == "__main__":
    main()
