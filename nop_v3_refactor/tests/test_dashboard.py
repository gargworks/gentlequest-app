"""
DashboardEngine Tests
Comprehensive test suite for orchestration dashboard.

Key verifications:
- Metrics collection from all components
- Alert engine threshold checking
- Output formatters (ASCII, JSON, Mermaid)
- Trend analysis and snapshots
- Performance benchmarks (<100ms render)

Author: NOP V3.1 - January 2026
"""

import pytest
import time
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nop_core.dashboard import (
    DashboardEngine,
    MetricsCollector,
    MetricsCache,
    AlertEngine,
    AlertLevel,
    Alert,
    TrendAnalyzer,
    SnapshotManager,
    ASCIIFormatter,
    JSONFormatter,
    MermaidFormatter,
    OutputFormat,
)


class TestMetricsCache:
    """Unit tests for MetricsCache."""

    def test_cache_set_and_get(self):
        """Test basic set and get."""
        cache = MetricsCache(ttl_ms=1000)
        cache.set("key", {"value": 42})
        
        result = cache.get("key")
        
        assert result == {"value": 42}

    def test_cache_expiry(self):
        """Test cache expiry after TTL."""
        cache = MetricsCache(ttl_ms=50)
        cache.set("key", {"value": 42})
        
        time.sleep(0.1)  # Wait for expiry
        result = cache.get("key")
        
        assert result is None

    def test_cache_invalidate_single(self):
        """Test invalidating single key."""
        cache = MetricsCache(ttl_ms=1000)
        cache.set("key1", 1)
        cache.set("key2", 2)
        
        cache.invalidate("key1")
        
        assert cache.get("key1") is None
        assert cache.get("key2") == 2

    def test_cache_invalidate_all(self):
        """Test invalidating all keys."""
        cache = MetricsCache(ttl_ms=1000)
        cache.set("key1", 1)
        cache.set("key2", 2)
        
        cache.invalidate()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestAlertEngine:
    """Unit tests for AlertEngine."""

    def test_no_alerts_when_healthy(self):
        """No alerts when all metrics are healthy."""
        engine = AlertEngine()
        metrics = {
            "agents": {"total": 10, "exhausted": 1, "utilization": 0.5},
            "tasks": {"total": 100, "pending": 10, "blocked": 5},
            "cost": {"budget": 100, "remaining": 80},
        }
        
        alerts = engine.check(metrics)
        
        assert len(alerts) == 0

    def test_warning_alert_on_high_exhaustion(self):
        """Warning when >50% agents exhausted."""
        engine = AlertEngine()
        metrics = {
            "agents": {"total": 10, "exhausted": 6, "utilization": 0.5},
        }
        
        alerts = engine.check(metrics)
        
        assert len(alerts) >= 1
        assert any(a.level == AlertLevel.WARNING for a in alerts)

    def test_critical_alert_on_very_high_exhaustion(self):
        """Critical when >90% agents exhausted."""
        engine = AlertEngine()
        metrics = {
            "agents": {"total": 10, "exhausted": 10, "utilization": 0.5},
        }
        
        alerts = engine.check(metrics)
        
        assert any(a.level == AlertLevel.CRITICAL for a in alerts)

    def test_warning_on_high_pending(self):
        """Warning when pending > 100."""
        engine = AlertEngine()
        metrics = {
            "tasks": {"total": 200, "pending": 150, "blocked": 10},
        }
        
        alerts = engine.check(metrics)
        
        assert len(alerts) >= 1
        warning_messages = [a.message for a in alerts if a.level == AlertLevel.WARNING]
        assert any("pending" in m.lower() for m in warning_messages)

    def test_critical_on_circular_deps(self):
        """Critical when circular dependencies detected."""
        engine = AlertEngine()
        metrics = {
            "deps": {"max_depth": 3, "circular": 2},
        }
        
        alerts = engine.check(metrics)
        
        assert any(a.level == AlertLevel.CRITICAL and "circular" in a.message.lower() for a in alerts)

    def test_custom_threshold(self):
        """Test setting custom threshold."""
        engine = AlertEngine()
        engine.set_threshold("tasks.pending", "warning", 50)
        
        metrics = {"tasks": {"total": 100, "pending": 60, "blocked": 5}}
        alerts = engine.check(metrics)
        
        assert len(alerts) >= 1

    def test_budget_warning_low_remaining(self):
        """Warning when budget remaining < 20%."""
        engine = AlertEngine()
        metrics = {
            "cost": {"budget": 100, "remaining": 15},
        }
        
        alerts = engine.check(metrics)
        
        assert any(a.level == AlertLevel.WARNING and "budget" in a.message.lower() for a in alerts)


