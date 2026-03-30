"""
E2E tests for Third Brother Autonomous Driver v2 (session resume architecture).

Tests cover: task management, crash recovery, auto-commit, trust ladder,
kill switch, RAFT shadow logging, template formatting, and locking.
"""

import json
import os
import sys
import time
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the driver module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp-server-nucleus" / "src"))


@pytest.fixture
def driver_env(tmp_path):
    """Create isolated driver environment with temp directories."""
    brain = tmp_path / ".brain"
    driver = brain / "driver"
    driver.mkdir(parents=True)
    (driver / ".locks").mkdir()

    # Minimal config
    config = {
        "mode": "supervised",
        "idle_check_minutes": 1,
        "session_timeout_minutes": 120,
        "max_retries": 2,
        "claude_max_turns": 30,
        "claude_effort": "max",
        "claude_model": "claude-opus-4-6",
        "cost_cap_tokens": 500000,
        "trust_ladder": {
            "current_phase": 1,
            "thresholds": {
                "phase_1_to_2": {"min_runs": 5, "unedited_ratio": 0.60},
                "phase_2_to_3": {"min_runs": 10, "acceptance_ratio": 0.70},
                "phase_3_to_4": {"min_runs": 5, "zero_critical_consecutive": 5},
                "demotion_consecutive_failures": 3,
            },
        },
    }
    (driver / "config.json").write_text(json.dumps(config, indent=2))

    # Empty task queue
    tasks = {"tasks": [], "schema_version": 1, "updated_at": datetime.now().isoformat()}
    (driver / "tasks.json").write_text(json.dumps(tasks, indent=2))

    # Patch module-level paths
    import scripts.third_brother_driver as drv
    orig_paths = {
        "BRAIN_PATH": drv.BRAIN_PATH,
        "DRIVER_DIR": drv.DRIVER_DIR,
        "CONFIG_PATH": drv.CONFIG_PATH,
        "TASKS_PATH": drv.TASKS_PATH,
        "STATE_PATH": drv.STATE_PATH,
        "STOP_FILE": drv.STOP_FILE,
        "ALERTS_PATH": drv.ALERTS_PATH,
        "RUNS_PATH": drv.RUNS_PATH,
        "SHADOW_LOG_PATH": drv.SHADOW_LOG_PATH,
        "LOCKS_DIR": drv.LOCKS_DIR,
        "PROJECT_ROOT": drv.PROJECT_ROOT,
    }

    drv.BRAIN_PATH = brain
    drv.DRIVER_DIR = driver
    drv.CONFIG_PATH = driver / "config.json"
    drv.TASKS_PATH = driver / "tasks.json"
    drv.STATE_PATH = driver / "state.json"
    drv.STOP_FILE = driver / "stop"
    drv.ALERTS_PATH = driver / "alerts.jsonl"
    drv.RUNS_PATH = driver / "runs.jsonl"
    drv.SHADOW_LOG_PATH = driver / "shadow_log.jsonl"
    drv.LOCKS_DIR = driver / ".locks"

    yield {"drv": drv, "tmp": tmp_path, "brain": brain, "driver": driver}

    # Restore original paths
    for attr, val in orig_paths.items():
        setattr(drv, attr, val)


def _add_task(drv, title="Test task", desc="Do something", scope=None, priority=3):
    """Helper to add a task via the driver module."""
    return drv.add_task(title, desc, scope or ["tests/**"], priority)


# ═══════════════════════════════════════════════════════════════
# TASK MANAGEMENT
# ═══════════════════════════════════════════════════════════════

