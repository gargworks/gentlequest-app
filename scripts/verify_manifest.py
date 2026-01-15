#!/usr/bin/env python3
"""
verify_manifest.py

Verification script for Phase 57: Chat 16 - The Manifest.
Tests the AgentManifest Schema and Validator.
"""

import os
import sys
import json
import logging
import yaml
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.identity.manifest import ManifestValidator, AgentManifest

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_MANIFEST")

def create_valid_manifest():
    return {
        "manifest_version": "1.0.0",
        "agent": {
            "id": "nucleus.core.ops",
            "name": "Nucleus Ops",
            "version": "1.0.0",
            "description": "Secure Operations Automation Agent",
            "author": "Antigravity",
            "license": "MIT"
        },
        "capabilities": [
            {
                "scope": "network",
                "reason": "Required to check AWS status",
                "domains": ["aws.amazon.com"]
            },
            {
                "scope": "filesystem",
                "reason": "Required to read local config",
                "paths": ["~/.aws/config"],
                "mode": "read"
            }
        ],
        "lifecycle": {
            "persistence": "session",  # or 'persistent'
            "cleanup": "strict"
        }
    }

def verify_valid_manifest():
    """Test Step 1: Validate a Correct Manifest"""
    logger.info("Step 1: Testing Valid Manifest...")
    
    data = create_valid_manifest()
    
    try:
        manifest = ManifestValidator.validate(data)
        logger.info(f"✅ Manifest '{manifest.agent.id}' validated successfully.")
        return True
    except Exception as e:
        logger.error(f"❌ Valid manifest failed validation: {e}")
        return False

def verify_invalid_manifest_missing_field():
    """Test Step 2: Validate Manifest with Missing Required Field"""
    logger.info("Step 2: Testing Missing Field (Expected Failure)...")
    
    data = create_valid_manifest()
    del data["agent"]["id"] # Remove required field
    
    try:
        ManifestValidator.validate(data)
        logger.error("❌ Invalid manifest PASSED validation (Expected Failure)")
        return False
    except ValueError as e:
        logger.info(f"✅ Caught expected error: {e}")
        return True
    except Exception as e:
        logger.error(f"❌ Unexpected error type: {type(e)}")
        return False

def verify_invalid_capability():
    """Test Step 3: Validate Manifest with Invalid Capability"""
    logger.info("Step 3: Testing Invalid Capability (Expected Failure)...")
    
    data = create_valid_manifest()
    # Add a bogus capability
    data["capabilities"].append({
        "scope": "god_mode", # Unknown scope
        "reason": "I want power"
    })
    
    try:
        ManifestValidator.validate(data)
        logger.error("❌ Invalid capability PASSED validation (Expected Failure)")
        return False
    except ValueError as e:
        logger.info(f"✅ Caught expected error: {e}")
        return True

def main():
    try:
        if not verify_valid_manifest():
            sys.exit(1)
            
        if not verify_invalid_manifest_missing_field():
            sys.exit(1)
            
        if not verify_invalid_capability():
            sys.exit(1)
            
        logger.info("✨ ALL MANIFEST CHECKS PASSED ✨")
        sys.exit(0)
        
    except ImportError as e:
        logger.error(f"❌ Import Error: {e}. Make sure implementation exists.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
