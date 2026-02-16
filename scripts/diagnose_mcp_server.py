#!/usr/bin/env python3
"""
Nucleus MCP Server Diagnostic
Tests if the server starts correctly and tools are registered.
"""
import sys
import os
import json

# Set environment
os.environ["PYTHONPATH"] = "/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src"
os.environ["NUCLEAR_BRAIN_PATH"] = "/Users/lokeshgarg/ai-mvp-backend/output/demos/.brain"

print("🔍 Nucleus MCP Server Diagnostic")
print("=" * 50)

# Test 1: Import the module
print("\n[1/4] Testing module import...")
try:
    sys.path.insert(0, "/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")
    import mcp_server_nucleus
    print(f"✅ Module imported successfully (v{mcp_server_nucleus.__version__})")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Check if mcp object exists
print("\n[2/4] Checking MCP server object...")
try:
    from mcp_server_nucleus import mcp
    print(f"✅ MCP server object exists: {type(mcp)}")
except Exception as e:
    print(f"❌ MCP object not found: {e}")
    sys.exit(1)

# Test 3: Check if tools are registered
print("\n[3/4] Checking tool registration...")
try:
    # Try to access the tools via the mcp object
    # FastMCP stores tools in _tools attribute
    if hasattr(mcp, '_tools'):
        tools = mcp._tools
        print(f"✅ Found {len(tools)} registered tools")
        
        # Check for our specific tools
        target_tools = ['nucleus_list_directory', 'nucleus_delete_file']
        for tool_name in target_tools:
            if tool_name in tools:
                print(f"   ✅ {tool_name} is registered")
            else:
                print(f"   ❌ {tool_name} is NOT registered")
    else:
        print("⚠️  Cannot inspect tools (FastMCP might be in fallback mode)")
        # Try calling the functions directly
        from mcp_server_nucleus import nucleus_list_directory, nucleus_delete_file
        print("✅ Functions exist and can be imported directly")
except Exception as e:
    print(f"❌ Tool check failed: {e}")

# Test 4: Test the tools directly
print("\n[4/4] Testing tools directly...")
try:
    from mcp_server_nucleus import nucleus_list_directory, nucleus_delete_file
    
    # Test list_directory
    result = nucleus_list_directory("/Users/lokeshgarg/ai-mvp-backend/output/demos")
    print(f"✅ nucleus_list_directory works:")
    print(result)
    
    # Test delete_file (should be blocked)
    result = nucleus_delete_file("/Users/lokeshgarg/ai-mvp-backend/output/demos/.env")
    print(f"\n✅ nucleus_delete_file works:")
    print(result)
    
except Exception as e:
    print(f"❌ Direct tool test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("🎯 Diagnosis Complete")
print("\nNext Steps:")
print("1. If tools are registered: Check Claude Desktop logs")
print("2. If tools are NOT registered: FastMCP decorator issue")
print("3. If import failed: Python path or dependency issue")
