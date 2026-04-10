"""
Integration / e2e tests for Frontier 4: FLYWHEEL
=================================================

These tests exercise the flywheel across multiple components at once — where
the hermetic tests in `test_flywheel.py` isolate each module, these drive the
full compound loop end-to-end against a real tmp brain path:

    driver hooks → file_ticket / record_survived
                 → CSR file on disk
                 → pending_issues.jsonl
                 → unified_dpo_pending.jsonl
                 → curriculum_refresh
                 → unified_dpo_ready.jsonl
                 → dashboard JSON reflects the new state

Two tests cover the two compound-loop surfaces called out in the plan (§1.13):

    test_driver_e2e_mixed_phases
        A fake driver run with Phase A success + Phase D failure. Asserts
        tickets filed, CSR moves, dashboard.json reflects the state.

    test_curriculum_loop_end_to_end
        Seeds a failure via file_ticket, later records a survived claim for
        the same step, runs curriculum_refresh, asserts a DPO pair is
        promoted to ready with the expected shape.

Both tests are hermetic — tmp_path per test, no network, no gh CLI — but they
compose multiple modules so a regression in any single boundary gets caught.
"""

import json
import sys
from pathlib import Path

import pytest

# Make the in-repo flywheel package + driver importable.
_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "mcp-server-nucleus" / "src"))
sys.path.insert(0, str(_REPO / "scripts"))

from mcp_server_nucleus.flywheel import (  # noqa: E402
    Flywheel,
    curriculum_refresh,
    read_csr,
    render_dashboard_json,
)


# ---------------------------------------------------------------------------
# E2E 1: fake driver run across Phase A..D
# ---------------------------------------------------------------------------


def test_driver_e2e_mixed_phases(tmp_path, monkeypatch):
    """
    Fake driver harness: Phase A + B + C survive, Phase D fails.

    The driver _fw_* helpers target BRAIN_PATH, so we monkeypatch that to a
    tmp dir and drive them directly. After the run we assert:

      * CSR total reflects founding claim (1) + 4 new claims (A/B/C survived,
        D unsurvived) → 5 total / 4 survived / ratio 0.8
      * pending_issues.jsonl contains exactly one entry — the phase D failure
      * unified_dpo_pending.jsonl contains the same failure as a DPO pair
      * pending_tasks.jsonl contains the phase D task at founder-escalation
      * render_dashboard_json sees the same state (this is how the MCP
        resource surface reads it, so the assertion doubles as a resource
        contract check)
    """
    import third_brother_driver as d
    monkeypatch.setattr(d, "BRAIN_PATH", tmp_path)
    config = {"flywheel_accountability_enabled": True}
    task_id = "e2e_task_001"

    # Phase A — classify succeeds.
    d._fw_record_survived("phase_a_classify", task_id, config)
    # Phase B — scout succeeds.
    d._fw_record_survived("phase_b_scout", task_id, config)
    # Phase C — prompt writer succeeds.
    d._fw_record_survived("phase_c_prompt_writer", task_id, config)
    # Phase D — reviewer crashes.
    d._fw_file_ticket(
        "phase_d_reviewer",
        task_id,
        error="reviewer timed out after 600s",
        config=config,
        logs="ollama: connection reset\nretry 1 failed\nretry 2 failed",
    )

    # ── CSR should reflect 4 new claims on top of the founding claim.
    csr = read_csr(tmp_path)
    assert csr["claims_total"] == 5, csr
    assert csr["claims_survived"] == 4
    assert csr["claims_unsurvived"] == 1
    assert csr["ratio"] == 0.8

    # ── The failure surfaces on three best-effort sinks.
    issues = tmp_path / "flywheel" / "pending_issues.jsonl"
    assert issues.exists()
    issue_lines = [json.loads(l) for l in issues.read_text().splitlines() if l.strip()]
    assert len(issue_lines) == 1
    assert issue_lines[0]["step"] == task_id
    assert issue_lines[0]["phase"] == "phase_d_reviewer"
    assert "timed out" in issue_lines[0]["error"]

    pairs = tmp_path / "training" / "exports" / "unified_dpo_pending.jsonl"
    assert pairs.exists()
    pair_lines = [json.loads(l) for l in pairs.read_text().splitlines() if l.strip()]
    assert len(pair_lines) == 1
    assert task_id in pair_lines[0]["prompt"]
    assert "phase_d_reviewer" in pair_lines[0]["prompt"]
    assert "timed out" in pair_lines[0]["rejected"]
    assert pair_lines[0]["chosen"] == ""  # curriculum_refresh fills later

    tasks = tmp_path / "flywheel" / "pending_tasks.jsonl"
    assert tasks.exists()
    task_entry = json.loads(tasks.read_text().splitlines()[0])
    assert task_id in task_entry["title"]
    assert task_entry["priority"] == "founder-escalation"

    # ── Dashboard JSON sees the same state (this is the MCP resource contract).
    dash = render_dashboard_json(tmp_path)
    assert dash["csr"]["claims_total"] == 5
    assert dash["csr"]["ratio"] == 0.8
    assert dash["tickets"]["open"] == 1
    assert dash["tasks"]["open"] == 1
    assert dash["curriculum"]["pending_pairs"] == 1
    # The last recent claim in the dashboard reflects the Phase D failure.
    recent_steps = [c.get("step", "") for c in dash["recent_claims"]]
    assert any(task_id in s for s in recent_steps)
    assert any(not c.get("survived") for c in dash["recent_claims"])


