"""Tests for shared_state_ops key sanitization edge cases."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server-nucleus" / "src"))

from mcp_server_nucleus.runtime.shared_state_ops import _sanitize_key, brain_sync_read, brain_sync_write, brain_sync_list


class TestSanitizeKey:
    """Test _sanitize_key edge cases."""

    def test_normal_key(self):
        assert _sanitize_key("my_key") == "my_key"

    def test_key_with_slashes(self):
        assert _sanitize_key("a/b") == "a_b"

    def test_key_with_backslashes(self):
        assert _sanitize_key("a\\b") == "a_b"

    def test_double_dots_replaced(self):
        assert _sanitize_key("a..b") == "a_b"

    def test_triple_dots_no_trailing_dot(self):
        # "..." -> replace("..", "_") -> "_." -> rstrip(".") -> "_"
        assert _sanitize_key("...") == "_"

    def test_five_dots_no_trailing_dot(self):
        # "....." -> replace("..", "_") -> "__." -> rstrip(".") -> "__"
        assert _sanitize_key(".....") == "__"

    def test_double_dots_only(self):
        # ".." -> replace("..", "_") -> "_"
        assert _sanitize_key("..") == "_"

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            _sanitize_key("   ")

    def test_tab_newline_raises(self):
        with pytest.raises(ValueError):
            _sanitize_key("\t\n")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            _sanitize_key("")

    def test_dot_prefix_raises(self):
        with pytest.raises(ValueError):
            _sanitize_key(".hidden")

    def test_single_dot_raises(self):
        # "." -> not replaced (no "..") -> startswith(".") -> raises
        with pytest.raises(ValueError):
            _sanitize_key(".")

    def test_key_with_valid_dot(self):
        assert _sanitize_key("a.b") == "a.b"

    def test_key_with_trailing_dot_stripped(self):
        assert _sanitize_key("abc.") == "abc"


class TestBrainSyncReadWrite:
    """Integration tests for read/write with sanitized keys."""

    @patch("mcp_server_nucleus.runtime.shared_state_ops._get_shared_dir")
    def test_write_and_read(self, mock_dir, tmp_path):
        mock_dir.return_value = tmp_path
        result = brain_sync_write("test_key", {"hello": "world"}, agent_id="agent-1")
        assert result["written"] is True
        assert result["value"] == {"hello": "world"}

        read = brain_sync_read("test_key")
        assert read["found"] is True
        assert read["value"] == {"hello": "world"}

    @patch("mcp_server_nucleus.runtime.shared_state_ops._get_shared_dir")
    def test_read_missing_key(self, mock_dir, tmp_path):
        mock_dir.return_value = tmp_path
        result = brain_sync_read("nonexistent")
        assert result["found"] is False

    @patch("mcp_server_nucleus.runtime.shared_state_ops._get_shared_dir")
    def test_list_keys(self, mock_dir, tmp_path):
        mock_dir.return_value = tmp_path
        brain_sync_write("key_a", 1, agent_id="a")
        brain_sync_write("key_b", 2, agent_id="b")
        result = brain_sync_list()
        assert result["count"] == 2

    @patch("mcp_server_nucleus.runtime.shared_state_ops._get_shared_dir")
    def test_write_rejects_bad_key(self, mock_dir, tmp_path):
        mock_dir.return_value = tmp_path
        with pytest.raises(ValueError):
            brain_sync_write("   ", "val")
