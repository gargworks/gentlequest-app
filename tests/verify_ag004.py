
import sys
import os
import json
import time
from unittest.mock import MagicMock
from pathlib import Path
import tempfile
import shutil
import builtins

# Setup paths
src_path = os.path.abspath("mcp-server-nucleus/src")
sys.path.append(src_path)

# Mock fastmcp
sys.modules["fastmcp"] = None

# IMPORTANT: Mock get_brain_path to return something valid or mock functionality
# Since _save_session and others use get_brain_path(), which expects env var.

# Also, mcp must be importable.
from mcp_server_nucleus import (
    brain_save_session, 
    brain_resume_session, 
    brain_emit_event, 
    brain_list_tasks, 
    brain_add_task
)

def test_ag004():
    temp_dir = tempfile.mkdtemp()
    try:
        os.environ["NUCLEAR_BRAIN_PATH"] = temp_dir
        
        # Initialize internal state if needed (directories)
        Path(temp_dir).joinpath("ledger").mkdir()
        Path(temp_dir).joinpath("sessions").mkdir()
        
        # Test 1: brain_add_task
        print("Testing brain_add_task...")
        result_add = brain_add_task("Test task")
        data = json.loads(result_add)
        assert data["success"] is True
        assert "data" in data
        assert "timestamp" in data
        assert data["timestamp"].endswith("Z")
        print("✅ brain_add_task passed")
        
        # Test 2: brain_list_tasks
        print("Testing brain_list_tasks...")
        result_list = brain_list_tasks()
        data = json.loads(result_list)
        assert data["success"] is True
        assert isinstance(data["data"], list)
        print("✅ brain_list_tasks passed")
        
        # Test 3: brain_save_session
        print("Testing brain_save_session...")
        result_save = brain_save_session("Test Context")
        data = json.loads(result_save)
        # Note: If _save_session actually works, it returns Dict.
        assert data["success"] is True
        sessionId = data["data"].get("session_id")
        print("✅ brain_save_session passed")
        
        # Test 4: brain_resume_session
        print("Testing brain_resume_session...")
        # Just resume whatever
        # Since we just saved, maybe we can resume?
        # _resume_session likely scans for sessions.
        result_resume = brain_resume_session(sessionId)
        data = json.loads(result_resume)
        assert data["success"] is True
        print("✅ brain_resume_session passed")
        
        # Test 5: brain_emit_event
        print("Testing brain_emit_event...")
        result_emit = brain_emit_event("test_type", "test_emitter", {})
        data = json.loads(result_emit)
        assert data["success"] is True
        assert "event_id" in data["data"]
        print("✅ brain_emit_event passed")
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    try:
        test_ag004()
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
