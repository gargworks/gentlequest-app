"""Tests for flywheel_capture_extractor — Wave 10 audit mode + regression.

Hermetic tests: each uses tmp_path to stand up a fake capture corpus,
fake .brain/audit/results.json, and fake brain/ledger. No disk I/O
outside tmp_path.

Coverage map:

    happy path           test_extracts_pair_from_audit_session_fixture
    marker filter        test_skips_non_audit_sessions_in_audit_kind
    verdict join primary test_joins_verdict_from_results_json_by_session_id
    verdict join fallback test_falls_back_to_audited_at_proximity_when_session_id_empty
    idempotency          test_idempotent_rerun_does_not_duplicate_pairs
    R7 malformed isolation test_malformed_session_does_not_halt_extraction
    R19 ambiguous verdict test_ambiguous_verdict_skips_session_with_reason
    R19 correction regression test_kind_correction_default_preserves_existing_behavior
"""

import json
import sys
import subprocess
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

import scripts.flywheel_capture_extractor as fce  # noqa: E402


# ─── fixture helpers ────────────────────────────────────────────────

def _write_session(
    captures_dir: Path,
    session_id: str,
    turns: list,
) -> Path:
    """Write a session JSONL to captures_dir/<project>/<session_id>.jsonl."""
    project = captures_dir / "-Users-test-project"
    project.mkdir(parents=True, exist_ok=True)
    path = project / f"{session_id}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for turn in turns:
            f.write(json.dumps(turn) + "\n")
    return path


def _audit_user_turn(title: str, filename: str, plan_text: str,
                     timestamp: str = "2026-04-13T10:00:00+00:00") -> dict:
    """Build a user turn carrying the STRUCTURED_AUDIT_TEMPLATE marker."""
    return {
        "type": "user",
        "timestamp": timestamp,
        "message": {
            "role": "user",
            "content": (
                f"## Plan Audit: {title}\n"
                f"Source: {filename}\n\n"
                f"### The Plan\n\n{plan_text}"
            ),
        },
    }


def _assistant_turn(text: str, timestamp: str = "2026-04-13T10:05:00+00:00") -> dict:
    return {
        "type": "assistant",
        "timestamp": timestamp,
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
        },
    }


def _tool_error_assistant_turn(timestamp: str = "2026-04-13T10:02:00+00:00") -> dict:
    return {
        "type": "assistant",
        "timestamp": timestamp,
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": "Let me run the tests."}],
        },
    }


def _tool_error_result_turn(timestamp: str = "2026-04-13T10:03:00+00:00") -> dict:
    return {
        "type": "user",
        "timestamp": timestamp,
        "message": {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "is_error": True,
                    "content": "Traceback: ModuleNotFoundError",
                }
            ],
        },
    }


def _run_main(captures: Path, brain: Path, kind: str = "correction",
              dry_run: bool = False, limit: int | None = None) -> dict:
    """Invoke main() via subprocess so argparse/stdout work naturally.
    Returns the parsed summary JSON."""
    cmd = [
        sys.executable,
        str(_REPO / "scripts" / "flywheel_capture_extractor.py"),
        "--captures", str(captures),
        "--brain-path", str(brain),
        "--kind", kind,
    ]
    if dry_run:
        cmd.append("--dry-run")
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def _write_results_json(brain: Path, entries: dict) -> Path:
    path = brain / "audit" / "results.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def _read_pairs(brain: Path) -> list:
    out = brain / "training" / "exports" / "unified_dpo_pending.jsonl"
    if not out.exists():
        return []
    return [json.loads(line) for line in out.read_text().splitlines() if line.strip()]


# ─── tests ──────────────────────────────────────────────────────────

