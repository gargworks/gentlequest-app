"""
TaskIngestionEngine Tests
Stress test: 1000 sources × 10K tasks with deduplication

Key verifications:
- Multi-source parsing (planning, todos, handoffs, meetings, api)
- Dedup accuracy 99%+
- Provenance tracking
- Rollback support
- Performance benchmarks

Author: NOP V3.1 - January 2026
"""

import pytest
import time
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nop_core.task_ingestion import (
    TaskIngestionEngine,
    PlanningParser,
    TodoParser,
    HandoffParser,
    MeetingParser,
    ApiParser,
    DedupEngine,
    IngestionResult,
    format_ingestion_result,
)


class TestPlanningParser:
    """Unit tests for planning document parser."""

    def test_parse_checkbox_basic(self):
        """Parse basic markdown checkbox."""
        content = "- [ ] Implement feature X"
        result = PlanningParser().parse(content)
        
        assert len(result) == 1
        assert "Implement feature X" in result[0]["description"]
        assert result[0]["ingestion_source"]["type"] == "planning"

    def test_parse_checkbox_with_priority_high(self):
        """Parse checkbox with HIGH priority annotation."""
        content = "- [ ] Deploy to production - HIGH"
        result = PlanningParser().parse(content)
        
        assert result[0]["priority"] == "HIGH"

    def test_parse_checkbox_with_priority_low(self):
        """Parse checkbox with LOW priority annotation."""
        content = "- [ ] Nice to have feature - LOW"
        result = PlanningParser().parse(content)
        
        assert result[0]["priority"] == "LOW"

    def test_parse_checkbox_with_tier(self):
        """Parse checkbox with tier annotation."""
        content = "- [ ] Design API schema - T1_PLANNING"
        result = PlanningParser().parse(content)
        
        assert result[0]["tier"] == "T1_PLANNING"

    def test_parse_nested_checkboxes(self):
        """Parse nested checkboxes."""
        content = """
- [ ] Parent task
  - [ ] Subtask 1
  - [ ] Subtask 2
"""
        result = PlanningParser().parse(content)
        
        assert len(result) == 3

    def test_parse_completed_checkbox_skipped(self):
        """Completed checkboxes should be skipped by default."""
        content = "- [x] Already done task"
        result = PlanningParser().parse(content, skip_completed=True)
        
        assert len(result) == 0

    def test_parse_completed_checkbox_included(self):
        """Completed checkboxes included when skip_completed=False."""
        content = "- [x] Already done task"
        result = PlanningParser().parse(content, skip_completed=False)
        
        assert len(result) == 1
        assert result[0]["status"] == "DONE"

    def test_parse_mixed_content(self):
        """Parse file with checkboxes and other content."""
        content = """
# Sprint 42 Planning

Some descriptive text here.

## Tasks
- [ ] Task 1
- [ ] Task 2

More text at the end.
"""
        result = PlanningParser().parse(content)
        
        assert len(result) == 2

    def test_line_numbers_tracked(self):
        """Verify line numbers are tracked."""
        content = """Line 1
Line 2
- [ ] Task on line 3
Line 4
"""
        result = PlanningParser().parse(content)
        
        assert result[0]["ingestion_source"]["line_number"] == 3


class TestTodoParser:
    """Unit tests for TODO comment parser."""

    def test_parse_python_todo(self):
        """Parse Python TODO comment."""
        content = "# TODO: Fix this bug"
        result = TodoParser().parse(content)
        
        assert len(result) == 1
        assert "Fix this bug" in result[0]["description"]

    def test_parse_python_fixme(self):
        """Parse FIXME with HIGH priority."""
        content = "# FIXME: Memory leak here"
        result = TodoParser().parse(content)
        
        assert len(result) == 1
        assert result[0]["priority"] == "HIGH"

    def test_parse_js_todo(self):
        """Parse JavaScript TODO comment."""
        content = "// TODO: Implement caching"
        result = TodoParser().parse(content)
        
        assert len(result) == 1

    def test_parse_c_style_hack(self):
        """Parse C-style HACK comment."""
        content = "/* HACK: Temporary workaround */"
        result = TodoParser().parse(content)
        
        assert len(result) == 1
        assert "[HACK]" in result[0]["description"]

    def test_parse_multiple_todos(self):
        """Parse multiple TODO comments."""
        content = """
# TODO: First task
# FIXME: Second task
# TODO: Third task
"""
        result = TodoParser().parse(content)
        
        assert len(result) == 3

    def test_line_numbers_tracked(self):
        """Verify line numbers are tracked."""
        content = """Line 1
Line 2
# TODO: Task on line 3
Line 4
"""
        result = TodoParser().parse(content)
        
        assert result[0]["ingestion_source"]["line_number"] == 3


