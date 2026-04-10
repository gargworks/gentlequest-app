"""
Tests for Frontier 4: FLYWHEEL — the compounding loop engine.
==============================================================

Hermetic tests for `mcp_server_nucleus.flywheel` and the driver hook
helpers. Each test runs in its own tmp_path so the founding claim,
ticket queues, and curriculum exports stay isolated from one another.

Coverage:
  TestCSR              — counter state, bumps, recent_claims cap
  TestFileTicket       — 6-action accountability fan-out
  TestDashboard        — JSON + HTML rendering
  TestWeekReport       — markdown report generation
  TestCurriculum       — pending → ready promotion
  TestDriverHooks      — _fw_record_survived / _fw_file_ticket
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Make the in-repo flywheel package importable.
_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "mcp-server-nucleus" / "src"))
sys.path.insert(0, str(_REPO / "scripts"))

from mcp_server_nucleus.flywheel import (  # noqa: E402
    Flywheel,
    bump_survived,
    bump_unsurvived,
    curriculum_refresh,
    generate_week_report,
    read_csr,
    render_dashboard_html,
    render_dashboard_json,
)


# ---------------------------------------------------------------------------
# CSR counter
# ---------------------------------------------------------------------------

class TestCSR:
    def test_first_read_writes_founding_claim(self, tmp_path):
        """A fresh brain dir gets a founding claim of 1/1 → ratio 1.0."""
        state = read_csr(tmp_path)
        assert state["claims_total"] == 1
        assert state["claims_survived"] == 1
        assert state["ratio"] == 1.0
        assert "first_claim_at" in state
        # And the file got persisted to disk on first read.
        assert (tmp_path / "flywheel" / "csr.json").exists()

    def test_bump_survived_keeps_ratio_at_one(self, tmp_path):
        """Survived bumps move both numerator and denominator → ratio stays 1.0."""
        read_csr(tmp_path)  # founding claim
        state = bump_survived(tmp_path, step="phase_a:task_001")
        assert state["claims_total"] == 2
        assert state["claims_survived"] == 2
        assert state["ratio"] == 1.0
        assert state["recent_claims"][-1]["survived"] is True
        assert state["recent_claims"][-1]["step"] == "phase_a:task_001"

    def test_bump_unsurvived_drops_ratio(self, tmp_path):
        """Unsurvived bump moves only the denominator → ratio drops."""
        read_csr(tmp_path)
        bump_unsurvived(tmp_path, step="phase_d:task_002", reason="reviewer crashed")
        state = read_csr(tmp_path)
        assert state["claims_total"] == 2
        assert state["claims_survived"] == 1
        assert state["ratio"] == 0.5

    def test_recent_claims_caps_at_50(self, tmp_path):
        """recent_claims is bounded — never grows past 50 entries."""
        read_csr(tmp_path)
        for i in range(75):
            bump_survived(tmp_path, step=f"phase_a:task_{i:03d}")
        state = read_csr(tmp_path)
        assert state["claims_total"] == 76  # founding + 75 bumps
        assert len(state["recent_claims"]) == 50
        # The most recent ones win — last entry should be task_074.
        assert state["recent_claims"][-1]["step"] == "phase_a:task_074"


# ---------------------------------------------------------------------------
# file_ticket: 6 accountability actions
# ---------------------------------------------------------------------------

class TestFileTicket:
    def _ticket(self, tmp_path):
        fw = Flywheel(tmp_path)
        return fw.file_ticket(
            step="phase_a_classify",
            error="boom",
            logs="traceback line 1\ntraceback line 2",
            phase="phase_a",
        )

    def test_action_1_memory_note(self, tmp_path):
        """Action 1: memory note appended to pending_issues.jsonl."""
        self._ticket(tmp_path)
        path = tmp_path / "flywheel" / "pending_issues.jsonl"
        assert path.exists()
        lines = path.read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["step"] == "phase_a_classify"
        assert entry["error"] == "boom"
        assert "at" in entry
        assert entry["ticket_id"].startswith("fw-")

    def test_action_2_csr_unsurvived(self, tmp_path):
        """Action 2: ticketing fires a CSR unsurvived bump."""
        self._ticket(tmp_path)
        csr = read_csr(tmp_path)
        # Founding claim (1/1) + ticket bump (0/1) → 1/2 = 0.5
        assert csr["claims_total"] == 2
        assert csr["claims_survived"] == 1
        assert csr["ratio"] == 0.5

    def test_action_3_training_pair_seeded(self, tmp_path):
        """Action 3: pending DPO pair appears in unified_dpo_pending.jsonl."""
        self._ticket(tmp_path)
        path = tmp_path / "training" / "exports" / "unified_dpo_pending.jsonl"
        assert path.exists()
        pair = json.loads(path.read_text().strip().splitlines()[0])
        assert pair["quality"] == "pending"
        # Step is encoded into the prompt field as "Step: <step>\nPhase: <phase>"
        assert "phase_a_classify" in pair["prompt"]
        assert "boom" in pair["rejected"]
        assert pair["chosen"] == ""  # curriculum_refresh fills this later

    def test_action_4_week_report_appended(self, tmp_path):
        """Action 4: ticket noted in the current week file."""
        self._ticket(tmp_path)
        # Week file glob — name varies (week-N.md)
        files = list((tmp_path / "flywheel").glob("week-*.md"))
        assert files, "expected at least one week-N.md file"
        text = files[0].read_text()
        assert "phase_a_classify" in text
        assert "boom" in text

    def test_action_5_github_issue_queue_or_real(self, tmp_path):
        """Action 5: GH issue either fires via gh CLI or falls back to queue."""
        result = self._ticket(tmp_path)
        # In hermetic CI we don't have gh auth or even network — fallback expected.
        queue_path = tmp_path / "flywheel" / "gh_issue_queue.jsonl"
        gh_status = result.get("gh_issue", {}).get("status", "unknown")
        # Either the queue exists OR the real path succeeded — both are valid.
        assert queue_path.exists() or gh_status == "created"

    def test_action_6_task_register(self, tmp_path):
        """Action 6: founder escalation row appended to pending_tasks.jsonl."""
        self._ticket(tmp_path)
        path = tmp_path / "flywheel" / "pending_tasks.jsonl"
        assert path.exists()
        entry = json.loads(path.read_text().strip().splitlines()[0])
        # Step is encoded into the title: "[flywheel] {step}: {error[:60]}"
        assert "phase_a_classify" in entry["title"]
        assert entry.get("priority") == "founder-escalation"
        assert entry.get("status") == "open"


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class TestDashboard:
    def test_render_json_shape(self, tmp_path):
        """JSON dashboard exposes csr, tickets, tasks, curriculum, recent_claims."""
        Flywheel(tmp_path).file_ticket(step="phase_b_scout", error="net down")
        snapshot = render_dashboard_json(tmp_path)
        assert "csr" in snapshot
        assert "tickets" in snapshot
        assert "tasks" in snapshot
        assert "curriculum" in snapshot
        assert "recent_claims" in snapshot
        assert snapshot["tickets"]["open"] == 1

    def test_render_html_is_self_contained(self, tmp_path):
        """HTML dashboard renders without external CDN refs (mentor.md rule)."""
        Flywheel(tmp_path).record_survived(phase="phase_a", step="t1")
        html = render_dashboard_html(tmp_path)
        assert html.lstrip().startswith("<!DOCTYPE html>")
        assert "</html>" in html
        # No CDN: must not import any http(s) asset.
        assert "https://cdn." not in html
        assert "<script src=\"https://" not in html
        # Inline CSS expected.
        assert "<style>" in html


# ---------------------------------------------------------------------------
# Weekly report
# ---------------------------------------------------------------------------

class TestWeekReport:
    def test_writes_week_file(self, tmp_path):
        """generate_week_report writes a week-N.md and returns its path."""
        Flywheel(tmp_path).record_survived(phase="phase_a", step="t1")
        out = generate_week_report(tmp_path)
        assert out.exists()
        assert out.name.startswith("week-")
        assert out.suffix == ".md"

    def test_report_contains_csr_block(self, tmp_path):
        """Week file includes the CSR scalar so the founder can read at a glance."""
        Flywheel(tmp_path).file_ticket(step="phase_d", error="bad review")
        out = generate_week_report(tmp_path)
        text = out.read_text()
        assert "CSR" in text or "Claim Survival" in text
        assert "phase_d" in text


# ---------------------------------------------------------------------------
# Curriculum refresh
# ---------------------------------------------------------------------------

class TestCurriculum:
    def _seed_pending(self, tmp_path, step="phase_a_classify"):
        """Drop a single pending DPO pair into the unified pending file.

        Shape must match what file_ticket() writes so curriculum_refresh can
        recover the step key from the prompt field.
        """
        path = tmp_path / "training" / "exports" / "unified_dpo_pending.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        pair = {
            "source": "flywheel_ticket",
            "quality": "pending",
            "prompt": f"Step: {step}\nPhase: phase_a",
            "rejected": "I broke it",
            "chosen": "",
            "ticket_id": "fw-test",
            "at": "2026-04-10T00:00:00Z",
        }
        path.write_text(json.dumps(pair) + "\n")
        return path

    def test_promotes_survived_steps(self, tmp_path):
        """Pending pair whose step survived later gets promoted to ready."""
        self._seed_pending(tmp_path, step="phase_a_classify")
        # Mark phase_a_classify survived after the failure.
        # Curriculum lookup uses the step key extracted from the pair's prompt
        # (first line), so write the step as the survived claim step.
        bump_survived(tmp_path, step="phase_a_classify")
        result = curriculum_refresh(tmp_path)
        assert result["ready"] == 1
        ready_path = tmp_path / "training" / "exports" / "unified_dpo_ready.jsonl"
        assert ready_path.exists()
        promoted = json.loads(ready_path.read_text().strip().splitlines()[0])
        assert promoted["quality"] == "curriculum"
        assert "promoted_at" in promoted

    def test_idempotent_when_no_survivors(self, tmp_path):
        """Pair stays pending if its step never survived — no promotion."""
        self._seed_pending(tmp_path, step="phase_b_scout")
        result = curriculum_refresh(tmp_path)
        assert result["ready"] == 0
        assert result["still_pending"] == 1
        ready_path = tmp_path / "training" / "exports" / "unified_dpo_ready.jsonl"
        assert not ready_path.exists() or ready_path.read_text().strip() == ""

    def test_handles_missing_pending_file(self, tmp_path):
        """Missing pending file is a no-op, not a crash."""
        result = curriculum_refresh(tmp_path)
        assert result["scanned"] == 0
        assert result["ready"] == 0


# ---------------------------------------------------------------------------
# Driver hook helpers
# ---------------------------------------------------------------------------

class TestDriverHooks:
    """Verify the driver's _fw_* helpers obey the feature flag and route correctly."""

    def test_disabled_flag_is_a_no_op(self, tmp_path, monkeypatch):
        """When flywheel_accountability_enabled=False the helpers do nothing."""
        import third_brother_driver as d
        monkeypatch.setattr(d, "BRAIN_PATH", tmp_path)
        d._fw_record_survived("phase_a", "task_x", {"flywheel_accountability_enabled": False})
        d._fw_file_ticket("phase_a", "task_x", "boom",
                          {"flywheel_accountability_enabled": False})
        # No flywheel directory was created → helpers respected the flag.
        assert not (tmp_path / "flywheel").exists()

    def test_enabled_flag_writes_to_brain_path(self, tmp_path, monkeypatch):
        """With the flag on, hooks land in the brain path's flywheel/ dir."""
        import third_brother_driver as d
        monkeypatch.setattr(d, "BRAIN_PATH", tmp_path)
        d._fw_record_survived("phase_a", "task_y", {"flywheel_accountability_enabled": True})
        csr_path = tmp_path / "flywheel" / "csr.json"
        assert csr_path.exists()
        state = json.loads(csr_path.read_text())
        # Founding claim + 1 survived bump.
        assert state["claims_total"] == 2
        assert state["claims_survived"] == 2