class TestPickNextTask:
    def test_picks_highest_priority(self, driver_env):
        drv = driver_env["drv"]
        _add_task(drv, "Low priority", priority=5)
        _add_task(drv, "High priority", priority=1)
        _add_task(drv, "Medium priority", priority=3)

        picked = drv.pick_next_task()
        assert picked is not None
        assert picked["title"] == "High priority"
        assert picked["priority"] == 1

    def test_only_picks_committed(self, driver_env):
        drv = driver_env["drv"]
        task = _add_task(drv, "Will be completed")
        drv.update_task_status(task["id"], "completed")
        _add_task(drv, "Still committed")

        picked = drv.pick_next_task()
        assert picked["title"] == "Still committed"

    def test_returns_none_when_empty(self, driver_env):
        drv = driver_env["drv"]
        assert drv.pick_next_task() is None

    def test_returns_none_when_all_done(self, driver_env):
        drv = driver_env["drv"]
        task = _add_task(drv, "Done task")
        drv.update_task_status(task["id"], "completed")
        assert drv.pick_next_task() is None

    def test_tiebreak_by_creation_time(self, driver_env):
        drv = driver_env["drv"]
        _add_task(drv, "First", priority=3)
        _add_task(drv, "Second", priority=3)

        picked = drv.pick_next_task()
        assert picked["title"] == "First"


class TestUpdateTaskStatus:
    def test_transitions_status(self, driver_env):
        drv = driver_env["drv"]
        task = _add_task(drv, "Transition test")
        drv.update_task_status(task["id"], "in_progress")

        tasks = drv.load_tasks()
        updated = [t for t in tasks if t["id"] == task["id"]][0]
        assert updated["status"] == "in_progress"

    def test_sets_completed_at(self, driver_env):
        drv = driver_env["drv"]
        task = _add_task(drv, "Completion test")
        drv.update_task_status(task["id"], "completed")

        tasks = drv.load_tasks()
        updated = [t for t in tasks if t["id"] == task["id"]][0]
        assert updated["status"] == "completed"
        assert updated["completed_at"] is not None

    def test_extra_fields(self, driver_env):
        drv = driver_env["drv"]
        task = _add_task(drv, "Extra fields test")
        drv.update_task_status(task["id"], "blocked", failure_reason="timeout")

        tasks = drv.load_tasks()
        updated = [t for t in tasks if t["id"] == task["id"]][0]
        assert updated["failure_reason"] == "timeout"


class TestAddTask:
    def test_auto_increments_id(self, driver_env):
        drv = driver_env["drv"]
        t1 = _add_task(drv, "First")
        t2 = _add_task(drv, "Second")
        assert t1["id"] == "task-001"
        assert t2["id"] == "task-002"

    def test_defaults(self, driver_env):
        drv = driver_env["drv"]
        task = _add_task(drv, "Defaults test", desc="test")
        assert task["status"] == "committed"
        assert task["max_turns"] == 30
        assert task["assigned_to"] == "third-brother-driver-v2"
        assert task["completed_at"] is None


# ═══════════════════════════════════════════════════════════════
# CRASH RECOVERY
# ═══════════════════════════════════════════════════════════════

class TestRecoverStaleTasks:
    def test_resets_in_progress_no_commit(self, driver_env):
        drv = driver_env["drv"]
        task = _add_task(drv, "Stale task")
        drv.update_task_status(task["id"], "in_progress")

        with patch.object(drv, "git", return_value=""):
            drv.recover_stale_tasks()

        tasks = drv.load_tasks()
        recovered = [t for t in tasks if t["id"] == task["id"]][0]
        assert recovered["status"] == "committed"

    def test_completes_if_commit_found(self, driver_env):
        drv = driver_env["drv"]
        task = _add_task(drv, "Committed task")
        drv.update_task_status(task["id"], "in_progress")

        with patch.object(drv, "git", return_value="abc1234 tb: Committed task"):
            drv.recover_stale_tasks()

        tasks = drv.load_tasks()
        recovered = [t for t in tasks if t["id"] == task["id"]][0]
        assert recovered["status"] == "completed"

    def test_ignores_non_in_progress(self, driver_env):
        drv = driver_env["drv"]
        task = _add_task(drv, "Committed task")  # status = committed

        with patch.object(drv, "git", return_value=""):
            drv.recover_stale_tasks()

        tasks = drv.load_tasks()
        t = [t for t in tasks if t["id"] == task["id"]][0]
        assert t["status"] == "committed"


# ═══════════════════════════════════════════════════════════════
# AUTO-COMMIT
# ═══════════════════════════════════════════════════════════════

