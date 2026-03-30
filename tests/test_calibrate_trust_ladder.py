"""Tests for scripts/calibrate_trust_ladder.py"""

import json
import sys
from pathlib import Path

import pytest

# Make the script importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import calibrate_trust_ladder as ctl


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_run(outcome="completed", duration=60):
    return {"outcome": outcome, "duration_seconds": duration}


@pytest.fixture()
def runs_15_good():
    """15 completed runs at 60s each."""
    return [_make_run("completed", 60) for _ in range(15)]


@pytest.fixture()
def runs_5_mixed():
    """5 runs: 3 completed, 1 blocked, 1 error."""
    return [
        _make_run("completed", 50),
        _make_run("completed", 55),
        _make_run("blocked", 200),
        _make_run("completed", 45),
        _make_run("error", 300),
    ]


@pytest.fixture()
def runs_35_high():
    """35 runs, 32 completed + 3 errors -- high completion."""
    runs = [_make_run("completed", 60) for _ in range(32)]
    runs += [_make_run("error", 120) for _ in range(3)]
    return runs


@pytest.fixture()
def runs_35_low():
    """35 runs, only 10 completed -- low completion."""
    runs = [_make_run("completed", 60) for _ in range(10)]
    runs += [_make_run("error", 120) for _ in range(25)]
    return runs


@pytest.fixture()
def tmp_driver_dir(tmp_path, monkeypatch):
    """Redirect module-level paths to a temp directory."""
    driver = tmp_path / "driver"
    driver.mkdir()
    monkeypatch.setattr(ctl, "CONFIG_PATH", driver / "config.json")
    monkeypatch.setattr(ctl, "RUNS_PATH", driver / "runs.jsonl")
    monkeypatch.setattr(ctl, "ALERTS_PATH", driver / "alerts.jsonl")
    return driver


# ---------------------------------------------------------------------------
# analyze() tests
# ---------------------------------------------------------------------------

class TestAnalyze:
    def test_completion_rate(self, runs_5_mixed):
        result = ctl.analyze(runs_5_mixed, [])
        # 3 completed out of 5
        assert result["completion_rate"] == 0.6

    def test_outlier_detection(self):
        """Durations > 2x mean are counted as outliers."""
        runs = [
            _make_run("completed", 50),
            _make_run("completed", 50),
            _make_run("completed", 50),
            _make_run("completed", 250),  # outlier: 250 > 2*100 = 200
        ]
        result = ctl.analyze(runs, [])
        assert result["outliers"] >= 1

    def test_empty_runs(self):
        result = ctl.analyze([], [])
        assert result["confidence"] == "none"

    def test_confidence_low(self, runs_5_mixed):
        result = ctl.analyze(runs_5_mixed, [])
        assert result["confidence"] == "low"

    def test_confidence_medium(self, runs_15_good):
        result = ctl.analyze(runs_15_good, [])
        assert result["confidence"] == "medium"

    def test_confidence_high(self, runs_35_high):
        result = ctl.analyze(runs_35_high, [])
        assert result["confidence"] == "high"

    def test_critical_alert_count(self, runs_15_good):
        alerts = [
            {"severity": "CRITICAL"},
            {"severity": "WARNING"},
            {"severity": "CRITICAL"},
        ]
        result = ctl.analyze(runs_15_good, alerts)
        assert result["critical_alerts"] == 2


# ---------------------------------------------------------------------------
# suggest_thresholds() tests
# ---------------------------------------------------------------------------

