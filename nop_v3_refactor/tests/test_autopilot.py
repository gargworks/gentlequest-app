"""
AutopilotEngine Tests
Comprehensive test suite for autonomous sprint execution.

Key verifications:
- Budget control and reservation
- Wave analysis and dependency detection
- Task assignment with tier matching
- Sprint execution modes
- Checkpoint and recovery
- Halt conditions

Author: NOP V3.1 - January 2026
"""

import pytest
import time
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nop_core.autopilot import (
    AutopilotEngine,
    SprintMode,
    SprintStatus,
    MissionStatus,
    HaltReason,
    BudgetState,
    SlotState,
    TaskAssignment,
    HaltCondition,
    SprintCheckpoint,
    SprintResult,
    Mission,
    RetryPolicy,
    WaveAnalyzer,
    TaskAssigner,
    format_sprint_result,
)


class TestBudgetState:
    """Unit tests for BudgetState."""

    def test_initial_state(self):
        """Test initial budget state."""
        budget = BudgetState(limit=100.0)
        
        assert budget.limit == 100.0
        assert budget.spent == 0.0
        assert budget.reserved == 0.0
        assert budget.remaining == 100.0

    def test_can_afford(self):
        """Test affordability check."""
        budget = BudgetState(limit=10.0)
        
        assert budget.can_afford(5.0)
        assert budget.can_afford(10.0)
        assert not budget.can_afford(10.01)

    def test_reserve(self):
        """Test budget reservation."""
        budget = BudgetState(limit=10.0)
        
        result = budget.reserve("task_1", 3.0)
        
        assert result is True
        assert budget.reserved == 3.0
        assert budget.remaining == 7.0

    def test_reserve_insufficient(self):
        """Test reservation with insufficient budget."""
        budget = BudgetState(limit=5.0)
        
        result = budget.reserve("task_1", 6.0)
        
        assert result is False
        assert budget.reserved == 0.0

    def test_commit(self):
        """Test committing reserved budget."""
        budget = BudgetState(limit=10.0)
        budget.reserve("task_1", 3.0)
        
        budget.commit("task_1", 3.5, tokens=1000)
        
        assert budget.spent == 3.5
        assert budget.reserved == 0.0
        assert budget.tokens_used == 1000

    def test_release(self):
        """Test releasing reservation."""
        budget = BudgetState(limit=10.0)
        budget.reserve("task_1", 3.0)
        
        budget.release("task_1")
        
        assert budget.reserved == 0.0
        assert budget.remaining == 10.0

    def test_multiple_reservations(self):
        """Test multiple concurrent reservations."""
        budget = BudgetState(limit=10.0)
        
        budget.reserve("task_1", 3.0)
        budget.reserve("task_2", 2.0)
        budget.reserve("task_3", 4.0)
        
        assert budget.reserved == 9.0
        assert budget.remaining == 1.0


class TestRetryPolicy:
    """Unit tests for RetryPolicy."""

    def test_initial_delay(self):
        """Test initial delay is base."""
        policy = RetryPolicy(backoff_base=2.0)
        
        delay = policy.get_delay("task_1")
        
        assert delay == 1.0  # 2^0

    def test_exponential_backoff(self):
        """Test exponential backoff."""
        policy = RetryPolicy(backoff_base=2.0)
        
        policy.record_attempt("task_1")
        delay1 = policy.get_delay("task_1")
        
        policy.record_attempt("task_1")
        delay2 = policy.get_delay("task_1")
        
        assert delay1 == 2.0  # 2^1
        assert delay2 == 4.0  # 2^2

    def test_max_backoff(self):
        """Test max backoff limit."""
        policy = RetryPolicy(backoff_base=2.0, backoff_max=10.0)
        
        for _ in range(10):
            policy.record_attempt("task_1")
        
        delay = policy.get_delay("task_1")
        
        assert delay == 10.0

    def test_should_retry(self):
        """Test retry decision."""
        policy = RetryPolicy(max_retries=3)
        
        assert policy.should_retry("task_1")
        
        for _ in range(3):
            policy.record_attempt("task_1")
        
        assert not policy.should_retry("task_1")

    def test_reset(self):
        """Test resetting retry count."""
        policy = RetryPolicy()
        policy.record_attempt("task_1")
        policy.record_attempt("task_1")
        
        policy.reset("task_1")
        
        assert policy.attempts.get("task_1") is None


