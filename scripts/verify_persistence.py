
import os
import sys
from pathlib import Path
import json

# Add mcp-server-nucleus to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus import commitment_ledger
from mcp_server_nucleus.runtime import storage

def test_local_persistence():
    print("Testing Local Persistence...")
    
    # Setup test brain
    brain_path = Path(".brain_test")
    brain_path.mkdir(exist_ok=True)
    
    ledger_path = brain_path / "commitments" / "ledger.json"
    if ledger_path.exists():
        ledger_path.unlink()
    
    # 1. Test Add Commitment
    print("1. Adding Commitment...")
    commitment_ledger.add_commitment(
        brain_path=brain_path,
        source_file="test.py",
        source_line=1,
        description="Test Persistence",
        comm_type="test"
    )
    
    # 2. Verify File Created
    if not ledger_path.exists():
        print("FAIL: Ledger file not created locally.")
        return
        
    content = ledger_path.read_text()
    data = json.loads(content)
    if len(data["commitments"]) != 1:
        print(f"FAIL: Expected 1 commitment, got {len(data['commitments'])}")
        return
        
    print(f"PASS: Ledger created with {len(data['commitments'])} item.")
    
    # 3. Test Storage Abstraction direct access
    print("3. Testing Storage Abstraction Read...")
    read_content = storage.read_brain_file(ledger_path)
    if len(read_content) != len(content):
        print("FAIL: Storage read content mismatch.")
        return
        
    print("PASS: Storage abstraction works.")
    
    # Cleanup
    import shutil
    shutil.rmtree(brain_path)
    print("Cleanup Complete.")

if __name__ == "__main__":
    test_local_persistence()
