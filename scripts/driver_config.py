"""
Shared driver configuration — paths, defaults, and config loader.

Used by: third_brother_driver.py, calibrate_trust_ladder.py, driver_guardrails.py
"""

import json
from pathlib import Path

# ── Shared paths ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRAIN_PATH = PROJECT_ROOT / ".brain"
DRIVER_DIR = BRAIN_PATH / "driver"
CONFIG_PATH = DRIVER_DIR / "config.json"
TASKS_PATH = DRIVER_DIR / "tasks.json"
STATE_PATH = DRIVER_DIR / "state.json"
STOP_FILE = DRIVER_DIR / "stop"
ALERTS_PATH = DRIVER_DIR / "alerts.jsonl"
RUNS_PATH = DRIVER_DIR / "runs.jsonl"

# ── Default config (authoritative source) ─────────────────────
DEFAULT_CONFIG = {
    "mode": "supervised",
    "idle_check_minutes": 30,
    "session_timeout_minutes": 120,
    "max_retries": 2,
    "claude_max_turns": 30,
    "claude_effort": "max",
    "claude_model": "claude-opus-4-6",
    "cost_cap_tokens": 500000,
    "trust_ladder": {
        "current_phase": 1,
        "thresholds": {
            "phase_1_to_2": {"min_runs": 20, "unedited_ratio": 0.75},
            "phase_2_to_3": {"min_runs": 30, "acceptance_ratio": 0.70},
            "phase_3_to_4": {"min_runs": 20, "zero_critical_consecutive": 20},
            "demotion_consecutive_failures": 3,
        },
    },
}


def load_config(config_path=None, defaults=None):
    """Load driver config from JSON file.

    Args:
        config_path: Path to config file. Defaults to CONFIG_PATH.
        defaults: Fallback dict when file is missing or corrupt. Defaults to {}.

    Returns:
        Parsed config dict, or a copy of defaults on failure.
    """
    path = config_path if config_path is not None else CONFIG_PATH
    fallback = defaults if defaults is not None else {}
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return dict(fallback)
    return dict(fallback)