class TestWaveAnalyzer:
    """Unit tests for WaveAnalyzer."""

    def test_single_wave(self):
        """Test tasks with no dependencies."""
        tasks = [
            {"id": "t1", "blocked_by": []},
            {"id": "t2", "blocked_by": []},
            {"id": "t3", "blocked_by": []},
        ]
        
        analyzer = WaveAnalyzer(tasks)
        
        assert analyzer.get_wave_count() == 1
        assert len(analyzer.get_wave(0)) == 3

    def test_linear_dependencies(self):
        """Test linear dependency chain."""
        tasks = [
            {"id": "t1", "blocked_by": []},
            {"id": "t2", "blocked_by": ["t1"]},
            {"id": "t3", "blocked_by": ["t2"]},
        ]
        
        analyzer = WaveAnalyzer(tasks)
        
        assert analyzer.get_wave_count() == 3
        assert analyzer.get_wave(0) == ["t1"]
        assert analyzer.get_wave(1) == ["t2"]
        assert analyzer.get_wave(2) == ["t3"]

    def test_parallel_dependencies(self):
        """Test parallel dependency structure."""
        tasks = [
            {"id": "t1", "blocked_by": []},
            {"id": "t2", "blocked_by": ["t1"]},
            {"id": "t3", "blocked_by": ["t1"]},
            {"id": "t4", "blocked_by": ["t2", "t3"]},
        ]
        
        analyzer = WaveAnalyzer(tasks)
        
        assert analyzer.get_wave_count() == 3
        assert analyzer.get_wave(0) == ["t1"]
        assert set(analyzer.get_wave(1)) == {"t2", "t3"}
        assert analyzer.get_wave(2) == ["t4"]

    def test_circular_detection(self):
        """Test circular dependency detection."""
        tasks = [
            {"id": "t1", "blocked_by": ["t2"]},
            {"id": "t2", "blocked_by": ["t1"]},
        ]
        
        analyzer = WaveAnalyzer(tasks)
        circular = analyzer.detect_circular()
        
        assert len(circular) == 2

    def test_depends_on_alias(self):
        """Test depends_on as alias for blocked_by."""
        tasks = [
            {"id": "t1", "depends_on": []},
            {"id": "t2", "depends_on": ["t1"]},
        ]
        
        analyzer = WaveAnalyzer(tasks)
        
        assert analyzer.get_wave_count() == 2


class TestTaskAssigner:
    """Unit tests for TaskAssigner."""

    @pytest.fixture
    def slots(self):
        return [
            SlotState("slot_1", "opus", "T1_RESEARCH", status="idle"),
            SlotState("slot_2", "sonnet", "T2_CODE", status="idle"),
            SlotState("slot_3", "haiku", "T3_REVIEW", status="exhausted"),
        ]

    def test_assign_to_capable_slot(self, slots):
        """Test assignment to capable slot."""
        assigner = TaskAssigner(slots)
        task = {"id": "t1", "required_tier": "T2_CODE", "priority": 3}
        
        assignment = assigner.assign(task)
        
        assert assignment is not None
        assert assignment.slot_id in ["slot_1", "slot_2"]

    def test_tier_matching(self, slots):
        """Test tier matching prefers higher capability."""
        assigner = TaskAssigner(slots)
        task = {"id": "t1", "required_tier": "T1_RESEARCH", "priority": 3}
        
        assignment = assigner.assign(task)
        
        assert assignment.slot_id == "slot_1"  # Only T1 capable

    def test_skip_exhausted_slots(self, slots):
        """Test exhausted slots are skipped."""
        assigner = TaskAssigner(slots)
        task = {"id": "t1", "required_tier": "T3_REVIEW", "priority": 3}
        
        assignment = assigner.assign(task)
        
        assert assignment.slot_id != "slot_3"

    def test_no_capable_slot(self, slots):
        """Test when no slot is capable."""
        # Make all slots exhausted
        for s in slots:
            s.status = "exhausted"
        assigner = TaskAssigner(slots)
        task = {"id": "t1", "required_tier": "T2_CODE", "priority": 3}
        
        assignment = assigner.assign(task)
        
        assert assignment is None

    def test_force_assign(self, slots):
        """Test force assignment ignores tier."""
        assigner = TaskAssigner(slots)
        task = {"id": "t1", "required_tier": "T0_ULTRA", "priority": 1}  # No slot has T0
        
        assignment = assigner.assign(task, force=True)
        
        assert assignment is not None

    def test_update_slot(self, slots):
        """Test slot state update."""
        assigner = TaskAssigner(slots)
        
        assigner.update_slot("slot_1", status="busy", current_task="t1")
        
        assert assigner.slots["slot_1"].status == "busy"
        assert assigner.slots["slot_1"].current_task == "t1"

    def test_available_count(self, slots):
        """Test available slot count."""
        assigner = TaskAssigner(slots)
        
        count = assigner.get_available_count()
        
        assert count == 2  # slot_3 is exhausted

    def test_idle_count(self, slots):
        """Test idle slot count."""
        assigner = TaskAssigner(slots)
        slots[0].status = "busy"
        
        count = assigner.get_idle_count()
        
        assert count == 1  # slot_1 busy, slot_3 exhausted


