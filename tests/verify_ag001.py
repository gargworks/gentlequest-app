
import sys
import os
import json

from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath("mcp-server-nucleus/src"))

# Mock FastMCP as missing to trigger ImportError and use internal MockMCP
sys.modules["fastmcp"] = None

# Now import
from mcp_server_nucleus import brain_health, START_TIME

def test_brain_health():
    # Setup environment
    os.environ["NUCLEAR_BRAIN_PATH"] = "/tmp/test_brain"
    
    # Mock get_brain_path to avoid FS checks if needed, 
    # but the tool handles exceptions gracefully.
    
    # Call the tool
    # Note: FastMCP decorators might wrap the function. 
    # If MockMCP was used (because we mocked fastmcp above to fail or just be a mock),
    # the decorator should return the function itself or a wrapper.
    # Our MockMCP implementation in __init__.py returns the function itself.
    
    result = brain_health()
    print(f"DEBUG RAW RESULT: '{result}'")
    data = json.loads(result)
    
    print(f"DEBUG: {data}")
    
    assert data["status"] == "healthy"
    assert data["version"] == "0.5.0"
    assert "uptime_seconds" in data
    assert "python_version" in data

if __name__ == "__main__":
    try:
        test_brain_health()
        print("✅ test_brain_health Passed")
    except Exception as e:
        print(f"❌ test_brain_health Failed: {e}")
        sys.exit(1)
