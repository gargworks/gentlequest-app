#!/usr/bin/env python3
import sys
import os
import logging

# Setup Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup Paths
PROJECT_ROOT = os.getcwd()
sys.path.append(os.path.join(PROJECT_ROOT, 'mcp-server-nucleus', 'src'))

try:
    from mcp_server_nucleus.runtime.capabilities.marketing_engine import brain_synthesize_strategy
except ImportError as e:
    logger.error(f"Failed to import Nucleus Marketing Engine: {e}")
    sys.exit(1)

import shutil

def main():
    logger.info("🧠 Nucleus Brain: Starting Weekly Strategy Sync...")
    logger.info(f"📂 Project Root: {PROJECT_ROOT}")

    # check if API key exists
    if not os.environ.get("GEMINI_API_KEY"):
        logger.error("❌ GEMINI_API_KEY not found in environment.")
        logger.info("Please export GEMINI_API_KEY='your_key' and try again.")
        sys.exit(1)

    # 🛡️ SAFETY NET: Create Backup
    strategy_path = os.path.join(PROJECT_ROOT, 'docs/marketing/strategy.md')
    backup_path = os.path.join(PROJECT_ROOT, 'docs/marketing/strategy.old.md')
    if os.path.exists(strategy_path):
        shutil.copy2(strategy_path, backup_path)
        logger.info(f"🛡️ Backup created: {backup_path}")

    # Execute Synthesis
    logger.info("🔄 Analyzing Marketing Logs & Synthesizing New Strategy...")
    result = brain_synthesize_strategy(PROJECT_ROOT, focus_topic="Weekly Auto-Sync")

    if result.get("status") == "success":
        logger.info("✅ Strategy Updated Successfully!")
        logger.info(f"📄 Path: {result.get('path')}")
        logger.info(f"💡 Insights: {result.get('insights')}")
        logger.info("👉 Review docs/marketing/strategy.md to see the changes.")
    else:
        logger.error("❌ Strategy Update Failed.")
        logger.error(f"Reason: {result.get('message')}")
        # Continue to workflow optimization anyway

    # Execute Workflow Optimization
    logger.info("🧬 Nucleus Brain: Checking for Workflow Improvements (Meta-Feedback)...")
    from mcp_server_nucleus.runtime.capabilities.marketing_engine import brain_optimize_workflow
    
    opt_result = brain_optimize_workflow(PROJECT_ROOT)
    
    if opt_result.get("status") == "success":
        logger.info("✅ Workflow Improvements Proposed!")
        logger.info(f"📄 Report: {opt_result.get('path')}")
        logger.info("👉 Review the report and update 'marketing_autopilot_cheatsheet.md' if agreed.")
    elif opt_result.get("status") == "skipped":
        logger.info("👌 No Meta-Feedback found. Workflow is stable.")
    else:
        logger.error(f"⚠️ Optimization Check Failed: {opt_result.get('message')}")

if __name__ == "__main__":
    main()
