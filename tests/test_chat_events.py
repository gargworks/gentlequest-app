"""Chat event publisher tests — Wave 6b.

Contract:
  1. ``publish_event`` writes typed LedgerEvent lines, rejects bad
     outcomes, never raises into the caller.
  2. ``publish_chat_request_received`` and
     ``publish_chat_response_completed`` forward to ``publish_event``
     with the documented event_type + field names.
  3. The ``chat.*`` event pair shares a ``request_id`` so downstream
     joins work.
  4. Importing ``backend.app.events`` does not create a circular import
     back through ``scripts.levers``.

Test organization:
  TestPublishEvent         — unit tests on scripts.levers.run_lever.publish_event
  TestChatEventAdapters    — unit tests on backend.app.events wrappers
  TestImportSafety         — circular-import smoke test
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from scripts.levers.run_lever import publish_event
from scripts.levers.base import LedgerEvent, LedgerSchemaError


class TestPublishEvent:
    """Generic module-event publisher.

    What lands on the ledger must survive ``LedgerEvent.from_jsonl`` —
    otherwise bull_audit flags the line as a schema failure on its next
    run and we've poisoned our own substrate.
    """

    def test_writes_event_with_outcome_and_extra(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        ok = publish_event(
            "chat.request.received",
            outcome="clean",
            request_id="abc123",
            session_id=7,
            ledger_path=ledger,
        )
        assert ok is True
        lines = ledger.read_text().splitlines()
        assert len(lines) == 1
        event = LedgerEvent.from_jsonl(lines[0])
        assert event.type == "chat.request.received"
        assert event.outcome == "clean"
        assert event.extra["request_id"] == "abc123"
        assert event.extra["session_id"] == 7

    def test_writes_without_outcome(self, tmp_path):
        """Outcome is optional — module events without verdicts (e.g.
        ``chat.request.received``) still write."""
        ledger = tmp_path / "events.jsonl"
        ok = publish_event(
            "chat.request.received",
            request_id="def456",
            session_id=1,
            ledger_path=ledger,
        )
        assert ok is True
        event = LedgerEvent.from_jsonl(ledger.read_text().splitlines()[0])
        assert event.outcome is None
        assert event.extra["request_id"] == "def456"

    def test_rejects_bad_outcome_and_logs_violation(self, tmp_path):
        """Bogus outcome must not land on the ledger — bull_audit would
        flag it as a schema_valid failure. We emit a
        ``lever.schema.violation`` marker and return False."""
        ledger = tmp_path / "events.jsonl"
        ok = publish_event(
            "chat.response.completed",
            outcome="success",
            request_id="bad",
            session_id=1,
            ledger_path=ledger,
        )
        assert ok is False
        lines = ledger.read_text().splitlines()
        assert len(lines) == 1
        marker = LedgerEvent.from_jsonl(lines[0])
        assert marker.type == "lever.schema.violation"
        assert marker.detail["source"] == "publish_event"
        assert marker.detail["bad_outcome"] == "success"

    def test_never_raises_on_write_failure(self, tmp_path):
        """Best-effort contract: a read-only ledger path must not
        propagate OSError into the caller."""
        ledger = tmp_path / "nope" / "events.jsonl"
        ledger.parent.mkdir()
        ledger.parent.chmod(0o500)
        try:
            result = publish_event(
                "chat.request.received",
                request_id="x",
                session_id=0,
                ledger_path=ledger,
            )
            assert result is False
        finally:
            ledger.parent.chmod(0o700)

    def test_strips_none_extras(self, tmp_path):
        """``None`` extras are dropped so the ledger line stays clean."""
        ledger = tmp_path / "events.jsonl"
        publish_event(
            "chat.request.received",
            request_id="k",
            session_id=2,
            trace_id=None,
            ledger_path=ledger,
        )
        raw = json.loads(ledger.read_text().splitlines()[0])
        assert "trace_id" not in raw
        assert raw["request_id"] == "k"


class TestChatEventAdapters:
    """Thin wrappers in ``backend/app/events.py``.

    These forward to ``publish_event`` with the contracted event_type.
    We patch at the adapter module's import site to verify the exact
    call shape.
    """

    def test_request_received_calls_publish(self):
        from app import events as app_events
        with patch.object(app_events, "_publish") as mock_pub:
            app_events.publish_chat_request_received(
                request_id="rid1", session_id=42
            )
            mock_pub.assert_called_once()
            args, kwargs = mock_pub.call_args
            assert args[0] == "chat.request.received"
            assert kwargs["request_id"] == "rid1"
            assert kwargs["session_id"] == 42

    def test_response_completed_calls_publish_with_outcome(self):
        from app import events as app_events
        with patch.object(app_events, "_publish") as mock_pub:
            app_events.publish_chat_response_completed(
                request_id="rid2",
                session_id=42,
                outcome="clean",
            )
            mock_pub.assert_called_once()
            _, kwargs = mock_pub.call_args
            assert kwargs["outcome"] == "clean"
            assert kwargs["request_id"] == "rid2"

    def test_response_completed_forwards_error_outcome(self):
        from app import events as app_events
        with patch.object(app_events, "_publish") as mock_pub:
            app_events.publish_chat_response_completed(
                request_id="rid3",
                session_id=42,
                outcome="error",
            )
            _, kwargs = mock_pub.call_args
            assert kwargs["outcome"] == "error"

    def test_request_and_response_share_request_id(self, tmp_path):
        """Correlation contract: downstream joins request_received to
        response_completed on ``request_id``. End-to-end via a real
        ledger so this is a true integration check, not just mock
        inspection."""
        from app import events as app_events
        ledger = tmp_path / "events.jsonl"

        def _go():
            rid = "corr-42"
            with patch("scripts.levers.run_lever.LEDGER_PATH", ledger):
                app_events.publish_chat_request_received(
                    request_id=rid, session_id=9
                )
                app_events.publish_chat_response_completed(
                    request_id=rid, session_id=9, outcome="clean"
                )

        _go()
        events = [
            LedgerEvent.from_jsonl(ln)
            for ln in ledger.read_text().splitlines()
        ]
        assert len(events) == 2
        assert events[0].type == "chat.request.received"
        assert events[1].type == "chat.response.completed"
        assert events[0].extra["request_id"] == events[1].extra["request_id"]

    def test_adapter_swallows_publisher_exception(self):
        """Publication failure must never break a chat request."""
        from app import events as app_events
        with patch.object(app_events, "_publish", side_effect=RuntimeError("nope")):
            app_events.publish_chat_request_received(
                request_id="x", session_id=1
            )
            app_events.publish_chat_response_completed(
                request_id="x", session_id=1, outcome="error"
            )


class TestImportSafety:
    """Circular-import smoke test.

    Flagged as a critical deployment-time failure mode by plan-eng-review:
    if any module under ``backend/app/`` ever imports back into
    ``scripts.levers``, we get a cycle and the backend fails to boot.
    This test boots the adapter import from a cold interpreter path
    and verifies the edge stays unidirectional.
    """

    def test_backend_events_imports_cleanly(self):
        """Fresh import of backend.app.events must succeed and not trigger
        a cycle. If ``scripts.levers.run_lever`` ever imports from
        ``backend.app.*`` this test fails loud."""
        for mod in list(sys.modules):
            if mod.startswith("app.events") or mod == "app.events":
                del sys.modules[mod]
        from app import events as app_events  # noqa: F401
        assert hasattr(app_events, "publish_chat_request_received")
        assert hasattr(app_events, "publish_chat_response_completed")

    def test_run_lever_does_not_import_backend(self):
        """Static check: the substrate module must not reach into the
        app layer. (If it ever does, that's the direction that creates
        a cycle.)"""
        import scripts.levers.run_lever as rl
        source = Path(rl.__file__).read_text()
        assert "from app" not in source
        assert "from backend" not in source
        assert "import app" not in source
        assert "import backend" not in source
