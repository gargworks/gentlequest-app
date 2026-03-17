
import pytest
import json
from pathlib import Path
from mcp_server_nucleus.runtime.pm_view_ops import (
    _brain_pm_summary_impl,
    _brain_pm_gantt_impl
)
from mcp_server_nucleus.runtime.task_ops import _add_task
import tempfile
import os

@pytest.fixture
def mock_brain():
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_brain = os.environ.get("NUCLEUS_BRAIN_PATH")
        os.environ["NUCLEUS_BRAIN_PATH"] = tmp_dir
        
        # Initialize basic brain structure
        p = Path(tmp_dir)
        (p / "ledger").mkdir(parents=True, exist_ok=True)
        (p / "slots").mkdir(parents=True, exist_ok=True)
        
        yield p
        
        if original_brain:
            os.environ["NUCLEUS_BRAIN_PATH"] = original_brain
        else:
            del os.environ["NUCLEUS_BRAIN_PATH"]

def test_pm_summary_basic(mock_brain):
    """Test that PM summary returns expected sections."""
    # Add a pseudo task to populate data
    _add_task("Test PM Task", priority=1)
    
    summary = _brain_pm_summary_impl()
    
    assert "NUCLEUS PROJECT MANAGEMENT HUD" in summary
    assert "📊 TASK PIPELINE" in summary
    assert "Total Tasks:   1" in summary
    assert "🎯 ROADMAP ALIGNMENT" in summary
    assert "PHASE 10" in summary

def test_pm_gantt_basic(mock_brain):
    """Test that PM Gantt chart renders tasks."""
    res1 = _add_task("Task Alpha", priority=1)
    alpha_id = res1["task"]["id"]
    
    _add_task("Task Beta", priority=2, blocked_by=[alpha_id])
    
    gantt = _brain_pm_gantt_impl()
    
    assert "TASK GANTT & DEPENDENCIES" in gantt
    assert "Task Alpha" in gantt
    assert "Task Beta" in gantt
    assert alpha_id in gantt

def test_pm_empty_pipeline(mock_brain):
    """Test Gantt behavior with no tasks."""
    gantt = _brain_pm_gantt_impl()
    assert "No tasks in pipeline" in gantt or "All tasks completed" in gantt
