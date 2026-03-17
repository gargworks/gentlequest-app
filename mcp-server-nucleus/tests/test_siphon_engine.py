import os
import shutil
import tempfile
import pytest
from mcp_server_nucleus.runtime.siphon_engine import SiphonEngine, AntigravityAdapter, WindsurfAdapter, Artifact

@pytest.fixture
def mock_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up mock Antigravity
        ag_dir = os.path.join(tmpdir, ".agents")
        ag_workflows = os.path.join(ag_dir, "workflows")
        os.makedirs(ag_workflows)
        with open(os.path.join(ag_workflows, "task.md"), "w") as f:
            f.write("# Task\n[ ] Ag Task")
            
        # Set up mock Windsurf
        ws_dir = os.path.join(tmpdir, ".windsurf")
        ws_rules = os.path.join(ws_dir, "rules")
        os.makedirs(ws_rules)
        with open(os.path.join(ws_rules, "plan.md"), "w") as f:
            f.write("# Plan\n[ ] Ws Plan")
            
        yield tmpdir

@pytest.fixture
def mock_vault():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_siphon_discovery(mock_workspace, mock_vault):
    adapters = [
        AntigravityAdapter(mock_workspace),
        WindsurfAdapter(mock_workspace)
    ]
    engine = SiphonEngine(mock_vault, adapters)
    
    count = engine.siphon_now()
    assert count == 2
    
    # Verify files exist in vault
    assert os.path.exists(os.path.join(mock_vault, "task.md"))
    assert os.path.exists(os.path.join(mock_vault, "plan.md"))

def test_siphon_caching(mock_workspace, mock_vault):
    adapters = [AntigravityAdapter(mock_workspace)]
    engine = SiphonEngine(mock_vault, adapters)
    
    # First siphon
    assert engine.siphon_now() == 1
    
    # Second siphon (no changes)
    assert engine.siphon_now() == 0
    
    # Update file
    with open(os.path.join(mock_workspace, ".agents", "workflows", "task.md"), "a") as f:
        f.write("\nNew line")
        
    # Third siphon (one change)
    assert engine.siphon_now() == 1

def test_siphon_locking(mock_workspace, mock_vault):
    adapters = [AntigravityAdapter(mock_workspace)]
    engine = SiphonEngine(mock_vault, adapters)
    
    # Manually create lock file
    lock_file = os.path.join(os.path.dirname(mock_vault), "lock", "siphon.lock")
    os.makedirs(os.path.dirname(lock_file), exist_ok=True)
    with open(lock_file, "w") as f:
        f.write("9999")
        
    # Siphon should be blocked
    assert engine.siphon_now() == 0
    
    # Remove lock
    os.remove(lock_file)
    assert engine.siphon_now() == 1

def test_silent_metadata(mock_workspace, mock_vault):
    adapters = [AntigravityAdapter(mock_workspace)]
    engine = SiphonEngine(mock_vault, adapters)
    
    # Create task with Antigravity status
    ag_task_file = os.path.join(mock_workspace, ".agents", "workflows", "task.md")
    with open(ag_task_file, "w") as f:
        f.write("- [ ] Normal\n- [/] In Progress\n- [B] Blocked")
        
    engine.siphon_now()
    
    # Verify Vault has statuses preserved or tagged
    with open(os.path.join(mock_vault, "task.md"), "r") as f:
        content = f.read()
        assert "- [/] In Progress <!-- n:s=p -->" in content
        assert "- [B] Blocked <!-- n:s=b -->" in content
        
    # Simulate editing in a tool that doesn't support [/]
    # It might change [/] to [ ] but keep the tag
    with open(os.path.join(mock_vault, "task.md"), "w") as f:
        f.write("- [ ] Normal\n- [ ] In Progress <!-- n:s=p -->\n- [ ] Blocked <!-- n:s=b -->")
        
    # Siphon back (AntigravityAdapter would discover this if we pointed it to the vault, 
    # but here we're testing the normalization logic in _commit_to_vault)
    # Let's mock a Windsurf artifact that has the standard [ ] boxes but our tags
    ws_task_file = os.path.join(mock_workspace, ".windsurf", "workflows")
    os.makedirs(ws_task_file, exist_ok=True)
    with open(os.path.join(ws_task_file, "task.md"), "w") as f:
        f.write("- [ ] Normal\n- [ ] In Progress <!-- n:s=p -->\n- [ ] Blocked <!-- n:s=b -->")
        
    adapters = [WindsurfAdapter(mock_workspace)]
    engine = SiphonEngine(mock_vault, adapters)
    engine.siphon_now()
    
    with open(os.path.join(mock_vault, "task.md"), "r") as f:
        content = f.read()
        assert "- [/] In Progress" in content
        assert "- [B] Blocked" in content
