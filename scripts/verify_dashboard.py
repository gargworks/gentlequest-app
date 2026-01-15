#!/usr/bin/env python3
"""
verify_dashboard.py

Verification script for Phase 57: Chat 28 - The Dashboard.
Verifies the existence and basic structure of the React Marketplace components.
"""

import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_DASHBOARD")

PROJECT_ROOT = Path("/Users/lokeshgarg/ai-mvp-backend")
HUD_ROOT = PROJECT_ROOT / "tools" / "nucleus-hud"

def verify_files_exist():
    logger.info("Step 1: Check Frontend Files...")
    
    files = [
        HUD_ROOT / "app" / "components" / "marketplace" / "AgentCard.tsx",
        HUD_ROOT / "app" / "components" / "marketplace" / "MarketplaceGrid.tsx",
        HUD_ROOT / "app" / "marketplace" / "page.tsx"
    ]
    
    all_exist = True
    for f in files:
        if not f.exists():
            logger.error(f"❌ Missing file: {f}")
            all_exist = False
        else:
            logger.info(f"✅ Found: {f.name}")
            
    return all_exist

def verify_content():
    logger.info("Step 2: Verify Content...")
    
    card = HUD_ROOT / "app" / "components" / "marketplace" / "AgentCard.tsx"
    if card.exists():
        content = card.read_text()
        if "interface Agent" not in content:
             logger.error("❌ AgentCard missing interface definition")
             return False
        if "export default function AgentCard" not in content:
             logger.error("❌ AgentCard missing export default")
             return False
             
    logger.info("✅ Content checks passed.")
    return True

def main():
    if not (HUD_ROOT).exists():
        logger.error("❌ HUD Root not found. Is tools/nucleus-hud initialized?")
        sys.exit(1)

    if not verify_files_exist():
        sys.exit(1)
        
    if not verify_content():
        sys.exit(1)
        
    logger.info("✨ ALL DASHBOARD CHECKS PASSED ✨")
    sys.exit(0)

if __name__ == "__main__":
    main()