class TestAutoCommit:
    def test_commits_when_changes_exist(self, driver_env):
        drv = driver_env["drv"]
        task = {"id": "task-001", "title": "Test commit"}

        with patch.object(drv, "git", side_effect=["M file.py", "", ""]) as mock_git:
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                # git status returns changes, then git add, then git log
                with patch.object(drv, "git", side_effect=[
                    "M file.py",        # status --porcelain
                    "",                  # add -A
                    "abc1234 tb: Test commit",  # log --oneline -1
                ]):
                    drv.auto_commit(task)

    def test_noop_when_clean(self, driver_env):
        drv = driver_env["drv"]
        task = {"id": "task-001", "title": "No changes"}

        with patch.object(drv, "git", return_value=""):
            drv.auto_commit(task)
            # Should not raise, just print "No changes"


# ═══════════════════════════════════════════════════════════════
# KILL SWITCH
# ═══════════════════════════════════════════════════════════════

class TestKillSwitch:
    def test_detects_stop_file(self, driver_env):
        drv = driver_env["drv"]
        assert drv.check_kill_switch() is False

        drv.STOP_FILE.touch()
        assert drv.check_kill_switch() is True

    def test_no_false_positive(self, driver_env):
        drv = driver_env["drv"]
        # No stop file exists
        assert drv.check_kill_switch() is False


# ═══════════════════════════════════════════════════════════════
# TRUST LADDER
# ═══════════════════════════════════════════════════════════════

class TestTrustLadder:
    def _write_runs(self, drv, outcomes):
        """Write synthetic runs to runs.jsonl."""
        with open(drv.RUNS_PATH, "w") as f:
            for i, outcome in enumerate(outcomes):
                entry = {
                    "ts": f"2026-03-22T10:{i:02d}:00",
                    "task_id": f"task-{i:03d}",
                    "task_title": f"Task {i}",
                    "outcome": outcome,
                    "turns": 10,
                    "duration_seconds": 60,
                }
                f.write(json.dumps(entry) + "\n")

    def test_no_runs_no_change(self, driver_env):
        drv = driver_env["drv"]
        config = drv.load_config()
        old, new, reason = drv.evaluate_trust_ladder(config)
        assert old == 1
        assert new == 1
        assert "no runs" in reason

    def test_phase_1_to_2_promotion(self, driver_env):
        drv = driver_env["drv"]
        # Config has min_runs=5, unedited_ratio=0.60
        self._write_runs(drv, ["completed"] * 5)

        config = drv.load_config()
        old, new, reason = drv.evaluate_trust_ladder(config)
        assert old == 1
        assert new == 2
        assert "Phase 1->2" in reason

    def test_phase_1_stays_if_too_few_runs(self, driver_env):
        drv = driver_env["drv"]
        self._write_runs(drv, ["completed"] * 3)

        config = drv.load_config()
        old, new, reason = drv.evaluate_trust_ladder(config)
        assert old == 1
        assert new == 1

    def test_phase_1_stays_if_low_ratio(self, driver_env):
        drv = driver_env["drv"]
        # 2 completed, 3 failed = 40% < 60% threshold
        self._write_runs(drv, ["completed", "completed", "blocked", "blocked", "error"])

        config = drv.load_config()
        old, new, reason = drv.evaluate_trust_ladder(config)
        assert old == 1
        assert new == 1

    def test_demotion_on_consecutive_failures(self, driver_env):
        drv = driver_env["drv"]
        # Start at phase 2
        config = drv.load_config()
        config["trust_ladder"]["current_phase"] = 2
        drv.CONFIG_PATH.write_text(json.dumps(config, indent=2))
        config = drv.load_config()

        self._write_runs(drv, ["completed", "completed", "blocked", "blocked", "blocked"])

        old, new, reason = drv.evaluate_trust_ladder(config)
        assert old == 2
        assert new == 1
        assert "consecutive failures" in reason

    def test_critical_alert_demotes_to_phase_1(self, driver_env):
        drv = driver_env["drv"]
        config = drv.load_config()
        config["trust_ladder"]["current_phase"] = 3
        drv.CONFIG_PATH.write_text(json.dumps(config, indent=2))
        config = drv.load_config()

        self._write_runs(drv, ["completed"] * 5)

        # Write a critical alert
        alert = {
            "ts": "2026-03-22T10:30:00",
            "rule": "destructive_op",
            "task_id": "task-003",
            "action": "killed",
            "severity": "CRITICAL",
        }
        with open(drv.ALERTS_PATH, "w") as f:
            f.write(json.dumps(alert) + "\n")

        old, new, reason = drv.evaluate_trust_ladder(config)
        assert old == 3
        assert new == 1
        assert "CRITICAL" in reason

    def test_apply_trust_ladder_writes_config(self, driver_env):
        drv = driver_env["drv"]
        self._write_runs(drv, ["completed"] * 5)

        config = drv.load_config()
        new_phase = drv.apply_trust_ladder(config)
        assert new_phase == 2

        # Verify config was written
        reloaded = drv.load_config()
        assert reloaded["trust_ladder"]["current_phase"] == 2


