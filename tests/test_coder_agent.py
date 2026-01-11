
import asyncio
import os
import sys
from pathlib import Path

# Setup Path
sys.path.append(os.path.join(os.getcwd(), 'mcp-server-nucleus', 'src'))

# Mock MCP
class MockMCP:
    def tool(self):
        def decorator(func):
            return func
        return decorator

import mcp_server_nucleus
mcp_server_nucleus.mcp = MockMCP()

# Import tool
from mcp_server_nucleus import brain_spawn_agent

async def test_coder():
    print("🤖 Testing Coder Agent (persona='developer')...")
    
    # We rely on GEMINI_API_KEY being present in env
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY missing")
        return

    result = await brain_spawn_agent(
        intent="Create a python script 'hello_code_ops.py' that prints 'Hello from CodeOps!'",
        persona="developer"
    )
    
    print("\n📝 AGENT OUTPUT:")
    print(result)
    
    # Verify file creation
    target = Path("hello_code_ops.py")
    if target.exists():
        print(f"\n✅ SUCCESS: File {target} created!")
        print(f"Content: {target.read_text()}")
        target.unlink() # Cleanup
    else:
        print(f"\n❌ FAILURE: File {target} NOT created.")

if __name__ == "__main__":
    asyncio.run(test_coder())
