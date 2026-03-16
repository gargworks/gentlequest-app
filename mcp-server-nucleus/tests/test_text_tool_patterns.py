"""Test text-based tool call detection patterns used in the ReAct loop."""
import re
from typing import Optional
import pytest


# The 5 patterns from cli.py's ReAct loop
EXECUTE_PATTERN = r"<execute>(.*?)</execute>"
TEXT_PATTERNS = [
    r'shell_execute[=(]\s*\{["\']command["\']\s*:\s*["\']([^"\']+)["\']',
    r'function=shell_execute>\s*\{\s*"command"\s*:\s*"([^"]+)"',
    r"shell_execute\(\[?['\"]([^'\"]+)['\"]\]?\)",
    r'shell_execute:\s+(.+?)$',
]


def _detect_tool_call(reply: str) -> Optional[str]:
    """Replicate the cli.py tool detection logic. Returns command or None."""
    match = re.search(EXECUTE_PATTERN, reply, flags=re.DOTALL)
    if not match:
        for tc_pattern in TEXT_PATTERNS:
            tc_match = re.search(tc_pattern, reply, re.DOTALL | re.MULTILINE)
            if tc_match:
                match = tc_match
                break
    return match.group(1).strip() if match else None


class TestExecuteTags:
    def test_basic(self):
        assert _detect_tool_call("<execute>ls -la</execute>") == "ls -la"

    def test_multiline(self):
        reply = "Let me check:\n<execute>nucleus status</execute>\nDone."
        assert _detect_tool_call(reply) == "nucleus status"

    def test_with_args(self):
        assert _detect_tool_call('<execute>nucleus engram search "youtube"</execute>') == 'nucleus engram search "youtube"'


class TestShellExecuteJSON:
    """Pattern: shell_execute={"command":"ls"} or shell_execute({"command":"ls"})"""

    def test_equals_format(self):
        assert _detect_tool_call('shell_execute={"command":"ls -la"}') == "ls -la"

    def test_paren_format(self):
        assert _detect_tool_call("shell_execute({'command': 'nucleus status'})") == "nucleus status"


class TestFunctionFormat:
    """Pattern: function=shell_execute>{"command":"ls"}"""

    def test_basic(self):
        reply = 'function=shell_execute>{"command":"nucleus engram list"}'
        assert _detect_tool_call(reply) == "nucleus engram list"

    def test_embedded(self):
        reply = 'I will run function=shell_execute>{"command":"ls"} to check.'
        assert _detect_tool_call(reply) == "ls"


class TestShellExecuteCall:
    """Pattern: shell_execute(['cmd']) or shell_execute('cmd')"""

    def test_single_quotes(self):
        assert _detect_tool_call("shell_execute('nucleus status')") == "nucleus status"

    def test_list_format(self):
        assert _detect_tool_call("shell_execute(['ls -la'])") == "ls -la"

    def test_double_quotes(self):
        assert _detect_tool_call('shell_execute("nucleus task list")') == "nucleus task list"


class TestColonFormat:
    """Pattern: shell_execute: <command> (common with Groq models)"""

    def test_basic(self):
        assert _detect_tool_call("shell_execute: nucleus status") == "nucleus status"

    def test_with_args(self):
        assert _detect_tool_call('shell_execute: nucleus engram search "youtube"') == 'nucleus engram search "youtube"'

    def test_embedded_in_prose(self):
        reply = "I will run the command:\nshell_execute: ls -la\nThen analyze."
        assert _detect_tool_call(reply) == "ls -la"

    def test_multiple_lines_takes_first(self):
        reply = "shell_execute: nucleus status\nshell_execute: nucleus task list"
        # Should catch the first one
        assert _detect_tool_call(reply) == "nucleus status"


class TestNoMatch:
    def test_plain_text(self):
        assert _detect_tool_call("Hello, how can I help?") is None

    def test_mentions_shell_execute_in_prose(self):
        assert _detect_tool_call("You can use shell_execute to run commands") is None

    def test_empty(self):
        assert _detect_tool_call("") is None
