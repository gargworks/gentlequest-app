import os
import json
import shutil
import subprocess
from pathlib import Path
from mcp_server_nucleus.runtime.dsor import DecisionLedger
from mcp_server_nucleus.runtime.context_graph import ContextGraph
from mcp_server_nucleus.runtime.trace_viewer import list_traces, get_trace

def test_trace_and_weighting_logic():
    # Setup temporary brain
    project_root = Path("/Users/lokeshgarg/ai-mvp-backend")
    brain_path = project_root / ".brain_test_phase19"
    if brain_path.exists():
        shutil.rmtree(brain_path)
    brain_path.mkdir(parents=True)
    
    os.environ["NUCLEUS_BRAIN_PATH"] = str(brain_path.absolute())
    
    ledger = DecisionLedger(brain_path)
    graph = ContextGraph(brain_path)
    
    # 1. Record Decisions
    d1 = ledger.record_decision("self_heal", "Fixing import error", "hash1", metadata={"file": "a.py"})
    d2 = ledger.record_decision("summon_sent", "Summoning developer for feature X", "hash2", metadata={"file": "b.py"})
    
    # 2. Link Context
    graph.add_node(d1.decision_id, "decision", {"intent": "self_heal"})
    graph.add_node("a.py", "file")
    graph.link_nodes(d1.decision_id, "a.py", "affects", weight=0.5)
    
    graph.add_node(d2.decision_id, "decision", {"intent": "summon_sent"})
    graph.add_node("b.py", "file")
    graph.link_nodes(d2.decision_id, "b.py", "affects", weight=0.8)
    
    # 3. Verify Initial Retrieval
    traces = list_traces(brain_path)
    assert traces["count"] == 2
    assert traces["traces"][0]["decision_id"] in [d1.decision_id, d2.decision_id]
    
    trace_detail = get_trace(brain_path, d1.decision_id)
    assert trace_detail["decision_id"] == d1.decision_id
    assert len(trace_detail["related_context"]) == 1
    assert trace_detail["related_context"][0]["weight"] == 0.5
    
    # 4. Test Dynamic Weighting
    # Strengthen d1 -> a.py
    graph.strengthen_link(d1.decision_id, "a.py", "affects", increment=0.2)
    trace_detail_updated = get_trace(brain_path, d1.decision_id)
    assert trace_detail_updated["related_context"][0]["weight"] == 0.7
    print(f"✅ Strengthened link weight: 0.5 -> {trace_detail_updated['related_context'][0]['weight']}")
    
    # Decay all links
    graph.decay_links(factor=0.5)
    after_decay = get_trace(brain_path, d1.decision_id)
    assert after_decay["related_context"][0]["weight"] == 0.35 # 0.7 * 0.5
    print(f"✅ Decayed link weight: 0.7 -> {after_decay['related_context'][0]['weight']}")
    
    # 5. Verify CLI Output (Mocked call)
    # We call nucleus trace list via subprocess if nucleus is installed, 
    # but here we can just verify the formatting function directly
    from mcp_server_nucleus.runtime.trace_viewer import format_trace_list, format_trace_detail
    
    list_output = format_trace_list(traces)
    assert "NUCLEUS DECISION LEDGER" in list_output
    assert d1.decision_id in list_output
    assert d2.decision_id in list_output
    
    detail_output = format_trace_detail(after_decay)
    assert d1.decision_id in detail_output
    assert "Fixing import error" in detail_output
    assert "CONNECTED CONTEXT" in detail_output
    assert "weight: 0.35" in detail_output
    
    print("\nPhase 19: Trace & Weighting Logic Verified!")

if __name__ == "__main__":
    test_trace_and_weighting_logic()
