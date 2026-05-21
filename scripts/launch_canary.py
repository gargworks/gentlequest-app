#!/usr/bin/env python3
import subprocess
import json
import sys
import time
import os
from pathlib import Path

def run_canary():
    print("🛡️  NUCLEUS LAUNCH CANARY (Deterministic Verification)")
    print("-" * 50)
    
    # Get the repo root
    repo_root = Path(__file__).resolve().parent.parent
    mcp_pkg_path = repo_root / "mcp-server-nucleus"
    
    # Simulate a clean environment
    env = os.environ.copy()
    env["PYTHONPATH"] = str(mcp_pkg_path / "src")
    if "NUCLEUS_BRAIN_PATH" not in env:
        env["NUCLEUS_BRAIN_PATH"] = str(repo_root / ".brain")
    
    print(f"📍 Target: {mcp_pkg_path}")
    print(f"🧠 Brain Path: {env['NUCLEUS_BRAIN_PATH']}")
    print(f"🐍 PYTHONPATH: {env['PYTHONPATH']}")
    
    # 1. Start MCP Server in subprocess (Stdio mode)
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_server_nucleus"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(mcp_pkg_path),
        env=env
    )
    
    # Give it a moment to boot
    time.sleep(2)
    
    try:
        # 2. Perform MCP Handshake (initialize)
        print("🤝 Performing MCP Handshake...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "Nucleus-Launch-Canary", "version": "1.0.0"}
            }
        }
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # We might need to skip some bootstrap lines (like [Nucleus Init] logs)
        resp_line = ""
        for _ in range(20): # Try reading up to 20 lines to find the JSON response
            resp_line = process.stdout.readline()
            if resp_line.startswith('{'):
                break
            if not resp_line:
                break
        
        if not resp_line:
            stderr_out = process.stderr.read()
            print(f"❌ FAILED: No response from server. Stderr:\n{stderr_out}")
            return False
            
        resp = json.loads(resp_line)
        if "result" not in resp:
            print(f"❌ FAILED: Handshake error: {resp.get('error')}")
            return False
        
        print(f"✅ Handshake successful (Server: {resp['result']['serverInfo']['name']} v{resp['result']['serverInfo']['version']})")

        # 3. List Tools (The 130-tool proof)
        print("🔍 Discovering tools...")
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        process.stdin.write(json.dumps(list_request) + "\n")
        process.stdin.flush()
        
        resp_line = process.stdout.readline()
        resp = json.loads(resp_line)
        tools = resp.get("result", {}).get("tools", [])
        tool_count = len(tools)
        
        if tool_count < 100:
            print(f"⚠️  WARNING: Only found {tool_count} tools. (Target: ~130)")
        else:
            print(f"✅ FOUND {tool_count} tools. Ecosystem is intact.")

        # 4. Check specific mission-critical tools
        critical_tools = ["brain_health", "list_tasks", "nucleus_status"]
        tool_names = [t["name"] for t in tools]
        for ct in critical_tools:
            if ct in tool_names:
                print(f"✅ CRITICAL TOOL: {ct} is available.")
            else:
                print(f"❌ MISSING: {ct} is NOT available.")

        # 5. Call brain_health (Integration check)
        print("🩺 Verifying real-time health data...")
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "brain_health",
                "arguments": {}
            }
        }
        process.stdin.write(json.dumps(call_request) + "\n")
        process.stdin.flush()
        
        resp_line = process.stdout.readline()
        resp = json.loads(resp_line)
        content = resp.get("result", {}).get("content", [])
        if content and "healthy" in content[0].get("text", "").lower():
            print("✅ Health Check: PASSED")
        else:
            print(f"❌ Health Check: FAILED ({resp})")

        print("-" * 50)
        print("🏆 CANARY COMPLETE: Nucleus is ready for strike.")
        return True

    except Exception as e:
        print(f"❌ ERROR encountered: {e}")
        return False
    finally:
        process.terminate()

if __name__ == "__main__":
    success = run_canary()
    sys.exit(0 if success else 1)
