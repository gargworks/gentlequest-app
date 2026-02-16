import json
import sys
import argparse

# Dynamic Tool Definitions
ECOSYSTEM_TOOLS = {
    "stripe": [
        {
            "name": "list_customers",
            "description": "Retrieve list of customers from Stripe",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "create_charge",
            "description": "Create a new payment charge",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "amount": {"type": "integer"},
                    "currency": {"type": "string"}
                }
            }
        }
    ],
    "postgres": [
        {
            "name": "query",
            "description": "Execute a read-only SQL query",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string"}
                }
            }
        }
    ],
    "brave_search": [
        {
            "name": "search",
            "description": "Search the web using Brave API",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            }
        }
    ],
    "default": [
        {
            "name": "echo",
            "description": "Echo back a message",
            "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}
        }
    ]
}

def handle_request(request: dict, server_name: str) -> dict:
    method = request.get("method", "")
    req_id = request.get("id", "1")
    tools = ECOSYSTEM_TOOLS.get(server_name.lower(), ECOSYSTEM_TOOLS["default"])

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": f"mock-{server_name}", "version": "1.0.0"},
                "capabilities": {"tools": {}}
            }
        }

    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}

    elif method in ["call_tool", "tools/call"]:
        params = request.get("params", {})
        tool_name = params.get("name", "")
        
        # Simple Mock Responses
        if server_name.lower() == "stripe":
            if tool_name == "list_customers":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": "Found 3 customers: User_A, User_B, User_C"}]}}
        elif server_name.lower() == "postgres":
            if tool_name == "query":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": "Rows: [id:1, name:'admin', role:'superuser']"}]}}
        
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": f"Mock response from {server_name}:{tool_name}"}]
            }
        }

    # IMPORTANT: Silent drop for notifications (no ID) or specifically initialized
    if "id" not in request or method == "notifications/initialized":
        return None

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", nargs="?", default="default")
    args = parser.parse_args()

    with open("/tmp/mock_mcp.log", "a") as log:
        log.write(f"\n--- Starting {args.name} ---\n")
        for line in sys.stdin:
            line = line.strip()
            if not line: continue
            try:
                log.write(f"REQ: {line}\n")
                request = json.loads(line)
                response = handle_request(request, args.name)
                if response is not None:
                    log.write(f"RES: {json.dumps(response)}\n")
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
                else:
                    log.write("RES: [Notification Dropped]\n")
            except Exception as e:
                log.write(f"ERR: {e}\n")
                error = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}
                sys.stdout.write(json.dumps(error) + "\n")
                sys.stdout.flush()

if __name__ == "__main__":
    main()
