
import pytest
import json
import os
import tempfile
from pathlib import Path
from mcp_server_nucleus.runtime.session_ops import _save_session, _resume_session
from mcp_server_nucleus.runtime.error_sanitizer import SanitizedError

@pytest.fixture
def mock_brain():
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_brain = os.environ.get("NUCLEUS_BRAIN_PATH")
        os.environ["NUCLEUS_BRAIN_PATH"] = tmp_dir
        
        p = Path(tmp_dir)
        (p / "sessions").mkdir(parents=True, exist_ok=True)
        (p / "ledger").mkdir(parents=True, exist_ok=True)
        (p / "secrets").mkdir(parents=True, exist_ok=True)
        
        # Create a mock secret
        (p / "secrets" / ".ipc_secret").write_bytes(b"test-signing-secret-123")
        
        yield p
        
        if original_brain:
            os.environ["NUCLEUS_BRAIN_PATH"] = original_brain
        else:
            del os.environ["NUCLEUS_BRAIN_PATH"]

def test_session_signing_and_resumption(mock_brain):
    """Test that a signed session can be saved and resumed correctly."""
    context = "Security Hardening"
    res = _save_session(context=context, active_task="Implement Phase 12")
    assert res["success"] is True
    session_id = res["session_id"]
    
    # Verify file exists and has a signature
    session_file = mock_brain / "sessions" / f"{session_id}.json"
    assert session_file.exists()
    
    with open(session_file, "r") as f:
        data = json.load(f)
        assert "signature" in data
        assert len(data["signature"]) == 32

    # Attempt to resume
    resumed = _resume_session(session_id)
    assert resumed["session_id"] == session_id
    assert resumed["context"] == context

def test_session_tampering_rejection(mock_brain):
    """Test that manual tampering with a session file causes rejection."""
    res = _save_session(context="Original Context")
    session_id = res["session_id"]
    session_file = mock_brain / "sessions" / f"{session_id}.json"
    
    # TAMPER: Change the context manually
    with open(session_file, "r") as f:
        data = json.load(f)
    
    data["context"] = "Hijacked Context"
    
    with open(session_file, "w") as f:
        json.dump(data, f)
        
    # Attempt to resume should fail
    result = _resume_session(session_id)
    
    assert result.get("success") is False
    assert result.get("error") == "permission_denied"
    assert "signature verification failed" in result.get("message", "")

def test_session_missing_signature_rejection(mock_brain):
    """Test that sessions without signatures are rejected."""
    # Create a raw session file without a signature (legacy style)
    session_id = "legacy_session_123"
    session_file = mock_brain / "sessions" / f"{session_id}.json"
    legacy_data = {
        "id": session_id,
        "context": "Legacy",
        "nucleus_version": "1.0.7"
    }
    with open(session_file, "w") as f:
        json.dump(legacy_data, f)
        
    # Attempt to resume should fail
    result = _resume_session(session_id)
        
    assert result.get("success") is False
    assert "signature verification failed or missing" in result.get("message", "")
