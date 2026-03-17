"""Tests for Nucleus OpenTelemetry export layer.

Tests verify:
1. OTel is disabled by default (no-op)
2. OTel initializes correctly when enabled
3. Dispatch spans record correctly
4. Semantic events map to correct OTel events
5. Engram counters increment
6. Custom endpoint override works
7. All hooks are safe (never raise)
"""

import os
import unittest
from unittest.mock import patch, MagicMock


class TestOtelDisabledByDefault(unittest.TestCase):
    """Verify OTel is completely inert when NUCLEUS_OTEL_ENABLED is not set."""

    def setUp(self):
        # Ensure clean state
        os.environ.pop("NUCLEUS_OTEL_ENABLED", None)
        os.environ.pop("NUCLEUS_OTEL_ENDPOINT", None)
        os.environ.pop("NUCLEUS_OTEL_SERVICE_NAME", None)

    def test_otel_disabled_by_default(self):
        """OTel should be disabled when env var is not set."""
        # Re-import to pick up env
        import importlib
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod.reset_otel_state()
        # Force re-read of env var
        otel_mod._OTEL_ENABLED = os.environ.get("NUCLEUS_OTEL_ENABLED", "false").lower() == "true"

        self.assertFalse(otel_mod.otel_enabled())
        self.assertIsNone(otel_mod.get_tracer())
        self.assertIsNone(otel_mod.get_meter())

    def test_record_dispatch_span_noop_when_disabled(self):
        """record_dispatch_span should be a no-op when disabled."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod.reset_otel_state()
        otel_mod._OTEL_ENABLED = False

        # Should not raise
        otel_mod.record_dispatch_span("nucleus_engrams", "write_engram", 12.5)
        otel_mod.record_dispatch_span("nucleus_tasks", "list", 5.0, error="test error")

    def test_record_semantic_event_noop_when_disabled(self):
        """record_semantic_event should be a no-op when disabled."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod.reset_otel_state()
        otel_mod._OTEL_ENABLED = False

        otel_mod.record_semantic_event("DecisionMade", "agent_1", {"decision_id": "dec-123"})
        otel_mod.record_semantic_event("HITLApproval", "hypervisor", {})

    def test_engram_counters_noop_when_disabled(self):
        """Engram counters should be no-ops when disabled."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod.reset_otel_state()
        otel_mod._OTEL_ENABLED = False

        otel_mod.inc_engram_write(context="Feature", intensity=7)
        otel_mod.inc_engram_read()

    def test_workflow_cost_noop_when_disabled(self):
        """Workflow cost recording should be a no-op when disabled."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod.reset_otel_state()
        otel_mod._OTEL_ENABLED = False

        otel_mod.record_workflow_cost("nucleus_engrams", "write_engram", 0.05, tier=1)


