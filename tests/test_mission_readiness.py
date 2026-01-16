
import sys
import os
import unittest
import importlib.util

# 1. Setup Environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
MCP_SOURCE = os.path.join(PROJECT_ROOT, "mcp-server-nucleus", "src")

print("🔍 Checking Nucleus Readiness...")
print(f"📂 Project Root: {PROJECT_ROOT}")
print(f"📂 MCP Source: {MCP_SOURCE}")

# 2. Add Path
if MCP_SOURCE not in sys.path:
    sys.path.append(MCP_SOURCE)
    print("✅ Added MCP Source to sys.path")

# 3. Test Import
try:
    import mcp_server_nucleus
    print(f"✅ Import Successful: {mcp_server_nucleus.__file__}")
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MCP Import Skipped (not installed): {e}")
    MCP_AVAILABLE = False
    # Don't exit - allow pytest collection to proceed

# 4. Run Unit Tests (only if run directly, not via pytest)
if __name__ == "__main__" and MCP_AVAILABLE:
    print("\n🧪 Running Unit Tests...")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Discover tests in current directory
    test_files = [
        'test_health_logic.py',
        'test_research_api.py',
        'test_chat_api.py'
    ]

    for test_file in test_files:
        # Load module dynamically
        module_name = test_file.replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, os.path.join(BASE_DIR, test_file))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Add tests from module
        module_suite = loader.loadTestsFromModule(module)
        suite.addTests(module_suite)

    # Run
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("\n🚀 ALL SYSTEMS NOMINAL. Ready for Launch.")
        sys.exit(0)
    else:
        print("\n⚠️ TESTS FAILED. Abort Launch.")
        sys.exit(1)
elif __name__ == "__main__":
    print("\n⚠️ MCP not available - skipping mission readiness tests")
    sys.exit(0)
