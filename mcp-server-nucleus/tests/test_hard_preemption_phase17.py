import os
import signal
import time
import subprocess
import pytest
from pathlib import Path
from mcp_server_nucleus.runtime.process_manager import SovereignProcess

def test_hard_preemption_group_kill():
    """
    Verify that SovereignProcess.kill_group() terminates the entire process tree.
    We'll spawn a Python script that spawns another Python script that sleeps.
    """
    # Create a nested sleeper script
    nested_sleeper = """
import time
import sys
try:
    with open('nested_active.txt', 'w') as f:
        f.write('running')
    time.sleep(60)
except Exception:
    pass
finally:
    with open('nested_active.txt', 'w') as f:
        f.write('killed')
"""
    with open('child_sleeper.py', 'w') as f:
        f.write(nested_sleeper)

    # Create a parent script that spawns the sleeper
    parent_script = """
import subprocess
import time
import sys
p = subprocess.Popen([sys.executable, 'child_sleeper.py'])
with open('parent_active.txt', 'w') as f:
    f.write(str(p.pid))
time.sleep(60)
"""
    with open('parent_runner.py', 'w') as f:
        f.write(parent_script)

    try:
        # Start the SovereignProcess
        proc = SovereignProcess([os.sys.executable, 'parent_runner.py'])
        
        # Give it a moment to spawn the child
        time.sleep(2)
        
        assert os.path.exists('parent_active.txt')
        with open('parent_active.txt', 'r') as f:
            child_pid = int(f.read())
        
        # Verify child is alive
        assert os.kill(child_pid, 0) is None
        
        # Now kill the group
        proc.kill_group()
        
        # Verify both parent and child are gone
        time.sleep(1)
        
        # Parent check
        assert proc.poll() is not None
        
        # Child check (should raise OSError/ProcessLookupError)
        with pytest.raises(OSError):
            os.kill(child_pid, 0)
            
        print("✅ Hard preemption verified: Parent and Child both terminated.")

    finally:
        # Cleanup
        for f in ['child_sleeper.py', 'parent_runner.py', 'parent_active.txt', 'nested_active.txt']:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    test_hard_preemption_group_kill()
