"""Test _execute_tool dispatcher for all 6 tool types."""
import os
import tempfile
from pathlib import Path
import pytest


# Import the function by extracting it from cli module patterns.
# Since _execute_tool is a nested function, we replicate its logic here for unit testing.

def _execute_tool(tool_name: str, tool_input: dict, step: int) -> str:
    """Mirrors cli.py _execute_tool — extracted for testability."""
    if tool_name == "shell_execute":
        command = tool_input.get("command", "")
        import subprocess as _sp
        try:
            res = _sp.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
        except Exception as e:
            return f"Execution failed: {e}"

    elif tool_name == "read_file":
        fpath = tool_input.get("path", "")
        offset = tool_input.get("offset", 1)
        limit = tool_input.get("limit", 500)
        try:
            p = Path(fpath).expanduser()
            if not p.exists():
                return f"Error: File not found: {fpath}"
            text = p.read_text()
            all_lines = text.split("\n")
            start = max(0, (offset or 1) - 1)
            end = start + (limit or 500)
            selected = all_lines[start:end]
            numbered = [f"{start + i + 1:>5}| {line}" for i, line in enumerate(selected)]
            return "\n".join(numbered)[:8000]
        except Exception as e:
            return f"Error reading file: {e}"

    elif tool_name == "write_file":
        fpath = tool_input.get("path", "")
        content = tool_input.get("content", "")
        try:
            p = Path(fpath).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            lines = content.count("\n") + 1
            return f"Successfully wrote {fpath} ({lines} lines, {len(content)} bytes)"
        except Exception as e:
            return f"Error writing file: {e}"

    elif tool_name == "edit_file":
        fpath = tool_input.get("path", "")
        old = tool_input.get("old_string", "")
        new = tool_input.get("new_string", "")
        try:
            p = Path(fpath).expanduser()
            if not p.exists():
                return f"Error: File not found: {fpath}"
            text = p.read_text()
            count = text.count(old)
            if count == 0:
                return f"Error: old_string not found in {fpath}"
            if count > 1:
                return f"Error: old_string matches {count} times in {fpath}. Make it more specific."
            new_text = text.replace(old, new, 1)
            p.write_text(new_text)
            return f"Successfully edited {fpath}"
        except Exception as e:
            return f"Error editing file: {e}"

    elif tool_name == "search_files":
        pattern = tool_input.get("pattern", "")
        search_path = tool_input.get("path", ".")
        try:
            p = Path(search_path).expanduser()
            matches = sorted(p.glob(pattern))[:50]
            result_lines = [str(m) for m in matches]
            return "\n".join(result_lines) if result_lines else "No files found"
        except Exception as e:
            return f"Error searching files: {e}"

    elif tool_name == "search_code":
        pattern = tool_input.get("pattern", "")
        search_path = tool_input.get("path", ".")
        file_glob = tool_input.get("glob", "")
        try:
            import subprocess as _sp
            cmd = ["grep", "-rn", "--include", file_glob, pattern, search_path] if file_glob else ["grep", "-rn", pattern, search_path]
            res = _sp.run(cmd, capture_output=True, text=True, timeout=15)
            return res.stdout[:8000] if res.stdout else "No matches found"
        except Exception as e:
            return f"Error searching code: {e}"

    return f"Unknown tool: {tool_name}"


class TestShellExecute:
    def test_echo(self):
        result = _execute_tool("shell_execute", {"command": "echo hello"}, 1)
        assert "hello" in result

    def test_bad_command(self):
        result = _execute_tool("shell_execute", {"command": "false"}, 1)
        assert "STDOUT:" in result  # Still returns, just with empty stdout


class TestReadFile:
    def test_read_existing(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("line1\nline2\nline3\n")
        result = _execute_tool("read_file", {"path": str(f)}, 1)
        assert "line1" in result
        assert "line2" in result
        assert "1|" in result  # Line numbers

    def test_read_missing(self):
        result = _execute_tool("read_file", {"path": "/nonexistent/file.txt"}, 1)
        assert "Error: File not found" in result

    def test_read_with_offset(self, tmp_path):
        f = tmp_path / "big.txt"
        f.write_text("\n".join(f"line{i}" for i in range(1, 20)))
        result = _execute_tool("read_file", {"path": str(f), "offset": 5, "limit": 3}, 1)
        assert "line5" in result
        assert "line7" in result
        assert "line8" not in result


class TestWriteFile:
    def test_write_new(self, tmp_path):
        f = tmp_path / "out.txt"
        result = _execute_tool("write_file", {"path": str(f), "content": "hello world"}, 1)
        assert "Successfully wrote" in result
        assert f.read_text() == "hello world"

    def test_write_creates_dirs(self, tmp_path):
        f = tmp_path / "sub" / "deep" / "file.txt"
        result = _execute_tool("write_file", {"path": str(f), "content": "nested"}, 1)
        assert "Successfully wrote" in result
        assert f.read_text() == "nested"


class TestEditFile:
    def test_edit_unique(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("def foo():\n    return 1\n")
        result = _execute_tool("edit_file", {"path": str(f), "old_string": "return 1", "new_string": "return 42"}, 1)
        assert "Successfully edited" in result
        assert "return 42" in f.read_text()

    def test_edit_not_found(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("def foo():\n    pass\n")
        result = _execute_tool("edit_file", {"path": str(f), "old_string": "NOPE", "new_string": "yes"}, 1)
        assert "not found" in result

    def test_edit_ambiguous(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("x = 1\nx = 1\n")
        result = _execute_tool("edit_file", {"path": str(f), "old_string": "x = 1", "new_string": "x = 2"}, 1)
        assert "matches 2 times" in result

    def test_edit_missing_file(self):
        result = _execute_tool("edit_file", {"path": "/nonexistent.py", "old_string": "a", "new_string": "b"}, 1)
        assert "File not found" in result


class TestSearchFiles:
    def test_glob(self, tmp_path):
        (tmp_path / "a.py").write_text("")
        (tmp_path / "b.py").write_text("")
        (tmp_path / "c.txt").write_text("")
        result = _execute_tool("search_files", {"pattern": "*.py", "path": str(tmp_path)}, 1)
        assert "a.py" in result
        assert "b.py" in result
        assert "c.txt" not in result

    def test_no_matches(self, tmp_path):
        result = _execute_tool("search_files", {"pattern": "*.xyz", "path": str(tmp_path)}, 1)
        assert "No files found" in result


class TestSearchCode:
    def test_grep(self, tmp_path):
        (tmp_path / "code.py").write_text("def main():\n    print('hello')\n")
        result = _execute_tool("search_code", {"pattern": "def main", "path": str(tmp_path)}, 1)
        assert "def main" in result

    def test_no_match(self, tmp_path):
        (tmp_path / "code.py").write_text("x = 1\n")
        result = _execute_tool("search_code", {"pattern": "NOTHERE", "path": str(tmp_path)}, 1)
        assert "No matches" in result


class TestUnknownTool:
    def test_unknown(self):
        result = _execute_tool("hack_server", {"target": "prod"}, 1)
        assert "Unknown tool" in result
