
import sys
import os
from pathlib import Path

# Setup paths
sys.path.append("mcp-server-nucleus/src")
from mcp_server_nucleus.runtime.factory import ContextFactory

def verify_plugins():
    print("🔌 Verifying Tool Marketplace (Plugins)...")
    
    # 1. Initialize Factory (which loads plugins)
    brain_path = Path(".brain").resolve()
    factory = ContextFactory(brain_path=brain_path)
    
    # 2. Check Registry
    caps = factory.list_capabilities()
    print(f"Loaded Capabilities: {caps}")
    
    if "example_echo" in caps:
        print("✅ Plugin 'example_echo' loaded successfully!")
    else:
        print("❌ Plugin 'example_echo' NOT found in registry.")
        sys.exit(1)
        
    # 3. Test Context Creation
    context = factory.create_context_for_persona(
        session_id="test",
        persona_name="devops", # Should have access if we add it? No, personas define their tools.
        # Wait, if I add a plugin, how does a persona GET it?
        # The current design loads it into registry, but no persona requests it.
        # However, for ephemeral/universal usage, maybe we want to auto-attach?
        # Or just verify it's registered for now.
        intent="admin"
    )
    
    # If the plugin is registered, we can manually request it in a persona definition
    # OR we can verify it's retrievable via get_capability("example_echo")
    
    echo_cap = factory._registry.get("example_echo")
    if echo_cap:
        result = echo_cap.execute_tool("echo_message", {"content": "Hello World"})
        print(f"Tool Execution Verification: {result}")
        if result == "ECHO: Hello World":
            print("✅ Tool Execution Verified!")
        else:
            print("❌ Tool Execution Failed.")
            sys.exit(1)

if __name__ == "__main__":
    verify_plugins()