# ═══════════════════════════════════════════════════════════════
# SHADOW LOG (RAFT)
# ═══════════════════════════════════════════════════════════════

class TestShadowRaftLog:
    def test_writes_correct_schema(self, driver_env):
        drv = driver_env["drv"]
        task = {"id": "task-001", "title": "Test RAFT"}
        rag_results = [
            {"chunk": "context chunk 1", "score": 0.9},
            {"chunk": "context chunk 2", "score": 0.7},
        ]

        drv.log_shadow_raft(
            task=task,
            instruction="Write tests for driver",
            response="Done. Created tests/test_driver.py with 10 tests.",
            session_id="test-session-123",
            rag_results=rag_results,
            context="Some brain context here",
            turn_count=15,
            outcome="completed",
            duration_ms=30000,
        )

        lines = drv.SHADOW_LOG_PATH.read_text().strip().split("\n")
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["task_id"] == "task-001"
        assert entry["session_id"] == "test-session-123"
        assert entry["outcome"] == "completed"
        assert entry["total_turns"] == 15
        assert entry["latency_ms"] == 30000
        assert entry["format"] == "raft_v2"
        assert entry["model_outer"] == "template"
        assert entry["model_inner"] == "claude-opus-4-6"
        assert len(entry["oracle_chunks"]) == 2
        assert entry["rag_context_words"] == 4  # "Some brain context here"

    def test_handles_empty_rag(self, driver_env):
        drv = driver_env["drv"]
        task = {"id": "task-002", "title": "No RAG"}

        drv.log_shadow_raft(
            task=task, instruction="test", response="done",
            session_id="s", rag_results=[], context="",
            turn_count=1, outcome="completed",
        )

        entry = json.loads(drv.SHADOW_LOG_PATH.read_text().strip())
        assert entry["oracle_chunks"] == []
        assert entry["rag_context_words"] == 0


# ═══════════════════════════════════════════════════════════════
# TEMPLATE
# ═══════════════════════════════════════════════════════════════

class TestTaskTemplate:
    def test_fills_all_fields(self, driver_env):
        drv = driver_env["drv"]
        result = drv.TASK_TEMPLATE.format(
            title="Build feature X",
            description="Implement feature X with tests",
            context="Relevant brain context here",
            scope="src/**, tests/**",
            scope_list="- src/**\n- tests/**",
        )
        assert "Build feature X" in result
        assert "Implement feature X with tests" in result
        assert "Relevant brain context here" in result
        assert "src/**, tests/**" in result
        assert "- src/**" in result

    def test_no_signal_phrases(self, driver_env):
        drv = driver_env["drv"]
        # Template should NOT contain v1 signal phrases used for detection
        template = drv.TASK_TEMPLATE
        assert "TASK COMPLETE" not in template
        assert "NEED HELP" not in template
        # Template says "No need to create branches" which is correct v2 behavior
        assert "Say TASK COMPLETE" not in template
        assert "Say NEED HELP" not in template


# ═══════════════════════════════════════════════════════════════
# STATE PERSISTENCE
# ═══════════════════════════════════════════════════════════════

