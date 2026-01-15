#!/usr/bin/env python3
"""
verify_client.py

Verification script for Phase 57: Chat 23 - The Client.
Tests RegistryClient for fetching and searching the Agent Catalog.
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

from mcp_server_nucleus.runtime.registry import RegistryClient, RegistryEntry

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_CLIENT")

def setup_mock_registry():
    """Create a temporary local file serving as the registry index."""
    tmp_dir = Path(tempfile.mkdtemp())
    index_path = tmp_dir / "index.json"
    
    data = {
        "agents": [
            {
                "id": "agent.std.librarian",
                "name": "Librarian",
                "description": "The keeper of knowledge.",
                "latest_version": "1.0.0",
                "repo_url": "https://github.com/nucleus/librarian",
                "tags": ["memory", "search"]
            },
            {
                "id": "agent.std.devops",
                "name": "DevOps",
                "description": "Infrastructure automation.",
                "latest_version": "0.5.0",
                "repo_url": "https://github.com/nucleus/devops",
                "tags": ["infra", "deployment"]
            }
        ]
    }
    
    index_path.write_text(json.dumps(data, indent=2))
    return tmp_dir, index_path

def verify_fetch_and_parse():
    logger.info("Step 1: Verify Index Fetching & Parsing...")
    
    tmp_dir, index_path = setup_mock_registry()
    
    # Use file:// URL scheme for local test
    registry_url = f"file://{index_path.absolute()}"
    client = RegistryClient(registry_url=registry_url)
    
    try:
        entries = client.fetch_index()
        logger.info(f"Fetched {len(entries)} entries.")
        
        if len(entries) != 2:
            logger.error(f"❌ Expected 2 entries, got {len(entries)}")
            return False
            
        first = entries[0]
        if not isinstance(first, RegistryEntry):
            logger.error("❌ Parsed objects are not RegistryEntry instances")
            return False
            
        if first.id != "agent.std.librarian":
            logger.error(f"❌ First entry mismatch: {first.id}")
            return False
            
        logger.info("✅ Successfully fetched and parsed index.")
        return True
        
    finally:
        shutil.rmtree(tmp_dir)

def verify_search():
    logger.info("Step 2: Verify Search Functionality...")
    
    tmp_dir, index_path = setup_mock_registry()
    registry_url = f"file://{index_path.absolute()}"
    client = RegistryClient(registry_url=registry_url)
    client.fetch_index() # Prime cache
    
    # Search by tag
    results = client.search("infra")
    if len(results) != 1 or results[0].id != "agent.std.devops":
        logger.error("❌ Search by 'infra' failed")
        return False
        
    # Search by name substring
    results = client.search("lib")
    if len(results) != 1 or results[0].id != "agent.std.librarian":
        logger.error("❌ Search by 'lib' failed")
        return False
        
    logger.info("✅ Search functionality verified.")
    shutil.rmtree(tmp_dir)
    return True

def main():
    try:
        if not verify_fetch_and_parse():
            sys.exit(1)
            
        if not verify_search():
            sys.exit(1)
            
        logger.info("✨ ALL CLIENT CHECKS PASSED ✨")
        sys.exit(0)
        
    except ImportError as e:
        logger.error(f"❌ Import Error: {e}. Implementation missing?")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
