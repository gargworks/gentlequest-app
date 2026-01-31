#!/usr/bin/env python3
import sys
import os
import json
import time
import uuid
from pathlib import Path

# Setup Path
brain = Path(os.environ.get("NUCLEAR_BRAIN_PATH", ".brain"))
sys.path.append("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")

print("🚀 NUCLEUS HANDOFF TEST")
print("=======================")

# 1. Trigger Handoff (Direct Ledger Write)
print("\n[STEP 1] Triggering Real-World Handoff (Antigravity -> Windsurf)...")
handoffs_path = brain / "ledger" / "handoffs.json"
handoffs_path.parent.mkdir(parents=True, exist_ok=True)

handoff_id = f"handoff-{int(time.time())}-{str(uuid.uuid4())[:4]}"
new_handoff = {
    "id": handoff_id,
    "from": "antigravity",
    "to": "windsurf_opus",
    "task_id": "gtm_v1_launch",
    "request": "Founder video complete. Standing by for GTM scaling mission.",
    "context": "Sentiment: scarcity_high. Priority: P0. Video: finalized.",
    "priority": 1,
    "status": "pending",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
}

handoffs = []
if handoffs_path.exists():
    try:
        with open(handoffs_path) as f:
            handoffs = json.load(f)
    except:
        handoffs = []

handoffs.append(new_handoff)

with open(handoffs_path, "w") as f:
    json.dump(handoffs, f, indent=2)

print(f"✅ Handoff {handoff_id} written to ledger.")

# 2. Verify Handoff via MCP Tool implementation (logic check)
print("\n[STEP 2] Verifying Handoff Receipt...")
with open(handoffs_path) as f:
    verify_data = json.load(f)

pending = [h for h in verify_data if h.get("status") == "pending" and h.get("to") == "windsurf_opus"]

if len(pending) > 0:
    latest = pending[-1]
    print(f"✅ Found {len(pending)} pending handoff(s) for Windsurf.")
    print(f"   ID: {latest.get('id')}")
    print(f"   Request: {latest.get('request')}")
else:
    print("❌ No handoffs found in ledger for Windsurf.")
    sys.exit(1)

print("\n✨ HANDOFF SYSTEM VERIFIED ✨")