class TestHandoffParser:
    """Unit tests for handoff JSON parser."""

    def test_parse_handoff_basic(self):
        """Parse basic handoff JSON."""
        content = json.dumps({
            "from_session": "ws_001",
            "to_session": "ag_001",
            "tasks": [
                {"description": "Continue task X"}
            ]
        })
        result = HandoffParser().parse(content)
        
        assert len(result) == 1
        assert result[0]["ingestion_source"]["type"] == "handoffs"

    def test_parse_handoff_with_context(self):
        """Parse handoff with context preserved."""
        content = json.dumps({
            "from_session": "ws_001",
            "to_session": "ag_001",
            "context": "Completed 50%, need to finish phase 2",
            "tasks": [
                {"description": "Complete phase 2"}
            ]
        })
        result = HandoffParser().parse(content)
        
        assert result[0]["context_summary"] is not None
        assert "Completed 50%" in result[0]["context_summary"]["summary"]

    def test_parse_handoff_multiple_tasks(self):
        """Parse handoff with multiple tasks."""
        content = json.dumps({
            "from_session": "ws_001",
            "to_session": "ag_001",
            "tasks": [
                {"description": "Task 1"},
                {"description": "Task 2"},
                {"description": "Task 3"},
            ]
        })
        result = HandoffParser().parse(content)
        
        assert len(result) == 3

    def test_parse_handoff_invalid_json(self):
        """Invalid JSON raises error."""
        content = '{"tasks": INVALID'
        
        with pytest.raises(ValueError, match="Invalid handoff JSON"):
            HandoffParser().parse(content)


class TestMeetingParser:
    """Unit tests for meeting notes parser."""

    def test_parse_action_item_basic(self):
        """Parse basic action item with @mention."""
        content = "@lokesh: Complete the implementation"
        result = MeetingParser().parse(content)
        
        assert len(result) == 1
        assert "Complete the implementation" in result[0]["description"]

    def test_parse_action_item_with_checkbox(self):
        """Parse action item with checkbox."""
        content = "- [ ] @alice: Review the PR"
        result = MeetingParser().parse(content)
        
        assert len(result) == 1

    def test_parse_action_keyword(self):
        """Parse ACTION keyword."""
        content = "ACTION: bob: Deploy to staging"
        result = MeetingParser().parse(content)
        
        assert len(result) == 1

    def test_mentioned_assignee_tracked(self):
        """Verify mentioned assignee is tracked in source."""
        content = "@charlie: Fix the bug"
        result = MeetingParser().parse(content)
        
        assert result[0]["ingestion_source"]["mentioned_assignee"] == "charlie"


class TestApiParser:
    """Unit tests for API payload parser."""

    def test_parse_jira_format(self):
        """Parse Jira-style API payload."""
        payload = {
            "issues": [
                {"key": "NOP-123", "summary": "Implement feature", "priority": "High"}
            ]
        }
        result = ApiParser().parse(payload, source_name="jira")
        
        assert len(result) == 1
        assert result[0]["description"] == "Implement feature"
        assert result[0]["priority"] == "HIGH"
        assert result[0]["ingestion_source"]["external_id"] == "NOP-123"

    def test_parse_github_format(self):
        """Parse GitHub-style API payload."""
        payload = {
            "issues": [
                {"number": 42, "title": "Bug in parser", "priority": "critical"}
            ]
        }
        result = ApiParser().parse(payload, source_name="github")
        
        assert len(result) == 1
        assert result[0]["description"] == "Bug in parser"
        assert result[0]["priority"] == "HIGH"

    def test_parse_priority_normalization(self):
        """Test priority normalization from various formats."""
        parser = ApiParser()
        
        assert parser._normalize_priority("Highest") == "HIGH"
        assert parser._normalize_priority("critical") == "HIGH"
        assert parser._normalize_priority("blocker") == "HIGH"
        assert parser._normalize_priority("Medium") == "MEDIUM"
        assert parser._normalize_priority("lowest") == "LOW"
        assert parser._normalize_priority("trivial") == "LOW"


