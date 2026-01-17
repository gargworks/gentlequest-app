#!/usr/bin/env python3
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/mcp-server-nucleus/src")

from mcp_server_nucleus.runtime.factory import ContextFactory

# Configure logging
logging.basicConfig(level=logging.ERROR)

def verify_proof_system():
    print("=== Proof System Verification ===")
    
    # 1. Initialize Factory and Context
    factory = ContextFactory()
    intent = "brain_generate_proof" # Should trigger ProofSystem
    context = factory.create_context("test-session", intent)
    
    tools = {t["name"]: t for t in context["tools"]}
    
    if "brain_generate_proof" in tools:
        print("✅ Proof tools loaded")
    else:
        print("❌ Proof tools NOT loaded")
        sys.exit(1)
        
    print()
    
    # 2. Test brain_generate_proof
    print(">> Intent: brain_generate_proof")
    proof_sys = context["capability_instances"][-1] # Assuming it's the last one added
    
    # Verify it is indeed ProofSystem
    if proof_sys.name != "proof_system":
         # Find it
         for cap in context["capability_instances"]:
             if cap.name == "proof_system":
                 proof_sys = cap
                 break
    
    result = proof_sys.execute_tool("brain_generate_proof", {
        "feature_id": "verification_test_feature",
        "thinking": "### Optimization Analysis\n1. Use fast path\n2. Cache results\n\nChoice: 2 (Caching)",
        "deployed_url": "https://test.gentlequest.com/api/v1/verify",
        "files_changed": ["src/main.py", "tests/test_main.py"],
        "risk_level": "low",
        "rollback_time": "5m"
    })
    
    if result.get("success"):
        print(f"✅ Proof Generated: {result['message']}")
        print(f"   Path: {result['path']}")
    else:
        print(f"❌ Generation Failed: {result}")
        sys.exit(1)

    print()
    
    # 3. Test brain_get_proof
    print(">> Intent: brain_get_proof")
    content = proof_sys.execute_tool("brain_get_proof", {"feature_id": "verification_test_feature"})
    
    if "Proof: verification_test_feature" in content and "Thinking" in content:
        print("✅ Proof Retrieved Successfully")
        print("   Content Snippet:")
        print("   " + content.split("\n")[0])
        print("   " + content.split("\n")[4]) # Thinking header
    else:
        print(f"❌ Retrieval Failed or Content Mismatch: {content[:100]}...")
        sys.exit(1)
        
    print()
    
    # 4. Verify File Existence
    path = Path(result['path'])
    if path.exists():
        print(f"✅ File exists on disk: {path}")
    else:
        print(f"❌ File missing on disk: {path}")

if __name__ == "__main__":
    verify_proof_system()