class TestStatePersistence:
    def test_save_and_read_state(self, driver_env):
        drv = driver_env["drv"]
        task = {"id": "task-001", "title": "Test"}
        drv.save_state("executing", task, session_id="session-abc")

        data = json.loads(drv.STATE_PATH.read_text())
        assert data["phase"] == "executing"
        assert data["task_id"] == "task-001"
        assert data["session_id"] == "session-abc"

    def test_save_without_task(self, driver_env):
        drv = driver_env["drv"]
        drv.save_state("idle")

        data = json.loads(drv.STATE_PATH.read_text())
        assert data["phase"] == "idle"
        assert data["task_id"] is None


# ═══════════════════════════════════════════════════════════════
# LOG RUN
# ═══════════════════════════════════════════════════════════════

class TestLogRun:
    def test_appends_entry(self, driver_env):
        drv = driver_env["drv"]
        task = {"id": "task-001", "title": "Test run"}

        drv.log_run(task, "completed", turns=10, duration_seconds=120)
        drv.log_run(task, "error", turns=5, duration_seconds=60, failure_reason="timeout")

        lines = drv.RUNS_PATH.read_text().strip().split("\n")
        assert len(lines) == 2

        e1 = json.loads(lines[0])
        assert e1["outcome"] == "completed"
        assert e1["driver_version"] == "v2"

        e2 = json.loads(lines[1])
        assert e2["outcome"] == "error"
        assert e2["failure_reason"] == "timeout"

    def test_records_retry_count(self, driver_env):
        drv = driver_env["drv"]
        task = {"id": "task-003", "title": "Retried run"}

        drv.log_run(task, "completed", turns=8, duration_seconds=90, retry_count=2)

        entry = json.loads(drv.RUNS_PATH.read_text().strip())
        assert entry["retry_count"] == 2

    def test_retry_count_defaults_to_zero(self, driver_env):
        drv = driver_env["drv"]
        task = {"id": "task-004", "title": "No retries"}

        drv.log_run(task, "completed", turns=5, duration_seconds=30)

        entry = json.loads(drv.RUNS_PATH.read_text().strip())
        assert entry["retry_count"] == 0


# ═══════════════════════════════════════════════════════════════
# LOCKING
# ═══════════════════════════════════════════════════════════════

class TestLocking:
    def test_fallback_lock_acquire_release(self, driver_env):
        drv = driver_env["drv"]
        lock = drv._FallbackLock(str(drv.LOCKS_DIR / "test.lock"))

        assert lock.acquire() is True
        # Lock file should contain PID
        content = Path(lock.lock_file).read_text()
        assert str(os.getpid()) in content

        lock.release()
        assert lock.fd is None

    def test_fallback_lock_guard_context(self, driver_env):
        drv = driver_env["drv"]
        lock = drv._FallbackLock(str(drv.LOCKS_DIR / "guard.lock"))

        with lock.guard():
            assert lock.fd is not None
        assert lock.fd is None


# ═══════════════════════════════════════════════════════════════
# EXECUTE TASK (mocked)
# ═══════════════════════════════════════════════════════════════

