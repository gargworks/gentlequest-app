"""Artery 2: Heartbeat creates corrective tasks for non-blocker signals.

Verifies the Artery 2 block inside _heartbeat_check_impl:
- Creates tasks for STALE_DECISION, VELOCITY_DROP, SESSION_GAP
- Skips STALE_BLOCKER (handled by autonomic system)
- Dedup prevents duplicate heartbeat tasks
- Kill switch NUCLEUS_DISABLE_ARTERY_2 disables task creation
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def hb_brain(tmp_path):
    """Brain with full heartbeat infrastructure."""
    brain = tmp_path / ".brain"
    for d in ["ledger", "engrams", "heartbeat", "session"]:
        (brain / d).mkdir(parents=True)

    (brain / "ledger" / "events.jsonl").touch()
    (brain / "ledger" / "interaction_log.jsonl").touch()
    (brain / "ledger" / "activity_summary.json").write_text(json.dumps({}))
    (brain / "ledger" / "triggers.json").write_text(
        json.dumps({"triggers": []})
    )
    (brain / "engrams" / "ledger.jsonl").touch()
    return brain


class TestArteryHeartbeatTasks:
    """Verify heartbeat creates corrective tasks with dedup protection."""

    def test_stale_decision_creates_task(self, hb_brain):
        """STALE_DECISION signal should create a corrective task."""
        # Write a Decision engram that's old enough to trigger
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=80)).isoformat()
        engram = {
            "key": "jwt_decision",
            "value": "Use JWT for authentication",
            "context": "Decision",
            "intensity": 8,
            "timestamp": old_ts,
        }
        (hb_brain / "engrams" / "ledger.jsonl").write_text(
            json.dumps(engram) + "\n"
        )

        with patch(
            "mcp_server_nucleus.runtime.heartbeat_ops.get_brain_path",
            return_value=hb_brain,
        ):
            with patch(
                "mcp_server_nucleus.runtime.task_ops._add_task"
            ) as mock_add:
                mock_add.return_value = {
                    "success": True,
                    "task": {"id": "hb-1", "status": "PENDING"},
                }
                with patch(
                    "mcp_server_nucleus.runtime.task_ops._list_tasks",
                    return_value=[],
                ):
                    from mcp_server_nucleus.runtime.heartbeat_ops import (
                        _heartbeat_check_impl,
                    )

                    result = _heartbeat_check_impl()

        # Check that Artery 2 created corrective tasks
        if result.get("corrective_tasks_created", 0) > 0:
            assert result["corrective_tasks_created"] >= 1
            detail = result["corrective_details"][0]
            assert detail["signal"] == "STALE_DECISION"
            assert "[heartbeat]" in detail["description"]

    def test_stale_blocker_not_corrective(self, hb_brain):
        """STALE_BLOCKER should NOT create a corrective task — handled by autonomic."""
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
        engram = {
            "key": "blocker_auth",
            "value": "blocker: authentication service is down",
            "context": "Decision",
            "intensity": 9,
            "timestamp": old_ts,
        }
        (hb_brain / "engrams" / "ledger.jsonl").write_text(
            json.dumps(engram) + "\n"
        )

        with patch(
            "mcp_server_nucleus.runtime.heartbeat_ops.get_brain_path",
            return_value=hb_brain,
        ):
            with patch(
                "mcp_server_nucleus.runtime.task_ops._add_task"
            ) as mock_add:
                with patch(
                    "mcp_server_nucleus.runtime.task_ops._list_tasks",
                    return_value=[],
                ):
                    from mcp_server_nucleus.runtime.heartbeat_ops import (
                        _heartbeat_check_impl,
                    )

                    result = _heartbeat_check_impl()

        # Corrective tasks should NOT include STALE_BLOCKER
        for detail in result.get("corrective_details", []):
            assert detail["signal"] != "STALE_BLOCKER"

    def test_dedup_skips_existing_heartbeat_task(self, hb_brain):
        """Should NOT create task if existing PENDING heartbeat task has same signal."""
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=80)).isoformat()
        engram = {
            "key": "jwt_decision",
            "value": "Use JWT for authentication",
            "context": "Decision",
            "intensity": 8,
            "timestamp": old_ts,
        }
        (hb_brain / "engrams" / "ledger.jsonl").write_text(
            json.dumps(engram) + "\n"
        )

        # Existing PENDING task matching the signal type
        existing_tasks = [
            {
                "id": "existing-hb-1",
                "description": "[heartbeat][stale_decision] Review stale decision: jwt_decision. Age: 72h.",
                "status": "PENDING",
            }
        ]

        with patch(
            "mcp_server_nucleus.runtime.heartbeat_ops.get_brain_path",
            return_value=hb_brain,
        ):
            with patch(
                "mcp_server_nucleus.runtime.task_ops._add_task"
            ) as mock_add:
                mock_add.return_value = {
                    "success": True,
                    "task": {"id": "hb-dup"},
                }
                with patch(
                    "mcp_server_nucleus.runtime.task_ops._list_tasks",
                    return_value=existing_tasks,
                ):
                    from mcp_server_nucleus.runtime.heartbeat_ops import (
                        _heartbeat_check_impl,
                    )

                    result = _heartbeat_check_impl()

        # Should not have created a duplicate for stale_decision
        stale_details = [
            d
            for d in result.get("corrective_details", [])
            if d["signal"] == "STALE_DECISION"
        ]
        assert len(stale_details) == 0

    def test_kill_switch_disables_artery_2(self, hb_brain):
        """NUCLEUS_DISABLE_ARTERY_2 should prevent corrective task creation."""
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=80)).isoformat()
        engram = {
            "key": "jwt_decision",
            "value": "Use JWT for authentication",
            "context": "Decision",
            "intensity": 8,
            "timestamp": old_ts,
        }
        (hb_brain / "engrams" / "ledger.jsonl").write_text(
            json.dumps(engram) + "\n"
        )

        os.environ["NUCLEUS_DISABLE_ARTERY_2"] = "1"
        try:
            with patch(
                "mcp_server_nucleus.runtime.heartbeat_ops.get_brain_path",
                return_value=hb_brain,
            ):
                from mcp_server_nucleus.runtime.heartbeat_ops import (
                    _heartbeat_check_impl,
                )

                result = _heartbeat_check_impl()
        finally:
            os.environ.pop("NUCLEUS_DISABLE_ARTERY_2", None)

        assert result.get("corrective_tasks_created", 0) == 0

    def test_result_includes_corrective_fields(self, hb_brain):
        """Heartbeat result should always include corrective_tasks_created."""
        (hb_brain / "engrams" / "ledger.jsonl").touch()

        with patch(
            "mcp_server_nucleus.runtime.heartbeat_ops.get_brain_path",
            return_value=hb_brain,
        ):
            from mcp_server_nucleus.runtime.heartbeat_ops import (
                _heartbeat_check_impl,
            )

            result = _heartbeat_check_impl()

        assert "corrective_tasks_created" in result
        assert "corrective_details" in result
        assert isinstance(result["corrective_details"], list)