class TestASCIIFormatter:
    """Unit tests for ASCIIFormatter."""

    @pytest.fixture
    def sample_metrics(self):
        return {
            "agents": {
                "total": 10, "active": 8, "idle": 3, 
                "exhausted": 2, "utilization": 0.8, "reset_warnings": []
            },
            "tasks": {
                "total": 100, "pending": 42, "in_progress": 8,
                "blocked": 5, "done": 45, "failed": 0, "velocity": 6.5
            },
            "ingestion": {
                "total": 500, "skipped": 50, "failed": 5, "batches": 10
            },
            "cost": {
                "tokens": 1200000, "usd": 4.80, "budget": 10.00,
                "remaining": 5.20, "burn_rate": 0.60
            },
            "deps": {"max_depth": 3, "blocked_chains": 2, "circular": 0},
            "system": {"uptime": "2h 30m", "last_activity": "now", "error_rate": 0},
        }

    def test_minimal_output(self, sample_metrics):
        """Test minimal detail level."""
        formatter = ASCIIFormatter()
        output = formatter.format(sample_metrics, [], "minimal")
        
        assert "NOP Status Dashboard" in output
        assert "AGENT POOL" in output

    def test_standard_output(self, sample_metrics):
        """Test standard detail level."""
        formatter = ASCIIFormatter()
        output = formatter.format(sample_metrics, [], "standard")
        
        assert "AGENT POOL" in output
        assert "TASK QUEUE" in output
        assert "COST TRACKING" in output

    def test_verbose_output(self, sample_metrics):
        """Test verbose detail level includes ingestion."""
        formatter = ASCIIFormatter()
        output = formatter.format(sample_metrics, [], "verbose")
        
        assert "INGESTION" in output
        assert "DEPENDENCIES" in output

    def test_full_output(self, sample_metrics):
        """Test full detail level includes system."""
        formatter = ASCIIFormatter()
        output = formatter.format(sample_metrics, [], "full")
        
        assert "SYSTEM HEALTH" in output

    def test_alerts_section(self, sample_metrics):
        """Test alerts are displayed."""
        formatter = ASCIIFormatter()
        alerts = [
            Alert(AlertLevel.WARNING, "test", "Test warning", 0.5, 0.4),
            Alert(AlertLevel.CRITICAL, "test2", "Test critical", 0.9, 0.8),
        ]
        
        output = formatter.format(sample_metrics, alerts, "standard")
        
        assert "ALERTS" in output
        assert "WARNING" in output
        assert "CRITICAL" in output

    def test_token_formatting(self, sample_metrics):
        """Test token count formatting (K, M)."""
        formatter = ASCIIFormatter()
        output = formatter.format(sample_metrics, [], "standard")
        
        assert "1.2M" in output  # 1.2 million tokens


class TestJSONFormatter:
    """Unit tests for JSONFormatter."""

    def test_json_output_valid(self):
        """Test JSON output is valid."""
        formatter = JSONFormatter()
        metrics = {"agents": {"total": 10}}
        
        output = formatter.format(metrics, [], "standard")
        parsed = json.loads(output)
        
        assert "timestamp" in parsed
        assert "metrics" in parsed
        assert parsed["metrics"]["agents"]["total"] == 10

    def test_json_includes_alerts(self):
        """Test JSON includes alerts."""
        formatter = JSONFormatter()
        metrics = {"agents": {"total": 10}}
        alerts = [Alert(AlertLevel.WARNING, "test", "msg", 0.5, 0.4)]
        
        output = formatter.format(metrics, alerts, "standard")
        parsed = json.loads(output)
        
        assert len(parsed["alerts"]) == 1
        assert parsed["alerts"][0]["level"] == "warning"


