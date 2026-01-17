#!/usr/bin/env python3
"""
verify_auth.py

Verification script for Phase 57: Chat 24 - The Auth.
Tests AuthManager and PrivateSource configuration.
"""

import os
import sys
import logging
import json
import shutil
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.auth import AuthManager, PrivateSource

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_AUTH")

TEST_BRAIN = Path("test_auth_brain")

def setup_env():
    if TEST_BRAIN.exists():
        shutil.rmtree(TEST_BRAIN)
    (TEST_BRAIN / "config").mkdir(parents=True)
    
    # Create valid config
    config = {
        "sources": [
            {
                "domain": "github.com",
                "org": "my-private-org",
                "token_env": "MY_ORG_GH_TOKEN"
            },
            {
                "domain": "gitlab.com",
                "token_env": "GITLAB_TOKEN"
            }
        ]
    }
    
    (TEST_BRAIN / "config" / "auth.json").write_text(json.dumps(config, indent=2))
    
    return AuthManager(TEST_BRAIN)

def verify_credential_resolution():
    logger.info("Step 1: Verify Credential Resolution...")
    
    # Mock Env Vars
    os.environ["MY_ORG_GH_TOKEN"] = "ghp_SECRET_123"
    os.environ["GITLAB_TOKEN"] = "glpat_SECRET_456"
    
    manager = setup_env()
    
    # 1. Match specific org
    creds = manager.get_credentials("https://github.com/my-private-org/repo.git")
    if not creds:
        logger.error("❌ Failed to resolve github org creds")
        return False
        
    if creds.token != "ghp_SECRET_123":
        logger.error(f"❌ Token mismatch. Got {creds.token}")
        return False
        
    logger.info("✅ Resolved GitHub Org token.")

    # 2. Match general domain
    creds_gl = manager.get_credentials("https://gitlab.com/someone/repo.git")
    if not creds_gl or creds_gl.token != "glpat_SECRET_456":
        logger.error("❌ Failed to resolve gitlab domain creds")
        return False
        
    logger.info("✅ Resolved GitLab domain token.")
    
    # 3. No Match
    creds_none = manager.get_credentials("https://bitbucket.org/someone/repo.git")
    if creds_none is not None:
        logger.error("❌ Resolved credentials for unknown source")
        return False
        
    logger.info("✅ Correctly returned None for unknown source.")
    
    return True

def verify_url_injection():
    logger.info("Step 2: Verify URL Injection...")
    
    manager = setup_env()
    # Mock Token
    os.environ["MY_ORG_GH_TOKEN"] = "ghp_SECRET"
    
    original_url = "https://github.com/my-private-org/repo.git"
    injected = manager.inject_credentials(original_url)
    
    expected = "https://oauth2:ghp_SECRET@github.com/my-private-org/repo.git"
    
    if injected != expected:
        logger.error(f"❌ Injection Failed.\nExpected: {expected}\nGot:      {injected}")
        return False
        
    logger.info("✅ URL Injection successful.")
    return True

def main():
    try:
        if not verify_credential_resolution():
            sys.exit(1)
            
        if not verify_url_injection():
            sys.exit(1)
            
        logger.info("✨ ALL AUTH CHECKS PASSED ✨")
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
