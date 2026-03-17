
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from mcp_server_nucleus.runtime.god_combos.self_healing_v2 import run_self_healing_v2

@pytest.fixture
def mock_brain():
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_brain = os.environ.get("NUCLEUS_BRAIN_PATH")
        os.environ["NUCLEUS_BRAIN_PATH"] = tmp_dir
        
        p = Path(tmp_dir)
        (p / "ledger").mkdir(parents=True, exist_ok=True)
        (p / "slots").mkdir(parents=True, exist_ok=True)
        
        yield p
        
        if original_brain:
            os.environ["NUCLEUS_BRAIN_PATH"] = original_brain
        else:
            del os.environ["NUCLEUS_BRAIN_PATH"]

def test_self_healing_v2_heartbeat(mock_brain):
    """Test standard heartbeat scan with healthy metrics."""
    with patch("mcp_server_nucleus.runtime.god_combos.self_healing_v2.get_metrics_json") as mock_metrics:
        mock_metrics.return_value = {
            "latencies": {"nucleus_tasks": {"avg": 0.1, "quantiles": {"0.99": 0.2}}},
            "tool_errors": {}
        }
        
        result = run_self_healing_v2()
        
        assert result["pipeline"] == "self_healing_v2"
        assert result["symptom"] == "HEARTBEAT_SCAN"
        assert len(result["predictions"]) == 0
        assert result["autonomous_fix"] is None

def test_self_healing_v2_latency_prediction(mock_brain):
    """Test detection of rising latency trend."""
    with patch("mcp_server_nucleus.runtime.god_combos.self_healing_v2.get_metrics_json") as mock_metrics:
        # Simulate high q99 latency
        mock_metrics.return_value = {
            "latencies": {
                "nucleus_tasks": {"avg": 0.5, "quantiles": {"0.99": 2.5}}
            },
            "tool_errors": {}
        }
        
        result = run_self_healing_v2()
        
        assert len(result["predictions"]) > 0
        assert "Latency Spike Trend" in result["predictions"][0]["issue"]
        assert result["autonomous_fix"]["action"] == "clear_memory"

def test_self_healing_v2_error_refactor(mock_brain):
    """Test detection of high error rate triggering refactor proposal."""
    with patch("mcp_server_nucleus.runtime.god_combos.self_healing_v2.get_metrics_json") as mock_metrics:
        # Simulate many tool errors
        mock_metrics.return_value = {
            "latencies": {},
            "tool_errors": {"nucleus_federation": 15}
        }
        
        result = run_self_healing_v2(symptom="recurring_auth_failures")
        
        assert any(p["severity"] == "HIGH" for p in result["predictions"])
        assert result["refactor_proposal"] is not None
        assert "Circuit Breaker" in result["refactor_proposal"]["suggestion"]
        assert result["autonomous_fix"]["action"] == "lock_and_inspect"

def test_self_healing_v2_memory_correlation(mock_brain):
    """Test correlation with historical engrams."""
    from mcp_server_nucleus.runtime.engram_ops import _brain_write_engram_impl
    
    # Pre-populate an engram with "fix" in it
    _brain_write_engram_impl(
        key="historical_fix_123",
        value="Found fix for high latency by clearing worker cache",
        context="Architecture",
        intensity=6
    )
    
    with patch("mcp_server_nucleus.runtime.god_combos.self_healing_v2.get_metrics_json") as mock_metrics:
        mock_metrics.return_value = {"latencies": {}, "tool_errors": {}}
        
        result = run_self_healing_v2(symptom="high latency")
        
        assert result["memory_correlation"]["relevant_engrams"] >= 1
        assert result["memory_correlation"]["historical_fix_found"] is True