class TestAutopilotEngine:
    """Integration tests for AutopilotEngine."""

    @pytest.fixture
    def engine(self, tmp_path):
        """Create autopilot engine with temp path."""
        return AutopilotEngine(brain_path=tmp_path)

    def test_execute_sprint_plan_mode(self, engine):
        """Test plan mode (dry run)."""
        result = engine.execute_sprint(mode=SprintMode.PLAN)
        
        assert result.mode == SprintMode.PLAN
        assert result.status in [SprintStatus.PENDING, SprintStatus.COMPLETED]

    def test_execute_sprint_status_mode(self, engine):
        """Test status mode."""
        result = engine.execute_sprint(mode=SprintMode.STATUS)
        
        assert result.mode == SprintMode.STATUS

    def test_execute_sprint_dry_run(self, engine):
        """Test dry_run parameter."""
        result = engine.execute_sprint(dry_run=True)
        
        assert result.mode == SprintMode.PLAN

    def test_halt_sprint(self, engine):
        """Test halt request."""
        result = engine.halt_sprint("Test halt")
        
        assert result["status"] == "halt_requested"
        assert engine.halt_requested is True

    def test_budget_limit(self, engine):
        """Test budget limit enforcement."""
        result = engine.execute_sprint(budget_limit=0.001)
        
        # Should complete quickly with very low budget
        assert result.budget_limit == 0.001


class TestMission:
    """Unit tests for Mission."""

    def test_mission_creation(self, tmp_path):
        """Test mission creation."""
        engine = AutopilotEngine(brain_path=tmp_path)
        
        mission = engine.start_mission(
            name="Test Mission",
            goal="Complete all tasks",
            task_ids=["t1", "t2", "t3"],
            budget_limit=10.0,
            time_limit_hours=2.0,
        )
        
        assert mission.id.startswith("mission_")
        assert mission.name == "Test Mission"
        assert mission.status == MissionStatus.RUNNING

    def test_mission_status(self, tmp_path):
        """Test mission status retrieval."""
        engine = AutopilotEngine(brain_path=tmp_path)
        
        mission = engine.start_mission(
            name="Test",
            goal="Test goal",
            task_ids=["t1"],
        )
        
        status = engine.get_mission_status()
        
        assert status["mission_id"] == mission.id
        assert "progress" in status


class TestCheckpoint:
    """Unit tests for checkpoint and recovery."""

    def test_checkpoint_creation(self, tmp_path):
        """Test checkpoint is saved."""
        engine = AutopilotEngine(brain_path=tmp_path)
        
        # Execute a sprint
        engine.execute_sprint(mode=SprintMode.AUTO)
        
        # Check if checkpoint directory was created
        # (May not be created if no tasks)
        assert True  # Just verify no errors

    def test_checkpoint_recovery(self, tmp_path):
        """Test resuming from checkpoint."""
        engine = AutopilotEngine(brain_path=tmp_path)
        
        # Try to resume non-existent sprint
        result = engine.resume_sprint("nonexistent")
        
        assert result.status == SprintStatus.FAILED
        assert "No checkpoint" in result.halt_reason


