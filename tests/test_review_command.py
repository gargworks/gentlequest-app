"""
Tests for Frontier 2: ALIGN — Human Review Command
===================================================
Tests handle_review_command in cli.py: list blocked tasks,
accept/reject/correct/direction verdicts, platinum DPO/SFT capture.

Uses tmp_path + monkeypatch — no network, no real brain dir.
"""

import json
import sys
import types
import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tasks(blocked=2, completed=1):
    """Build a tasks.json dict with blocked + completed tasks."""
    tasks = []
    for i in range(blocked):
        tasks.append({
            "id": f"blocked-{i+1:03d}",
            "description": f"Blocked task {i+1} description",
            "status": "blocked",
            "last_output": f"Claude output for blocked task {i+1}",
        })
    for i in range(completed):
        tasks.append({
            "id": f"done-{i+1:03d}",
            "description": f"Completed task {i+1}",
            "status": "completed",
        })
    return {"tasks": tasks, "schema_version": 2, "updated_at": "2026-03-29T00:00:00"}


def _make_args(task_id=None, accept=False, reject=None, correct=None, direction=None):
    """Build an argparse-like namespace."""
    ns = types.SimpleNamespace()
    ns.task_id = task_id
    ns.accept = accept
    ns.reject = reject
    ns.correct = correct
    ns.direction = direction
    return ns


@pytest.fixture
def review_env(tmp_path, monkeypatch):
    """Set up isolated driver + training dirs with blocked tasks."""
    driver_dir = tmp_path / ".brain" / "driver"
    driver_dir.mkdir(parents=True)
    inbox = tmp_path / ".brain" / "training" / "inbox"
    inbox.mkdir(parents=True)

    tasks_data = _make_tasks(blocked=2, completed=1)
    tasks_path = driver_dir / "tasks.json"
    tasks_path.write_text(json.dumps(tasks_data, indent=2))

    # Monkeypatch _PROJECT_ROOT in the cli module
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent /
                          "mcp-server-nucleus" / "src"))
    import mcp_server_nucleus.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_PROJECT_ROOT", tmp_path)

    return types.SimpleNamespace(
        tmp_path=tmp_path,
        driver_dir=driver_dir,
        tasks_path=tasks_path,
        inbox=inbox,
        verdicts_path=driver_dir / "human_verdicts.jsonl",
        dpo_path=inbox / "sparring_dpo.jsonl",
        sft_path=inbox / "sparring_sft.jsonl",
        cli_mod=cli_mod,
    )


# ===========================================================================
# List mode
# ===========================================================================

class TestListBlocked:
    def test_list_blocked_tasks(self, review_env, capsys):
        """No task_id → prints blocked task list."""
        args = _make_args()
        review_env.cli_mod.handle_review_command(args)
        out = capsys.readouterr().out
        assert "2 task(s) awaiting human review" in out
        assert "blocked-001" in out
        assert "blocked-002" in out

    def test_list_empty(self, review_env, capsys):
        """No blocked tasks → 'No blocked tasks' message."""
        # Overwrite with no blocked tasks
        tasks_data = _make_tasks(blocked=0, completed=2)
        review_env.tasks_path.write_text(json.dumps(tasks_data))
        args = _make_args()
        review_env.cli_mod.handle_review_command(args)
        out = capsys.readouterr().out
        assert "No blocked tasks" in out


# ===========================================================================
# Accept verdict
# ===========================================================================

class TestAcceptVerdict:
    def test_accept_writes_platinum_sft(self, review_env):
        """--accept → sparring_sft.jsonl has platinum entry."""
        args = _make_args(task_id="blocked-001", accept=True)
        review_env.cli_mod.handle_review_command(args)
        entries = [json.loads(l) for l in review_env.sft_path.read_text().splitlines()]
        assert len(entries) == 1
        assert entries[0]["metadata"]["quality"] == "platinum"
        assert entries[0]["metadata"]["source"] == "human_review"
        assert entries[0]["metadata"]["verdict"] == "accept"

    def test_accept_updates_task_status(self, review_env):
        """--accept → task status becomes 'completed'."""
        args = _make_args(task_id="blocked-001", accept=True)
        review_env.cli_mod.handle_review_command(args)
        data = json.loads(review_env.tasks_path.read_text())
        task = next(t for t in data["tasks"] if t["id"] == "blocked-001")
        assert task["status"] == "completed"