class TestExecuteTask:
    def test_returns_parsed_json(self, driver_env):
        drv = driver_env["drv"]
        task = {
            "id": "task-001", "title": "Test exec",
            "description": "Write a test", "scope": ["tests/**"],
            "max_turns": 10,
        }
        config = drv.load_config()

        mock_result = MagicMock()
        mock_result.stdout = json.dumps({
            "result": "Created tests/test_example.py",
            "num_turns": 8,
        })
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            with patch("providers.brain_rag.build_full_context",
                       return_value=("context", [{"chunk": "c1"}])):
                response = drv.execute_task(task, "session-123", config)

        assert response["duration_seconds"] >= 0
        assert "context" in response
        assert "rag_results" in response

    def test_handles_timeout(self, driver_env):
        drv = driver_env["drv"]
        task = {
            "id": "task-002", "title": "Slow task",
            "description": "Takes forever", "scope": ["**"],
        }
        config = drv.load_config()
        config["session_timeout_minutes"] = 0  # immediate timeout

        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 1)):
            response = drv.execute_task(task, "session-123", config)

        assert response["outcome"] == "timeout"

    def test_handles_non_json_output(self, driver_env):
        drv = driver_env["drv"]
        task = {
            "id": "task-003", "title": "Bad output",
            "description": "Returns garbage", "scope": ["**"],
        }
        config = drv.load_config()

        mock_result = MagicMock()
        mock_result.stdout = "not valid json"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            response = drv.execute_task(task, "session-123", config)

        assert response.get("result") == "not valid json"

    def _make_task(self, task_id="task-004", title="Test"):
        return {"id": task_id, "title": title, "description": "test", "scope": ["**"]}

    def _mock_rag(self):
        return patch("providers.brain_rag.build_full_context",
                      return_value=("ctx", []))

    def test_retries_on_nonzero_exit(self, driver_env):
        """Non-zero exit triggers exponential backoff retry, then succeeds."""
        drv = driver_env["drv"]
        task = self._make_task("task-004", "Flaky task")
        config = drv.load_config()
        config["max_retries"] = 2

        fail_result = MagicMock()
        fail_result.returncode = 1
        fail_result.stdout = ""
        fail_result.stderr = "segfault in node"

        ok_result = MagicMock()
        ok_result.returncode = 0
        ok_result.stdout = json.dumps({"result": "done", "num_turns": 5})

        with self._mock_rag():
            with patch("subprocess.run", side_effect=[fail_result, ok_result]):
                with patch("time.sleep"):
                    response = drv.execute_task(task, "session-123", config)

        assert response["retry_count"] == 1
        assert response.get("result") == "done"

        # Verify alert was logged
        alerts = drv.ALERTS_PATH.read_text().strip().split("\n")
        alert = json.loads(alerts[-1])
        assert alert["rule"] == "exec_retry"
        assert alert["severity"] == "WARNING"
        assert alert["action"] == "retry_1"

    def test_no_retry_on_guardrail_violation(self, driver_env):
        """Guardrail stderr patterns should NOT trigger retry."""
        drv = driver_env["drv"]
        task = self._make_task("task-005", "Guardrail hit")
        config = drv.load_config()
        config["max_retries"] = 2

        blocked_result = MagicMock()
        blocked_result.returncode = 1
        blocked_result.stdout = ""
        blocked_result.stderr = "Guardrail violation: destructive operation blocked"

        with self._mock_rag():
            with patch("subprocess.run", return_value=blocked_result) as mock_run:
                with patch("time.sleep"):
                    response = drv.execute_task(task, "session-123", config)

        # Should have been called exactly once — no retry
        assert mock_run.call_count == 1
        assert response["retry_count"] == 0

    def test_retries_exhausted_returns_last_result(self, driver_env):
        """When all retries fail, return the last result with retry_count."""
        drv = driver_env["drv"]
        task = self._make_task("task-006", "Always fails")
        config = drv.load_config()
        config["max_retries"] = 2

        fail_result = MagicMock()
        fail_result.returncode = 1
        fail_result.stdout = ""
        fail_result.stderr = "unknown error"

        with self._mock_rag():
            with patch("subprocess.run", return_value=fail_result):
                with patch("time.sleep"):
                    response = drv.execute_task(task, "session-123", config)

        assert response["retry_count"] == 2
        assert "unknown error" in response.get("result", "")

    def test_retry_backoff_is_exponential(self, driver_env):
        """Backoff delays should be 5s, 15s (base=5, mult=3)."""
        drv = driver_env["drv"]
        task = self._make_task("task-007", "Backoff test")
        config = drv.load_config()
        config["max_retries"] = 2

        fail_result = MagicMock()
        fail_result.returncode = 1
        fail_result.stdout = ""
        fail_result.stderr = "transient error"

        ok_result = MagicMock()
        ok_result.returncode = 0
        ok_result.stdout = json.dumps({"result": "ok"})

        sleep_calls = []
        def track_sleep(secs):
            sleep_calls.append(secs)

        with self._mock_rag():
            with patch("subprocess.run", side_effect=[fail_result, fail_result, ok_result]):
                with patch("time.sleep", side_effect=track_sleep):
                    response = drv.execute_task(task, "session-123", config)

        assert response["retry_count"] == 2
        # Backoff: 5 * 3^0 = 5, 5 * 3^1 = 15
        assert 5 in sleep_calls
        assert 15 in sleep_calls
