
import sys
import os
import json
import time
from unittest.mock import MagicMock
from pathlib import Path
import tempfile
import shutil

# Setup paths
src_path = os.path.abspath("mcp-server-nucleus/src")
sys.path.append(src_path)

# Mock fastmcp (None to avoid MagicMock pollution)
sys.modules["fastmcp"] = None

from mcp_server_nucleus import brain_save_session, brain_resume_session, get_brain_path

def test_ag005():
    temp_dir = tempfile.mkdtemp()
    try:
        os.environ["NUCLEAR_BRAIN_PATH"] = temp_dir
        Path(temp_dir).joinpath("sessions").mkdir()
        Path(temp_dir).joinpath("ledger").mkdir()
        
        # 1. Save Session
        print("Saving session...")
        result_save = brain_save_session("Version Test")
        data_save = json.loads(result_save)
        assert data_save["success"] is True
        session_id = data_save["data"]["session_id"]
        
        # 2. Verify File Content
        session_path = Path(temp_dir) / "sessions" / f"{session_id}.json"
        with open(session_path, "r") as f:
            session_data = json.load(f)
            
        print(f"Session Data: {session_data}")
        assert session_data.get("schema_version") == "1.0"
        assert session_data.get("nucleus_version") == "0.5.0"
        print("✅ Version fields present")
        
        # 3. Tamper with file
        print("Tampering with versions...")
        session_data["schema_version"] = "0.9"
        session_data["nucleus_version"] = "0.4.0"
        with open(session_path, "w") as f:
            json.dump(session_data, f)
            
        # 4. Resume
        print("Resuming session...")
        result_resume = brain_resume_session(session_id)
        data_resume = json.loads(result_resume)
        assert data_resume["success"] is True
        
        warnings = data_resume["data"].get("warnings", [])
        print(f"Warnings: {warnings}")
        
        assert len(warnings) >= 2
        assert any("Schema mismatch" in w for w in warnings)
        assert any("Nucleus update" in w for w in warnings)
        print("✅ Warnings verified")
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    try:
        test_ag005()
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
