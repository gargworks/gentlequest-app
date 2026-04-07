import os
import json
import shutil
from pathlib import Path
import pytest
try:
    from mcp_server_nucleus.runtime.context_graph import ContextGraph
    from mcp_server_nucleus.runtime.task_ops import _add_task, _get_next_task, _list_tasks
    from mcp_server_nucleus.runtime.common import get_brain_path
except ImportError as e:
    pytest.skip(f"ContextGraph not implemented: {e}", allow_module_level=True)

def test_neural_prioritization():
    # Setup temporary brain
    project_root = Path("/Users/lokeshgarg/ai-mvp-backend")
    brain_path = project_root / ".brain_test_phase20"
    if brain_path.exists():
        shutil.rmtree(brain_path)
    brain_path.mkdir(parents=True)
    
    os.environ["NUCLEUS_BRAIN_PATH"] = str(brain_path.absolute())
    
    graph = ContextGraph(brain_path)
    
    # 1. Create Baseline Tasks (Static Priority)
    # Task A: Prio 2 (High)
    # Task B: Prio 3 (Medium)
    res_a = _add_task("High priority task A", priority=2, task_id="task-a")
    res_b = _add_task("Medium priority task B", priority=3, task_id="task-b")
    
    assert res_a["success"] and res_b["success"]
    
    # Verify static selection: Task A should be picked first
    next_task = _get_next_task([])
    assert next_task["id"] == "task-a"
    print(f"✅ Static selection verified: {next_task['id']}")
    
    # 2. Apply Neural Boost to Task B
    # Create a context link to Task B
    graph.add_node("task-b", "task")
    graph.add_node("hot_file.py", "file")
    graph.link_nodes("task-b", "hot_file.py", "related", weight=1.5)
    
    # Now Task B has a boost of 1.5. 
    # Adjusted Priority for B: 3.0 - min(3.0 - 0.1, 1.5) = 3.0 - 1.5 = 1.5
    # Task A remains at Priority 2.0.
    # Task B (1.5) < Task A (2.0) -> Task B should be picked.
    
    next_task_boosted = _get_next_task([])
    assert next_task_boosted["id"] == "task-b"
    print(f"✅ Neural Boost verified: {next_task_boosted['id']} picked over task-a")
    
    # 3. Deep Boost Verification
    # Task C: Prio 5 (Low)
    _add_task("Low priority task C", priority=5, task_id="task-c")
    
    # Strengthen Task C with massive weight
    graph.add_node("task-c", "task")
    graph.link_nodes("task-c", "hot_file.py", "related", weight=10.0)
    
    # Adjusted Priority for C: 5.0 - min(5.0 - 0.1, 10.0) = 5.0 - 4.9 = 0.1
    # Task C should now be the top priority (0.1)
    next_task_deep = _get_next_task([])
    assert next_task_deep["id"] == "task-c"
    print(f"✅ Deep Boost verified: {next_task_deep['id']} (Prio 5) jumped to top (Prio 0.1)")
    
    # 4. Decay Impact Verification
    # Decay factor 0.1 (aggressive)
    graph.decay_links(factor=0.1)
    
    # Task B weight: 1.5 * 0.1 = 0.15
    # Adjusted Prio for B: 3.0 - 0.15 = 2.85
    
    # Task C weight: 10.0 * 0.1 = 1.0
    # Adjusted Prio for C: 5.0 - 1.0 = 4.0
    
    # Task A remains at 2.0.
    # Task A (2.0) is now higher than Task B (2.85) and Task C (4.0) again.
    
    next_task_after_decay = _get_next_task([])
    assert next_task_after_decay["id"] == "task-a"
    print(f"✅ Decay verified: {next_task_after_decay['id']} reclaimed top spot after neural decay")

if __name__ == "__main__":
    test_neural_prioritization()
