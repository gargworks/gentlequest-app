import subprocess
import os
from pathlib import Path
import json
import pytest

def test_summon_integrity():
    """Verify that 'nucleus summon' correctly passes session IDs and environment."""
    project_root = Path("/Users/lokeshgarg/ai-mvp-backend")
    raw_brain_path = project_root / ".brain_test_summon"
    brain_path = raw_brain_path / ".brain"
    raw_brain_path.mkdir(parents=True, exist_ok=True)
    brain_path.mkdir(parents=True, exist_ok=True)
    (brain_path / "session").mkdir(parents=True, exist_ok=True)
    (brain_path / "session" / "current_id").write_text("mother-session-123")
    
    env = os.environ.copy()
    env["NUCLEUS_BRAIN_PATH"] = str(brain_path.absolute())
    env["NUCLEUS_SESSION_ID"] = "mother-session-123"
    env["NUCLEAR_BRAIN_PATH"] = str(brain_path.absolute())
    
    # We'll use a mock 'chief' command by setting up a dummy script if needed,
    # but here we just want to verify the 'summon' logic in cli.py
    # We can mock TaskBridge or just check the log
    
    # Run summon command
    cmd = ["python3", "-m", "mcp_server_nucleus.cli", "summon", "Critic", "Review my code"]
    project_root = Path("/Users/lokeshgarg/ai-mvp-backend")
    env["PYTHONPATH"] = f"{project_root / 'mcp-server-nucleus' / 'src'}:{project_root}:{env.get('PYTHONPATH', '')}"
    
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    
    print(f"STDOUT: {proc.stdout}")
    print(f"STDERR: {proc.stderr}")
    
    assert proc.returncode == 0, f"Summon failed with code {proc.returncode}. STDERR: {proc.stderr}"
    assert "Summoning Critic" in proc.stdout
    assert "mother-session-123" in proc.stdout
    
    # Check summon.log in the brain
    log_path = brain_path / "logs" / "summon.log"
    assert log_path.exists()
    
    # Clean up
    import shutil
    shutil.rmtree(raw_brain_path)

if __name__ == "__main__":
    test_summon_integrity()
