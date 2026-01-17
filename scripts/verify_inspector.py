#!/usr/bin/env python3
"""
verify_inspector.py

Verification script for Phase 57: Chat 29 - The Inspector.
Tests ManifestViewer's ability to render human-readable security reports.
"""

import os
import sys
import logging
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.identity.manifest import AgentManifest
from mcp_server_nucleus.runtime.inspector import ManifestViewer

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_INSPECTOR")

def verify_inspector():
    logger.info("Step 1: Create Sample Manifest...")
    
    manifest_data = {
        "manifest_version": "1.0.0",
        "agent": {
            "id": "agent.test.spy",
            "name": "Super Spy",
            "version": "0.0.7",
            "description": "A very suspicious agent.",
            "author": "The Agency",
            "license": "MIT"
        },
        "capabilities": [
            {
                "scope": "network",
                "reason": "To phone home",
                "domains": ["api.agency.secret", "google.com"]
            },
            {
                "scope": "filesystem",
                "reason": "To read secrets",
                "paths": ["/tmp/secrets"],
                "mode": "read"
            }
        ],
        "lifecycle": {
            "persistence": "persistent",
            "cleanup": "lazy"
        }
    }
    
    manifest = AgentManifest(**manifest_data)
    
    logger.info("Step 2: Inspect Manifest...")
    report = ManifestViewer.render_report(manifest)
    
    print("\n--- INSPECTION REPORT START ---")
    print(report)
    print("--- INSPECTION REPORT END ---\n")
    
    # Assertions
    if "Super Spy" not in report: 
        logger.error("❌ Agent Name missing from report")
        return False
        
    if "0.0.7" not in report: 
        logger.error("❌ Agent Version missing from report")
        return False
        
    if "⚠️  NETWORK" not in report:
        logger.error("❌ Network capability warning missing")
        return False
        
    if "api.agency.secret" not in report:
        logger.error("❌ Network domain detail missing")
        return False
        
    if "filesystem" not in report.lower() and "FILESYSTEM" not in report:
        logger.error("❌ Filesystem capability missing")
        return False

    logger.info("✅ Report validated successfully.")
    return True

def main():
    try:
        if not verify_inspector():
            sys.exit(1)
            
        logger.info("✨ ALL INSPECTOR CHECKS PASSED ✨")
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
