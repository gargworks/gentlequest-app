
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

from mcp_server_nucleus import _emit_event

if __name__ == "__main__":
    _emit_event("feature_validated", "brain", {
        "feature": "self_healing_fixer",
        "category": "nucleus_core",
        "status": "verified",
        "metrics": {
            "initial_score": 70,
            "fixed_score": 85,
            "target": "generic_crisis_modal.tsx"
        }
    })
    print("Emitted feature_validated: self_healing_fixer")
