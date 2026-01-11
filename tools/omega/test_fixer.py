
import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

try:
    from mcp_server_nucleus import brain_fix_code
    print("✅ Successfully imported brain_fix_code")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

TARGET_FILE = "/Users/lokeshgarg/ai-mvp-backend/tools/nucleus-hud/app/components/clinical/GenericCrisisModal.tsx"

ISSUES = """
[
    {"severity": "WARNING", "line": 9, "message": "Inline styles are used which reduces maintainability. Use Tailwind classes."},
    {"severity": "WARNING", "line": 14, "message": "No ARIA role defined for modal. Use role='alertdialog'."},
    {"severity": "WARNING", "line": 15, "message": "Warning text is too generic. Be specific about resources."}
]
"""

if __name__ == "__main__":
    print(f"🔧 Attempting to FIX: {TARGET_FILE}")
    
    # Run Fixer
    result = brain_fix_code(TARGET_FILE, ISSUES)
    print(f"Result: {result}")
    
    # Read file to verify change
    content = Path(TARGET_FILE).read_text()
    if "role='alertdialog'" in content or 'role="alertdialog"' in content:
         print("✅ VERIFIED: ARIA role added.")
    else:
         print("❌ FAILED: ARIA role missing.")
         
    if "className=" in content:
         print("✅ VERIFIED: Tailwind classes added.")
    else:
         print("❌ FAILED: Tailwind classes missing.")
