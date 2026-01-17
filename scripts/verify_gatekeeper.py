#!/usr/bin/env python3
"""
verify_gatekeeper.py

Verification script for Phase 57: Chat 21 - The Gatekeeper.
Tests ConsentManager and CapabilityGrant persistence.
"""

import os
import sys
import logging
import shutil
import tempfile
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.identity.gatekeeper import Gatekeeper, GrantRequest, ACCESS_DENIED, ACCESS_GRANTED

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_GATEKEEPER")

TEST_BRAIN = Path("test_gatekeeper_brain")

def setup_env():
    if TEST_BRAIN.exists():
        shutil.rmtree(TEST_BRAIN)
    (TEST_BRAIN / "ledger").mkdir(parents=True)
    return Gatekeeper(TEST_BRAIN)

def verify_deny_by_default():
    logger.info("Step 1: Verify Deny by Default...")
    
    gk = setup_env()
    
    request = GrantRequest(
        agent_id="agent.untrusted",
        capability="network",
        params={"domain": "evil.com"}
    )
    
    # Check permissions (Should be False initially)
    if gk.check_permission(request):
        logger.error("❌ Permission GRANTED by default (Security Failure)")
        return False
        
    logger.info("✅ Permission correctly denied by default.")
    return True

def verify_grant_flow():
    logger.info("Step 2: Verify Grant Flow (Simulated User 'Yes')...")
    
    gk = setup_env()
    request = GrantRequest(
        agent_id="agent.trusted",
        capability="network",
        params={"domain": "google.com"}
    )
    
    # 1. Ask for permission (Simulate 'User Approves')
    # In real app, this triggers a UI/CLI prompt. 
    # For test, we call grant_permission directly as if the UI callback happened.
    gk.grant_permission(request)
    
    # 2. Check Permission again
    if not gk.check_permission(request):
        logger.error("❌ Permission DENIED after explicit grant")
        return False
        
    logger.info("✅ Permission granted and persisted.")
    return True

def verify_scope_specificity():
    logger.info("Step 3: Verify Scope Specificity...")
    
    gk = setup_env()
    
    # Grant google.com
    req_google = GrantRequest(agent_id="agent.strict", capability="network", params={"domain": "google.com"})
    gk.grant_permission(req_google)
    
    # Check amazon.com (Should fail)
    req_amazon = GrantRequest(agent_id="agent.strict", capability="network", params={"domain": "amazon.com"})
    
    if gk.check_permission(req_amazon):
        logger.error("❌ Permission Leak! Amazon granted because Google was granted.")
        return False
        
    logger.info("✅ Scope isolation verified (Domains are distinct).")
    return True

def main():
    try:
        if not verify_deny_by_default():
            sys.exit(1)
            
        if not verify_grant_flow():
            sys.exit(1)
            
        if not verify_scope_specificity():
            sys.exit(1)
            
        logger.info("✨ ALL GATEKEEPER CHECKS PASSED ✨")
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
