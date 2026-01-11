
import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

from mcp_server_nucleus import brain_list_services

if __name__ == "__main__":
    print("Function imported successfully.")
    result = brain_list_services()
    print("Result:")
    print(result)
    
    # Parse to verify structure
    data = json.loads(result)
    if data.get("mock") is True:
        print("VERIFIED: Mock data returned.")
    else:
        print("VERIFIED: Real data returned.")
