
import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

try:
    from mcp_server_nucleus import brain_fix_code, _critique_code
    print("✅ Libraries imported")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

TARGET = "/Users/lokeshgarg/ai-mvp-backend/tools/nucleus-hud/app/components/clinical/NucleusCrisisModal.tsx"

# These were the issues identified by the Critic in the previous run
ISSUES = """
[
    {"severity": "WARNING", "line": 25, "message": "Consider externalizing hardcoded strings like 'SAFETY_INTERVENTION' for i18n."},
    {"severity": "WARNING", "line": 19, "message": "The role='alertdialog' should be used with aria-modal='true'."},
    {"severity": "WARNING", "line": 17, "message": "Ensure animate-fadeIn classes are defined in globals.css."}
]
"""

if __name__ == "__main__":
    print(f"🔧 Applying Self-Healing to Nucleus Code: {TARGET}")
    
    # 1. Apply Fix
    result = brain_fix_code(TARGET, ISSUES)
    print(f"Fix Status: {result}")
    
    # 2. Re-verify with Critic
    print("🧐 Re-evaluating Score...")
    critique_result = _critique_code(TARGET, "Verify Self-Healing Efficacy")
    print(f"Final Score: {critique_result.get('score')}")
    print("Issues Remaining:")
    print(json.dumps(critique_result.get("issues"), indent=2))
