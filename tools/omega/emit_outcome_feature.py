
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

from mcp_server_nucleus import _emit_event

if __name__ == "__main__":
    _emit_event("feature_registered", "brain", {
        "feature": "outcome_dashboard",
        "component": "NucleusWellnessChart",
        "category": "clinical_frontend",
        "status": "implemented"
    })
    print("Emitted feature_registered: outcome_dashboard")
