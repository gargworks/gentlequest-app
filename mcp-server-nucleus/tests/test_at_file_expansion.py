"""Test @file reference expansion in user input."""
import re
from pathlib import Path
import pytest


# Replicate the @file expansion logic from cli.py (simplified for testing)
def _expand_at_files(user_input: str, cwd: Path = None, track_fn=None, brain_fn=None):
    """Expand @file references. Simplified from cli.py for unit testing."""
    _at_pattern = re.compile(r'@([\w./\-*]+(?::\d+)?)')
    matches = _at_pattern.findall(user_input)
    if not matches:
        return user_input

    attachments = []
    for ref in matches:
        if ":" in ref and ref.rsplit(":", 1)[1].isdigit():
            fpath, line_str = ref.rsplit(":", 1)
            target_line = int(line_str)
        else:
            fpath = ref
            target_line = None

        p = Path(fpath).expanduser()

        # Glob pattern
        if "*" in fpath:
            try:
                base = cwd or Path(".")
                glob_matches = sorted(base.glob(fpath))[:20]
                if glob_matches:
                    file_list = "\n".join(f"  {m}" for m in glob_matches)
                    attachments.append(f"[Files matching @{fpath}]\n{file_list}")
            except Exception:
                pass
            continue

        # Single file
        if not p.exists() and cwd:
            p = cwd / fpath
        if not p.exists():
            continue

        try:
            text = p.read_text()
            lines = text.split("\n")
            if track_fn:
                track_fn("read", str(p))

            if target_line:
                start = max(0, target_line - 10)
                end = min(len(lines), target_line + 10)
                selected = lines[start:end]
                numbered = [f"{start + i + 1:>5}| {l}" for i, l in enumerate(selected)]
                attachments.append(
                    f"[File: {p.name}:{target_line} (lines {start+1}-{end})]\n" +
                    "\n".join(numbered)
                )
            else:
                if len(lines) > 200:
                    numbered = [f"{i+1:>5}| {l}" for i, l in enumerate(lines[:200])]
                    attachments.append(
                        f"[File: {p.name} ({len(lines)} lines, showing first 200)]\n" +
                        "\n".join(numbered)
                    )
                else:
                    numbered = [f"{i+1:>5}| {l}" for i, l in enumerate(lines)]
                    attachments.append(
                        f"[File: {p.name} ({len(lines)} lines)]\n" +
                        "\n".join(numbered)
                    )
        except Exception:
            pass

    if not attachments:
        return user_input

    return user_input + "\n\n" + "\n\n".join(attachments)


class TestAtFileBasic:
    def test_no_at_refs(self):
        assert _expand_at_files("hello world") == "hello world"

    def test_at_ref_nonexistent_file(self):
        result = _expand_at_files("check @nonexistent_file_xyz.py")
        assert result == "check @nonexistent_file_xyz.py"

    def test_at_ref_existing_file(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("line1\nline2\nline3\n")
        result = _expand_at_files(f"fix @{f}", cwd=tmp_path)
        assert "[File: test.py" in result
        assert "line1" in result
        assert "line2" in result

    def test_at_ref_with_line_number(self, tmp_path):
        f = tmp_path / "big.py"
        content = "\n".join(f"line{i}" for i in range(1, 50))
        f.write_text(content)
        result = _expand_at_files(f"fix @{f}:25", cwd=tmp_path)
        assert ":25" in result
        assert "line25" in result
        # Should show lines around 25 (±10)
        assert "line16" in result  # 25-10+1=16 (0-indexed start)
        assert "line34" in result  # within range


class TestAtFileGlob:
    def test_glob_pattern(self, tmp_path):
        (tmp_path / "a.py").write_text("aa")
        (tmp_path / "b.py").write_text("bb")
        (tmp_path / "c.txt").write_text("cc")
        result = _expand_at_files("list @*.py", cwd=tmp_path)
        assert "[Files matching @*.py]" in result
        assert "a.py" in result
        assert "b.py" in result
        assert "c.txt" not in result


class TestAtFileMultiple:
    def test_two_files(self, tmp_path):
        f1 = tmp_path / "one.py"
        f2 = tmp_path / "two.py"
        f1.write_text("first file")
        f2.write_text("second file")
        result = _expand_at_files(f"compare @{f1} with @{f2}", cwd=tmp_path)
        assert "[File: one.py" in result
        assert "[File: two.py" in result
        assert "first file" in result
        assert "second file" in result


class TestAtFileTracking:
    def test_tracks_read(self, tmp_path):
        f = tmp_path / "tracked.py"
        f.write_text("content")
        tracked = []
        _expand_at_files(f"read @{f}", cwd=tmp_path, track_fn=lambda op, p: tracked.append((op, p)))
        assert len(tracked) == 1
        assert tracked[0][0] == "read"


class TestAtFileLargeFile:
    def test_caps_at_200_lines(self, tmp_path):
        f = tmp_path / "huge.py"
        f.write_text("\n".join(f"line{i}" for i in range(500)))
        result = _expand_at_files(f"check @{f}", cwd=tmp_path)
        assert "showing first 200" in result
        assert "line199" in result
        # Line 300 should NOT be in the output
        assert "line300" not in result
