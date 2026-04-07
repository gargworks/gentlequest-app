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
import uuid


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

    def test_static_attributes_contain_expected_keys(self):
        """Static attributes should contain version/platform info plus telemetry signals."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        attrs = mod._get_static_attributes()
        expected_keys = {
            "nucleus.version", "python.version", "os.platform", "os.arch",
            "nucleus.install_id", "nucleus.session_id",
            "nucleus.is_ci", "nucleus.is_dev",
        }
        self.assertEqual(set(attrs.keys()), expected_keys)

    def test_static_attributes_no_file_paths(self):
        """No attribute value should contain file paths or home directory references."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        attrs = mod._get_static_attributes()
        for k, v in attrs.items():
            val = str(v)
            # install_id and session_id are hex UUIDs, skip path checks
            if k in ("nucleus.install_id", "nucleus.session_id"):
                continue
            self.assertNotIn("/", val)
            self.assertNotIn("\\", val)
            self.assertNotIn("home", val.lower())


class TestSessionId(unittest.TestCase):
    """Verify session_id behavior."""

    def test_session_id_is_hex(self):
        """Session ID should be a valid hex string."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        sid = mod._SESSION_ID
        self.assertEqual(len(sid), 32)
        int(sid, 16)  # Should not raise

    def test_session_id_stable_within_module(self):
        """Session ID should be the same across multiple reads."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        self.assertEqual(mod._SESSION_ID, mod._SESSION_ID)

    def test_session_id_in_static_attrs(self):
        """Session ID should appear in static attributes."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        attrs = mod._get_static_attributes()
        self.assertEqual(attrs["nucleus.session_id"], mod._SESSION_ID)


class TestInstallId(unittest.TestCase):
    """Verify install_id behavior."""

    def test_install_id_created_on_first_call(self):
        """Install ID should be created if it doesn't exist."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            id_file = fake_home / ".config" / "nucleus" / "install_id"
            self.assertFalse(id_file.exists())
            with patch.object(Path, 'home', return_value=fake_home):
                result = mod._get_install_id()
            self.assertTrue(id_file.exists())
            self.assertEqual(len(result), 32)
            int(result, 16)  # Valid hex

    def test_install_id_persists_across_calls(self):
        """Install ID should return the same value on subsequent calls."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                first = mod._get_install_id()
                second = mod._get_install_id()
            self.assertEqual(first, second)

    def test_install_id_returns_unknown_on_error(self):
        """Install ID should return 'unknown' if filesystem fails."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            id_file = fake_home / ".config" / "nucleus" / "install_id"
            # Make the parent dir a file so mkdir fails
            id_file.parent.parent.mkdir(parents=True, exist_ok=True)
            (fake_home / ".config" / "nucleus").mkdir(parents=True, exist_ok=True)
            # Remove write permission on the directory
            os.chmod(str(fake_home / ".config" / "nucleus"), 0o000)
            try:
                with patch.object(Path, 'home', return_value=fake_home):
                    result = mod._get_install_id()
                self.assertEqual(result, "unknown")
            finally:
                os.chmod(str(fake_home / ".config" / "nucleus"), 0o755)