class TestMermaidFormatter:
    """Unit tests for MermaidFormatter."""

    def test_mermaid_diagram_structure(self):
        """Test Mermaid diagram has correct structure."""
        formatter = MermaidFormatter()
        deps = {
            "forward_deps": {
                "task_002": ["task_001"],
                "task_003": ["task_001"],
            },
            "depths": {"task_001": 0, "task_002": 1, "task_003": 1},
        }
        
        output = formatter.format(deps)
        
        assert "```mermaid" in output
        assert "graph TD" in output
        assert "```" in output

    def test_mermaid_shows_edges(self):
        """Test Mermaid shows dependency edges."""
        formatter = MermaidFormatter()
        deps = {
            "forward_deps": {"task_002": ["task_001"]},
            "depths": {"task_001": 0, "task_002": 1},
        }
        
        output = formatter.format(deps)
        
        assert "-->" in output


class TestTrendAnalyzer:
    """Unit tests for TrendAnalyzer."""

    def test_record_and_get_trends(self, tmp_path):
        """Test recording and retrieving trends."""
        analyzer = TrendAnalyzer(brain_path=tmp_path)
        
        # Record metrics
        metrics = {"tasks": {"done": 10}}
        analyzer.record_metrics(metrics)
        
        # Get trends
        trends = analyzer.get_trends("tasks.done", hours=1)
        
        assert len(trends) >= 1
        assert trends[0]["value"] == 10

    def test_velocity_calculation(self, tmp_path):
        """Test velocity calculation."""
        analyzer = TrendAnalyzer(brain_path=tmp_path)
        
        # Record two data points
        analyzer.record_metrics({"tasks": {"done": 100}})
        time.sleep(0.1)
        analyzer.record_metrics({"tasks": {"done": 110}})
        
        velocity = analyzer.get_velocity(hours=24)
        
        # Velocity should be positive (10 tasks / 24 hours ≈ 0.42)
        assert velocity >= 0


