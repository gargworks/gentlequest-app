
import os
import sys
import json
import pytest
from pathlib import Path

# Add source to path
sys.path.append(str(Path.cwd() / "mcp-server-nucleus/src"))

from mcp_server_nucleus.runtime.critic import _critique_code

@pytest.mark.skipif(bool(os.getenv("CI")) or bool(os.getenv("GITHUB_ACTIONS")), reason="Requires local brain fixture")
def test_critique_logic():
    print("🧪 Testing Critic Logic...")
    
    # 1. Create Bad Code
    bad_code_path = Path("tests/bad_code.py")
    bad_code_content = """
import os

def delete_database():
    # SECURITY RISK: Hardcoded credentials
    password = "super_secret_password"
    
    # DANGEROUS: System command injection risk
    os.system("rm -rf /")
    
    print("Database deleted")
"""
    bad_code_path.write_text(bad_code_content)
    
    try:
        # 2. Run Critique
        print(f"🧐 Critiquing {bad_code_path}...")
        result = _critique_code(str(bad_code_path))
        
        # 3. Analyze Result
        print("📊 Result:", json.dumps(result, indent=2))
        
        if not result["success"]:
            print("❌ Critique failed to run")
            sys.exit(1)
            
        status = result["status"]
        critique = result["critique"]
        payload = critique.get("payload", {})
        
        # 4. Assertions
        if status != "BLOCKED":
            print(f"❌ Expected BLOCKED, got {status}")
            sys.exit(1)
            
        issues = str(payload)
        if "rm -rf" not in issues and "system" not in issues:
            print("❌ Critic missed the dangerous system command")
            sys.exit(1)
            
        if "password" not in issues:
            print("❌ Critic missed the hardcoded password")
            sys.exit(1)
            
        print("✅ Critic successfully caught the bad code!")
        
    finally:
        # Cleanup
        if bad_code_path.exists():
            bad_code_path.unlink()

if __name__ == "__main__":
    test_critique_logic()