class TestIsCi(unittest.TestCase):
    """Verify CI detection."""

    @patch.dict(os.environ, {"CI": "true"})
    def test_ci_true(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        self.assertTrue(mod._is_ci())

    @patch.dict(os.environ, {"CI": "1"})
    def test_ci_one(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        self.assertTrue(mod._is_ci())

    @patch.dict(os.environ, {"CI": "yes"})
    def test_ci_yes(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        self.assertTrue(mod._is_ci())

    @patch.dict(os.environ, {}, clear=True)
    def test_ci_not_set(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        os.environ.pop("CI", None)
        self.assertFalse(mod._is_ci())

    @patch.dict(os.environ, {"CI": "false"})
    def test_ci_false(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        self.assertFalse(mod._is_ci())


class TestIsDev(unittest.TestCase):
    """Verify dev machine detection."""

    @patch.dict(os.environ, {"NUCLEUS_DEV": "1"})
    def test_dev_env_var(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        self.assertTrue(mod._is_dev())

    def test_dev_marker_file(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            marker = fake_home / ".config" / "nucleus" / "is_dev"
            marker.parent.mkdir(parents=True)
            marker.touch()
            with patch.object(Path, 'home', return_value=fake_home):
                with patch.dict(os.environ, {}, clear=True):
                    os.environ.pop("NUCLEUS_DEV", None)
                    self.assertTrue(mod._is_dev())

    def test_not_dev_by_default(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir)
            with patch.object(Path, 'home', return_value=fake_home):
                with patch.dict(os.environ, {}, clear=True):
                    os.environ.pop("NUCLEUS_DEV", None)
                    self.assertFalse(mod._is_dev())


class TestV2TelemetryNotice(unittest.TestCase):
    """Verify version-gated v2 telemetry notice."""

    def setUp(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()

    def tearDown(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY": "true"})
    def test_v2_notice_creates_marker(self):
        """show_v2_telemetry_notice should create v2 marker file."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        with tempfile.TemporaryDirectory() as tmpdir:
            marker = Path(tmpdir) / mod._TELEMETRY_V2_MARKER
            self.assertFalse(marker.exists())
            with patch.dict(os.environ, {"NUCLEAR_BRAIN_PATH": tmpdir}):
                mod.show_v2_telemetry_notice()
            self.assertTrue(marker.exists())

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY": "true"})
    def test_v2_notice_skips_when_marker_exists(self):
        """show_v2_telemetry_notice should be silent if v2 marker exists."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        with tempfile.TemporaryDirectory() as tmpdir:
            marker = Path(tmpdir) / mod._TELEMETRY_V2_MARKER
            marker.touch()
            with patch.dict(os.environ, {"NUCLEAR_BRAIN_PATH": tmpdir}):
                with patch('builtins.print') as mock_print:
                    mod.show_v2_telemetry_notice()
                    mock_print.assert_not_called()

    @patch.dict(os.environ, {"NUCLEUS_ANON_TELEMETRY": "false"})
    def test_v2_notice_skips_when_disabled(self):
        """show_v2_telemetry_notice should be silent if telemetry disabled."""
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        mod.reset_anon_telemetry_state()
        with patch('builtins.print') as mock_print:
            mod.show_v2_telemetry_notice()
            mock_print.assert_not_called()


class TestSpanContainsNewFields(unittest.TestCase):
    """Verify built OTLP spans include the new telemetry fields."""

    def test_span_has_install_id(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        span = mod._build_otlp_span("test-cmd", "cli", 100.0)
        attrs = span["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["attributes"]
        keys = [a["key"] for a in attrs]
        self.assertIn("nucleus.install_id", keys)

    def test_span_has_session_id(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        span = mod._build_otlp_span("test-cmd", "cli", 100.0)
        attrs = span["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["attributes"]
        keys = [a["key"] for a in attrs]
        self.assertIn("nucleus.session_id", keys)

    def test_span_has_ci_flag(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        span = mod._build_otlp_span("test-cmd", "cli", 100.0)
        attrs = span["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["attributes"]
        ci_attr = [a for a in attrs if a["key"] == "nucleus.is_ci"][0]
        self.assertIn(ci_attr["value"]["stringValue"], ("true", "false"))

    def test_span_has_dev_flag(self):
        import mcp_server_nucleus.runtime.anon_telemetry as mod
        span = mod._build_otlp_span("test-cmd", "cli", 100.0)
        attrs = span["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["attributes"]
        dev_attr = [a for a in attrs if a["key"] == "nucleus.is_dev"][0]
        self.assertIn(dev_attr["value"]["stringValue"], ("true", "false"))


if __name__ == "__main__":
    unittest.main()
