"""Tests for the lever substrate contract.

Levers are modular operators that compound through the .brain/ ledger.
These tests exercise:
  - the Lever contract (ruff_chain concrete impl)
  - the manifest loader + dispatcher
  - the ledger-append contract (observation → events.jsonl)

The pattern here is the template for the other 30 shippable levers from
the 71-item blitz — if this contract is right, they all slot in the same way.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.levers import run_lever
from scripts.levers.base import (
    OUTCOMES,
    LedgerEvent,
    LedgerSchemaError,
    Lever,
    SubprocessFailure,
    iter_events,
)
from scripts.levers.ruff_chain import RuffChainLever
from scripts.levers.todo_chain import TodoChainLever


class TestRuffChainLever:
    def test_reports_clean_when_no_py_files_changed(self, tmp_path):
        lever = RuffChainLever()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            obs = lever.run({"inputs": {"diff_spec": "HEAD~1..HEAD"}}, tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["files_checked"] == 0

    def test_reports_clean_when_ruff_passes(self, tmp_path):
        lever = RuffChainLever()
        files_result = MagicMock(returncode=0, stdout="a.py\nb.py\n")
        ruff_result = MagicMock(returncode=0, stdout="")
        with patch("subprocess.run", side_effect=[files_result, ruff_result]):
            obs = lever.run({"inputs": {"diff_spec": "HEAD~1..HEAD"}}, tmp_path)
        assert obs["outcome"] == "clean"
        assert obs["detail"]["files_checked"] == 2

    def test_reports_findings_when_ruff_fails(self, tmp_path):
        lever = RuffChainLever()
        files_result = MagicMock(returncode=0, stdout="a.py\n")
        ruff_result = MagicMock(
            returncode=1,
            stdout="a.py:3:1: F401 [*] `os` imported but unused\n",
        )
        with patch("subprocess.run", side_effect=[files_result, ruff_result]):
            obs = lever.run({"inputs": {"diff_spec": "HEAD~1..HEAD"}}, tmp_path)
        assert obs["outcome"] == "found"
        assert obs["detail"]["files_checked"] == 1
        assert any("F401" in f for f in obs["detail"]["findings"])

    def test_reports_error_when_ruff_missing(self, tmp_path):
        lever = RuffChainLever()
        files_result = MagicMock(returncode=0, stdout="a.py\n")
        with patch("subprocess.run", side_effect=[files_result, FileNotFoundError()]):
            obs = lever.run({"inputs": {"diff_spec": "HEAD~1..HEAD"}}, tmp_path)
        assert obs["outcome"] == "error"
        assert "ruff" in obs["detail"]["error"].lower()


class TestTodoChainLever:
    def test_reports_clean_when_no_markers_in_diff(self, tmp_path):
        lever = TodoChainLever()
        diff_output = (
            "diff --git a/a.py b/a.py\n"
            "--- a/a.py\n+++ b/a.py\n"
            "@@ -1 +1 @@\n+def foo(): pass\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff_output)
            obs = lever.run({"inputs": {}}, tmp_path)
        assert obs["outcome"] == "clean"

    def test_detects_todo_and_fixme_in_added_lines(self, tmp_path):
        lever = TodoChainLever()
        diff_output = (
            "diff --git a/a.py b/a.py\n"
            "--- a/a.py\n+++ b/a.py\n"
            "@@ -1 +1,3 @@\n"
            "+def foo():\n"
            "+    # TODO: implement\n"
            "+    pass  # FIXME later\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff_output)
            obs = lever.run({"inputs": {}}, tmp_path)
        assert obs["outcome"] == "found"
        findings = obs["detail"]["findings"]
        assert len(findings) == 2
        assert any("TODO" in f for f in findings)
        assert any("FIXME" in f for f in findings)
        assert all(f.startswith("a.py:") for f in findings)

    def test_ignores_markers_already_in_code_not_added(self, tmp_path):
        """Only '+' lines count — existing markers in unchanged code are skipped."""
        lever = TodoChainLever()
        diff_output = (
            "diff --git a/a.py b/a.py\n"
            "--- a/a.py\n+++ b/a.py\n"
            "@@ -1,3 +1,3 @@\n"
            " # TODO: pre-existing\n"
            "-def old(): pass\n"
            "+def new(): pass\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff_output)
            obs = lever.run({"inputs": {}}, tmp_path)
        assert obs["outcome"] == "clean"

    def test_respects_max_findings_cap(self, tmp_path):
        lever = TodoChainLever()
        lines = ["diff --git a/a.py b/a.py", "--- a/a.py", "+++ b/a.py", "@@ -1 +1,6 @@"]
        lines.extend(f"+    # TODO: item {i}" for i in range(10))
        diff_output = "\n".join(lines) + "\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=diff_output)
            obs = lever.run({"inputs": {"max_findings": 3}}, tmp_path)
        assert obs["outcome"] == "found"
        assert len(obs["detail"]["findings"]) == 3

    def test_reports_error_when_git_fails(self, tmp_path):
        lever = TodoChainLever()
        with patch("subprocess.run", side_effect=FileNotFoundError("git missing")):
            obs = lever.run({"inputs": {}}, tmp_path)
        assert obs["outcome"] == "error"


class TestDispatcherAndLedgerContract:
    def test_append_observation_writes_valid_entry(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        entry = run_lever.append_observation(
            "ruff_chain",
            {"outcome": "clean", "detail": {"files_checked": 5}},
            ledger_path=ledger,
        )
        lines = ledger.read_text().strip().splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["type"] == "lever.ruff_chain.observation"
        assert parsed["lever"] == "ruff_chain"
        assert parsed["outcome"] == "clean"
        assert parsed["detail"]["files_checked"] == 5
        assert entry == parsed

    def test_disabled_manifest_skips_execution(self, tmp_path):
        manifests = tmp_path / "manifests"
        manifests.mkdir()
        (manifests / "ruff_chain.yaml").write_text(
            "name: ruff_chain\nenabled: false\n"
        )
        ledger = tmp_path / "events.jsonl"
        obs = run_lever.run("ruff_chain", manifests_dir=manifests, ledger_path=ledger)
        assert obs["outcome"] == "skipped"
        assert ledger.exists()
        parsed = json.loads(ledger.read_text().strip())
        assert parsed["outcome"] == "skipped"

    def test_missing_manifest_raises(self, tmp_path):
        manifests = tmp_path / "manifests"
        manifests.mkdir()
        with pytest.raises(FileNotFoundError):
            run_lever.run("nonexistent", manifests_dir=manifests)


class TestRunTrigger:
    """The post-executor auto-fire is what actually makes the gate fire.

    These tests cover manifest filtering by trigger, non-fatal lever
    failures, and missing directory handling.
    """

    def test_returns_empty_when_manifests_dir_missing(self, tmp_path):
        missing = tmp_path / "nope"
        assert run_lever.run_trigger("post_executor", manifests_dir=missing) == []

    def test_only_fires_levers_matching_trigger(self, tmp_path):
        manifests = tmp_path / "manifests"
        manifests.mkdir()
        # Match: post_executor trigger, enabled
        (manifests / "ruff_chain.yaml").write_text(
            "name: ruff_chain\nenabled: true\n"
            "triggers:\n  - post_executor\n  - manual\n"
        )
        # Mismatch: different trigger
        (manifests / "cron_lever.yaml").write_text(
            "name: cron_lever\nenabled: true\n"
            "triggers:\n  - cron\n"
        )
        # Mismatch: disabled
        (manifests / "off_lever.yaml").write_text(
            "name: off_lever\nenabled: false\n"
            "triggers:\n  - post_executor\n"
        )
        ledger = tmp_path / "events.jsonl"

        # Patch load_lever to return a lever that succeeds cheaply.
        class _FakeLever:
            name = "ruff_chain"

            def run(self, manifest, brain_path):
                return {"outcome": "clean", "detail": {"files_checked": 0}}

        with patch("scripts.levers.run_lever.load_lever", return_value=_FakeLever()):
            results = run_lever.run_trigger(
                "post_executor", manifests_dir=manifests, ledger_path=ledger
            )

        names = [r["lever"] for r in results]
        assert names == ["ruff_chain"]

    def test_lever_failure_is_non_fatal(self, tmp_path):
        manifests = tmp_path / "manifests"
        manifests.mkdir()
        (manifests / "broken.yaml").write_text(
            "name: broken\nenabled: true\n"
            "triggers:\n  - post_executor\n"
        )
        (manifests / "ruff_chain.yaml").write_text(
            "name: ruff_chain\nenabled: true\n"
            "triggers:\n  - post_executor\n"
        )
        ledger = tmp_path / "events.jsonl"

        class _FakeLever:
            name = "ruff_chain"

            def run(self, manifest, brain_path):
                return {"outcome": "clean", "detail": {}}

        def _loader(name):
            if name == "broken":
                raise RuntimeError("boom")
            return _FakeLever()

        with patch("scripts.levers.run_lever.load_lever", side_effect=_loader):
            results = run_lever.run_trigger(
                "post_executor", manifests_dir=manifests, ledger_path=ledger
            )

        # ruff_chain still ran, broken was caught.
        names = [r["lever"] for r in results]
        assert "ruff_chain" in names
        assert "broken" not in names

    def test_no_matching_trigger_returns_empty(self, tmp_path):
        manifests = tmp_path / "manifests"
        manifests.mkdir()
        (manifests / "only_cron.yaml").write_text(
            "name: only_cron\nenabled: true\n"
            "triggers:\n  - cron\n"
        )
        ledger = tmp_path / "events.jsonl"
        assert run_lever.run_trigger(
            "post_executor", manifests_dir=manifests, ledger_path=ledger
        ) == []


class TestLedgerEventSchema:
    """LedgerEvent is the typed contract. Schema errors must surface loudly."""

    def test_from_jsonl_accepts_valid_lever_observation(self):
        line = (
            '{"ts": "2026-04-12T00:00:00+00:00", "type": "lever.x.observation",'
            ' "lever": "x", "outcome": "clean", "detail": {"n": 0}}'
        )
        event = LedgerEvent.from_jsonl(line)
        assert event.type == "lever.x.observation"
        assert event.outcome == "clean"
        assert event.detail == {"n": 0}

    def test_from_jsonl_rejects_missing_ts(self):
        line = '{"type": "lever.x.observation", "outcome": "clean"}'
        with pytest.raises(LedgerSchemaError, match="ts"):
            LedgerEvent.from_jsonl(line)

    def test_from_jsonl_rejects_missing_type(self):
        line = '{"ts": "2026-04-12T00:00:00+00:00"}'
        with pytest.raises(LedgerSchemaError, match="type"):
            LedgerEvent.from_jsonl(line)

    def test_from_jsonl_rejects_invalid_outcome(self):
        line = (
            '{"ts": "2026-04-12T00:00:00+00:00", "type": "lever.x.observation",'
            ' "outcome": "whatever"}'
        )
        with pytest.raises(LedgerSchemaError, match="outcome"):
            LedgerEvent.from_jsonl(line)

    def test_from_jsonl_rejects_corrupt_json(self):
        with pytest.raises(LedgerSchemaError, match="JSON"):
            LedgerEvent.from_jsonl("{not json")

    def test_to_jsonl_round_trip(self):
        event = LedgerEvent(
            ts="2026-04-12T00:00:00+00:00",
            type="tb.review.decided",
            extra={"task_id": "t-1", "verdict": "ACCEPT"},
        )
        line = event.to_jsonl()
        parsed = LedgerEvent.from_jsonl(line)
        assert parsed.type == "tb.review.decided"
        assert parsed.extra["task_id"] == "t-1"

    def test_outcomes_frozenset_contents(self):
        assert OUTCOMES == frozenset({"clean", "found", "error", "skipped", "unknown"})

    def test_for_lever_observation_strips_control_chars(self):
        event = LedgerEvent.for_lever_observation(
            "my_lever",
            {"outcome": "found", "detail": {"msg": "bad\x00evil"}},
        )
        assert event.detail["msg"] == "badevil"


class TestAppendObservationContract:
    """append_observation validates + writes exactly one LedgerEvent line."""

    def test_append_observation_rejects_invalid_outcome(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        with pytest.raises(LedgerSchemaError, match="outcome"):
            run_lever.append_observation(
                "my_lever",
                {"outcome": "bogus", "detail": {}},
                ledger_path=ledger,
            )
        # Schema violation itself is recorded so the substrate sees the bug.
        assert ledger.exists()
        lines = ledger.read_text().strip().splitlines()
        assert any("lever.schema.violation" in line for line in lines)

    def test_append_observation_writes_valid_event(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        entry = run_lever.append_observation(
            "my_lever",
            {"outcome": "found", "detail": {"findings": ["x"]}},
            ledger_path=ledger,
        )
        assert entry["outcome"] == "found"
        line = ledger.read_text().strip().splitlines()[0]
        parsed = LedgerEvent.from_jsonl(line)
        assert parsed.lever == "my_lever"
        assert parsed.outcome == "found"


class TestDispatcherFailureEvents:
    """Dispatcher failures emit lever.dispatcher.failure — never silent swallow."""

    def test_failing_lever_emits_dispatcher_failure_event(self, tmp_path):
        manifests = tmp_path / "manifests"
        manifests.mkdir()
        (manifests / "explode.yaml").write_text(
            "name: explode\nenabled: true\ntriggers:\n  - post_executor\n"
        )
        ledger = tmp_path / "events.jsonl"

        def _loader(name):
            raise RuntimeError("boom")

        with patch("scripts.levers.run_lever.load_lever", side_effect=_loader):
            run_lever.run_trigger(
                "post_executor", manifests_dir=manifests, ledger_path=ledger
            )

        lines = ledger.read_text().strip().splitlines()
        assert any("lever.dispatcher.failure" in line for line in lines)
        # Failure event carries error_class for forensics.
        failure_event = next(
            json.loads(line) for line in lines
            if "lever.dispatcher.failure" in line
        )
        assert failure_event["detail"]["lever"] == "explode"
        assert failure_event["detail"]["error_class"] == "RuntimeError"

    def test_manifest_parse_error_writes_manifest_error_event(self, tmp_path):
        manifests = tmp_path / "manifests"
        manifests.mkdir()
        # Force a YAML parse error with an explicit syntax violation.
        (manifests / "bad.yaml").write_text("name: bad\n  - : : : [\n")
        ledger = tmp_path / "events.jsonl"

        run_lever.run_trigger(
            "post_executor", manifests_dir=manifests, ledger_path=ledger
        )

        lines = ledger.read_text().strip().splitlines() if ledger.exists() else []
        assert any("lever.manifest.error" in line for line in lines)


class TestIterEvents:
    """iter_events is the canonical reader path."""

    def test_iter_events_skips_corrupt_lines_by_default(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        ledger.write_text(
            '{"ts": "2026-04-12T00:00:00+00:00", "type": "a"}\n'
            '{not json\n'
            '{"ts": "2026-04-12T00:00:01+00:00", "type": "b"}\n'
        )
        events = list(iter_events(ledger))
        assert [e.type for e in events] == ["a", "b"]

    def test_iter_events_raises_on_corrupt_when_strict(self, tmp_path):
        ledger = tmp_path / "events.jsonl"
        ledger.write_text('{not json\n')
        with pytest.raises(LedgerSchemaError):
            list(iter_events(ledger, skip_invalid=False))

    def test_iter_events_returns_nothing_for_missing_ledger(self, tmp_path):
        assert list(iter_events(tmp_path / "nope.jsonl")) == []


class TestLeverBaseHelpers:
    """_run_subprocess contract: argv-only, named exceptions."""

    def test_run_subprocess_rejects_non_list_argv(self):
        with pytest.raises(TypeError):
            Lever._run_subprocess("git status", timeout=1, stage="test")

    def test_run_subprocess_throws_named_exception_on_nonzero(self):
        with pytest.raises(SubprocessFailure) as exc_info:
            Lever._run_subprocess(
                ["false"], timeout=2, stage="fail_test", check=True
            )
        assert exc_info.value.stage == "fail_test"
        assert exc_info.value.returncode != 0
