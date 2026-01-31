#!/usr/bin/env python3
"""
Direct test of the swarm orchestration system.
Bypasses MCP to verify the core functionality works.
"""

import sys
import os
import time

# Add the package to path
sys.path.insert(0, '/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src')

# Set environment
os.environ['NUCLEUS_BRAIN_PATH'] = '/Users/lokeshgarg/ai-mvp-backend/.brain'

from mcp_server_nucleus.runtime.swarm import _orchestrate_swarm

print("=" * 60)
print("DIRECT SWARM TEST")
print("=" * 60)

# Test the swarm
mission = "Research 3 top universities known for mental health innovation and identify their counseling directors"
agents = ["researcher", "critic"]

print(f"\n📋 Mission: {mission}")
print(f"🤖 Agents: {agents}")
print("\n🚀 Starting swarm...\n")

result = _orchestrate_swarm(mission, agents)

print("\n" + "=" * 60)
print("RESULT:")
print("=" * 60)
import json
print(json.dumps(result, indent=2))

if result.get("success"):
    mission_id = result.get("mission_id")
    print(f"\n✅ Swarm started successfully!")
    print(f"📁 Check results at: .brain/swarms/{mission_id}/summary.md")
    print(f"\n⏳ Waiting 20 seconds for agents to execute...")
    time.sleep(20)
    
    # Check for results
    summary_path = f"/Users/lokeshgarg/ai-mvp-backend/.brain/swarms/{mission_id}/summary.md"
    if os.path.exists(summary_path):
        print(f"\n📄 Summary file created!")
        with open(summary_path) as f:
            print(f.read()[:500])
    else:
        print(f"\n⚠️ Summary not yet available (agents may still be running)")
else:
    print(f"\n❌ Swarm failed: {result.get('error')}")