def test_extracts_pair_from_audit_session_fixture(tmp_path):
    """Happy path: marker-carrying session + results.json join by session_id
    → one audit_dpo pair with reasoning from assistant turns, verdict from
    results entry."""
    captures = tmp_path / "captures"
    brain = tmp_path / "brain"
    sid = "aaaa-bbbb-cccc"

    _write_session(captures, sid, [
        _audit_user_turn("My Plan", "plan_x.md", "## Files Modified\n- a.py"),
        _assistant_turn("I will check a.py. It has the function."),
        _assistant_turn("Verdict: ACCEPT — the plan is implemented."),
    ])
    _write_results_json(brain, {
        "plan_x.md": {
            "session_id": sid,
            "verdict": "ACCEPT",
            "audited_at": "2026-04-13T10:00:30+00:00",
            "verification_quality": "strong",
        }
    })

    summary = _run_main(captures, brain, kind="audit")

    assert summary["pairs_extracted"] == 1
    pairs = _read_pairs(brain)
    assert len(pairs) == 1
    p = pairs[0]
    assert p["kind"] == "audit_dpo"
    assert p["source"] == "capture_extractor"
    assert p["session_id"] == sid
    assert p["quality"] == "ready"
    assert p["plan_name"] == "plan_x.md"
    assert p["verdict"] == "ACCEPT"
    assert p["audited_at"] == "2026-04-13T10:00:30+00:00"
    assert "I will check a.py" in p["chosen"]
    assert "Verdict: ACCEPT" in p["chosen"]
    assert "## Plan Audit: My Plan" in p["prompt"]
    assert p["rejected"] == ""


def test_skips_non_audit_sessions_in_audit_kind(tmp_path):
    """Session without the marker is skipped in audit mode."""
    captures = tmp_path / "captures"
    brain = tmp_path / "brain"
    sid = "no-marker-sid"

    _write_session(captures, sid, [
        {
            "type": "user", "timestamp": "2026-04-13T10:00:00+00:00",
            "message": {"role": "user", "content": "Refactor the chat module."},
        },
        _assistant_turn("OK, let me look."),
    ])

    summary = _run_main(captures, brain, kind="audit")

    assert summary["pairs_extracted"] == 0
    # Non-audit sessions are fast-path-skipped and never counted as processed.
    assert summary["sessions_processed"] == 0
    assert _read_pairs(brain) == []


def test_joins_verdict_from_results_json_by_session_id(tmp_path):
    """Primary join: exact session_id match beats proximity candidates."""
    captures = tmp_path / "captures"
    brain = tmp_path / "brain"
    sid = "primary-join-sid"

    _write_session(captures, sid, [
        _audit_user_turn("P", "plan_p.md", "## Files Modified\n- x.py",
                         timestamp="2026-04-13T12:00:00+00:00"),
        _assistant_turn("Reasoning here for plan P"),
    ])
    # Two candidates for plan_p.md. One has matching session_id; the other
    # is close in time with empty session_id. Primary MUST win.
    _write_results_json(brain, {
        "plan_p.md": {
            "session_id": sid,
            "verdict": "ACCEPT",
            "audited_at": "2026-04-13T11:00:00+00:00",  # 1h away from turn
            "verification_quality": "weak",
        },
        "plan_p.md#dup": {  # distinct key, same filename — matches on "plan_name"
            "session_id": "",
            "verdict": "REJECT",
            "audited_at": "2026-04-13T12:00:00+00:00",  # exact match
        },
    })

    _run_main(captures, brain, kind="audit")
    pairs = _read_pairs(brain)

    assert len(pairs) == 1
    assert pairs[0]["verdict"] == "ACCEPT"  # primary won, not REJECT


def test_falls_back_to_audited_at_proximity_when_session_id_empty(tmp_path):
    """Fallback: when results entry has empty session_id, match by
    plan_name + audited_at within ±10min of first-turn timestamp."""
    captures = tmp_path / "captures"
    brain = tmp_path / "brain"
    sid = "proximity-sid"

    _write_session(captures, sid, [
        _audit_user_turn("P", "plan_q.md", "## Files Modified\n- y.py",
                         timestamp="2026-04-13T14:00:00+00:00"),
        _assistant_turn("Reasoning for plan Q"),
    ])
    _write_results_json(brain, {
        "plan_q.md": {
            "session_id": "",   # empty → primary can't match
            "verdict": "DEEPEN",
            "audited_at": "2026-04-13T14:05:00+00:00",  # 5min away < 10min
        },
    })

    _run_main(captures, brain, kind="audit")
    pairs = _read_pairs(brain)

    assert len(pairs) == 1
    assert pairs[0]["verdict"] == "DEEPEN"


def test_idempotent_rerun_does_not_duplicate_pairs(tmp_path):
    """Second run with same ledger produces zero new pairs."""
    captures = tmp_path / "captures"
    brain = tmp_path / "brain"
    sid = "idem-sid"

    _write_session(captures, sid, [
        _audit_user_turn("T", "plan_t.md", "plan", timestamp="2026-04-13T09:00:00+00:00"),
        _assistant_turn("reasoning"),
    ])
    _write_results_json(brain, {
        "plan_t.md": {"session_id": sid, "verdict": "ACCEPT",
                      "audited_at": "2026-04-13T09:00:00+00:00"},
    })

    first = _run_main(captures, brain, kind="audit")
    second = _run_main(captures, brain, kind="audit")

    assert first["pairs_extracted"] == 1
    assert second["pairs_extracted"] == 0
    assert second["sessions_skipped"] == 1
    assert len(_read_pairs(brain)) == 1  # only the first run's pair


