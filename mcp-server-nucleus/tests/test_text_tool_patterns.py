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


# ── New: rich tool detection (mirrors cli.py priority 1-3) ──

EXECUTE_TOOL_PATTERN = r"<execute_tool>(.*?)</execute_tool>"
RICH_TOOLS = ("read_file", "write_file", "edit_file", "search_files", "search_code", "write_engram", "search_engrams", "list_tasks", "add_task", "update_task")


def _detect_rich_tool(reply: str):
    """Replicate cli.py full tool detection. Returns (tool_name, tool_input) or None."""
    import json

    # 1. <execute_tool>{JSON}</execute_tool>
    etool_m = re.search(EXECUTE_TOOL_PATTERN, reply, flags=re.DOTALL)
    if etool_m:
        try:
            td = json.loads(etool_m.group(1).strip())
            tn = td.pop("tool", "")
            if tn in RICH_TOOLS:
                return (tn, td)
        except Exception:
            pass

    # 2. <execute>cmd</execute>
    exec_m = re.search(EXECUTE_PATTERN, reply, flags=re.DOTALL)
    if exec_m:
        return ("shell_execute", {"command": exec_m.group(1).strip()})

    # 3. JSON-style: tool_name({"key":"val"}) or tool_name={"key":"val"}
    for tname in RICH_TOOLS:
        jm = re.search(rf'{tname}[=(]\s*(\{{.*?\}})', reply, re.DOTALL)
        if jm:
            try:
                return (tname, json.loads(jm.group(1)))
            except Exception:
                pass
            break

    # 4. shell_execute text patterns
    for tc_pattern in TEXT_PATTERNS:
        tc_match = re.search(tc_pattern, reply, re.DOTALL | re.MULTILINE)
        if tc_match:
            return ("shell_execute", {"command": tc_match.group(1).strip()})

    return None


class TestExecuteToolTag:
    """<execute_tool> JSON tag for file operations."""

    def test_read_file(self):
        reply = '<execute_tool>{"tool": "read_file", "path": "src/main.py"}</execute_tool>'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "read_file"
        assert ti == {"path": "src/main.py"}

    def test_write_file(self):
        reply = '<execute_tool>{"tool": "write_file", "path": "out.txt", "content": "hello world"}</execute_tool>'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "write_file"
        assert ti == {"path": "out.txt", "content": "hello world"}

    def test_edit_file(self):
        reply = '<execute_tool>{"tool": "edit_file", "path": "f.py", "old_string": "foo", "new_string": "bar"}</execute_tool>'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "edit_file"
        assert ti == {"path": "f.py", "old_string": "foo", "new_string": "bar"}

    def test_search_files(self):
        reply = '<execute_tool>{"tool": "search_files", "pattern": "**/*.py"}</execute_tool>'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "search_files"
        assert ti == {"pattern": "**/*.py"}

    def test_search_code(self):
        reply = '<execute_tool>{"tool": "search_code", "pattern": "def main", "path": "src/"}</execute_tool>'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "search_code"
        assert ti == {"pattern": "def main", "path": "src/"}

    def test_embedded_in_prose(self):
        reply = 'Let me read the file:\n<execute_tool>{"tool": "read_file", "path": "README.md"}</execute_tool>\nDone.'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "read_file"
        assert ti == {"path": "README.md"}

    def test_invalid_json_falls_through(self):
        reply = '<execute_tool>not valid json</execute_tool>'
        assert _detect_rich_tool(reply) is None

    def test_unknown_tool_ignored(self):
        reply = '<execute_tool>{"tool": "hack_server", "target": "prod"}</execute_tool>'
        assert _detect_rich_tool(reply) is None


class TestRichToolTextPatterns:
    """Models printing file tool calls as text (JSON-style)."""

    def test_read_file_equals(self):
        reply = 'read_file={"path": "/tmp/test.py"}'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "read_file"
        assert ti["path"] == "/tmp/test.py"

    def test_edit_file_paren(self):
        reply = 'edit_file({"path": "f.py", "old_string": "a", "new_string": "b"})'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "edit_file"
        assert ti["old_string"] == "a"

    def test_search_code_in_prose(self):
        reply = 'I will search: search_code={"pattern": "import os", "path": "src/"}'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "search_code"
        assert ti["pattern"] == "import os"


class TestRichToolPriority:
    """execute_tool tag takes priority over execute tag."""

    def test_execute_tool_beats_execute(self):
        reply = '<execute_tool>{"tool": "read_file", "path": "f.py"}</execute_tool>\n<execute>ls</execute>'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "read_file"

    def test_execute_still_works(self):
        reply = "Check this:\n<execute>ls -la</execute>"
        tn, ti = _detect_rich_tool(reply)
        assert tn == "shell_execute"
        assert ti["command"] == "ls -la"

    def test_shell_text_pattern_still_works(self):
        reply = "shell_execute: nucleus status"
        tn, ti = _detect_rich_tool(reply)
        assert tn == "shell_execute"
        assert ti["command"] == "nucleus status"


class TestEngramToolPatterns:
    """Brain tool detection via <execute_tool> and text patterns."""

    def test_write_engram_execute_tool_tag(self):
        reply = '<execute_tool>{"tool": "write_engram", "key": "fastapi_pattern", "value": "uses dependency injection", "context": "Architecture"}</execute_tool>'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "write_engram"
        assert ti["key"] == "fastapi_pattern"
        assert ti["context"] == "Architecture"

    def test_search_engrams_execute_tool_tag(self):
        reply = '<execute_tool>{"tool": "search_engrams", "query": "database"}</execute_tool>'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "search_engrams"
        assert ti["query"] == "database"

    def test_write_engram_text_pattern(self):
        reply = 'write_engram={"key": "test_key", "value": "test_val", "context": "Decision"}'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "write_engram"
        assert ti["key"] == "test_key"

    def test_search_engrams_text_pattern(self):
        reply = 'search_engrams({"query": "compliance", "limit": 3})'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "search_engrams"
        assert ti["query"] == "compliance"
        assert ti["limit"] == 3

    def test_write_engram_with_intensity(self):
        reply = '<execute_tool>{"tool": "write_engram", "key": "critical_bug", "value": "DB connection pool leaks under load", "context": "Architecture", "intensity": 9}</execute_tool>'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "write_engram"
        assert ti["intensity"] == 9


class TestTaskToolPatterns:
    """Task tool detection via <execute_tool> and text patterns."""

    def test_list_tasks_tag(self):
        reply = '<execute_tool>{"tool": "list_tasks"}</execute_tool>'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "list_tasks"

    def test_list_tasks_with_status(self):
        reply = '<execute_tool>{"tool": "list_tasks", "status": "PENDING"}</execute_tool>'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "list_tasks"
        assert ti["status"] == "PENDING"

    def test_add_task_tag(self):
        reply = '<execute_tool>{"tool": "add_task", "description": "Implement auth", "priority": 2}</execute_tool>'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "add_task"
        assert ti["description"] == "Implement auth"
        assert ti["priority"] == 2

    def test_update_task_tag(self):
        reply = '<execute_tool>{"tool": "update_task", "task_id": "task-abc123", "status": "DONE"}</execute_tool>'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "update_task"
        assert ti["task_id"] == "task-abc123"

    def test_add_task_text_pattern(self):
        reply = 'add_task={"description": "Fix login bug", "priority": 1}'
        tn, ti = _detect_rich_tool(reply)
        assert tn == "add_task"
        assert ti["priority"] == 1
