
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

from mcp_server_nucleus import _emit_event

if __name__ == "__main__":
    _emit_event("omega_launched", "omega", {
        "status": "initiated",
        "phase": "verification"
    })
    print("Emitted omega_launched")
