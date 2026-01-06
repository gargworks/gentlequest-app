#!/usr/bin/env python3
import os
import sys
import json
import time
import logging
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/mcp-server-nucleus/src")

from mcp_server_nucleus.runtime.factory import ContextFactory

# Configure logging
logging.basicConfig(level=logging.ERROR)

async def verify_render_poller():
    print("=== Render Poller Verification ===")
    
    # 1. Initialize Factory and Context
    factory = ContextFactory()
    intent = "start deploy poll"
    context = factory.create_context("test-session-render", intent)
    
    tools = {t["name"]: t for t in context["tools"]}
    
    if "brain_start_deploy_poll" in tools:
        print("✅ Render Poller tools loaded")
    else:
        print("❌ Render Poller tools NOT loaded")
        sys.exit(1)
        
    print()
    
    # Get capability instance
    render_cap = None
    for cap in context["capability_instances"]:
        if cap.name == "render_poller":
            render_cap = cap
            break
            
    if not render_cap:
        print("❌ RenderCapability instance not found")
        print(f"Active caps: {[c.name for c in context['capability_instances']]}")
        sys.exit(1)

    # 2. Test brain_start_deploy_poll (Simulation)
    print(">> Intent: brain_start_deploy_poll (srv-test)")
    
    # Execute tool (it's sync wrapper around async create_task)
    # But for verification to work, we need a running loop.
    # verify_render_poller is async, so there IS a running loop! 
    # ContextFactory and Capability are instantiated in this process.
    # The 'run_in_executor' calls in render_poller will use this loop.
    
    result = render_cap.execute_tool("brain_start_deploy_poll", {
        "service_id": "srv-test",
        "commit_sha": "abc1234"
    })
    
    if isinstance(result, dict) and result.get("success"):
        print(f"✅ Polling Started: {result['message']}")
        poll_id = result.get("poll_id")
    else:
        print(f"❌ Start Failed: {result}")
        sys.exit(1)

    print()
    
    # 3. Test brain_check_deploy (Wait for simulation)
    print(">> Intent: brain_check_deploy")
    print("   Waiting 3 seconds for simulation to complete...")
    await asyncio.sleep(3) 
    
    status = render_cap.execute_tool("brain_check_deploy", {"service_id": "srv-test"})
    
    if isinstance(status, dict) and status.get("status") == "complete":
        print(f"✅ Poll Complete!")
        print(f"   Result: {status['result']}")
        if status['result'].get("simulated"):
             print("   (Confirmed Simulation Mode)")
    else:
        print(f"❌ Unexpected Status: {status}")
        
    print()

    # 4. Test brain_smoke_test
    print(">> Intent: brain_smoke_test")
    # Using a reliable public API for smoke test
    smoke = render_cap.execute_tool("brain_smoke_test", {
        "url": "https://httpbin.org",
        "endpoint": "/get" 
    })
    
    if isinstance(smoke, dict) and smoke.get("passed"):
        print(f"✅ Smoke Test Passed: {smoke['latency_ms']:.2f}ms")
    else:
        print(f"❌ Smoke Test Failed: {smoke}")

if __name__ == "__main__":
    asyncio.run(verify_render_poller())