def test_malformed_session_does_not_halt_extraction(tmp_path):
    """R7: a truncated/malformed session in a directory of 3 → other 2
    sessions still produce pairs."""
    captures = tmp_path / "captures"
    brain = tmp_path / "brain"

    _write_session(captures, "ok-1", [
        _audit_user_turn("A", "plan_a.md", "pa", timestamp="2026-04-13T01:00:00+00:00"),
        _assistant_turn("ra"),
    ])
    # Hand-write a truncated JSONL: half a line, no newline.
    proj = captures / "-Users-test-project"
    (proj / "bad-2.jsonl").write_text('{"type": "user", "timestam')
    _write_session(captures, "ok-3", [
        _audit_user_turn("C", "plan_c.md", "pc", timestamp="2026-04-13T01:00:00+00:00"),
        _assistant_turn("rc"),
    ])
    _write_results_json(brain, {
        "plan_a.md": {"session_id": "ok-1", "verdict": "ACCEPT",
                      "audited_at": "2026-04-13T01:00:00+00:00"},
        "plan_c.md": {"session_id": "ok-3", "verdict": "DEEPEN",
                      "audited_at": "2026-04-13T01:00:00+00:00"},
    })

    summary = _run_main(captures, brain, kind="audit")

    # Malformed session is filtered by fast-path (no valid first user turn),
    # so it doesn't appear in sessions_processed but also doesn't crash.
    assert summary["pairs_extracted"] == 2
    pairs = _read_pairs(brain)
    verdicts = sorted(p["verdict"] for p in pairs)
    assert verdicts == ["ACCEPT", "DEEPEN"]


def test_ambiguous_verdict_skips_session_with_reason(tmp_path):
    """R19: ≥2 results.json candidates inside the ±10min proximity
    window → skip with skip_reason=ambiguous_verdict (no pair emitted)."""
    captures = tmp_path / "captures"
    brain = tmp_path / "brain"
    sid = "amb-sid"

    _write_session(captures, sid, [
        _audit_user_turn("P", "plan_z.md", "plan text",
                         timestamp="2026-04-13T15:00:00+00:00"),
        _assistant_turn("reasoning"),
    ])
    # Two entries for plan_z.md under distinct dict keys, both carrying
    # plan_name="plan_z.md" in the entry body; both empty session_id
    # (forces fallback); both within ±10min of 15:00:00. Exercises the
    # defensive ambiguous_verdict branch that protects against a future
    # schema where multiple results entries may reference the same plan.
    _write_results_json(brain, {
        "plan_z.md": {
            "plan_name": "plan_z.md",
            "session_id": "",
            "verdict": "ACCEPT",
            "audited_at": "2026-04-13T14:58:00+00:00",
        },
        "plan_z.md#v2": {
            "plan_name": "plan_z.md",
            "session_id": "",
            "verdict": "REJECT",
            "audited_at": "2026-04-13T15:03:00+00:00",
        },
    })

    summary = _run_main(captures, brain, kind="audit")

    assert summary["pairs_extracted"] == 0
    assert summary["skip_reasons"].get("ambiguous_verdict") == 1
    assert _read_pairs(brain) == []


def test_kind_correction_default_preserves_existing_behavior(tmp_path):
    """R19 regression: adding --kind must not change correction-mode
    extraction. Fixture with a tool-error turn produces a
    kind=tool_error pair under default (correction) mode."""
    captures = tmp_path / "captures"
    brain = tmp_path / "brain"
    sid = "corr-sid"

    _write_session(captures, sid, [
        {
            "type": "user", "timestamp": "2026-04-13T08:00:00+00:00",
            "message": {"role": "user", "content": "Please run the tests."},
        },
        _tool_error_assistant_turn(),
        _tool_error_result_turn(),
    ])

    summary = _run_main(captures, brain, kind="correction")
    pairs = _read_pairs(brain)

    assert summary["pairs_extracted"] >= 1
    assert any(p["kind"] == "tool_error" for p in pairs)
    # No audit_dpo pairs should ever appear in correction mode.
    assert not any(p["kind"] == "audit_dpo" for p in pairs)
