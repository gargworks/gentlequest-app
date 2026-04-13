"""Tests for scripts/levers/_plan_parser.

Wave 9 — shared parser used by both the plan_audit lever and TB's
_auto_verification_commands. Tests pin the contract so the TB
delegation refactor (R12) is bounded.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.levers._plan_parser import (  # noqa: E402
    extract_modified_files,
    has_files_modified_section,
    has_verification_section,
)


class TestExtractModifiedFiles:
    def test_bullet_list_under_files_modified(self):
        text = (
            "# Plan\n\n"
            "## Files Modified\n\n"
            "- `scripts/levers/plan_audit.py`\n"
            "- `tests/test_levers.py`\n\n"
            "## Verification\n"
            "- pytest -q\n"
        )
        assert extract_modified_files(text) == [
            "scripts/levers/plan_audit.py",
            "tests/test_levers.py",
        ]

    def test_affected_files_header_alias(self):
        text = (
            "## Affected Files\n"
            "- `scripts/foo.py`\n"
            "- `scripts/bar.py`\n"
        )
        assert extract_modified_files(text) == [
            "scripts/foo.py",
            "scripts/bar.py",
        ]

    def test_table_row_backtick_path(self):
        text = (
            "## Files Modified\n\n"
            "| File | Change |\n"
            "|------|--------|\n"
            "| `scripts/baz.py` | new |\n"
            "| `scripts/qux.py` | modified |\n"
        )
        paths = extract_modified_files(text)
        assert "scripts/baz.py" in paths
        assert "scripts/qux.py" in paths

    def test_em_dash_inline_comment_stripped(self):
        text = (
            "## Files Modified\n"
            "- `scripts/x.py` — adds new helper\n"
            "- `scripts/y.py` — refactor\n"
        )
        assert extract_modified_files(text) == [
            "scripts/x.py",
            "scripts/y.py",
        ]

    def test_missing_section_returns_empty(self):
        text = "# Plan\n\nSome prose with no Files Modified header.\n"
        assert extract_modified_files(text) == []

    def test_empty_files_modified_section_is_empty_list(self):
        text = (
            "## Files Modified\n\n"
            "## Verification\n"
            "- pytest -q\n"
        )
        assert extract_modified_files(text) == []

    def test_garbage_lines_under_header_dropped(self):
        text = (
            "## Files Modified\n"
            "Some prose without a path.\n"
            "- `scripts/keep.py`\n"
            "Just text.\n"
        )
        assert extract_modified_files(text) == ["scripts/keep.py"]


class TestHasSectionHelpers:
    def test_has_files_modified_section_true(self):
        text = "## Files Modified\n- `a.py`\n"
        assert has_files_modified_section(text) is True

    def test_has_files_modified_section_alias(self):
        text = "## Affected Files\n- `a.py`\n"
        assert has_files_modified_section(text) is True

    def test_has_files_modified_section_false(self):
        text = "## Other\n- not paths\n"
        assert has_files_modified_section(text) is False

    def test_has_verification_section_true(self):
        text = "## Verification\n- pytest -q\n"
        assert has_verification_section(text) is True

    def test_has_verification_section_with_trailing_text(self):
        text = "## Verification (Wave 9)\n- pytest -q\n"
        assert has_verification_section(text) is True

    def test_has_verification_section_false(self):
        text = "## Files Modified\n- `a.py`\n"
        assert has_verification_section(text) is False


class TestNumberedAndSynonymHeaders:
    """Revised R1 — parser accepts numbered prefixes and the
    ``Files Changed`` synonym after the ci_test_triage_pr1_db_init
    live-fire surfaced the gap."""

    def test_numbered_prefix_files_modified(self):
        text = "## 4. Files Modified\n- `scripts/x.py`\n"
        assert extract_modified_files(text) == ["scripts/x.py"]
        assert has_files_modified_section(text) is True

    def test_files_changed_synonym_plain(self):
        text = "## Files Changed\n- `scripts/y.py`\n"
        assert extract_modified_files(text) == ["scripts/y.py"]
        assert has_files_modified_section(text) is True

    def test_numbered_prefix_files_changed_combo(self):
        """The exact form used by ci_test_triage_pr1_db_init.md."""
        text = (
            "## 4. Files Changed\n\n"
            "| File | Change |\n"
            "|------|--------|\n"
            "| `app.py` | two keyword adds |\n"
            "| `.github/workflows/test_on_pr.yml` | env lines |\n"
        )
        paths = extract_modified_files(text)
        assert "app.py" in paths
        assert ".github/workflows/test_on_pr.yml" in paths

    def test_numbered_prefix_verification_sequence(self):
        """The exact form used by ci_test_triage_pr1_db_init.md."""
        text = "## 6. Verification Sequence\n```bash\npytest -q\n```\n"
        assert has_verification_section(text) is True


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
