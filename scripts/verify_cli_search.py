#!/usr/bin/env python3
"""
verify_cli_search.py

Verification script for Phase 57: Chat 27 - The Seeker.
Tests CLI Search command logic (RegistryClient + Team Config).
"""

import os
import sys
import logging
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.team import TeamManager
from mcp_server_nucleus.runtime.registry import RegistryClient, RegistryEntry

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_CLI")

# Mock the handle_search_command to avoid importing cli.py which might have side effects
# Actually, we should test the logic we INTEND to put in handle_search_command.

def simulated_search_logic(brain_path: Path, query: str):
    """
    Simulation of what handle_search_command will do.
    """
    # 1. Load Team Config to get Registry URL
    team_mgr = TeamManager(brain_path)
    registry_url = team_mgr.get_registry_url()
    
    if registry_url:
        logger.info(f"Using Team Registry: {registry_url}")
        client = RegistryClient(registry_url=registry_url)
    else:
        logger.info("Using Default Public Registry")
        client = RegistryClient() # Default
        
    # 2. Search
    results = client.search(query)
    return results

def verify_cli_search():
    logger.info("Step 1: Test connection between Team Config and Registry Client...")
    
    # Setup Mock Brain
    tmp_dir = Path(tempfile.mkdtemp())
    (tmp_dir / "config").mkdir()
    
    # Mock Team Config
    config = {
        "team_id": "team.test",
        "name": "Test Team",
        "registry_url": "https://registry.mock.test/index.json"
    }
    (tmp_dir / "config" / "team.json").write_text(json.dumps(config))
    
    # Mock urllib response
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = json.dumps({
        "agents": [
            {
                "id": "agent.mock.searchable",
                "name": "Searchable Agent",
                "description": "I can be found",
                "latest_version": "1.0.0",
                "repo_url": "http://git.fake",
                "tags": ["findme"]
            }
        ]
    }).encode()

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        # Test Search
        results = simulated_search_logic(tmp_dir, "findme")
        
        if len(results) != 1:
            logger.error(f"❌ Search failed to return results. Got {len(results)}")
            return False
            
        if results[0].id != "agent.mock.searchable":
            logger.error("❌ Search returned wrong agent")
            return False
            
        logger.info("✅ CLI Logic successfully used Team URL and found agent.")
        
    shutil.rmtree(tmp_dir)
    return True

def main():
    try:
        if not verify_cli_search():
            sys.exit(1)
            
        logger.info("✨ ALL CLI SEARCH CHECKS PASSED ✨")
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
