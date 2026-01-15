
import sys
import os
from pathlib import Path

# Setup paths
sys.path.append("mcp-server-nucleus/src")
from mcp_server_nucleus.runtime.factory import ContextFactory

def verify_fixer():
    print("🚑 Verifying Self-Healing (The Fixer)...")
    
    # 1. Initialize Factory
    brain_path = Path(".brain").resolve()
    factory = ContextFactory(brain_path=brain_path)
    
    # 2. Check Registry
    caps = factory.list_capabilities()
    if "self_healing_ops" not in caps:
        print("❌ 'self_healing_ops' NOT found in registry.")
        sys.exit(1)
    print("✅ 'self_healing_ops' loaded.")
    
    fixer = factory._registry.get("self_healing_ops")
    
    # 3. Test brain_scan_health (With Mock Command)
    print("\n[Test 1] brain_scan_health (Simulating Success)")
    os.environ["NUCLEUS_HEALTH_CMD"] = "echo 'All Systems Nominal'"
    # Re-init capability to pick up env var (or just hack it since it's already instantiated)
    fixer.health_cmd = "echo 'All Systems Nominal'" # Manual override for test
    
    result = fixer.execute_tool("brain_scan_health", {})
    print(f"Result: {result}")
    
    if result.get("success") and "All Systems Nominal" in result.get("output"):
        print("✅ Health Check (Success) Verified.")
    else:
        print("❌ Health Check Failed.")
        sys.exit(1)

    # 4. Test brain_scan_health (Simulating Failure)
    print("\n[Test 2] brain_scan_health (Simulating Failure)")
    fixer.health_cmd = "echo 'Simulated Syntax Error'; exit 1"
    
    result = fixer.execute_tool("brain_scan_health", {})
    print(f"Result: {result}")
    
    if not result.get("success") and "Simulated Syntax Error" in result.get("output"):
        print("✅ Health Check (Failure Detection) Verified.")
    else:
        print("❌ Failure Detection Failed.")
        sys.exit(1)

    # 5. Test brain_generate_fix_plan
    print("\n[Test 3] brain_generate_fix_plan")
    plan = fixer.execute_tool("brain_generate_fix_plan", {
        "error_log": "SyntaxError: invalid syntax in file.py line 10",
        "context_files": ["file.py"]
    })
    
    print(f"Generated Plan:\n{plan}")
    if "Recommended Strategy" in plan:
        print("✅ Fix Plan Generation Verified.")
    else:
        print("❌ Fix Plan Generation Failed.")
        sys.exit(1)

if __name__ == "__main__":
    verify_fixer()