# ---------------------------------------------------------------------------
# E2E 2: full compound loop (ticket → survived → curriculum promotion)
# ---------------------------------------------------------------------------


def test_curriculum_loop_end_to_end(tmp_path):
    """
    Seed a failure, later record the matching survived claim, run the
    curriculum refresh. The pair should promote from pending → ready with
    chosen filled in and quality flipped to "curriculum".

    This is the full compound loop: every failure becomes training data if
    (and only if) the system later demonstrates the same step can survive.
    """
    fw = Flywheel(tmp_path)
    step = "phase_a_classify_compound"

    # Step 1: a real failure gets the 6-action treatment.
    fw.file_ticket(step=step, error="classifier returned None", phase="phase_a")

    # Sanity: pending pair seeded, nothing promoted yet.
    pending = tmp_path / "training" / "exports" / "unified_dpo_pending.jsonl"
    ready = tmp_path / "training" / "exports" / "unified_dpo_ready.jsonl"
    assert pending.exists()
    assert not ready.exists() or ready.read_text().strip() == ""

    # Step 2: a later run of the same step survives — e.g. a retry worked,
    # or a fix landed and the next task classified fine.
    fw.record_survived(phase="phase_a", step=step)

    # Step 3: refresh the curriculum — the pending pair should now promote
    # because its step shows up in recent_claims as survived.
    result = curriculum_refresh(tmp_path)
    assert result["scanned"] == 1
    assert result["ready"] == 1
    assert result["still_pending"] == 0

    # Ready file exists, pending file is now empty.
    assert ready.exists()
    promoted = [json.loads(l) for l in ready.read_text().splitlines() if l.strip()]
    assert len(promoted) == 1
    assert promoted[0]["quality"] == "curriculum"
    assert promoted[0]["chosen"], "chosen must be filled in on promotion"
    assert step in promoted[0]["chosen"]
    assert "promoted_at" in promoted[0]
    # The rejected side (original error) is preserved.
    assert "classifier returned None" in promoted[0]["rejected"]

    assert pending.read_text().strip() == ""

    # Dashboard should show 0 pending now (the pair moved to ready).
    dash = render_dashboard_json(tmp_path)
    assert dash["curriculum"]["pending_pairs"] == 0
    # CSR shows 1 survived + 1 unsurvived + founding claim = 3 total, 2 survived.
    assert dash["csr"]["claims_total"] == 3
    assert dash["csr"]["claims_survived"] == 2
    assert dash["csr"]["claims_unsurvived"] == 1
