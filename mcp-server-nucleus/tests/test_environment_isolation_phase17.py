import os
import pytest
from pathlib import Path
from mcp_server_nucleus.runtime.isolation_layer import EnvironmentSanitizer

def test_environment_sanitization():
    """
    Verify that EnvironmentSanitizer correctly strips non-whitelisted variables
    and virtualizes HOME/TMPDIR.
    """
    # 1. Setup a dirty environment
    dirty_env = {
        "PATH": "/usr/bin:/bin",
        "SECRET_KEY": "supersecret",
        "USER": "attacker",
        "HOME": "/home/attacker",
        "GEMINI_API_KEY": "actual-key",
        "CUSTOM_VAR": "leave-me-out"
    }
    
    sanitizer = EnvironmentSanitizer(sandbox_root=Path("/tmp/nucleus_test_sandbox"))
    isolated = sanitizer.get_isolated_env(base_env=dirty_env)
    
    # 2. Verify Whitelist
    assert "PATH" in isolated
    assert "GEMINI_API_KEY" in isolated
    assert isolated["GEMINI_API_KEY"] == "actual-key"
    
    # 3. Verify Stripping
    assert "SECRET_KEY" not in isolated
    assert "USER" not in isolated
    assert "CUSTOM_VAR" not in isolated
    
    # 4. Verify Virtualization
    assert isolated["HOME"] == "/tmp/nucleus_test_sandbox"
    assert isolated["TMPDIR"] == "/tmp/nucleus_test_sandbox/tmp"
    assert isolated["SHELL"] == "/bin/sh"
    
    # 5. Verify filesystem creation
    assert Path("/tmp/nucleus_test_sandbox/tmp").is_dir()
    
    print("✅ Environment isolation verified: Whitelist applied, sensitive vars stripped.")

if __name__ == "__main__":
    test_environment_sanitization()
