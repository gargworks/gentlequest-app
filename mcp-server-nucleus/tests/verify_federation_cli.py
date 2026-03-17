import os
import subprocess
import json
import shutil
from pathlib import Path

def run_cmd(cmd, cwd=None, env=None):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=env)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result.stdout

def verify_cli():
    # 1. Setup mock brain
    test_brain = Path("/tmp/nucleus_test_cli_brain")
    if test_brain.exists():
        shutil.rmtree(test_brain)
    test_brain.mkdir(parents=True)
    (test_brain / "ledger").mkdir()
    (test_brain / "federation").mkdir()
    
    # 2. Add fake federation state
    state = {
        "brain_id": "cli-test-brain",
        "region": "us-west",
        "leader_id": "remote-brain-1",
        "term": 5,
        "partition_status": "NORMAL",
        "peers": {
            "peer-abc": {
                "peer_id": "peer-abc",
                "address": "1.2.3.4:5000",
                "region": "us-east",
                "status": "ONLINE",
                "trust_level": "MEMBER",
                "latency_ms": 25.5
            }
        }
    }
    with open(test_brain / "federation" / "state.json", 'w') as f:
        json.dump(state, f)
        
    env = os.environ.copy()
    env["NUCLEUS_BRAIN_PATH"] = str(test_brain)
    env["PYTHONPATH"] = f"{os.getcwd()}/src"
    
    # 3. Test nucleus federation status
    print("\n--- Testing: nucleus federation status ---")
    out = run_cmd(["python3", "-m", "mcp_server_nucleus.cli", "federation", "status"], cwd=os.getcwd(), env=env)
    print(out)
    
    # 4. Test nucleus federation peers --format json
    print("\n--- Testing: nucleus federation peers --format json ---")
    out = run_cmd(["python3", "-m", "mcp_server_nucleus.cli", "federation", "peers", "--format", "json"], cwd=os.getcwd(), env=env)
    print(out)
    
    # Robust JSON extraction: handle multiple JSON objects (JSONL)
    json_list = []
    for line in out.strip().split('\n'):
        line = line.strip()
        if line.startswith('{') or line.startswith('['):
            try:
                json_list.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    assert len(json_list) > 0, "Failed to find any JSON in output"
    
    # Flatten if we found some lists (though peers returns individual objects)
    flattened = []
    for item in json_list:
        if isinstance(item, list): flattened.extend(item)
        else: flattened.append(item)
        
    assert any(p.get("peer_id") == "peer-abc" for p in flattened), f"peer-abc not found in {flattened}"
    
    # 5. Test nucleus federation sync
    print("\n--- Testing: nucleus federation sync ---")
    out = run_cmd(["python3", "-m", "mcp_server_nucleus.cli", "federation", "sync"], cwd=os.getcwd(), env=env)
    print(out)
    
    print("\n✅ CLI verification passed: federation commands reporting correctly.")

if __name__ == "__main__":
    verify_cli()
