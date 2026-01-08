"""
Nightly Agent - MDR_005 Compliant
=================================

This script acts as a CRON TRIGGER for the Nucleus Agent Runtime.
It spawns an Ephemeral Agent with the 'Librarian' persona to perform 
maintenance tasks (scanning commitments, archiving, etc.).

MDR_005: "The nightly script becomes a thin wrapper that just wakes up the agent."
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NightlyTrigger")

# Ensure mcp-server-nucleus is in path
CURRENT_DIR = Path(__file__).parent
SERVER_SRC = CURRENT_DIR.parent / "mcp-server-nucleus" / "src"
sys.path.append(str(SERVER_SRC))

try:
    import warnings
    warnings.filterwarnings('ignore', category=FutureWarning, module='google.generativeai')
    import google.generativeai as genai
    from mcp_server_nucleus.runtime.factory import ContextFactory
    from mcp_server_nucleus.runtime.agent import EphemeralAgent
except ImportError as e:
    logger.error(f"Failed to import Nucleus Runtime: {e}")
    sys.exit(1)

async def main():
    logger.info("🌙 Nightly Agent Trigger - Waking up Nucleus...")

    # 1. Initialize LLM (Gemini)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not set")
        sys.exit(1)
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"))
    
    # 2. Initialize Runtime Factory
    factory = ContextFactory()
    
    # 3. Create Context for Librarian (Intent = 'admin')
    # Use a descriptive intent that triggers classify_intent -> 'admin'
    intent = "Perform daily admin scan of commitments and archive stale items."
    session_id = f"nightly-{datetime.now().strftime('%Y%m%d')}"
    
    context = factory.create_context(session_id=session_id, intent=intent)
    
    logger.info(f"Spawned Agent: {context['persona']}")
    logger.info(f"Active Capabilities: {context['capabilities']}")
    
    # 4. Spawn and Run Agent
    agent = EphemeralAgent(model=model, context=context)
    
    print("\n" + "="*60)
    print(f"🤖 AGENT OUTPUT ({context['persona']})")
    print("="*60 + "\n")
    
    result = await agent.run()
    
    print("\n" + "="*60)
    print("🏁 SESSION COMPLETE")
    print("="*60 + "\n")
    
    logger.info(f"Agent finished. Result type: {type(result).__name__}")

if __name__ == "__main__":
    asyncio.run(main())