# ===========================================================================
# Reject verdict
# ===========================================================================

class TestRejectVerdict:
    def test_reject_writes_platinum_dpo(self, review_env):
        """--reject → sparring_dpo.jsonl has entry, chosen=reason."""
        args = _make_args(task_id="blocked-001", reject="Wrong approach entirely")
        review_env.cli_mod.handle_review_command(args)
        entries = [json.loads(l) for l in review_env.dpo_path.read_text().splitlines()]
        assert len(entries) == 1
        assert entries[0]["chosen"] == "Wrong approach entirely"
        assert entries[0]["metadata"]["quality"] == "platinum"
        assert "Claude output" in entries[0]["rejected"]

    def test_reject_requeues_task(self, review_env):
        """--reject → task status becomes 'committed' (re-queued)."""
        args = _make_args(task_id="blocked-001", reject="Bad")
        review_env.cli_mod.handle_review_command(args)
        data = json.loads(review_env.tasks_path.read_text())
        task = next(t for t in data["tasks"] if t["id"] == "blocked-001")
        assert task["status"] == "committed"


# ===========================================================================
# Correct verdict
# ===========================================================================

class TestCorrectVerdict:
    def test_correct_writes_dpo_and_sft(self, review_env):
        """--correct → both DPO and SFT written, both platinum."""
        args = _make_args(task_id="blocked-001", correct="Use middleware instead")
        review_env.cli_mod.handle_review_command(args)
        dpo = [json.loads(l) for l in review_env.dpo_path.read_text().splitlines()]
        sft = [json.loads(l) for l in review_env.sft_path.read_text().splitlines()]
        assert len(dpo) == 1
        assert len(sft) == 1
        assert dpo[0]["chosen"] == "Use middleware instead"
        assert dpo[0]["metadata"]["quality"] == "platinum"
        assert sft[0]["metadata"]["quality"] == "platinum"
        assert sft[0]["messages"][-1]["content"] == "Use middleware instead"


# ===========================================================================
# Direction verdict
# ===========================================================================

class TestDirectionVerdict:
    def test_direction_logs_only(self, review_env):
        """--direction → human_verdicts.jsonl has entry, no DPO/SFT files."""
        args = _make_args(task_id="blocked-001", direction="Wrong hill, deprioritize")
        review_env.cli_mod.handle_review_command(args)
        verdicts = [json.loads(l) for l in review_env.verdicts_path.read_text().splitlines()]
        assert len(verdicts) == 1
        assert verdicts[0]["verdict"] == "direction"
        assert verdicts[0]["human_input"] == "Wrong hill, deprioritize"
        # No DPO or SFT should be written for direction
        assert not review_env.dpo_path.exists()
        assert not review_env.sft_path.exists()


# ===========================================================================
# Edge cases
# ===========================================================================

class TestEdgeCases:
    def test_task_not_found(self, review_env):
        """Invalid task_id → sys.exit(1)."""
        args = _make_args(task_id="nonexistent-999", accept=True)
        with pytest.raises(SystemExit) as exc_info:
            review_env.cli_mod.handle_review_command(args)
        assert exc_info.value.code == 1

    def test_preserves_tasks_format(self, review_env):
        """Dict-format tasks.json preserved after update."""
        args = _make_args(task_id="blocked-001", accept=True)
        review_env.cli_mod.handle_review_command(args)
        data = json.loads(review_env.tasks_path.read_text())
        assert "tasks" in data
        assert "schema_version" in data
        assert "updated_at" in data
        assert isinstance(data["tasks"], list)
