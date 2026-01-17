import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.factory import ContextFactory
from mcp_server_nucleus.runtime.agent import EphemeralAgent

def main():
    print("=== NAR Verification: Whiteboard -> DB ===")
    
    # 1. Define Intent (The "Whiteboard" Input)
    intent = "Add a task to Review NAR Architecture"
    print(f"Intent: '{intent}'")
    
    # 2. Spawn Agent
    factory = ContextFactory()
    context = factory.create_context(intent)
    agent = EphemeralAgent(context)
    
    # 3. Execute
    log = agent.run()
    print("\n--- Execution Log ---")
    print(log)
    
    # 4. Verify DB (The Ledger)
    print("\n--- Verifying Ledger ---")
    ledger_path = Path("/Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/commitments/ledger.json")
    if ledger_path.exists():
        data = json.loads(ledger_path.read_text())
        # Find our task
        found = False
        for c in data['commitments']:
            if "Review NAR Architecture" in c['description']:
                print(f"✅ Success! Found task in DB: {c['id']}")
                print(f"   Source: {c['source']}")
                found = True
                break
        
        if not found:
            print("❌ Failed: Task not found in ledger.")
    else:
        print("❌ Failed: Ledger file not found.")

if __name__ == "__main__":
    main()
