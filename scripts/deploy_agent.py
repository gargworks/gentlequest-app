"""
Deploy Agent - DevOps Persona Trigger
=====================================
Triggers the 'DevOps' persona to perform infrastructure tasks.
Connects to Render via the NAR OS.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DeployTrigger")

# Ensure mcp-server-nucleus is in path
CURRENT_DIR = Path(__file__).parent
SERVER_SRC = CURRENT_DIR.parent / "mcp-server-nucleus" / "src"
sys.path.append(str(SERVER_SRC))

try:
    from mcp_server_nucleus.runtime.factory import ContextFactory
    from mcp_server_nucleus.runtime.agent import EphemeralAgent
except ImportError as e:
    logger.error(f"Failed to import Nucleus Runtime: {e}")
    sys.exit(1)

async def main():
    logger.info("🚀 Deploy Agent Trigger - Spawning DevOps (Heuristic Mode)...")

    # 1. Initialize LLM (Skipped for Heuristic Mode / Missing Dep)
    # api_key = os.getenv("GEMINI_API_KEY")
    # if not api_key:
    #    logger.error("GEMINI_API_KEY not set")
    #    sys.exit(1)
        
    # genai.configure(api_key=api_key)
    # model = genai.GenerativeModel("gemini-1.5-flash-latest") 
    model = None # Force Heuristic Mode (MDR_005 Fast Path)
    
    # 2. Initialize Runtime Factory
    factory = ContextFactory()
    
    # 3. Create Context for DevOps
    # Intent must trigger 'devops' category
    intent = "Check status of enabled services on Render."
    session_id = f"deploy-{datetime.now().strftime('%Y%m%d-%H%M')}"
    
    context = factory.create_context(session_id=session_id, intent=intent)
    
    if context.get('persona') != 'DevOps':
        logger.warning(f"⚠️ Intent routed to {context.get('persona')} instead of DevOps!")
    
    logger.info(f"Spawned Agent: {context['persona']}")
    logger.info(f"Tools: {[t['name'] for t in context.get('tools', [])]}")
    
    # 4. Inject System Prompt override (Not needed for Heuristic, but good practice)
    # context['system_prompt'] += "\nBe concise. Check services and report status."

    # 5. Spawn and Run Agent
    agent = EphemeralAgent(model=model, context=context)
    
    print("\n" + "="*60)
    print(f"🤖 DEVOPS AGENT ({context['persona']})")
    print("="*60 + "\n")
    
    result = await agent.run()
    
    print("\n" + "="*60)
    print("🏁 SESSION COMPLETE")
    print("="*60 + "\n")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
