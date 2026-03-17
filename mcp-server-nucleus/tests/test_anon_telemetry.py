"""Tests for Nucleus anonymous opt-out telemetry.

Tests verify:
1. Telemetry enabled by default (opt-out model)
2. Disabled via env var NUCLEUS_ANON_TELEMETRY=false
3. Disabled via YAML config
4. record_anon_command is no-op when disabled
5. record_anon_command works when enabled
6. All hooks are safe (never raise)
7. First-run notice logic
8. Config priority: env > yaml > default
9. Custom endpoint override
10. reset cleans state
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile


class TestAnonTelemetryDisabledViaEnv(unittest.TestCase):
    """Verify telemetry can be disabled via env var."""

    def setUp(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()

    def tearDown(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY": "false"})
    def test_disabled_via_env_false(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        self.assertFalse(mod.is_anon_telemetry_enabled())

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY": "0"})
    def test_disabled_via_env_zero(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        self.assertFalse(mod.is_anon_telemetry_enabled())

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY": "off"})
    def test_disabled_via_env_off(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        self.assertFalse(mod.is_anon_telemetry_enabled())

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY": "no"})
    def test_disabled_via_env_no(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        self.assertFalse(mod.is_anon_telemetry_enabled())

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY": "false"})
    def test_record_noop_when_disabled(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        # Should not raise
        mod.record_anon_command("morning-brief", "cli", 100.0)
        mod.record_anon_command("engram.write", "nucleus_engrams", 50.0, error_type="ValueError")


class TestAnonTelemetryEnabledByDefault(unittest.TestCase):
    """Verify telemetry is enabled by default (opt-out model)."""

    def setUp(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        # Clear env var to test default behavior
        os.environ.pop("NUCLEUS_ANON_TELEMETRY", None)

    def tearDown(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()

    def test_enabled_by_default_no_config(self):
        """When no env var and no yaml config, telemetry should be enabled."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        # Mock _read_yaml_config to return empty (no config file)
        with patch.object(mod, '_read_yaml_config', return_value={}):
            self.assertTrue(mod.is_anon_telemetry_enabled())

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY": "true"})
    def test_enabled_via_env_true(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        self.assertTrue(mod.is_anon_telemetry_enabled())

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY": "1"})
    def test_enabled_via_env_one(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        self.assertTrue(mod.is_anon_telemetry_enabled())


class TestAnonTelemetryYamlConfig(unittest.TestCase):
    """Verify telemetry respects YAML config."""

    def setUp(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        os.environ.pop("NUCLEUS_ANON_TELEMETRY", None)

    def tearDown(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()

    def test_disabled_via_yaml(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        yaml_config = {"telemetry": {"anonymous": {"enabled": False}}}
        with patch.object(mod, '_read_yaml_config', return_value=yaml_config):
            self.assertFalse(mod.is_anon_telemetry_enabled())

    def test_enabled_via_yaml(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        yaml_config = {"telemetry": {"anonymous": {"enabled": True}}}
        with patch.object(mod, '_read_yaml_config', return_value=yaml_config):
            self.assertTrue(mod.is_anon_telemetry_enabled())

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY": "false"})
    def test_env_overrides_yaml(self):
        """Env var should take priority over YAML config."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        yaml_config = {"telemetry": {"anonymous": {"enabled": True}}}
        with patch.object(mod, '_read_yaml_config', return_value=yaml_config):
            self.assertFalse(mod.is_anon_telemetry_enabled())


class TestAnonTelemetryRecording(unittest.TestCase):
    """Verify record_anon_command works when enabled."""

    def setUp(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()

    def tearDown(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY": "true"})
    def test_record_success(self):
        """record_anon_command should not raise when enabled."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        mod._ensure_initialized()
        mod.record_anon_command("morning-brief", "cli", 150.0)

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY": "true"})
    def test_record_with_error(self):
        """record_anon_command with error_type should not raise."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        mod._ensure_initialized()
        mod.record_anon_command("engram.write", "nucleus_engrams", 50.0, error_type="ValueError")

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY": "true"})
    def test_record_minimal(self):
        """record_anon_command with just command name should work."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        mod._ensure_initialized()
        mod.record_anon_command("status")


class TestAnonTelemetrySafety(unittest.TestCase):
    """Verify all hooks are safe — never propagate exceptions."""

    def setUp(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()

    def tearDown(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()

    def test_survives_broken_counter(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod._enabled_cache = True
        mod._config_checked = True
        mod._initialized = True
        mod._command_counter = MagicMock()
        mod._command_counter.add.side_effect = RuntimeError("broken")
        mod._command_duration_histogram = MagicMock()
        mod._command_duration_histogram.record.side_effect = RuntimeError("broken")
        mod._tracer = MagicMock()
        mod._tracer.start_as_current_span.side_effect = RuntimeError("broken")

        # Should not raise
        mod.record_anon_command("test", "cli", 10.0)

    def test_survives_broken_tracer(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod._enabled_cache = True
        mod._config_checked = True
        mod._initialized = True
        mod._command_counter = None
        mod._command_duration_histogram = None
        mod._tracer = MagicMock()
        mod._tracer.start_as_current_span.side_effect = RuntimeError("broken")

        mod.record_anon_command("test", "cli", 10.0, error_type="RuntimeError")


class TestAnonTelemetryEndpoint(unittest.TestCase):
    """Verify custom endpoint configuration."""

    def setUp(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()

    def tearDown(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        os.environ.pop("NUCLEUS_ANON_TELEMETRY_ENDPOINT", None)

    def test_default_endpoint(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        os.environ.pop("NUCLEUS_ANON_TELEMETRY_ENDPOINT", None)
        with patch.object(mod, '_read_yaml_config', return_value={}):
            self.assertEqual(mod._get_endpoint(), "https://telemetry.nucleusos.dev:4317")

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY_ENDPOINT": "https://custom.example.com:4317"})
    def test_env_endpoint_override(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        self.assertEqual(mod._get_endpoint(), "https://custom.example.com:4317")

    def test_yaml_endpoint_override(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        os.environ.pop("NUCLEUS_ANON_TELEMETRY_ENDPOINT", None)
        yaml_config = {"telemetry": {"anonymous": {"endpoint": "https://yaml.example.com:4317"}}}
        with patch.object(mod, '_read_yaml_config', return_value=yaml_config):
            self.assertEqual(mod._get_endpoint(), "https://yaml.example.com:4317")


class TestAnonTelemetryFirstRunNotice(unittest.TestCase):
    """Verify first-run notice behavior."""

    def setUp(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()

    def tearDown(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()

    def test_notice_creates_marker(self):
        """show_first_run_notice should create marker file."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Path(tmpdir)
            (brain / "config").mkdir(parents=True)
            marker = brain / "config" / ".telemetry_notice_shown"
            self.assertFalse(marker.exists())
            with patch('mcp_server_nucleus.runtime.common.get_brain_path', return_value=brain):
                mod.show_first_run_notice()
            self.assertTrue(marker.exists())

    def test_notice_skips_when_marker_exists(self):
        """show_first_run_notice should be silent if marker exists."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Path(tmpdir)
            config_dir = brain / "config"
            config_dir.mkdir(parents=True)
            (config_dir / ".telemetry_notice_shown").write_text("shown\n")
            # Should not print anything
            from unittest.mock import patch as mock_patch
            with mock_patch.object(mod, '_read_yaml_config', return_value={}):
                with mock_patch('mcp_server_nucleus.runtime.common.get_brain_path', return_value=brain):
                    mod.show_first_run_notice()  # Should be silent


class TestAnonTelemetryReset(unittest.TestCase):
    """Verify reset cleans all state."""

    def test_reset_cleans_state(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod._enabled_cache = True
        mod._config_checked = True
        mod._initialized = True
        mod._tracer = "fake"
        mod._meter = "fake"
        mod._command_counter = "fake"
        mod._command_duration_histogram = "fake"

        mod.reset_anon_telemetry_state()

        self.assertFalse(mod._initialized)
        self.assertIsNone(mod._tracer)
        self.assertIsNone(mod._meter)
        self.assertIsNone(mod._command_counter)
        self.assertIsNone(mod._command_duration_histogram)
        self.assertIsNone(mod._enabled_cache)
        self.assertFalse(mod._config_checked)


class TestAnonTelemetryPrivacy(unittest.TestCase):
    """Verify no sensitive data leaks into telemetry attributes."""

    def test_static_attributes_contain_no_pii(self):
        """Static attributes should only contain version/platform info."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        attrs = mod._get_static_attributes()
        # Only safe keys
        allowed_keys = {"nucleus.version", "python.version", "os.platform", "os.arch"}
        self.assertEqual(set(attrs.keys()), allowed_keys)
        # No file paths
        for v in attrs.values():
            self.assertNotIn("/", str(v))
            self.assertNotIn("\\", str(v))
            self.assertNotIn("home", str(v).lower())


if __name__ == "__main__":
    unittest.main()
