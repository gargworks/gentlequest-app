"""Tests for Outbound I/O Subsystem (outbound_ops.py).

Test coverage:
  - Hash computation (deterministic, body-sensitive, channel-sensitive)
  - Outbound check (ready, skip, retry, cross-channel, different-content)
  - Outbound record (writes engram, marks task, emits event, returns key)
  - Outbound fail (writes failed engram, emits event)
  - Outbound status (groups by channel, filters, empty state)
  - Outbound plan (shows ready, excludes done)
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone

from mcp_server_nucleus.runtime.outbound_ops import (
    _compute_outbound_hash,
    _normalize_channel,
    _make_engram_key,
    outbound_check,
    outbound_record,
    outbound_fail,
    outbound_status,
    outbound_plan,
)


# ═══════════════════════════════════════════════════════════════
# TEST HASH COMPUTATION
# ═══════════════════════════════════════════════════════════════

class TestHashComputation:
    """Test hash computation for idempotency."""

    def test_hash_deterministic(self):
        """Same inputs produce same hash."""
        h1 = _compute_outbound_hash("reddit", "r/programming", "Check out Nucleus!")
        h2 = _compute_outbound_hash("reddit", "r/programming", "Check out Nucleus!")
        assert h1 == h2
        assert len(h1) == 12  # 48-bit hash

    def test_hash_body_sensitive(self):
        """Different body produces different hash."""
        h1 = _compute_outbound_hash("reddit", "r/programming", "Check out Nucleus!")
        h2 = _compute_outbound_hash("reddit", "r/programming", "Different content")
        assert h1 != h2

    def test_hash_channel_sensitive(self):
        """Different channel produces different hash."""
        h1 = _compute_outbound_hash("reddit", "r/programming", "Check out Nucleus!")
        h2 = _compute_outbound_hash("hackernews", "r/programming", "Check out Nucleus!")
        assert h1 != h2

    def test_hash_case_insensitive(self):
        """Hash is case-insensitive (normalized)."""
        h1 = _compute_outbound_hash("Reddit", "R/Programming", "Check Out Nucleus!")
        h2 = _compute_outbound_hash("reddit", "r/programming", "check out nucleus!")
        assert h1 == h2

    def test_normalize_channel(self):
        """Channel normalization works correctly."""
        assert _normalize_channel("Reddit") == "reddit"
        assert _normalize_channel("Hacker News") == "hacker_news"
        assert _normalize_channel("Dev.to") == "dev.to"
        assert _normalize_channel("X/Twitter") == "x_twitter"

    def test_make_engram_key(self):
        """Engram key format is correct."""
        key = _make_engram_key("reddit", "abc123def456")
        assert key == "outbound_reddit_abc123def456"
        assert key.startswith("outbound_")


# ═══════════════════════════════════════════════════════════════
# TEST OUTBOUND CHECK
# ═══════════════════════════════════════════════════════════════

class TestOutboundCheck:
    """Test outbound_check idempotency gate."""

    def test_check_ready_no_existing_record(self, tmp_brain):
        """Returns READY when no existing record."""
        result = outbound_check("reddit", "r/programming", "Test post")
        assert result["status"] == "READY"
        assert result["channel"] == "reddit"
        assert result["identifier"] == "r/programming"
        assert "hash" in result
        assert "engram_key" in result

    def test_check_skip_already_posted(self, tmp_brain):
        """Returns SKIP when already posted."""
        # First post
        outbound_record("reddit", "r/programming", "Test post", "https://reddit.com/123", "test_workhorse")
        
        # Check again
        result = outbound_check("reddit", "r/programming", "Test post")
        assert result["status"] == "SKIP"
        assert result["reason"] == "already posted"
        assert "existing_record" in result

    def test_check_retry_previously_failed(self, tmp_brain):
        """Returns RETRY when previously failed."""
        # Record failure
        outbound_fail("reddit", "r/programming", "Test post", "Rate limit", "test_workhorse")
        
        # Check again
        result = outbound_check("reddit", "r/programming", "Test post")
        assert result["status"] == "RETRY"
        assert "previously failed" in result["reason"]

    def test_check_override_on_failed(self, tmp_brain):
        """Returns READY when override=True on failed record."""
        # Record failure
        outbound_fail("reddit", "r/programming", "Test post", "Rate limit", "test_workhorse")
        
        # Check with override
        result = outbound_check("reddit", "r/programming", "Test post", override=True)
        assert result["status"] == "READY"
        assert result["reason"] == "override on failed record"

    def test_check_cross_channel_independence(self, tmp_brain):
        """Same content on different channels is independent."""
        # Post to reddit
        outbound_record("reddit", "r/programming", "Test post", "https://reddit.com/123", "test_workhorse")
        
        # Check on hackernews (should be READY)
        result = outbound_check("hackernews", "show hn", "Test post")
        assert result["status"] == "READY"

    def test_check_different_content_same_channel(self, tmp_brain):
        """Different content on same channel is independent."""
        # Post first content
        outbound_record("reddit", "r/programming", "First post", "https://reddit.com/123", "test_workhorse")
        
        # Check different content (should be READY)
        result = outbound_check("reddit", "r/programming", "Second post")
        assert result["status"] == "READY"


# ═══════════════════════════════════════════════════════════════
# TEST OUTBOUND RECORD
# ═══════════════════════════════════════════════════════════════

class TestOutboundRecord:
    """Test outbound_record success recording."""

    def test_record_writes_engram(self, tmp_brain):
        """Records write to engram ledger."""
        result = outbound_record(
            "reddit",
            "r/programming",
            "Test post",
            "https://reddit.com/123",
            "test_workhorse",
            title="My Test Post"
        )
        
        assert result["status"] == "recorded"
        assert result["channel"] == "reddit"
        assert "engram_key" in result
        assert "hash" in result
        
        # Verify engram exists
        engram_path = tmp_brain / "engrams" / "ledger.jsonl"
        assert engram_path.exists()
        
        # Find the engram
        found = False
        with open(engram_path, "r") as f:
            for line in f:
                engram = json.loads(line)
                if engram["key"] == result["engram_key"]:
                    found = True
                    record = json.loads(engram["value"])
                    assert record["status"] == "posted"
                    assert record["channel"] == "reddit"
                    assert record["permalink"] == "https://reddit.com/123"
                    assert record["workhorse"] == "test_workhorse"
                    assert record["title"] == "My Test Post"
                    break
        assert found, "Engram not found in ledger"

    def test_record_marks_task_done(self, tmp_brain):
        """Records mark associated task as DONE."""
        # Create a task first
        from mcp_server_nucleus.runtime.task_ops import _add_task
        task_result = _add_task("Post to Reddit", priority=2)
        task_id = task_result["id"]
        
        # Record outbound with task_id
        result = outbound_record(
            "reddit",
            "r/programming",
            "Test post",
            "https://reddit.com/123",
            "test_workhorse",
            task_id=task_id
        )
        
        assert result["task_updated"] is True
        
        # Verify task is DONE
        from mcp_server_nucleus.runtime.task_ops import _list_tasks
        tasks = _list_tasks()
        task = next((t for t in tasks if t["id"] == task_id), None)
        assert task is not None
        assert task["status"] == "DONE"

    def test_record_emits_event(self, tmp_brain):
        """Records emit outbound_posted event."""
        result = outbound_record(
            "reddit",
            "r/programming",
            "Test post",
            "https://reddit.com/123",
            "test_workhorse"
        )
        
        # Verify event exists
        events_path = tmp_brain / "ledger" / "events.jsonl"
        assert events_path.exists()
        
        # Find the event
        found = False
        with open(events_path, "r") as f:
            for line in f:
                event = json.loads(line)
                if event.get("event_type") == "outbound_posted":
                    found = True
                    assert event["data"]["channel"] == "reddit"
                    assert event["data"]["permalink"] == "https://reddit.com/123"
                    break
        assert found, "outbound_posted event not found"

    def test_record_returns_key(self, tmp_brain):
        """Records return engram key for reference."""
        result = outbound_record(
            "reddit",
            "r/programming",
            "Test post",
            "https://reddit.com/123",
            "test_workhorse"
        )
        
        assert "engram_key" in result
        assert result["engram_key"].startswith("outbound_reddit_")


# ═══════════════════════════════════════════════════════════════
# TEST OUTBOUND FAIL
# ═══════════════════════════════════════════════════════════════

class TestOutboundFail:
    """Test outbound_fail failure recording."""

    def test_fail_writes_failed_engram(self, tmp_brain):
        """Failures write to engram ledger with status=failed."""
        result = outbound_fail(
            "reddit",
            "r/programming",
            "Test post",
            "Rate limit exceeded",
            "test_workhorse"
        )
        
        assert result["status"] == "failed_recorded"
        assert result["channel"] == "reddit"
        
        # Verify engram exists
        engram_path = tmp_brain / "engrams" / "ledger.jsonl"
        assert engram_path.exists()
        
        # Find the engram
        found = False
        with open(engram_path, "r") as f:
            for line in f:
                engram = json.loads(line)
                if engram["key"] == result["engram_key"]:
                    found = True
                    record = json.loads(engram["value"])
                    assert record["status"] == "failed"
                    assert record["error"] == "Rate limit exceeded"
                    assert record["workhorse"] == "test_workhorse"
                    break
        assert found, "Failed engram not found in ledger"

    def test_fail_emits_event(self, tmp_brain):
        """Failures emit outbound_failed event."""
        result = outbound_fail(
            "reddit",
            "r/programming",
            "Test post",
            "Rate limit exceeded",
            "test_workhorse"
        )
        
        # Verify event exists
        events_path = tmp_brain / "ledger" / "events.jsonl"
        assert events_path.exists()
        
        # Find the event
        found = False
        with open(events_path, "r") as f:
            for line in f:
                event = json.loads(line)
                if event.get("event_type") == "outbound_failed":
                    found = True
                    assert event["data"]["channel"] == "reddit"
                    assert "Rate limit" in event["data"]["error"]
                    break
        assert found, "outbound_failed event not found"


# ═══════════════════════════════════════════════════════════════
# TEST OUTBOUND STATUS
# ═══════════════════════════════════════════════════════════════

class TestOutboundStatus:
    """Test outbound_status reporting."""

    def test_status_groups_by_channel(self, tmp_brain):
        """Status groups records by channel."""
        # Post to multiple channels
        outbound_record("reddit", "r/programming", "Post 1", "https://reddit.com/1", "test")
        outbound_record("reddit", "r/python", "Post 2", "https://reddit.com/2", "test")
        outbound_record("hackernews", "show hn", "Post 3", "https://news.ycombinator.com/1", "test")
        outbound_fail("reddit", "r/golang", "Post 4", "Error", "test")
        
        result = outbound_status()
        
        assert "channels" in result
        assert "reddit" in result["channels"]
        assert "hackernews" in result["channels"]
        
        assert result["channels"]["reddit"]["posted"] == 2
        assert result["channels"]["reddit"]["failed"] == 1
        assert result["channels"]["reddit"]["total"] == 3
        
        assert result["channels"]["hackernews"]["posted"] == 1
        assert result["channels"]["hackernews"]["failed"] == 0
        
        assert result["total_posted"] == 3
        assert result["total_failed"] == 1

    def test_status_filters_by_channel(self, tmp_brain):
        """Status can filter by specific channel."""
        # Post to multiple channels
        outbound_record("reddit", "r/programming", "Post 1", "https://reddit.com/1", "test")
        outbound_record("hackernews", "show hn", "Post 2", "https://news.ycombinator.com/1", "test")
        
        result = outbound_status(channel="reddit")
        
        assert result["filter"] == "reddit"
        assert "reddit" in result["channels"]
        assert "hackernews" not in result["channels"]

    def test_status_empty_state(self, tmp_brain):
        """Status handles empty state gracefully."""
        result = outbound_status()
        
        assert result["channels"] == {}
        assert result["total_posted"] == 0
        assert result["total_failed"] == 0
        assert result["total_records"] == 0


# ═══════════════════════════════════════════════════════════════
# TEST OUTBOUND PLAN
# ═══════════════════════════════════════════════════════════════

class TestOutboundPlan:
    """Test outbound_plan ready/posted/failed reporting."""

    def test_plan_shows_ready_posted_failed(self, tmp_brain):
        """Plan shows ready, posted, and failed lists."""
        # Create some tasks
        from mcp_server_nucleus.runtime.task_ops import _add_task
        _add_task("Post to Reddit about Nucleus", priority=2, source="outbound")
        
        # Post some content
        outbound_record("reddit", "r/programming", "Posted content", "https://reddit.com/1", "test", title="My Post")
        outbound_fail("hackernews", "show hn", "Failed content", "Error", "test")
        
        result = outbound_plan()
        
        assert "ready" in result
        assert "already_posted" in result
        assert "failed" in result
        assert "summary" in result
        
        assert result["summary"]["posted_count"] == 1
        assert result["summary"]["failed_count"] == 1
        assert result["summary"]["ready_count"] >= 1  # At least the task we created

    def test_plan_excludes_done_tasks(self, tmp_brain):
        """Plan excludes tasks that are already DONE."""
        from mcp_server_nucleus.runtime.task_ops import _add_task, _update_task
        
        # Create task and mark it DONE
        task_result = _add_task("Post to Reddit", priority=2, source="outbound")
        _update_task(task_result["id"], {"status": "DONE"})
        
        result = outbound_plan()
        
        # Should not show in ready list
        ready_descriptions = [t["description"] for t in result["ready"]]
        assert "Post to Reddit" not in ready_descriptions


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def tmp_brain(tmp_path, monkeypatch):
    """Create a temporary brain directory for testing."""
    # Use a unique subdirectory for each test
    import uuid
    brain = tmp_path / f".brain_{uuid.uuid4().hex[:8]}"
    brain.mkdir()
    
    # Create required subdirectories
    (brain / "engrams").mkdir()
    (brain / "ledger").mkdir()
    (brain / "memory").mkdir()
    
    # Initialize engram ledger
    (brain / "engrams" / "ledger.jsonl").write_text("")
    
    # Initialize event ledger
    (brain / "ledger" / "events.jsonl").write_text("")
    
    # Initialize tasks
    (brain / "ledger" / "tasks.json").write_text(json.dumps([]))
    
    # Patch get_brain_path to return our temp brain
    from mcp_server_nucleus.runtime import common
    monkeypatch.setattr(common, "get_brain_path", lambda: brain)
    
    # Also patch task_ops and event_ops to use the temp brain
    from mcp_server_nucleus.runtime import task_ops, event_ops, engram_ops
    monkeypatch.setattr(task_ops, "get_brain_path", lambda: brain)
    monkeypatch.setattr(event_ops, "get_brain_path", lambda: brain)
    monkeypatch.setattr(engram_ops, "get_brain_path", lambda: brain)
    
    yield brain
    
    # Cleanup is automatic with tmp_path
