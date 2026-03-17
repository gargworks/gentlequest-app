import os
import sys
import json
import pytest
from mcp_server_nucleus.runtime.stdio_server import StdioServer

@pytest.mark.asyncio
async def test_fusion_reactor_via_stdio():
    # Setup standard test environment
    os.environ["NUCLEUS_AGENT_TIER"] = "T2_CODE"
    server = StdioServer()
    
    # 1. Perform Handshake to get an IPC token
    handshake_req = {
        "jsonrpc": "2.0",
        "id": "init",
        "method": "tools/call",
        "params": {
            "name": "nucleus_governance",
            "arguments": {
                "action": "handshake"
            }
        }
    }
    handshake_resp = await server.handle_request(handshake_req)
    # The response content string has the token somewhere, or we can use the manager directly for testing.
    # Actually, in testing it's easier to use the manager directly:
    from mcp_server_nucleus.runtime.auth.ipc_provider import get_ipc_auth_manager
    manager = get_ipc_auth_manager()
    token = manager.issue_token(scope="admin", agent_tier="T2_CODE")

    # 2. We simulate a tools/call request for the fusion reactor
    request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/call",
        "params": {
            "name": "nucleus_engrams",
            "arguments": {
                "action": "fusion_reactor",
                "token_id": token.token_id,
                "params": {
                    "observation": "Testing the fusion reactor tool execution via stdio",
                    "context": "Testing",
                    "intensity": 5,
                    "write_engrams": False  # Dry run
                }
            }
        }
    }
    
    response = await server.handle_request(request)
    
    # Assertions
    assert response is not None
    assert response.get("error") is None
    
    result = response.get("result", {})
    assert not result.get("isError", True)
    
    content = result.get("content", [])
    assert len(content) > 0
    text = content[0].get("text", "")
    
    # Parse the inner JSON response that _make_response generates
    data = json.loads(text)
    assert data["success"] is True
    
    payload = data["data"]
    assert payload["pipeline"] == "fusion_reactor"
    assert "capture" in payload["sections"]
    assert payload["sections"]["capture"]["observation"] == "Testing the fusion reactor tool execution via stdio"
    assert payload["meta"]["execution_time_ms"] > 0
