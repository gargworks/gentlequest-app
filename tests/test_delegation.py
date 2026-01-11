
import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("mcp-server-nucleus/src"))

from mcp_server_nucleus.runtime.capabilities.brain_ops import BrainOps

def test_delegation():
    print("🧪 Testing BrainOps.brain_delegate_task...")
    
    ops = BrainOps()
    
    # 1. Delegate a simple task to the Librarian (Fast Persona)
    # The Librarian should just check commitments or fail gracefully if no tools match, 
    # but the goal is to see the agent spawn and return a log.
    
    args = {
        "persona": "librarian",
        "intent": "Scan for any open commitments in the system."
    }
    
    print(f"   Invoking brain_delegate_task(persona='librarian')...")
    
    # This calls asyncio.run() internally, so we must be in sync mode here.
    try:
        result = ops.execute_tool("brain_delegate_task", args)
        print("\n✅ Delegation Result Received:")
        print("---------------------------------------------------")
        print(result[:500] + "..." if len(result) > 500 else result)
        print("---------------------------------------------------")
        
        if "Delegation Complete" in result:
            print("✅ TEST PASSED: Agent executed successfully.")
        else:
            print("❌ TEST FAILED: Unexpected output.")
            
    except Exception as e:
        print(f"❌ TEST FAILED: Exception raised: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_delegation()
