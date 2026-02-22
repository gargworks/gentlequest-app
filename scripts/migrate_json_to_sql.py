#!/usr/bin/env python3
"""
Sovereign OS Migration Script
=============================
Migrates JSON-based ledger files (V1/V2) to the new SQLite/Postgres StorageBackend (V3 Scale).
Usage: python scripts/migrate_json_to_sql.py --brain-path .brain
"""

import sys
import argparse
import logging
from pathlib import Path

# Adjust path to import from src
# The correct path is mcp-server-nucleus/src relative to the repo root
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server-nucleus" / "src"))

try:
    from mcp_server_nucleus.runtime.db import JSONBackend, get_storage_backend
    from mcp_server_nucleus.runtime.broker import ContextTransaction
except ImportError as e:
    logger = logging.getLogger("nucleus-migration")
    logger.error(f"Import failed: {e}")
    logger.info(f"sys.path: {sys.path}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("nucleus-migration")

def main():
    parser = argparse.ArgumentParser(description="Migrate Nucleus OS ledgers from JSON to SQL backend.")
    parser.add_argument("--brain-path", default=".brain", help="Path to the Nucleus brain directory")
    args = parser.parse_args()
    
    brain = Path(args.brain_path).resolve()
    if not brain.exists():
        logger.error(f"Brain path not found: {brain}")
        sys.exit(1)
        
    logger.info(f"🚀 Starting Migration for Brain: {brain}")
    
    # 1. Initialize Backends
    legacy_backend = JSONBackend(brain)
    
    # This automatically picks up SQLite or Postgres based on ENV/config
    new_backend = get_storage_backend(brain)
    
    if isinstance(new_backend, JSONBackend):
        logger.error("❌ Target backend is configured as JSON. Cannot migrate JSON to JSON.")
        logger.info("Please configure 'backend: sqlite' in nucleus.yaml or set NUCLEUS_DATABASE_URL.")
        sys.exit(1)
        
    logger.info(f"🎯 Target backend: {new_backend.__class__.__name__}")
    
    # 2. Migrate Tasks
    logger.info("Migrating Tasks...")
    legacy_tasks = legacy_backend.list_tasks()
    tasks_migrated = 0
    for task in legacy_tasks:
        try:
            if not new_backend.get_task(task.get("id")):
                new_backend.add_task(task)
                tasks_migrated += 1
        except Exception as e:
            logger.error(f"Failed to migrate task {task.get('id')}: {e}")
            
    logger.info(f"✅ Migrated {tasks_migrated} tasks.")
    
    # 3. Migrate Listings
    logger.info("Migrating Context Marketplace Listings...")
    legacy_listings = legacy_backend.search_listings("", limit=1000000)
    listings_migrated = 0
    for listing in legacy_listings:
        try:
            if not new_backend.get_listing(listing.id):
                new_backend.create_listing(listing)
                listings_migrated += 1
        except Exception as e:
            logger.error(f"Failed to migrate listing {listing.id}: {e}")
            
    logger.info(f"✅ Migrated {listings_migrated} listings.")
    
    # 4. Migrate Transactions
    logger.info("Migrating Transactions...")
    tx_file = brain / "ledger" / "transactions.jsonl"
    tx_migrated = 0
    if tx_file.exists():
        import json
        with open(tx_file, "r") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    tx = ContextTransaction(**data)
                    new_backend.create_transaction(tx)
                    tx_migrated += 1
                except Exception as e:
                    # Silently skip duplicate transactions if we re-run
                    if "UNIQUE constraint failed" in str(e):
                        continue
                    logger.error(f"Failed to migrate transaction: {e}")
                    
    logger.info(f"✅ Migrated {tx_migrated} transactions.")
    
    logger.info("🎉 Migration Complete! You may now safely delete your JSON ledger files or keep them as a backup.")
    
if __name__ == "__main__":
    main()