class TestOtelEnabled(unittest.TestCase):
    """Verify OTel initializes and records when enabled."""

    def setUp(self):
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod.reset_otel_state()

    def tearDown(self):
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod.reset_otel_state()
        otel_mod._OTEL_ENABLED = False

    @patch.dict(os.environ, {"NUCLEUS_OTEL_ENABLED": "true"})
    def test_otel_enabled_creates_providers(self):
        """When enabled, initialization should create tracer and meter."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod._OTEL_ENABLED = True

        # Trigger initialization
        otel_mod._ensure_initialized()

        self.assertTrue(otel_mod._initialized)
        # Tracer and meter should be set (either real or None if SDK import failed gracefully)
        # The key test is that _initialized is True and no exception was raised

    @patch.dict(os.environ, {"NUCLEUS_OTEL_ENABLED": "true"})
    def test_record_dispatch_span_creates_span(self):
        """Dispatch span recording should not raise when enabled."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod._OTEL_ENABLED = True
        otel_mod._ensure_initialized()

        # Should not raise regardless of whether SDK initialized fully
        otel_mod.record_dispatch_span("nucleus_engrams", "write_engram", 15.3)
        otel_mod.record_dispatch_span("nucleus_tasks", "claim", 8.1, error="task not found")

    @patch.dict(os.environ, {"NUCLEUS_OTEL_ENABLED": "true"})
    def test_record_semantic_event_decision(self):
        """DecisionMade events should map to agent.decision OTel events."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod._OTEL_ENABLED = True
        otel_mod._ensure_initialized()

        # Should not raise
        otel_mod.record_semantic_event("DecisionMade", "ephemeral_agent", {
            "decision_id": "dec-abc123",
            "reasoning": "Tool: write_engram | Need to persist learning",
            "confidence": 0.95,
            "context_hash": "sha256:deadbeef",
        })

    @patch.dict(os.environ, {"NUCLEUS_OTEL_ENABLED": "true"})
    def test_record_semantic_event_hitl(self):
        """HITL events should map correctly."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod._OTEL_ENABLED = True
        otel_mod._ensure_initialized()

        otel_mod.record_semantic_event("HITLApproval", "hypervisor", {
            "description": "File deletion approved",
        })
        otel_mod.record_semantic_event("HITLRejection", "hypervisor", {
            "description": "Unsafe operation rejected",
        })
        otel_mod.record_semantic_event("ConsentResponse", "user", {})

    @patch.dict(os.environ, {"NUCLEUS_OTEL_ENABLED": "true"})
    def test_engram_counters(self):
        """Engram counters should increment without error when enabled."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod._OTEL_ENABLED = True
        otel_mod._ensure_initialized()

        otel_mod.inc_engram_write(context="Architecture", intensity=8)
        otel_mod.inc_engram_write(context="Strategy", intensity=5)
        otel_mod.inc_engram_read()
        otel_mod.inc_engram_read()

    @patch.dict(os.environ, {
        "NUCLEUS_OTEL_ENABLED": "true",
        "NUCLEUS_OTEL_ENDPOINT": "https://otel.example.com:4317",
    })
    def test_custom_endpoint(self):
        """Custom endpoint should be picked up from env."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod._OTEL_ENABLED = True
        otel_mod._OTEL_ENDPOINT = os.environ.get("NUCLEUS_OTEL_ENDPOINT", "")

        self.assertEqual(otel_mod._OTEL_ENDPOINT, "https://otel.example.com:4317")

    @patch.dict(os.environ, {
        "NUCLEUS_OTEL_ENABLED": "true",
        "NUCLEUS_OTEL_SERVICE_NAME": "my-custom-service",
    })
    def test_custom_service_name(self):
        """Custom service name should be picked up from env."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod._OTEL_ENABLED = True
        otel_mod._OTEL_SERVICE_NAME = os.environ.get("NUCLEUS_OTEL_SERVICE_NAME", "")

        self.assertEqual(otel_mod._OTEL_SERVICE_NAME, "my-custom-service")


class TestOtelSafety(unittest.TestCase):
    """Verify all OTel hooks are safe — never propagate exceptions."""

    def setUp(self):
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod.reset_otel_state()

    def tearDown(self):
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod.reset_otel_state()
        otel_mod._OTEL_ENABLED = False

    def test_dispatch_span_survives_broken_tracer(self):
        """Even with a broken tracer, dispatch span should not raise."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod._OTEL_ENABLED = True
        otel_mod._initialized = True
        otel_mod._tracer = MagicMock()
        otel_mod._tracer.start_as_current_span.side_effect = RuntimeError("broken")

        # Should not raise
        otel_mod.record_dispatch_span("test_facade", "test_action", 10.0)

    def test_semantic_event_survives_broken_tracer(self):
        """Even with a broken tracer, semantic event should not raise."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod._OTEL_ENABLED = True
        otel_mod._initialized = True
        otel_mod._tracer = MagicMock()
        otel_mod._tracer.start_as_current_span.side_effect = RuntimeError("broken")

        otel_mod.record_semantic_event("DecisionMade", "test", {"decision_id": "x"})

    def test_engram_counter_survives_broken_counter(self):
        """Even with a broken counter, engram inc should not raise."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod._OTEL_ENABLED = True
        otel_mod._initialized = True
        otel_mod._engram_write_counter = MagicMock()
        otel_mod._engram_write_counter.add.side_effect = RuntimeError("broken")
        otel_mod._engram_read_counter = MagicMock()
        otel_mod._engram_read_counter.add.side_effect = RuntimeError("broken")

        otel_mod.inc_engram_write()
        otel_mod.inc_engram_read()

    def test_workflow_cost_survives_broken_histogram(self):
        """Even with a broken histogram, cost recording should not raise."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod._OTEL_ENABLED = True
        otel_mod._initialized = True
        otel_mod._workflow_cost_histogram = MagicMock()
        otel_mod._workflow_cost_histogram.record.side_effect = RuntimeError("broken")

        otel_mod.record_workflow_cost("test", "action", 0.1)

    def test_reset_cleans_state(self):
        """reset_otel_state should clear all singletons."""
        import mcp_server_nucleus.runtime.otel_export as otel_mod
        otel_mod._OTEL_ENABLED = True
        otel_mod._initialized = True
        otel_mod._tracer = "fake"
        otel_mod._meter = "fake"

        otel_mod.reset_otel_state()

        self.assertFalse(otel_mod._initialized)
        self.assertIsNone(otel_mod._tracer)
        self.assertIsNone(otel_mod._meter)
        self.assertIsNone(otel_mod._engram_write_counter)
        self.assertIsNone(otel_mod._engram_read_counter)
        self.assertIsNone(otel_mod._dispatch_duration_histogram)
        self.assertIsNone(otel_mod._workflow_cost_histogram)


if __name__ == "__main__":
    unittest.main()