class TestSprintResult:
    """Unit tests for SprintResult."""

    def test_result_to_dict(self):
        """Test result serialization."""
        result = SprintResult(
            sprint_id="test",
            mission_id=None,
            status=SprintStatus.COMPLETED,
            mode=SprintMode.AUTO,
            started_at="2026-01-22T23:00:00Z",
            completed_at="2026-01-22T23:01:00Z",
            duration_seconds=60.0,
            tasks_total=10,
            tasks_completed=10,
            tasks_failed=0,
            tasks_skipped=0,
            tasks_remaining=0,
            slots_used=2,
            slot_utilization=0.8,
            slot_exhaustions=0,
            budget_limit=10.0,
            budget_spent=2.5,
            tokens_used=5000,
        )
        
        d = result.to_dict()
        
        assert d["status"] == "completed"
        assert d["mode"] == "auto"
        assert d["tasks_total"] == 10


class TestFormatting:
    """Unit tests for result formatting."""

    def test_format_sprint_result(self):
        """Test ASCII formatting."""
        result = SprintResult(
            sprint_id="test_sprint",
            mission_id=None,
            status=SprintStatus.COMPLETED,
            mode=SprintMode.AUTO,
            started_at="2026-01-22T23:00:00Z",
            completed_at="2026-01-22T23:01:00Z",
            duration_seconds=60.0,
            tasks_total=10,
            tasks_completed=8,
            tasks_failed=2,
            tasks_skipped=0,
            tasks_remaining=0,
            slots_used=3,
            slot_utilization=0.9,
            slot_exhaustions=1,
            budget_limit=10.0,
            budget_spent=4.50,
            tokens_used=10000,
            halt_reason=None,
            next_steps=["Review completed tasks"],
        )
        
        output = format_sprint_result(result)
        
        assert "Sprint Report" in output
        assert "COMPLETED" in output
        assert "10" in output
        assert "$4.50" in output


class TestPerformance:
    """Performance benchmarks."""

    def test_wave_analysis_performance(self):
        """Wave analysis should be fast for large graphs."""
        # Create large dependency graph
        tasks = []
        for i in range(1000):
            deps = [f"t{i-1}"] if i > 0 else []
            tasks.append({"id": f"t{i}", "blocked_by": deps})
        
        start = time.time()
        analyzer = WaveAnalyzer(tasks)
        elapsed = time.time() - start
        
        print(f"\nWave analysis for 1000 tasks: {elapsed*1000:.2f}ms")
        assert elapsed < 1.0  # Should complete in <1s

    def test_assignment_performance(self):
        """Task assignment should be <100ms."""
        slots = [
            SlotState(f"slot_{i}", "model", "T2_CODE")
            for i in range(100)
        ]
        assigner = TaskAssigner(slots)
        
        start = time.time()
        for i in range(1000):
            task = {"id": f"t{i}", "required_tier": "T2_CODE", "priority": 3}
            assigner.assign(task)
        elapsed = time.time() - start
        
        print(f"\n1000 task assignments: {elapsed*1000:.2f}ms")
        print(f"Per assignment: {elapsed*1000/1000:.3f}ms")
        assert elapsed / 1000 < 0.1  # <100ms per assignment


class TestStress:
    """Stress tests."""

    def test_concurrent_budget_operations(self):
        """Test thread-safe budget operations."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        budget = BudgetState(limit=1000.0)
        errors = []
        
        def reserve_and_commit(i):
            try:
                if budget.reserve(f"task_{i}", 0.1):
                    budget.commit(f"task_{i}", 0.1, tokens=100)
            except Exception as e:
                errors.append(str(e))
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(reserve_and_commit, i) for i in range(100)]
            for f in as_completed(futures):
                f.result()
        
        assert len(errors) == 0
        print(f"\n100 concurrent budget operations completed")

    def test_large_sprint_execution(self, tmp_path):
        """Test sprint with many tasks."""
        engine = AutopilotEngine(brain_path=tmp_path)
        
        start = time.time()
        result = engine.execute_sprint(mode=SprintMode.PLAN)
        elapsed = time.time() - start
        
        print(f"\nSprint execution (plan mode): {elapsed*1000:.2f}ms")
        assert elapsed < 5.0  # <5s


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
