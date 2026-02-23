"""Tests for V3.1 Checkpoint & Handoff Operations on UnifiedOrchestrator."""

import time
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from mcp_server_nucleus.runtime.orchestrator_unified import UnifiedOrchestrator


@pytest.fixture
def orch(tmp_path):
    """Create a fresh UnifiedOrchestrator with a temp brain path."""
    with patch("mcp_server_nucleus.runtime.orchestrator_unified.DirectivesLoader") as mock_dl, \
         patch("mcp_server_nucleus.runtime.orchestrator_unified.ContextFactory") as mock_cf:
        mock_dl.return_value = MagicMock()
        mock_cf.return_value = MagicMock()
        return UnifiedOrchestrator(brain_path=tmp_path)


@pytest.fixture
def task_with_checkpoint(orch):
    """Create a task and checkpoint it."""
    result = orch.add_task("Phase 5 outreach", priority=1, tier="T1_STRATEGY")
    task_id = result["task"]["id"]
    orch.checkpoint_task(task_id, {"step": 3, "progress_percent": 60, "context": "Drafting Reddit posts"})
    return task_id


class TestCheckpointTask:
    def test_checkpoint_success(self, orch):
        result = orch.add_task("Test checkpoint", priority=2)
        task_id = result["task"]["id"]

        cp_result = orch.checkpoint_task(task_id, {"step": 1, "progress_percent": 25})

        assert cp_result["success"] is True
        assert cp_result["checkpoint"]["enabled"] is True
        assert cp_result["checkpoint"]["data"]["step"] == 1
        assert cp_result["checkpoint"]["data"]["progress_percent"] == 25
        assert "last_checkpoint_at" in cp_result["checkpoint"]

    def test_checkpoint_not_found(self, orch):
        result = orch.checkpoint_task("nonexistent_task", {"step": 1})
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_checkpoint_overwrites_previous(self, orch):
        result = orch.add_task("Overwrite test", priority=2)
        task_id = result["task"]["id"]

        orch.checkpoint_task(task_id, {"step": 1})
        cp2 = orch.checkpoint_task(task_id, {"step": 5, "progress_percent": 90})

        assert cp2["checkpoint"]["data"]["step"] == 5
        assert cp2["checkpoint"]["data"]["progress_percent"] == 90


class TestResumeFromCheckpoint:
    def test_resume_success(self, task_with_checkpoint, orch):
        result = orch.resume_from_checkpoint(task_with_checkpoint)

        assert result["success"] is True
        assert result["task_id"] == task_with_checkpoint
        assert result["checkpoint"]["data"]["step"] == 3
        assert result["checkpoint"]["data"]["progress_percent"] == 60
        assert "Resume from step 3" in result["resume_instructions"]

    def test_resume_not_found(self, orch):
        result = orch.resume_from_checkpoint("nonexistent_task")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_resume_no_checkpoint(self, orch):
        result = orch.add_task("No checkpoint task", priority=2)
        task_id = result["task"]["id"]

        result = orch.resume_from_checkpoint(task_id)
        assert result["success"] is False
        assert "No checkpoint found" in result["error"]


class TestGenerateContextSummary:
    def test_summary_success(self, orch):
        result = orch.add_task("Summary test", priority=2)
        task_id = result["task"]["id"]

        summary_result = orch.generate_context_summary(
            task_id,
            summary="Completed 3 of 5 outreach posts",
            key_decisions=["Use lowercase tone", "No direct links"],
            handoff_notes="Next agent should post to r/LocalLLaMA first"
        )

        assert summary_result["success"] is True
        cs = summary_result["context_summary"]
        assert cs["summary"] == "Completed 3 of 5 outreach posts"
        assert len(cs["key_decisions"]) == 2
        assert cs["handoff_notes"] == "Next agent should post to r/LocalLLaMA first"
        assert "generated_at" in cs

    def test_summary_not_found(self, orch):
        result = orch.generate_context_summary("nonexistent", "test")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_summary_defaults(self, orch):
        result = orch.add_task("Defaults test", priority=2)
        task_id = result["task"]["id"]

        summary_result = orch.generate_context_summary(task_id, "Minimal summary")

        cs = summary_result["context_summary"]
        assert cs["key_decisions"] == []
        assert cs["handoff_notes"] == ""


class TestCheckpointResumeRoundtrip:
    def test_full_cycle(self, orch):
        """Create → Checkpoint → Summary → Resume: full roundtrip."""
        # Create
        result = orch.add_task("Roundtrip test", priority=1, tier="T1_STRATEGY")
        task_id = result["task"]["id"]

        # Checkpoint
        orch.checkpoint_task(task_id, {
            "step": 2,
            "progress_percent": 40,
            "context": "Halfway through outreach",
            "artifacts": ["draft_secithub.md", "draft_pwnhub.md"]
        })

        # Summary
        orch.generate_context_summary(
            task_id,
            summary="2 of 3 Reddit drafts complete",
            key_decisions=["Security-first angle", "No product links"],
            handoff_notes="LocalLLaMA draft still pending"
        )

        # Resume
        resume = orch.resume_from_checkpoint(task_id)

        assert resume["success"] is True
        assert resume["checkpoint"]["data"]["step"] == 2
        assert resume["checkpoint"]["data"]["artifacts"] == ["draft_secithub.md", "draft_pwnhub.md"]
        assert resume["context_summary"]["summary"] == "2 of 3 Reddit drafts complete"
        assert len(resume["context_summary"]["key_decisions"]) == 2
        assert resume["context_summary"]["handoff_notes"] == "LocalLLaMA draft still pending"
        assert "Resume from step 2" in resume["resume_instructions"]
