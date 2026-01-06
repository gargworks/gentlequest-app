
import sys
import os
from pathlib import Path

# Add src to path
CURRENT_DIR = Path(__file__).parent
SERVER_SRC = CURRENT_DIR / "mcp-server-nucleus" / "src"
sys.path.append(str(SERVER_SRC))

try:
    from mcp_server_nucleus.runtime.factory import ContextFactory
    from mcp_server_nucleus.runtime.capabilities.brain_ops import BrainOps
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def verify():
    print("🧪 Verifying Nucleus Runtime (MDR Compliance)...")
    
    # 1. Factory Initialization
    factory = ContextFactory()
    print("✅ ContextFactory initialized")
    
    # 2. Intent Classification (MDR_004)
    intent = "Perform daily admin scan of commitments and archive stale items."
    context = factory.create_context(session_id="test-1", intent=intent)
    
    print(f"   Intent: '{intent}'")
    print(f"   Classified Intent: {context.get('intent_category')}")
    print(f"   Persona: {context.get('persona')}")
    
    if context.get('persona') != "Librarian":
        print("❌ Persona Mismatch! Expected Librarian.")
        sys.exit(1)
    else:
        print("✅ Persona Routing Correct (Librarian)")
        
    # 3. Tool Availability (MDR_005)
    tools = context.get('tools', [])
    tool_names = [t['name'] for t in tools]
    
    print(f"   Tools: {tool_names}")
    
    required = ["brain_scan_commitments", "brain_archive_stale", "brain_export"]
    missing = [r for r in required if r not in tool_names]
    
    if missing:
        print(f"❌ Missing Tools: {missing}")
        # Check BrainOps directly to see why
        ops = BrainOps()
        print(f"   BrainOps raw tools: {[t['name'] for t in ops.get_tools()]}")
        sys.exit(1)
    else:
        print("✅ All Librarian Tools Present")
        
    print("\n🎉 VERIFICATION SUCCESSFUL")

if __name__ == "__main__":
    verify()