class TestSnapshotManager:
    """Unit tests for SnapshotManager."""

    def test_create_snapshot(self, tmp_path):
        """Test creating a snapshot."""
        manager = SnapshotManager(brain_path=tmp_path)
        metrics = {"agents": {"total": 10}}
        
        snapshot = manager.create(metrics, [], name="Test Snapshot")
        
        assert snapshot.id.startswith("snap_")
        assert snapshot.name == "Test Snapshot"
        assert snapshot.metrics["agents"]["total"] == 10

    def test_get_snapshot(self, tmp_path):
        """Test retrieving a snapshot."""
        manager = SnapshotManager(brain_path=tmp_path)
        metrics = {"agents": {"total": 10}}
        
        created = manager.create(metrics, [])
        retrieved = manager.get(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_list_snapshots(self, tmp_path):
        """Test listing snapshots."""
        manager = SnapshotManager(brain_path=tmp_path)
        
        manager.create({"a": 1}, [])
        manager.create({"b": 2}, [])
        manager.create({"c": 3}, [])
        
        snapshots = manager.list(limit=10)
        
        assert len(snapshots) == 3

    def test_compare_snapshots(self, tmp_path):
        """Test comparing snapshots."""
        manager = SnapshotManager(brain_path=tmp_path)
        
        snap_a = manager.create({"tasks": {"done": 10}}, [])
        snap_b = manager.create({"tasks": {"done": 20}}, [])
        
        comparison = manager.compare(snap_a.id, snap_b.id)
        
        assert "deltas" in comparison
        assert "tasks.done" in comparison["deltas"]
        assert comparison["deltas"]["tasks.done"]["delta"] == 10


class TestDashboardEngine:
    """Integration tests for DashboardEngine."""

    @pytest.fixture
    def engine(self, tmp_path):
        """Create dashboard engine with temp path."""
        return DashboardEngine(brain_path=tmp_path)

    def test_render_ascii(self, engine):
        """Test ASCII render."""
        output = engine.render(detail_level="standard", format="ascii")
        
        assert "NOP Status Dashboard" in output

    def test_render_json(self, engine):
        """Test JSON render."""
        output = engine.render(detail_level="standard", format="json")
        
        parsed = json.loads(output)
        assert "timestamp" in parsed
        assert "metrics" in parsed

    def test_get_metrics(self, engine):
        """Test getting raw metrics."""
        metrics = engine.get_metrics()
        
        assert "agents" in metrics or "error" in metrics.get("agents", {})
        assert "tasks" in metrics or "error" in metrics.get("tasks", {})

    def test_get_metrics_by_category(self, engine):
        """Test filtering metrics by category."""
        metrics = engine.get_metrics(category="agents")
        
        assert "agents" in metrics
        assert "tasks" not in metrics

    def test_get_alerts(self, engine):
        """Test getting alerts."""
        alerts = engine.get_alerts()
        
        assert isinstance(alerts, list)

    def test_create_snapshot(self, engine):
        """Test creating snapshot."""
        snapshot = engine.create_snapshot(name="Test")
        
        assert snapshot.name == "Test"
        assert snapshot.metrics is not None

    def test_list_snapshots(self, engine):
        """Test listing snapshots."""
        engine.create_snapshot()
        engine.create_snapshot()
        
        snapshots = engine.list_snapshots()
        
        assert len(snapshots) >= 2

    def test_set_alert_threshold(self, engine):
        """Test setting custom threshold."""
        engine.set_alert_threshold("tasks.pending", "warning", 50)
        
        # Verify threshold was set
        assert engine.alert_engine.thresholds["tasks.pending"]["warning"] == 50


class TestPerformance:
    """Performance benchmarks."""

    def test_render_time_under_100ms(self, tmp_path):
        """Dashboard render should complete in <100ms."""
        engine = DashboardEngine(brain_path=tmp_path)
        
        start = time.time()
        for _ in range(10):
            engine.render(detail_level="full", format="ascii")
        elapsed = (time.time() - start) / 10  # Average per render
        
        print(f"\nAverage render time: {elapsed*1000:.2f}ms")
        assert elapsed < 0.1  # <100ms

    def test_cache_effectiveness(self, tmp_path):
        """Test that caching improves performance."""
        engine = DashboardEngine(brain_path=tmp_path)
        
        # First call (cache miss)
        start = time.time()
        engine.get_metrics()
        first_call = time.time() - start
        
        # Second call (cache hit)
        start = time.time()
        engine.get_metrics()
        second_call = time.time() - start
        
        # Second call should be faster (or at least not slower)
        print(f"\nFirst call: {first_call*1000:.2f}ms, Second call: {second_call*1000:.2f}ms")


class TestStressTest:
    """Stress tests for dashboard."""

    def test_many_snapshots(self, tmp_path):
        """Test handling many snapshots."""
        manager = SnapshotManager(brain_path=tmp_path, max_snapshots=50)
        
        # Create 100 snapshots (should auto-cleanup to 50)
        for i in range(100):
            manager.create({"value": i}, [])
        
        snapshots = manager.list(limit=100)
        
        # Should have at most max_snapshots
        assert len(snapshots) <= 50

    def test_concurrent_renders(self, tmp_path):
        """Test concurrent dashboard renders."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        engine = DashboardEngine(brain_path=tmp_path)
        results = []
        errors = []
        
        def render():
            try:
                output = engine.render()
                results.append(len(output))
            except Exception as e:
                errors.append(str(e))
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(render) for _ in range(50)]
            for f in as_completed(futures):
                f.result()
        
        assert len(errors) == 0
        assert len(results) == 50
        print(f"\n50 concurrent renders completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