class TestDedupEngine:
    """Unit tests for deduplication engine."""

    def test_exact_hash_match(self):
        """Test exact hash deduplication."""
        engine = DedupEngine()
        
        existing = [
            {"id": "task_001", "ingestion_source": {
                "dedup_key": DedupEngine.compute_dedup_key("Implement feature X")
            }}
        ]
        
        result = engine.check_duplicate("Implement feature X", existing)
        
        assert result.is_duplicate is True
        assert result.matching_task_id == "task_001"
        assert result.match_type == "exact"

    def test_no_match(self):
        """Test non-duplicate detection."""
        engine = DedupEngine()
        
        existing = [
            {"id": "task_001", "ingestion_source": {
                "dedup_key": DedupEngine.compute_dedup_key("Implement feature X")
            }}
        ]
        
        result = engine.check_duplicate("Completely different task", existing)
        
        assert result.is_duplicate is False

    def test_normalize_handles_case(self):
        """Normalization is case-insensitive."""
        key1 = DedupEngine.compute_dedup_key("Implement Feature X")
        key2 = DedupEngine.compute_dedup_key("implement feature x")
        
        assert key1 == key2

    def test_normalize_handles_whitespace(self):
        """Normalization handles extra whitespace."""
        key1 = DedupEngine.compute_dedup_key("Implement   feature   X")
        key2 = DedupEngine.compute_dedup_key("Implement feature X")
        
        assert key1 == key2

    def test_cache_warmup(self):
        """Test cache warmup."""
        engine = DedupEngine(cache_size=100)
        
        tasks = [
            {"id": f"task_{i}", "ingestion_source": {"dedup_key": f"key_{i}"}}
            for i in range(50)
        ]
        
        engine.warm_up(tasks)
        
        assert len(engine.hash_cache) == 50

    def test_cache_lru_eviction(self):
        """Test LRU cache eviction."""
        engine = DedupEngine(cache_size=5)
        
        for i in range(10):
            engine._cache_put(f"key_{i}", f"task_{i}")
        
        # Only last 5 should remain
        assert len(engine.hash_cache) == 5
        assert "key_0" not in engine.hash_cache
        assert "key_9" in engine.hash_cache


