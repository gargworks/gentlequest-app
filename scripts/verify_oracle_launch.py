#!/usr/bin/env python3
"""
verify_oracle_launch.py

Phase 61 (Chat 38): The Sovereign Launch.
Verifies that the Oracle can list itself as a SERVICE on the Marketplace.
"""
import os
import sys
import logging
import shutil
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.broker import ContextBroker

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("LAUNCH")

TEST_ROOT = Path("test_oracle_launch")

def setup_env():
    if TEST_ROOT.exists():
        shutil.rmtree(TEST_ROOT)
    TEST_ROOT.mkdir()
    (TEST_ROOT / "ledger").mkdir()
    return TEST_ROOT

def main():
    try:
        brain = setup_env()
        broker = ContextBroker(brain)
        
        logger.info("--- Phase 1: The Listing ---")
        PROVIDER_ID = "nucleus.core.oracle"
        
        listing_id = broker.publish_listing(
            provider_id=PROVIDER_ID,
            topic="services/consulting/strategy",
            description="The Antifragile Co-Founder. Strategic Simulation & Advice.",
            content="Use tool: brain_consult_oracle",
            price=100.0,
            type="service"
        )
        
        logger.info(f"✅ Published Oracle Service: {listing_id}")
        
        logger.info("--- Phase 2: The Search ---")
        results = broker.search_listings("strategy")
        
        found = False
        for r in results:
            if r.id == listing_id:
                logger.info(f"🔎 Found Listing: {r.topic} ({r.type})")
                if r.type == "service":
                    logger.info("✅ Verified Type: SERVICE")
                    found = True
                else:
                    logger.error(f"❌ Type Mismatch: Expected service, got {r.type}")
                    
        if not found:
            logger.error("❌ Listing not found in search results.")
            sys.exit(1)
            
        logger.info("✨ SOVEREIGN LAUNCH COMPLETE ✨")
        if TEST_ROOT.exists():
            shutil.rmtree(TEST_ROOT)
        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        if TEST_ROOT.exists():
            shutil.rmtree(TEST_ROOT)
        sys.exit(1)

if __name__ == "__main__":
    main()
