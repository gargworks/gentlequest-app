"""Test circuit breaker logic for nucleus chat batch mode.

Replicates the logic from cli.py without importing it.
State file: <brain_dir>/heartbeat/circuit_breaker.json
"""
import json
import pytest
from datetime import datetime, timezone
from pathlib import Path


# ── Replicate the circuit breaker logic from cli.py ──

def cb_file(brain_dir: Path) -> Path:
    return brain_dir / "heartbeat" / "circuit_breaker.json"


def check_circuit_breaker(brain_dir: Path) -> tuple[bool, int, str]:
    """Check if circuit breaker is open.

    Returns (is_open, consecutive_failures, last_error).
    """
    f = cb_file(brain_dir)
    if not f.exists():
        return False, 0, ""
    try:
        state = json.loads(f.read_text())
        failures = state.get("consecutive_failures", 0)
        return failures >= 3, failures, state.get("last_error", "")
    except Exception:
        return False, 0, ""


def record_failure(brain_dir: Path, error: str) -> dict:
    """Increment consecutive_failures and record error. Returns updated state."""
    f = cb_file(brain_dir)
    state = {}
    if f.exists():
        try:
            state = json.loads(f.read_text())
        except Exception:
            state = {}
    state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
    state["last_error"] = error[:200]
    state["last_failure_ts"] = datetime.now(timezone.utc).isoformat()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(state, indent=2))
    return state


def record_success(brain_dir: Path) -> dict:
    """Reset consecutive_failures to 0 on success. Returns updated state."""
    f = cb_file(brain_dir)
    state = {"consecutive_failures": 0, "last_success_ts": datetime.now(timezone.utc).isoformat()}
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(state, indent=2))
    return state


# ── Tests ──

class TestCircuitBreakerFreshState:
    def test_no_file_allows_run(self, tmp_path):
        """Fresh brain dir with no circuit_breaker.json — batch should run."""
        is_open, failures, _ = check_circuit_breaker(tmp_path)
        assert not is_open
        assert failures == 0

    def test_no_heartbeat_dir_allows_run(self, tmp_path):
        """Heartbeat subdir doesn't exist yet — should still allow run."""
        assert not (tmp_path / "heartbeat").exists()
        is_open, failures, _ = check_circuit_breaker(tmp_path)
        assert not is_open

    def test_empty_json_allows_run(self, tmp_path):
        """circuit_breaker.json with no consecutive_failures key — defaults to 0."""
        f = cb_file(tmp_path)
        f.parent.mkdir(parents=True)
        f.write_text(json.dumps({}))
        is_open, failures, _ = check_circuit_breaker(tmp_path)
        assert not is_open
        assert failures == 0


class TestCircuitBreakerPartialFailures:
    def test_one_failure_allows_run(self, tmp_path):
        record_failure(tmp_path, "timeout")
        is_open, failures, _ = check_circuit_breaker(tmp_path)
        assert not is_open
        assert failures == 1

    def test_two_failures_allows_run(self, tmp_path):
        record_failure(tmp_path, "timeout")
        record_failure(tmp_path, "503 Service Unavailable")
        is_open, failures, _ = check_circuit_breaker(tmp_path)
        assert not is_open
        assert failures == 2

    def test_failure_count_increments(self, tmp_path):
        for i in range(2):
            record_failure(tmp_path, f"error {i}")
        state = json.loads(cb_file(tmp_path).read_text())
        assert state["consecutive_failures"] == 2


class TestCircuitBreakerTripped:
    def test_three_failures_trips_breaker(self, tmp_path):
        for _ in range(3):
            record_failure(tmp_path, "connection refused")
        is_open, failures, _ = check_circuit_breaker(tmp_path)
        assert is_open
        assert failures == 3

    def test_four_failures_still_open(self, tmp_path):
        for _ in range(4):
            record_failure(tmp_path, "quota exceeded")
        is_open, failures, _ = check_circuit_breaker(tmp_path)
        assert is_open
        assert failures == 4

    def test_tripped_breaker_returns_last_error(self, tmp_path):
        record_failure(tmp_path, "first")
        record_failure(tmp_path, "second")
        record_failure(tmp_path, "third error message")
        is_open, _, last_error = check_circuit_breaker(tmp_path)
        assert is_open
        assert last_error == "third error message"

    def test_error_truncated_to_200_chars(self, tmp_path):
        long_error = "x" * 500
        record_failure(tmp_path, long_error)
        state = json.loads(cb_file(tmp_path).read_text())
        assert len(state["last_error"]) == 200


class TestCircuitBreakerReset:
    def test_success_resets_counter(self, tmp_path):
        for _ in range(3):
            record_failure(tmp_path, "err")
        record_success(tmp_path)
        is_open, failures, _ = check_circuit_breaker(tmp_path)
        assert not is_open
        assert failures == 0

    def test_success_after_two_failures_resets(self, tmp_path):
        record_failure(tmp_path, "err")
        record_failure(tmp_path, "err")
        record_success(tmp_path)
        is_open, failures, _ = check_circuit_breaker(tmp_path)
        assert not is_open
        assert failures == 0

    def test_success_writes_last_success_ts(self, tmp_path):
        record_success(tmp_path)
        state = json.loads(cb_file(tmp_path).read_text())
        assert "last_success_ts" in state
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(state["last_success_ts"])

    def test_failures_accumulate_again_after_reset(self, tmp_path):
        """After a reset, new failures should start fresh from 1."""
        for _ in range(3):
            record_failure(tmp_path, "err")
        record_success(tmp_path)
        record_failure(tmp_path, "new error")
        is_open, failures, _ = check_circuit_breaker(tmp_path)
        assert not is_open
        assert failures == 1


class TestCircuitBreakerJsonStructure:
    def test_fail_json_has_keys(self, tmp_path):
        record_failure(tmp_path, "some error")
        state = json.loads(cb_file(tmp_path).read_text())
        assert "consecutive_failures" in state
        assert "last_error" in state
        assert "last_failure_ts" in state

    def test_ok_json_has_keys(self, tmp_path):
        record_success(tmp_path)
        state = json.loads(cb_file(tmp_path).read_text())
        assert "consecutive_failures" in state
        assert state["consecutive_failures"] == 0
        assert "last_success_ts" in state

    def test_fail_ts_is_valid_iso(self, tmp_path):
        record_failure(tmp_path, "err")
        state = json.loads(cb_file(tmp_path).read_text())
        datetime.fromisoformat(state["last_failure_ts"])

    def test_file_is_valid_json(self, tmp_path):
        record_failure(tmp_path, "err")
        raw = cb_file(tmp_path).read_text()
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)

    def test_file_in_correct_location(self, tmp_path):
        record_failure(tmp_path, "err")
        expected = tmp_path / "heartbeat" / "circuit_breaker.json"
        assert expected.exists()

    def test_consecutive_is_integer(self, tmp_path):
        record_failure(tmp_path, "err")
        state = json.loads(cb_file(tmp_path).read_text())
        assert isinstance(state["consecutive_failures"], int)

    def test_corrupted_file_allows_run(self, tmp_path):
        """Corrupted JSON should not crash — defaults to open=False."""
        f = cb_file(tmp_path)
        f.parent.mkdir(parents=True)
        f.write_text("not valid json {{{{")
        is_open, failures, _ = check_circuit_breaker(tmp_path)
        assert not is_open
        assert failures == 0
