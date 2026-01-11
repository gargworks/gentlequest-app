
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

from mcp_server_nucleus import _depth_push

if __name__ == "__main__":
    _depth_push("Verifying Omega")
    print("Depth pushed.")
