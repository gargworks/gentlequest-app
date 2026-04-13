"""Tests for the lever → Phase D compounding loop.

Proves that lever observations written to .brain/ledger/events.jsonl
actually affect TB's Phase D review scoring — i.e. the ledger is a
*hot* substrate, not just a log file.

If this contract holds, any future lever (#15 ruff_chain plus the other
~30 from the 71-item blitz) automatically compounds the moment it writes
a `lever.<name>.observation outcome=found` event.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scripts.third_brother_driver as tb_driver
from scripts.third_brother_driver import (
    _find_lever_findings_in_diff,
    _record_audit_result,
    _spawn_lever_fix_task,
    _spawn_plan_audit_fix_tasks,
)


DIFF_WITH_DRIVER = (
    "diff --git a/scripts/third_brother_driver.py b/scripts/third_brother_driver.py\n"
    "index abc..def 100644\n"
    "--- a/scripts/third_brother_driver.py\n"
    "+++ b/scripts/third_brother_driver.py\n"
    "@@ -42,1 +42,2 @@\n"
    "+from driver_config import X\n"
)

DIFF_UNRELATED = (
    "diff --git a/README.md b/README.md\n"
    "index abc..def 100644\n"
    "--- a/README.md\n"
    "+++ b/README.md\n"
    "@@ -1,1 +1,1 @@\n"
    "+hello\n"
)


def _write_ledger(path: Path, events: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n")


class TestFindLeverFindingsInDiff:
    def test_empty_diff_returns_empty(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        _write_ledger(ledger, [{
            "type": "lever.ruff_chain.observation",
            "outcome": "found",
            "detail": {"findings": ["scripts/third_brother_driver.py:42:1: E402"]},
        }])
        assert _find_lever_findings_in_diff("", ledger_path=ledger) == []

    def test_missing_ledger_returns_empty(self, tmp_path):
        assert _find_lever_findings_in_diff(
            DIFF_WITH_DRIVER, ledger_path=tmp_path / "nope.jsonl"
        ) == []

    def test_clean_outcome_does_not_match(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        _write_ledger(ledger, [{
            "type": "lever.ruff_chain.observation",
            "outcome": "clean",
            "detail": {"files_checked": 1},
        }])
        assert _find_lever_findings_in_diff(DIFF_WITH_DRIVER, ledger_path=ledger) == []

    def test_non_lever_events_ignored(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        _write_ledger(ledger, [{
            "type": "phase.failure",
            "outcome": "found",
            "detail": {"findings": ["scripts/third_brother_driver.py:42 error"]},
        }])
        assert _find_lever_findings_in_diff(DIFF_WITH_DRIVER, ledger_path=ledger) == []

    def test_found_but_different_file_does_not_match(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        _write_ledger(ledger, [{
            "type": "lever.ruff_chain.observation",
            "outcome": "found",
            "detail": {"findings": ["some_other_file.py:10:1: E402"]},
        }])
        assert _find_lever_findings_in_diff(DIFF_WITH_DRIVER, ledger_path=ledger) == []

    def test_found_on_diff_file_matches(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        _write_ledger(ledger, [{
            "type": "lever.ruff_chain.observation",
            "outcome": "found",
            "detail": {"findings": ["scripts/third_brother_driver.py:42:1: E402"]},
        }])
        matches = _find_lever_findings_in_diff(DIFF_WITH_DRIVER, ledger_path=ledger)
        assert len(matches) == 1
        assert matches[0]["type"] == "lever.ruff_chain.observation"

    def test_malformed_json_lines_skipped(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        valid = json.dumps({
            "type": "lever.ruff_chain.observation",
            "outcome": "found",
            "detail": {"findings": ["scripts/third_brother_driver.py:42 E402"]},
        })
        ledger.write_text(f"{{malformed\nnot-json\n{valid}\n")
        matches = _find_lever_findings_in_diff(DIFF_WITH_DRIVER, ledger_path=ledger)
        assert len(matches) == 1

    def test_window_limits_lookback(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        old_match = {
            "type": "lever.ruff_chain.observation",
            "outcome": "found",
            "detail": {"findings": ["scripts/third_brother_driver.py:42 E402"]},
        }
        noise = {"type": "phase.noise", "outcome": "clean", "detail": {}}
        # Put the match at index 0, then 50 noise entries after.
        events = [old_match] + [noise] * 50
        _write_ledger(ledger, events)
        # With a small window, the old match falls outside the lookback.
        matches = _find_lever_findings_in_diff(
            DIFF_WITH_DRIVER, ledger_path=ledger, window=10
        )
        assert matches == []
        # With a big window, it's visible again.
        matches = _find_lever_findings_in_diff(
            DIFF_WITH_DRIVER, ledger_path=ledger, window=100
        )
        assert len(matches) == 1

    def test_unrelated_diff_does_not_match(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        _write_ledger(ledger, [{
            "type": "lever.ruff_chain.observation",
            "outcome": "found",
            "detail": {"findings": ["scripts/third_brother_driver.py:42 E402"]},
        }])
        # README.md diff should not match a driver.py finding.
        assert _find_lever_findings_in_diff(
            DIFF_UNRELATED, ledger_path=ledger
        ) == []

    def test_multiple_levers_all_returned(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        _write_ledger(ledger, [
            {
                "type": "lever.ruff_chain.observation",
                "outcome": "found",
                "lever": "ruff_chain",
                "detail": {"findings": ["scripts/third_brother_driver.py:42 E402"]},
            },
            {
                "type": "lever.mypy_chain.observation",
                "outcome": "found",
                "lever": "mypy_chain",
                "detail": {"findings": ["scripts/third_brother_driver.py:99 type error"]},
            },
        ])
        matches = _find_lever_findings_in_diff(DIFF_WITH_DRIVER, ledger_path=ledger)
        assert len(matches) == 2
        levers = {m.get("lever") for m in matches}
        assert levers == {"ruff_chain", "mypy_chain"}


class TestSpawnLeverFixTask:
    def _match(self, lever="ruff_chain", finding="scripts/third_brother_driver.py:42:1: E402"):
        return {
            "type": f"lever.{lever}.observation",
            "outcome": "found",
            "lever": lever,
            "detail": {"findings": [finding]},
        }

    def test_creates_task_with_lever_gate_source(self, tmp_path):
        tasks_path = tmp_path / "tasks.json"
        parent = {"id": "t-100", "scope": ["scripts/**"]}
        new_id = _spawn_lever_fix_task(
            parent, [self._match()], tasks_path=tasks_path
        )
        assert new_id is not None
        assert new_id.startswith("lever-fix-ruff_chain-")
        data = json.loads(tasks_path.read_text())
        created = [t for t in data["tasks"] if t["id"] == new_id]
        assert len(created) == 1
        assert created[0]["source"] == "lever_gate"
        assert created[0]["status"] == "pending"
        assert created[0]["priority"] == "high"
        assert created[0]["lever_gate_parent_task_id"] == "t-100"
        assert created[0]["scope"] == ["scripts/third_brother_driver.py"]

    def test_dedupes_same_finding_set(self, tmp_path):
        tasks_path = tmp_path / "tasks.json"
        parent = {"id": "t-200", "scope": ["scripts/**"]}
        match = self._match()
        first = _spawn_lever_fix_task(parent, [match], tasks_path=tasks_path)
        second = _spawn_lever_fix_task(parent, [match], tasks_path=tasks_path)
        assert first == second
        data = json.loads(tasks_path.read_text())
        lever_tasks = [t for t in data["tasks"] if t.get("source") == "lever_gate"]
        assert len(lever_tasks) == 1

    def test_new_task_when_finding_set_differs(self, tmp_path):
        tasks_path = tmp_path / "tasks.json"
        parent = {"id": "t-300", "scope": ["scripts/**"]}
        first = _spawn_lever_fix_task(
            parent,
            [self._match(finding="scripts/third_brother_driver.py:42:1: E402")],
            tasks_path=tasks_path,
        )
        second = _spawn_lever_fix_task(
            parent,
            [self._match(finding="scripts/other_file.py:10:1: F401")],
            tasks_path=tasks_path,
        )
        assert first != second
        data = json.loads(tasks_path.read_text())
        lever_tasks = [t for t in data["tasks"] if t.get("source") == "lever_gate"]
        assert len(lever_tasks) == 2

    def test_creates_tasks_json_if_missing(self, tmp_path):
        tasks_path = tmp_path / "nested" / "tasks.json"
        tasks_path.parent.mkdir()
        parent = {"id": "t-400"}
        new_id = _spawn_lever_fix_task(
            parent, [self._match()], tasks_path=tasks_path
        )
        assert new_id is not None
        assert tasks_path.exists()
        data = json.loads(tasks_path.read_text())
        assert len(data["tasks"]) == 1

    def test_completed_dedup_task_allows_new_spawn(self, tmp_path):
        """If the prior lever-fix task is completed, a new one should spawn
        because the finding re-surfaced despite being 'fixed'."""
        tasks_path = tmp_path / "tasks.json"
        parent = {"id": "t-500"}
        first = _spawn_lever_fix_task(parent, [self._match()], tasks_path=tasks_path)
        # Mark the first task as completed.
        data = json.loads(tasks_path.read_text())
        for t in data["tasks"]:
            if t["id"] == first:
                t["status"] = "completed"
        tasks_path.write_text(json.dumps(data))
        # Spawn again with same findings — should create a NEW task.
        second = _spawn_lever_fix_task(parent, [self._match()], tasks_path=tasks_path)
        assert second is not None
        assert second != first
        data = json.loads(tasks_path.read_text())
        pending = [t for t in data["tasks"]
                   if t.get("source") == "lever_gate" and t.get("status") == "pending"]
        assert len(pending) == 1


class TestSpawnPlanAuditFixTasks:
    """Wave 7 — plan_audit → TB task bank.

    Spawner reads newest ``lever.plan_audit.observation`` from the ledger
    and creates one ``audit-plan-<stem>`` task per plan in ``top_rot``.
    Emission policy is silent-unless-action-or-degraded:

        created >0 tasks   → lever.plan_audit_spawner.observation found
        tasks.json read err → lever.plan_audit_spawner.observation skipped
                              (stage=tasks_json_read)
        ledger read err    → lever.plan_audit_spawner.observation skipped
                              (stage=ledger_read)
        no obs / all dedup → silent
    """

    def _write_tasks(self, tasks_path: Path, tasks=None):
        tasks_path.parent.mkdir(parents=True, exist_ok=True)
        tasks_path.write_text(json.dumps({
            "tasks": tasks or [],
            "schema_version": 1,
        }))

    def _write_plan_audit_found(self, ledger_path: Path, top_rot):
        _write_ledger(ledger_path, [{
            "ts": "2026-04-13T00:00:00+00:00",
            "type": "lever.plan_audit.observation",
            "lever": "plan_audit",
            "outcome": "found",
            "detail": {
                "plans_total": len(top_rot) + 1,
                "plans_rotting": len(top_rot),
                "by_bucket": {},
                "top_rot": top_rot,
            },
        }])

    def _read_spawner_events(self, ledger_path: Path):
        out = []
        if not ledger_path.exists():
            return out
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            if raw.get("type") == "lever.plan_audit_spawner.observation":
                out.append(raw)
        return out

    def test_spawn_plan_audit_tasks_zero_when_no_obs(self, tmp_path, monkeypatch):
        """No plan_audit event on the ledger → silent no-op."""
        ledger = tmp_path / "events.jsonl"
        tasks = tmp_path / "tasks.json"
        self._write_tasks(tasks)
        ledger.write_text("")  # empty ledger
        got = _spawn_plan_audit_fix_tasks(tasks_path=tasks, ledger_path=ledger)
        assert got == []
        assert self._read_spawner_events(ledger) == []

    def test_spawn_plan_audit_tasks_creates_one_per_rotting_plan(
        self, tmp_path, monkeypatch,
    ):
        """Observation with 2 rotting plans → 2 tasks created + 1 found event."""
        plans_dir = tmp_path / ".claude_plans"
        plans_dir.mkdir()
        (plans_dir / "alpha.md").write_text("# alpha")
        (plans_dir / "beta.md").write_text("# beta")
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        # Home is now tmp_path → ~/.claude/plans resolves under it. Move
        # files into the expected layout.
        claude_plans = tmp_path / ".claude" / "plans"
        claude_plans.mkdir(parents=True)
        (claude_plans / "alpha.md").write_text("# alpha")
        (claude_plans / "beta.md").write_text("# beta")

        ledger = tmp_path / "events.jsonl"
        tasks = tmp_path / "tasks.json"
        self._write_tasks(tasks)
        self._write_plan_audit_found(ledger, [
            {"name": "alpha.md", "bucket": "never_audited", "age_days": 3},
            {"name": "beta.md", "bucket": "stale", "age_days": 10},
        ])
        got = _spawn_plan_audit_fix_tasks(tasks_path=tasks, ledger_path=ledger)
        assert sorted(got) == ["audit-plan-alpha", "audit-plan-beta"]

        data = json.loads(tasks.read_text())
        ids = {t["id"] for t in data["tasks"]}
        assert "audit-plan-alpha" in ids
        assert "audit-plan-beta" in ids

        events = self._read_spawner_events(ledger)
        assert len(events) == 1
        assert events[0]["outcome"] == "found"
        assert events[0]["detail"]["created_count"] == 2

    def test_spawn_plan_audit_tasks_dedupes_existing_pending_task(
        self, tmp_path, monkeypatch,
    ):
        """Pending audit-plan-<stem> task already present → silent no-op."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        claude_plans = tmp_path / ".claude" / "plans"
        claude_plans.mkdir(parents=True)
        (claude_plans / "alpha.md").write_text("# alpha")

        ledger = tmp_path / "events.jsonl"
        tasks = tmp_path / "tasks.json"
        self._write_tasks(tasks, [{
            "id": "audit-plan-alpha",
            "title": "already queued",
            "status": "pending",
            "assigned_to": "tb",
            "source": "plan_audit_spawner",
        }])
        self._write_plan_audit_found(ledger, [
            {"name": "alpha.md", "bucket": "stale", "age_days": 1},
        ])
        got = _spawn_plan_audit_fix_tasks(tasks_path=tasks, ledger_path=ledger)
        assert got == []
        # Silent: no spawner event when everything deduped.
        assert self._read_spawner_events(ledger) == []

    def test_spawn_plan_audit_tasks_skips_orphan_plan_not_on_disk(
        self, tmp_path, monkeypatch,
    ):
        """Plan in observation but removed from both plan dirs → skip it."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        # No plans on disk at all.
        ledger = tmp_path / "events.jsonl"
        tasks = tmp_path / "tasks.json"
        self._write_tasks(tasks)
        self._write_plan_audit_found(ledger, [
            {"name": "ghost.md", "bucket": "never_audited", "age_days": 99},
        ])
        got = _spawn_plan_audit_fix_tasks(tasks_path=tasks, ledger_path=ledger)
        # No task created. Silent — no tasks means no emission.
        assert got == []
        assert self._read_spawner_events(ledger) == []

    def test_spawn_plan_audit_tasks_graceful_on_tasks_json_unreadable(
        self, tmp_path, monkeypatch,
    ):
        """tasks.json JSONDecodeError → returns [], emits skipped event."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        claude_plans = tmp_path / ".claude" / "plans"
        claude_plans.mkdir(parents=True)
        (claude_plans / "alpha.md").write_text("# alpha")

        ledger = tmp_path / "events.jsonl"
        tasks = tmp_path / "tasks.json"
        tasks.write_text("{not valid json")
        self._write_plan_audit_found(ledger, [
            {"name": "alpha.md", "bucket": "stale", "age_days": 1},
        ])
        got = _spawn_plan_audit_fix_tasks(tasks_path=tasks, ledger_path=ledger)
        assert got == []
        events = self._read_spawner_events(ledger)
        assert len(events) == 1
        assert events[0]["outcome"] == "skipped"
        assert events[0]["detail"]["stage"] == "tasks_json_read"

    def test_spawn_plan_audit_tasks_graceful_on_ledger_unreadable(
        self, tmp_path, monkeypatch,
    ):
        """Ledger read OSError → returns [], emits skipped event.

        We simulate by pointing at a path that exists but raises on read.
        Easiest: create a directory at the ledger path so read_text hits
        IsADirectoryError (an OSError subclass)."""
        ledger = tmp_path / "events.jsonl"
        ledger.mkdir()  # directory, not a file → OSError on read
        tasks = tmp_path / "tasks.json"
        self._write_tasks(tasks)
        got = _spawn_plan_audit_fix_tasks(tasks_path=tasks, ledger_path=ledger)
        assert got == []
        # Can't read original path to check events (it's a dir). The
        # emitter swallows the write error silently — that's acceptable;
        # what matters is we returned [] without raising.

    def test_spawn_plan_audit_tasks_emits_found_event_when_tasks_created(
        self, tmp_path, monkeypatch,
    ):
        """N>0 path emits lever.plan_audit_spawner.observation outcome=found
        with detail.created_count == N."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        claude_plans = tmp_path / ".claude" / "plans"
        claude_plans.mkdir(parents=True)
        for name in ("a.md", "b.md", "c.md"):
            (claude_plans / name).write_text(f"# {name}")

        ledger = tmp_path / "events.jsonl"
        tasks = tmp_path / "tasks.json"
        self._write_tasks(tasks)
        self._write_plan_audit_found(ledger, [
            {"name": n, "bucket": "never_audited", "age_days": i}
            for i, n in enumerate(("a.md", "b.md", "c.md"))
        ])
        got = _spawn_plan_audit_fix_tasks(tasks_path=tasks, ledger_path=ledger)
        assert len(got) == 3
        events = self._read_spawner_events(ledger)
        assert len(events) == 1
        assert events[0]["outcome"] == "found"
        assert events[0]["detail"]["created_count"] == 3
        assert sorted(events[0]["detail"]["plan_names"]) == ["a.md", "b.md", "c.md"]

    def test_spawn_plan_audit_tasks_event_type_conforms_to_contract(
        self, tmp_path, monkeypatch,
    ):
        """Emitted event type must match for_lever_observation's hardcoded
        suffix: lever.plan_audit_spawner.observation. outcome ∈ OUTCOMES.
        Regression guard against the plan's original draft that used
        .skipped as the suffix directly."""
        from scripts.levers.base import OUTCOMES

        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        claude_plans = tmp_path / ".claude" / "plans"
        claude_plans.mkdir(parents=True)
        (claude_plans / "only.md").write_text("# only")

        ledger = tmp_path / "events.jsonl"
        tasks = tmp_path / "tasks.json"
        self._write_tasks(tasks)
        self._write_plan_audit_found(ledger, [
            {"name": "only.md", "bucket": "failed_audit", "age_days": 7},
        ])
        _spawn_plan_audit_fix_tasks(tasks_path=tasks, ledger_path=ledger)
        events = self._read_spawner_events(ledger)
        assert len(events) == 1
        assert events[0]["type"] == "lever.plan_audit_spawner.observation"
        assert events[0]["lever"] == "plan_audit_spawner"
        assert events[0]["outcome"] in OUTCOMES


class TestRecordAuditResultAtomic:
    """TODO 6: _record_audit_result must use tmp+os.replace so concurrent
    readers (plan_audit lever, spawner, future MCP resources) never see
    a half-written file → JSONDecodeError."""

    def _write_plan(self, tmp_path: Path) -> float:
        p = tmp_path / "fake_plan.md"
        p.write_text("# Fake plan\n")
        return p.stat().st_mtime

    def test_writer_creates_valid_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tb_driver, "BRAIN_PATH", tmp_path)
        plan_mtime = self._write_plan(tmp_path)
        _record_audit_result(
            "fake_plan.md", plan_mtime, "ACCEPT",
            turns=3, duration_s=12, session_id="abc1234567890def",
        )
        results_path = tmp_path / "audit" / "results.json"
        data = json.loads(results_path.read_text())
        assert data["fake_plan.md"]["verdict"] == "ACCEPT"
        assert not (tmp_path / "audit" / "results.json.tmp").exists(), \
            "tmp file must be renamed away, not left behind"

    def test_concurrent_readers_never_see_partial_write(self, tmp_path, monkeypatch):
        """Hammer 4 readers in parallel while writer replaces 10 times.
        Pre-fix: readers occasionally hit JSONDecodeError on partial
        write_text. Post-fix: os.replace is atomic, readers always see
        a valid JSON file (or FileNotFoundError on the very first
        iteration before the file exists)."""
        import threading

        monkeypatch.setattr(tb_driver, "BRAIN_PATH", tmp_path)
        plan_mtime = self._write_plan(tmp_path)
        results_path = tmp_path / "audit" / "results.json"

        # Seed once so readers don't race the initial create.
        _record_audit_result(
            "fake_plan.md", plan_mtime, "ACCEPT",
            turns=1, duration_s=1, session_id="seed1234567890ab",
        )

        decode_errors: list = []
        stop = threading.Event()

        def reader():
            while not stop.is_set():
                try:
                    json.loads(results_path.read_text())
                except json.JSONDecodeError as e:
                    decode_errors.append(str(e))
                except FileNotFoundError:
                    pass

        readers = [threading.Thread(target=reader, daemon=True) for _ in range(4)]
        for t in readers:
            t.start()

        for i in range(10):
            _record_audit_result(
                f"plan_{i}.md", plan_mtime, "ACCEPT",
                turns=i, duration_s=i, session_id=f"sess{i:012d}xx",
            )

        stop.set()
        for t in readers:
            t.join(timeout=2)

        assert not decode_errors, (
            f"Atomic write contract violated — readers saw partial JSON "
            f"{len(decode_errors)} times: {decode_errors[:3]}"
        )
