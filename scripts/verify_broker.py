#!/usr/bin/env python3
"""
verify_broker.py

Verification script for Phase 57: Chat 31 - The Broker.
Tests the Context Economy: Publishing listings, discovering them, and executing transactions.
"""

import os
import sys
import logging
import json
import shutil
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.broker import ContextBroker, ContextListing

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_BROKER")

TEST_BRAIN = Path("test_broker_brain")

def setup_env():
    if TEST_BRAIN.exists():
        shutil.rmtree(TEST_BRAIN)
    (TEST_BRAIN / "ledger").mkdir(parents=True)
    return ContextBroker(TEST_BRAIN)

def verify_broker():
    broker = setup_env()
    
    logger.info("Step 1: Publish Listings...")
    
    # Agent A publishes "Market Research"
    listing_id = broker.publish_listing(
        provider_id="agent.researcher",
        topic="market_analysis",
        description="Deep dive into AI Agent Market 2026",
        content="The market is booming. Buy buy buy.",
        price=10
    )
    
    logger.info(f"✅ Published Listing: {listing_id}")
    
    logger.info("Step 2: Discovery...")
    results = broker.search_listings("market")
    
    if len(results) != 1:
        logger.error(f"❌ Discovery failed. Expected 1, got {len(results)}")
        return False
        
    found = results[0]
    if found.provider_id != "agent.researcher":
        logger.error("❌ Wrong provider found")
        return False
        
    logger.info(f"✅ Found: {found.topic} by {found.provider_id}")
    
    logger.info("Step 3: Transaction...")
    # Agent B buys the context
    transaction = broker.buy_context(
        buyer_id="agent.strategist",
        listing_id=listing_id
    )
    
    if not transaction:
        logger.error("❌ Transaction failed")
        return False
        
    if transaction.content != "The market is booming. Buy buy buy.":
        logger.error("❌ Content mismatch in transaction receipt")
        return False
        
    # Verify Ledger
    ledger_path = TEST_BRAIN / "ledger" / "transactions.jsonl"
    if not ledger_path.exists():
        logger.error("❌ Transaction ledger not created")
        return False
        
    logger.info("✅ Transaction completed and logged.")
    return True

def main():
    try:
        if not verify_broker():
            sys.exit(1)
            
        logger.info("✨ ALL BROKER CHECKS PASSED ✨")
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