class TestTaskIngestionEngine:
    """Integration tests for TaskIngestionEngine."""

    @pytest.fixture
    def engine(self):
        """Create ingestion engine."""
        return TaskIngestionEngine()

    def test_ingest_batch_basic(self, engine):
        """Test basic batch ingestion."""
        tasks = [
            {"description": "Task A"},
            {"description": "Task B"},
            {"description": "Task C"},
        ]
        
        result = engine.ingest_batch(tasks)
        
        assert result.success is True
        assert result.tasks_created == 3
        assert len(result.created_task_ids) == 3

    def test_ingest_batch_with_dedup(self, engine):
        """Test batch ingestion with deduplication."""
        tasks = [
            {"description": "Task A"},
            {"description": "Task B"},
            {"description": "Task A"},  # Duplicate
            {"description": "Task C"},
            {"description": "Task B"},  # Duplicate
        ]
        
        result = engine.ingest_batch(tasks)
        
        assert result.tasks_created == 3
        assert result.tasks_skipped == 2

    def test_ingest_batch_skip_dedup(self, engine):
        """Test batch ingestion with dedup disabled."""
        tasks = [
            {"description": "Task A"},
            {"description": "Task A"},  # Would be duplicate
        ]
        
        result = engine.ingest_batch(tasks, skip_dedup=True)
        
        assert result.tasks_created == 2
        assert result.tasks_skipped == 0

    def test_ingest_batch_dry_run(self, engine):
        """Test dry run mode."""
        tasks = [{"description": f"Task {i}"} for i in range(10)]
        
        result = engine.ingest_batch(tasks, dry_run=True)
        
        assert result.tasks_created == 10
        assert len(result.created_task_ids) == 0  # Nothing actually created

    def test_ingest_from_text_planning(self, engine):
        """Test ingestion from planning text."""
        content = """
# Sprint Planning
- [ ] Task 1 - HIGH
- [ ] Task 2
- [ ] Task 3 - T3_REVIEW
"""
        result = engine.ingest_from_text(content, source_type="planning")
        
        assert result.success is True
        assert result.tasks_created == 3

    def test_rollback(self, engine):
        """Test rollback functionality."""
        tasks = [{"description": f"Task {i}"} for i in range(5)]
        
        result = engine.ingest_batch(tasks)
        batch_id = result.batch_id
        
        assert result.tasks_created == 5
        
        rollback_result = engine.rollback(batch_id)
        
        assert rollback_result["success"] is True
        assert rollback_result["tasks_removed"] == 5

    def test_rollback_already_rolled_back(self, engine):
        """Test double rollback fails."""
        tasks = [{"description": "Task A"}]
        
        result = engine.ingest_batch(tasks)
        batch_id = result.batch_id
        
        engine.rollback(batch_id)
        second_rollback = engine.rollback(batch_id)
        
        assert second_rollback["success"] is False
        assert "already" in second_rollback["error"].lower()

    def test_get_ingestion_stats(self, engine):
        """Test stats retrieval."""
        engine.ingest_batch([
            {"description": "Task 1"},
            {"description": "Task 2"},
        ])
        engine.ingest_batch([
            {"description": "Task 3"},
            {"description": "Task 1"},  # Duplicate
        ])
        
        stats = engine.get_ingestion_stats()
        
        assert stats["total_ingested"] == 3
        assert stats["total_skipped"] == 1

    def test_list_batches(self, engine):
        """Test batch listing."""
        engine.ingest_batch([{"description": "Batch 1 Task"}])
        engine.ingest_batch([{"description": "Batch 2 Task"}])
        engine.ingest_batch([{"description": "Batch 3 Task"}])
        
        batches = engine.list_batches(limit=2)
        
        assert len(batches) == 2

    def test_check_duplicate(self, engine):
        """Test duplicate check without ingesting."""
        engine.ingest_batch([{"description": "Existing task"}])
        
        result = engine.check_duplicate("Existing task")
        
        assert result.is_duplicate is True

    def test_provenance_tracked(self, engine):
        """Test provenance tracking."""
        result = engine.ingest_batch(
            [{"description": "Test task"}],
            source_type="manual",
            session_id="test_session"
        )
        
        batch = engine.batches[result.batch_id]
        
        assert batch.session_id == "test_session"
        assert batch.source_type == "manual"


class TestIngestionFromFile:
    """Tests for file-based ingestion."""

    def test_ingest_markdown_file(self, tmp_path):
        """Test ingestion from markdown file."""
        engine = TaskIngestionEngine()
        
        md_file = tmp_path / "sprint.md"
        md_file.write_text("""
# Sprint 42
- [ ] Task A
- [ ] Task B
- [ ] Task C
""")
        
        result = engine.ingest_from_file(str(md_file), source_type="planning")
        
        assert result.success is True
        assert result.tasks_created == 3

    def test_ingest_python_file_todos(self, tmp_path):
        """Test ingestion of TODOs from Python file."""
        engine = TaskIngestionEngine()
        
        py_file = tmp_path / "main.py"
        py_file.write_text("""
def main():
    # TODO: Implement feature
    pass

def other():
    # FIXME: Fix bug
    pass
""")
        
        result = engine.ingest_from_file(str(py_file), source_type="todos")
        
        assert result.success is True
        assert result.tasks_created == 2

    def test_ingest_nonexistent_file(self):
        """Test error handling for missing file."""
        engine = TaskIngestionEngine()
        
        result = engine.ingest_from_file("/nonexistent/file.md")
        
        assert result.success is False
        assert "not found" in result.errors[0].lower()

    def test_auto_detect_source_type(self, tmp_path):
        """Test automatic source type detection."""
        engine = TaskIngestionEngine()
        
        # Markdown with checkboxes -> planning
        md_file = tmp_path / "plan.md"
        md_file.write_text("- [ ] Task")
        
        result = engine.ingest_from_file(str(md_file), source_type="auto")
        
        assert result.success is True


