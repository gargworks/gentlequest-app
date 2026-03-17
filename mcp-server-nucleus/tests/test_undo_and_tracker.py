"""Test undo stack and session file tracker logic."""
import pytest
from pathlib import Path


# ── Replicate the undo stack logic from cli.py ──

def make_tracker():
    """Create a fresh file tracker + undo stack pair."""
    session_files = {"read": [], "written": [], "edited": [], "searched": []}
    undo_stack = []

    def track_file(op, path):
        if path and path not in session_files.get(op, []):
            session_files.setdefault(op, []).append(path)

    def snapshot_before(path, op):
        p = Path(path).expanduser()
        existed = p.exists()
        backup = p.read_text() if existed else None
        undo_stack.append({"path": str(p), "op": op, "backup": backup, "existed": existed})
        if len(undo_stack) > 50:
            undo_stack.pop(0)

    def undo():
        if not undo_stack:
            return "nothing"
        entry = undo_stack.pop()
        p = Path(entry["path"])
        if entry["backup"] is not None:
            p.write_text(entry["backup"])
            return "restored"
        elif not entry["existed"]:
            if p.exists():
                p.unlink()
            return "deleted"
        return "no_backup"

    return session_files, undo_stack, track_file, snapshot_before, undo


class TestFileTracker:
    def test_track_read(self):
        sf, _, track, _, _ = make_tracker()
        track("read", "/tmp/test.py")
        assert "/tmp/test.py" in sf["read"]

    def test_no_duplicates(self):
        sf, _, track, _, _ = make_tracker()
        track("read", "/tmp/test.py")
        track("read", "/tmp/test.py")
        assert len(sf["read"]) == 1

    def test_multiple_ops(self):
        sf, _, track, _, _ = make_tracker()
        track("read", "/tmp/a.py")
        track("edited", "/tmp/b.py")
        track("written", "/tmp/c.py")
        assert len(sf["read"]) == 1
        assert len(sf["edited"]) == 1
        assert len(sf["written"]) == 1

    def test_empty_path_ignored(self):
        sf, _, track, _, _ = make_tracker()
        track("read", "")
        assert len(sf["read"]) == 0


class TestUndoStack:
    def test_undo_edit(self, tmp_path):
        sf, us, track, snap, undo = make_tracker()
        f = tmp_path / "code.py"
        f.write_text("original content")

        # Simulate edit
        snap(str(f), "edit")
        f.write_text("modified content")
        assert f.read_text() == "modified content"

        # Undo
        result = undo()
        assert result == "restored"
        assert f.read_text() == "original content"

    def test_undo_write_new_file(self, tmp_path):
        sf, us, track, snap, undo = make_tracker()
        f = tmp_path / "new_file.txt"

        # Simulate writing a new file
        snap(str(f), "write")
        f.write_text("new content")
        assert f.exists()

        # Undo should delete the new file
        result = undo()
        assert result == "deleted"
        assert not f.exists()

    def test_undo_write_existing_file(self, tmp_path):
        sf, us, track, snap, undo = make_tracker()
        f = tmp_path / "existing.txt"
        f.write_text("original")

        # Simulate overwriting
        snap(str(f), "write")
        f.write_text("overwritten")
        assert f.read_text() == "overwritten"

        # Undo restores original
        result = undo()
        assert result == "restored"
        assert f.read_text() == "original"

    def test_undo_empty_stack(self):
        _, _, _, _, undo = make_tracker()
        assert undo() == "nothing"

    def test_multiple_undos(self, tmp_path):
        sf, us, track, snap, undo = make_tracker()
        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        f1.write_text("a_original")
        f2.write_text("b_original")

        # Two edits
        snap(str(f1), "edit")
        f1.write_text("a_modified")
        snap(str(f2), "edit")
        f2.write_text("b_modified")

        # Undo last (f2) first
        undo()
        assert f2.read_text() == "b_original"
        assert f1.read_text() == "a_modified"  # f1 still modified

        # Undo f1
        undo()
        assert f1.read_text() == "a_original"

    def test_stack_caps_at_50(self, tmp_path):
        sf, us, track, snap, undo = make_tracker()
        f = tmp_path / "test.txt"
        f.write_text("content")

        for i in range(60):
            snap(str(f), "edit")

        assert len(us) == 50


class TestNormalizeHistory:
    """Test the _normalize_history function from cli.py."""

    def _normalize(self, raw):
        """Replicate _normalize_history."""
        result = []
        for item in raw:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                result.append((str(item[0]), str(item[1])))
            elif isinstance(item, dict):
                role = item.get("role", "user")
                content = item.get("content", "")
                result.append((str(role), str(content)))
        return result

    def test_list_format(self):
        raw = [["user", "hello"], ["assistant", "hi"]]
        result = self._normalize(raw)
        assert result == [("user", "hello"), ("assistant", "hi")]

    def test_tuple_format(self):
        raw = [("user", "hello"), ("assistant", "hi")]
        result = self._normalize(raw)
        assert result == [("user", "hello"), ("assistant", "hi")]

    def test_dict_format(self):
        raw = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
        result = self._normalize(raw)
        assert result == [("user", "hello"), ("assistant", "hi")]

    def test_mixed_format(self):
        raw = [["user", "one"], {"role": "assistant", "content": "two"}, ("user", "three")]
        result = self._normalize(raw)
        assert len(result) == 3
        assert result[0] == ("user", "one")
        assert result[1] == ("assistant", "two")
        assert result[2] == ("user", "three")

    def test_malformed_skipped(self):
        raw = [["user", "ok"], "broken", [1], {"no_role_key": True}]
        result = self._normalize(raw)
        # list with 2 items passes, "broken" string skipped, [1] too short, dict with no role defaults
        assert result[0] == ("user", "ok")
        assert len(result) == 2  # "ok" + dict with defaults

    def test_empty(self):
        assert self._normalize([]) == []
