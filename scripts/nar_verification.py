import sys
import os

# Add src to path
# Assuming script is run from project root or scripts folder
# We need to target /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.factory import ContextFactory
from mcp_server_nucleus.runtime.agent import EphemeralAgent

def main():
    print("=== NAR Fire Drill: Cognitive FaaS ===")
    
    factory = ContextFactory()
    
    # Scenario 1: Deploy (Should get Render tools)
    intent = "I need to deploy the production service."
    print(f"\n[1] Intent: '{intent}'")
    context = factory.create_context(intent)
    
    if not context['tools']:
        print(" FAIL: No tools mapped.")
    else:
        print(f" SUCCESS: Mapped {len(context['tools'])} tools.")

    agent = EphemeralAgent(context)
    agent.run()
    
    # Scenario 2: Unknown (Should get 0 tools)
    intent = "Write a poem about agents."
    print(f"\n[2] Intent: '{intent}'")
    context = factory.create_context(intent)
    
    if not context['tools']:
        print(" SUCCESS: Zero tools mapped (Correct Isolation).")
    else:
        print(f" FAIL: Leaked tools: {len(context['tools'])}")
        
    agent = EphemeralAgent(context)
    agent.run()

if __name__ == "__main__":
    main()
