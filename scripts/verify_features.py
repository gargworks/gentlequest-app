
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/mcp-server-nucleus/src")

from mcp_server_nucleus.runtime.factory import ContextFactory
import inspect
print(f"DEBUG: ContextFactory file: {inspect.getfile(ContextFactory)}")
print(f"DEBUG: create_context signature: {inspect.signature(ContextFactory.create_context)}")

# Configure logging
logging.basicConfig(level=logging.ERROR)

def verify_feature_map():
    print("=== Feature Map Verification ===")
    
    # 1. Initialize Runtime
    factory = ContextFactory()
    
    # 2. Simulate User Intent ("I want to add a feature to the map")
    intent = "add feature map"
    context = factory.create_context("test-session", intent)
    
    # Verify tools loaded
    tool_names = [t["name"] for t in context["tools"]]
    if "brain_add_feature" in tool_names:
        print("✅ Feature Map tools loaded")
    else:
        print("❌ Feature Map tools MISSING")
        return

    # 3. Test: Add Feature
    print("\n>> Intent: brain_add_feature")
    feature_map_cap = factory._registry["feature_map"]
    
    add_args = {
        "product": "gentlequest",
        "name": "Integration Test Feature",
        "description": "A feature created during verification script run",
        "source": "verification_script",
        "version": "1.0.0",
        "status": "development",
        "how_to_test": ["Run verify_features.py"],
        "expected_result": "Feature appears in JSON",
        "tags": ["test", "verification"]
    }
    
    result_add = feature_map_cap.execute_tool("brain_add_feature", add_args)
    if isinstance(result_add, dict) and result_add.get("success"):
        print(f"✅ Feature Added: {result_add['feature']['id']}")
    else:
        print(f"❌ Failed to add feature: {result_add}")
    
    # 4. Test: List Features
    print("\n>> Intent: brain_list_features")
    list_args = {"product": "gentlequest"}
    result_list = feature_map_cap.execute_tool("brain_list_features", list_args)
    
    found = False
    for f in result_list:
        if f["name"] == "Integration Test Feature":
            found = True
            print(f"✅ Found in list: {f['id']} (v{f['version']})")
    
    if not found:
        print("❌ Feature not found in list")
        
    # 5. Test: Update Feature
    print("\n>> Intent: brain_update_feature")
    update_args = {
        "feature_id": "integration_test_feature",
        "status": "staged",
        "version": "1.0.1"
    }
    result_update = feature_map_cap.execute_tool("brain_update_feature", update_args)
    
    if isinstance(result_update, dict) and result_update.get("success"):
        print(f"✅ Feature Updated: Status={result_update['feature']['status']}, Version={result_update['feature']['version']}")
    else:
        print(f"❌ Failed to update feature: {result_update}")

    # 6. Test: Validate Feature
    print("\n>> Intent: brain_mark_validated")
    val_args = {
        "feature_id": "integration_test_feature",
        "result": "passed"
    }
    result_val = feature_map_cap.execute_tool("brain_mark_validated", val_args)
    
    if isinstance(result_val, dict) and result_val.get("success"):
        print(f"✅ Feature Validated: Result={result_val['result']} at {result_val['timestamp']}")
    else:
        print(f"❌ Failed to validate feature: {result_val}")

if __name__ == "__main__":
    verify_feature_map()
