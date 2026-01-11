
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "mcp-server-nucleus/src"))

from mcp_server_nucleus import commitment_ledger

def force_scan():
    # Set brain path to current artifact dir
    brain_path = Path("/Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1")
    
    print(f"Scanning Brain: {brain_path}")
    
    # Reset Ledger for clean state
    ledger_path = brain_path / "ledger" / "commitments.json"
    if ledger_path.exists():
        print("Resetting existing ledger...")
        ledger_path.unlink()
    
    # Run scan
    try:
        result = commitment_ledger.scan_for_commitments(brain_path)
        print("Scan Result:", result)
        
        # Load ledger to see count
        ledger = commitment_ledger.load_ledger(brain_path)
        count = len([c for c in ledger["commitments"] if c["status"] == "open"])
        print(f"Total Open Commitments: {count}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    force_scan()