class TestSuggestThresholds:
    def test_lower_thresholds_high_completion(self, runs_35_high):
        analysis = ctl.analyze(runs_35_high, [])
        suggested = ctl.suggest_thresholds(analysis)
        # High completion -> lower min_runs and tighter ratio
        assert suggested["phase_1_to_2"]["min_runs"] <= 20
        assert suggested["phase_1_to_2"]["unedited_ratio"] < 0.95

    def test_higher_thresholds_high_failure(self, runs_35_low):
        analysis = ctl.analyze(runs_35_low, [])
        suggested = ctl.suggest_thresholds(analysis)
        # Low completion -> keeps defaults or conservative values
        assert suggested["phase_1_to_2"]["min_runs"] >= 10
        # With ~28.6% completion, ratio should be clamped to floor
        assert suggested["phase_1_to_2"]["unedited_ratio"] >= 0.6

    def test_defaults_with_few_runs(self, runs_5_mixed):
        analysis = ctl.analyze(runs_5_mixed, [])
        suggested = ctl.suggest_thresholds(analysis)
        # Not enough data -> defaults
        assert suggested["phase_1_to_2"]["min_runs"] == 20
        assert suggested["phase_1_to_2"]["unedited_ratio"] == 0.75
        assert suggested["phase_2_to_3"]["min_runs"] == 30
        assert suggested["phase_2_to_3"]["acceptance_ratio"] == 0.70

    def test_demotion_derived_from_fail_streak(self):
        runs = (
            [_make_run("error")] * 4
            + [_make_run("completed")] * 10
        )
        analysis = ctl.analyze(runs, [])
        suggested = ctl.suggest_thresholds(analysis)
        assert suggested["demotion_consecutive_failures"] == max(2, min(5, 4 + 1))


# ---------------------------------------------------------------------------
# apply_thresholds() tests
# ---------------------------------------------------------------------------

class TestApplyThresholds:
    def test_writes_valid_json(self, tmp_driver_dir):
        config = {"existing_key": True}
        suggested = {
            "phase_1_to_2": {"min_runs": 15, "unedited_ratio": 0.80},
            "phase_2_to_3": {"min_runs": 25, "acceptance_ratio": 0.70},
            "phase_3_to_4": {"min_runs": 15, "zero_critical_consecutive": 15},
            "demotion_consecutive_failures": 3,
        }
        ctl.apply_thresholds(config, suggested)

        written = json.loads(ctl.CONFIG_PATH.read_text())
        assert written["existing_key"] is True
        assert written["trust_ladder"]["thresholds"] == suggested

    def test_creates_trust_ladder_key(self, tmp_driver_dir):
        ctl.apply_thresholds({}, {"phase_1_to_2": {"min_runs": 10}})
        written = json.loads(ctl.CONFIG_PATH.read_text())
        assert "trust_ladder" in written


# ---------------------------------------------------------------------------
# display() tests
# ---------------------------------------------------------------------------

class TestDisplay:
    def test_no_crash_empty_data(self, capsys):
        analysis = {
            "confidence": "none",
            "total_runs": 0,
            "outcomes": {},
            "completion_rate": 0,
            "avg_duration_s": 0,
            "max_duration_s": 0,
            "outlier_threshold_s": 0,
            "outliers": 0,
            "max_success_streak": 0,
            "max_fail_streak": 0,
            "critical_alerts": 0,
        }
        suggested = {
            "phase_1_to_2": {"min_runs": 20, "unedited_ratio": 0.75},
            "phase_2_to_3": {"min_runs": 30, "acceptance_ratio": 0.70},
            "phase_3_to_4": {"min_runs": 20, "zero_critical_consecutive": 20},
            "demotion_consecutive_failures": 3,
        }
        # Should not raise
        ctl.display(analysis, {}, suggested)
        captured = capsys.readouterr()
        assert "Trust Ladder Calibration" in captured.out


# ---------------------------------------------------------------------------
# load helpers with fixture files
# ---------------------------------------------------------------------------

class TestLoadHelpers:
    def test_load_runs_from_jsonl(self, tmp_driver_dir):
        data = [_make_run("completed", 60), _make_run("error", 90)]
        ctl.RUNS_PATH.write_text("\n".join(json.dumps(d) for d in data) + "\n")
        loaded = ctl.load_runs()
        assert len(loaded) == 2
        assert loaded[0]["outcome"] == "completed"

    def test_load_runs_missing_file(self, tmp_driver_dir):
        assert ctl.load_runs() == []

    def test_load_config_missing_file(self, tmp_driver_dir):
        assert ctl.load_config() == {}

    def test_load_config_existing(self, tmp_driver_dir):
        ctl.CONFIG_PATH.write_text(json.dumps({"trust_ladder": {}}))
        assert ctl.load_config() == {"trust_ladder": {}}
