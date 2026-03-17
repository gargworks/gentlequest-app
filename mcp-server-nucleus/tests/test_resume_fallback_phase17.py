import subprocess
import os
from pathlib import Path
import time
import pytest

def test_resume_fallback():
    """Verify that the coordinator falls back to a fresh session if resume fails."""
    project_root = Path("/Users/lokeshgarg/ai-mvp-backend")
    raw_brain_path = project_root / ".brain_test_resume"
    brain_path = raw_brain_path / ".brain"
    raw_brain_path.mkdir(parents=True, exist_ok=True)
    brain_path.mkdir(parents=True, exist_ok=True)
    (brain_path / "session").mkdir(parents=True, exist_ok=True)
    
    env = os.environ.copy()
    env["NUCLEUS_BRAIN_PATH"] = str(brain_path.absolute())
    env["NUCLEUS_SESSION_ID"] = "invalid-session-123"
    env["NUCLEAR_BRAIN_PATH"] = str(brain_path.absolute())
    env["NUCLEUS_MAX_DEPTH"] = "10"
    
    # We want to simulate 'gemini' CLI failure on resume.
    # Since we can't easily mock the 'gemini' binary here without a real shell environment,
    # we'll look for the "Error resuming session" logic in coordinator.py.
    
    # We'll create a mock 'gemini' script
    mock_gemini = Path("gemini")
    mock_gemini.write_text("""#!/usr/bin/env python3
import sys
if "--resume" in sys.argv:
    print("Error resuming session: Session not found")
    sys.exit(1)
else:
    print("Starting fresh session...")
    sys.exit(0)
""", encoding="utf-8")
    mock_gemini.chmod(0o755)
    
    env["PATH"] = f".:{env.get('PATH', '')}"
    project_root = Path("/Users/lokeshgarg/ai-mvp-backend")
    env["PYTHONPATH"] = f"{project_root / 'mcp-server-nucleus' / 'src'}:{project_root}:{env.get('PYTHONPATH', '')}"
    
    # Run coordinator in a separate process
    # Use -u for unbuffered output
    cmd = ["python3", "-u", "-m", "nucleus.agents.coordinator", "--task", "test task"]
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired as e:
        print(f"TIMEOUT. STDOUT: {e.stdout.decode() if e.stdout else ''}")
        print(f"STDOUT: {e.stderr.decode() if e.stderr else ''}")
        raise
    
    print(f"STDOUT: {proc.stdout}")
    print(f"STDERR: {proc.stderr}")
    
    assert "Gemini resume failed" in proc.stderr or "Gemini resume failed" in proc.stdout
    assert "Retrying fresh" in proc.stderr or "Retrying fresh" in proc.stdout
    assert "Starting fresh session..." in proc.stdout
    
    # Clean up
    mock_gemini.unlink()
    import shutil
    shutil.rmtree(raw_brain_path)

if __name__ == "__main__":
    test_resume_fallback()
