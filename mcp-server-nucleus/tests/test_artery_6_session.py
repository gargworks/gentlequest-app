"""Artery 6: Session start shows past session summaries + today's brief rec.

Verifies _load_session_arc returns last 3 session engrams, excludes
deleted ones, and picks up today's brief recommendation.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server_nucleus.runtime.session_ops import _load_session_arc


@pytest.fixture
def session_brain(tmp_path):
    """Brain with engrams directory for session arc loading."""
    brain = tmp_path / ".brain"
    (brain / "engrams").mkdir(parents=True)
    (brain / "ledger").mkdir(parents=True)
    return brain


class TestArterySessionArc:
    """Verify session start displays session arc."""

    def test_returns_last_3_sessions(self, session_brain):
        """Should show last 3 session summaries, most recent first."""
        with open(session_brain / "engrams" / "ledger.jsonl", "w") as f:
            for i in range(5):
                ts = (datetime.now() - timedelta(days=5 - i)).isoformat()
                f.write(json.dumps({
                    "key": f"session_{1000 + i}",
                    "value": f"Session {i}: worked on feature {i}",
                    "context": "Strategy",
                    "intensity": 5,
                    "timestamp": ts,
                }) + "\n")

        arc = _load_session_arc(session_brain)
        assert len(arc["recent_sessions"]) == 3
        assert "feature 4" in arc["recent_sessions"][0]["value"]

    def test_includes_brief_recommendation(self, session_brain):
        """Should show today's brief recommendation."""
        today_key = f"brief_rec_{datetime.now().strftime('%Y%m%d')}"
        (session_brain / "engrams" / "ledger.jsonl").write_text(
            json.dumps({
                "key": today_key,
                "value": "[CONTINUE] Deploy auth fix",
                "context": "Strategy",
                "intensity": 7,
                "timestamp": datetime.now().isoformat(),
            }) + "\n"
        )

        arc = _load_session_arc(session_brain)
        assert arc["todays_focus"] == "[CONTINUE] Deploy auth fix"

    def test_graceful_when_empty(self, session_brain):
        """Should return empty data when no sessions or brief exist."""
        (session_brain / "engrams" / "ledger.jsonl").touch()

        arc = _load_session_arc(session_brain)
        assert arc["recent_sessions"] == []
        assert arc["todays_focus"] is None
        assert arc["arc_summary"] == ""

    def test_graceful_when_missing_ledger(self, session_brain):
        """Should return empty data when ledger.jsonl doesn't exist."""
        arc = _load_session_arc(session_brain)
        assert arc["recent_sessions"] == []
        assert arc["todays_focus"] is None

    def test_deleted_sessions_excluded(self, session_brain):
        """Soft-deleted session engrams should not appear in arc."""
        with open(session_brain / "engrams" / "ledger.jsonl", "w") as f:
            f.write(json.dumps({
                "key": "session_100",
                "value": "Active session",
                "context": "Strategy",
                "intensity": 5,
                "timestamp": datetime.now().isoformat(),
            }) + "\n")
            f.write(json.dumps({
                "key": "session_101",
                "value": "Deleted session",
                "context": "Strategy",
                "intensity": 5,
                "timestamp": datetime.now().isoformat(),
                "deleted": True,
            }) + "\n")

        arc = _load_session_arc(session_brain)
        assert len(arc["recent_sessions"]) == 1
        assert "Active" in arc["recent_sessions"][0]["value"]

    def test_non_session_engrams_excluded(self, session_brain):
        """Only session_* keys should appear in recent_sessions."""
        with open(session_brain / "engrams" / "ledger.jsonl", "w") as f:
            f.write(json.dumps({
                "key": "session_200",
                "value": "Real session work",
                "context": "Strategy",
                "intensity": 5,
                "timestamp": datetime.now().isoformat(),
            }) + "\n")
            f.write(json.dumps({
                "key": "architecture_note",
                "value": "Not a session",
                "context": "Architecture",
                "intensity": 8,
                "timestamp": datetime.now().isoformat(),
            }) + "\n")

        arc = _load_session_arc(session_brain)
        assert len(arc["recent_sessions"]) == 1

    def test_arc_summary_is_chronological(self, session_brain):
        """arc_summary should be oldest→newest."""
        with open(session_brain / "engrams" / "ledger.jsonl", "w") as f:
            for i in range(3):
                ts = (datetime.now() - timedelta(days=3 - i)).isoformat()
                f.write(json.dumps({
                    "key": f"session_{i}",
                    "value": f"Day{i}",
                    "context": "Strategy",
                    "intensity": 5,
                    "timestamp": ts,
                }) + "\n")

        arc = _load_session_arc(session_brain)
        assert "Day0" in arc["arc_summary"]
        # Chronological: Day0 appears before Day2
        pos0 = arc["arc_summary"].index("Day0")
        pos2 = arc["arc_summary"].index("Day2")
        assert pos0 < pos2

    def test_corrupt_lines_skipped(self, session_brain):
        """Corrupt engram lines should be skipped without error."""
        with open(session_brain / "engrams" / "ledger.jsonl", "w") as f:
            f.write("CORRUPT\n")
            f.write(json.dumps({
                "key": "session_300",
                "value": "Valid session",
                "context": "Strategy",
                "intensity": 5,
                "timestamp": datetime.now().isoformat(),
            }) + "\n")

        arc = _load_session_arc(session_brain)
        assert len(arc["recent_sessions"]) == 1
