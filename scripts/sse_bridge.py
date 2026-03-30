#!/usr/bin/env python3
"""
Nucleus SSE Bridge for ChatGPT (2026 Developer Beta Mode)
Connects ChatGPT web browser to your local Nucleus MCP brain via SSE.

Usage:
    python scripts/sse_bridge.py

Requirements:
    pip install starlette uvicorn sse-starlette mcp
"""

import os
import sys
import logging
import asyncio
import json
from pathlib import Path

# --- Path Bootstrapping ---
workspace_root = Path(__file__).resolve().parent.parent
# Priority 1: mcp-server-nucleus/src (Internal dev mode)
dev_src = workspace_root / "mcp-server-nucleus" / "src"
if dev_src.exists():
    sys.path.insert(0, str(dev_src))
# Priority 2: root (Fallback)
sys.path.append(str(workspace_root))

try:
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from mcp.server.models import InitializationOptions
    import mcp.types as types
    from mcp.server import NotificationOptions, Server
    from mcp.server.sse import SseServerTransport
    import uvicorn
    
    # Initialize Nucleus Logic (Hypervisor, Engrams, Tasks)
    # We leverage the existing StdioServer handler to avoid duplication
    from mcp_server_nucleus.runtime.stdio_server import StdioServer
except ImportError as e:
    print(f"❌ Error: Missing dependencies. {e}")
    print("Please run: pip install starlette uvicorn sse-starlette mcp")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] Nucleus Bridge: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("nucleus_bridge")

# --- Nucleus Integration ---
nucleus = StdioServer()
server = Server("nucleus")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Expose all Nucleus tools to the SSE client (ChatGPT)."""
    try:
        # Mock a stdio request to our internal handler
        resp = await nucleus.handle_request({
            "jsonrpc": "2.0",
            "method": "tools/list", 
            "id": "bridge_init"
        })
        
        tools_data = resp["result"]["tools"]
        tools = []
        for t in tools_data:
            # MCP SDK Tool model expects name, description, inputSchema
            tools.append(types.Tool(
                name=t["name"],
                description=t.get("description", ""),
                inputSchema=t.get("inputSchema", {"type": "object", "properties": {}})
            ))
        return tools
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        return []

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Execute tools via the Nucleus Hypervisor."""
    try:
        logger.info(f"Tool Call: {name}") # Log activity for the user to see in terminal
        
        # Dispatch to Nucleus internal handler
        resp = await nucleus.handle_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": "bridge_call",
            "params": {
                "name": name,
                "arguments": arguments or {}
            }
        })
        
        if "error" in resp:
            logger.error(f"Tool Error ({name}): {resp['error']['message']}")
            return [types.TextContent(
                type="text", 
                text=f"Error: {resp['error']['message']}"
            )]
        
        result = resp["result"]
        content = []
        
        # Handle different response formats (Nucleus vs Mounted Plugins)
        for item in result.get("content", []):
            if item.get("type") == "text":
                content.append(types.TextContent(type="text", text=item["text"]))
        
        if not content:
            # Fallback if content is missing but success happened
            content.append(types.TextContent(type="text", text="Command executed successfully (no output)."))
            
        return content
    except Exception as e:
        logger.error(f"Exception calling tool {name}: {e}")
        return [types.TextContent(type="text", text=f"Bridge Exception: {str(e)}")]

# --- Starlette Web app ---
app = Starlette(debug=True)
sse = SseServerTransport("/messages")

@app.route("/sse")
async def handle_sse(request):
    """Bridge endpoint for ChatGPT."""
    logger.info("New SSE Connection established from ChatGPT.")
    async with sse.connect_scope(request.scope, request.receive, request._send) as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="nucleus-sse-bridge",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

app.mount("/messages", Mount("", app=sse.handle_post_resource))

def main():
    port = int(os.environ.get("PORT", 8000))
    print("\n" + "="*50)
    print("🧠 NUCLEUS SSE BRIDGE FOR CHATGPT")
    print("="*50)
    print(f"1. Connection URL: http://localhost:{port}/sse")
    print("2. In ChatGPT: Settings -> Apps -> Advanced -> Developer Mode")
    print(f"3. Add Endpoint: http://localhost:{port}/sse")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")

if __name__ == "__main__":
    main()
