#!/usr/bin/env python3
"""
verify_team.py

Verification script for Phase 57: Chat 26 - The Team.
Tests TeamSync configuration loading and validation.
"""

import os
import sys
import logging
import json
import shutil
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.team import TeamManager, TeamConfig

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_TEAM")

TEST_BRAIN = Path("test_team_brain")

def setup_env():
    if TEST_BRAIN.exists():
        shutil.rmtree(TEST_BRAIN)
    (TEST_BRAIN / "config").mkdir(parents=True)
    
    # Create valid team config
    config = {
        "team_id": "team.nucleus.core",
        "name": "Nucleus Core Team",
        "registry_url": "https://registry.internal.nucleus.dev",
        "trusted_keys": [
            "key_fingerprint_123",
            "key_fingerprint_456"
        ],
        "policy": {
            "require_signed": True,
            "min_trust_level": "verified"
        }
    }
    
    (TEST_BRAIN / "config" / "team.json").write_text(json.dumps(config, indent=2))
    
    return TeamManager(TEST_BRAIN)

def verify_config_loading():
    logger.info("Step 1: Verify Team Config Loading...")
    
    manager = setup_env()
    config = manager.get_config()
    
    if not config:
        logger.error("❌ Failed to load team config")
        return False
        
    if config.team_id != "team.nucleus.core":
        logger.error(f"❌ Team ID mismatch: {config.team_id}")
        return False
        
    logger.info(f"✅ Loaded Team: {config.name}")
    return True

def verify_trust_roots():
    logger.info("Step 2: Verify Trust Roots...")
    
    manager = setup_env()
    roots = manager.get_trusted_roots()
    
    if len(roots) != 2:
        logger.error(f"❌ Expected 2 trust roots, got {len(roots)}")
        return False
        
    if "key_fingerprint_123" not in roots:
        logger.error("❌ Missing expected root key")
        return False
        
    logger.info("✅ Verified Trust Roots.")
    return True

def main():
    try:
        if not verify_config_loading():
            sys.exit(1)
            
        if not verify_trust_roots():
            sys.exit(1)
            
        logger.info("✨ ALL TEAM CHECKS PASSED ✨")
        if TEST_BRAIN.exists():
            shutil.rmtree(TEST_BRAIN)
        sys.exit(0)
        
    except ImportError as e:
        logger.error(f"❌ Import Error: {e}. Implementation missing?")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        if TEST_BRAIN.exists():
            shutil.rmtree(TEST_BRAIN)
        sys.exit(1)

if __name__ == "__main__":
    main()