class TestIngestionScale:
    """Scale and performance tests."""

    def test_1000_tasks_ingestion(self):
        """Test ingesting 1000 tasks."""
        engine = TaskIngestionEngine()
        
        tasks = [{"description": f"Task {i}"} for i in range(1000)]
        
        start = time.time()
        result = engine.ingest_batch(tasks)
        elapsed = time.time() - start
        
        assert result.tasks_created == 1000
        assert elapsed < 5.0  # Should complete in <5 seconds
        print(f"\n1000 tasks ingested in {elapsed*1000:.2f}ms")

    def test_dedup_with_50_percent_duplicates(self):
        """Test dedup with 50% duplicates."""
        engine = TaskIngestionEngine()
        
        # Create 500 unique + 500 duplicates
        unique_tasks = [{"description": f"Unique task {i}"} for i in range(500)]
        duplicate_tasks = [{"description": f"Unique task {i}"} for i in range(500)]
        
        all_tasks = unique_tasks + duplicate_tasks
        
        result = engine.ingest_batch(all_tasks)
        
        assert result.tasks_created == 500
        assert result.tasks_skipped == 500

    def test_concurrent_ingestion(self):
        """Test thread-safe concurrent ingestion."""
        engine = TaskIngestionEngine()
        
        results = []
        errors = []
        
        def ingest_batch(batch_idx):
            try:
                tasks = [{"description": f"Batch{batch_idx}_Task{i}"} for i in range(100)]
                result = engine.ingest_batch(tasks)
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(ingest_batch, i) for i in range(5)]
            for f in as_completed(futures):
                f.result()
        
        assert len(errors) == 0
        total_created = sum(r.tasks_created for r in results)
        assert total_created == 500
        print(f"\nConcurrent: 500 tasks created across 5 threads")


class TestStressTest:
    """
    Main stress test: 10K tasks with deduplication
    """

    def test_10k_tasks_with_2k_duplicates(self):
        """
        STRESS TEST: 10K tasks with 2K duplicates
        
        Verifies:
        - 8K unique tasks created
        - 2K duplicates skipped
        - Ingestion time <10s
        - 99%+ dedup accuracy
        """
        engine = TaskIngestionEngine()
        
        print("\n" + "="*60)
        print("STRESS TEST: 10K tasks with 2K duplicates")
        print("="*60)
        
        # Create 8K unique + 2K duplicates
        unique_tasks = [{"description": f"Unique task number {i}"} for i in range(8000)]
        duplicate_tasks = [{"description": f"Unique task number {i}"} for i in range(2000)]
        all_tasks = unique_tasks + duplicate_tasks
        
        start = time.time()
        result = engine.ingest_batch(all_tasks)
        elapsed = time.time() - start
        
        print(f"\n📊 Results:")
        print(f"   Tasks created: {result.tasks_created}")
        print(f"   Tasks skipped: {result.tasks_skipped}")
        print(f"   Tasks failed: {result.tasks_failed}")
        print(f"   Time: {elapsed:.2f}s")
        
        # Assertions
        assert result.tasks_created == 8000, f"Expected 8000, got {result.tasks_created}"
        assert result.tasks_skipped == 2000, f"Expected 2000 skipped, got {result.tasks_skipped}"
        assert result.tasks_failed == 0, f"Expected 0 failed, got {result.tasks_failed}"
        assert elapsed < 10.0, f"Expected <10s, took {elapsed:.2f}s"
        
        # Dedup accuracy
        dedup_accuracy = result.tasks_skipped / 2000
        print(f"   Dedup accuracy: {dedup_accuracy*100:.1f}%")
        assert dedup_accuracy >= 0.99, f"Dedup accuracy {dedup_accuracy} < 99%"
        
        # Stats
        stats = engine.get_ingestion_stats()
        print(f"\n📊 Stats:")
        print(f"   Total ingested: {stats['total_ingested']}")
        print(f"   Cache size: {stats['dedup_cache_size']}")
        
        print("\n" + "="*60)
        print("✅ STRESS TEST PASSED")
        print("="*60)


class TestFormatOutput:
    """Test output formatting."""

    def test_format_success(self):
        """Test successful result formatting."""
        result = IngestionResult(
            success=True,
            batch_id="batch_123",
            tasks_created=10,
            tasks_skipped=2,
        )
        
        output = format_ingestion_result(result)
        
        assert "✅" in output
        assert "batch_123" in output
        assert "Created: 10" in output
        assert "Skipped: 2" in output

    def test_format_with_errors(self):
        """Test result formatting with errors."""
        result = IngestionResult(
            success=False,
            batch_id="batch_456",
            tasks_created=5,
            tasks_failed=2,
            errors=["Error 1", "Error 2"],
        )
        
        output = format_ingestion_result(result)
        
        assert "⚠️" in output
        assert "Failed: 2" in output
        assert "Error 1" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
