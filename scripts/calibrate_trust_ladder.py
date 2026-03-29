#!/usr/bin/env python3
"""
Trust Ladder Calibration
=========================
Analyze real run data and suggest threshold adjustments.

Usage:
    python3 scripts/calibrate_trust_ladder.py            # show analysis
    python3 scripts/calibrate_trust_ladder.py --apply     # write new thresholds
"""

import json
import argparse
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from driver_config import DRIVER_DIR, CONFIG_PATH, RUNS_PATH, ALERTS_PATH, VERIFICATION_LOG_PATH, load_config as _load_config_shared


def load_runs() -> list:
    if not RUNS_PATH.exists():
        return []
    entries = []
    for line in RUNS_PATH.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def load_alerts() -> list:
    if not ALERTS_PATH.exists():
        return []
    entries = []
    for line in ALERTS_PATH.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def load_config() -> dict:
    return _load_config_shared(CONFIG_PATH)


def analyze(runs: list, alerts: list) -> dict:
    """Analyze run data for threshold calibration."""
    total = len(runs)
    if total == 0:
        return {"confidence": "none", "reason": "no runs yet"}

    # Outcome distribution
    outcomes = defaultdict(int)
    for r in runs:
        outcomes[r.get("outcome", "unknown")] += 1

    # Completion rate (exclude non-actionable outcomes from denominator)
    _non_actionable = {"session_exhausted", "timeout", "session_busy", "completed_no_pr"}
    completed = outcomes.get("completed", 0)
    actionable_total = sum(v for k, v in outcomes.items() if k not in _non_actionable)
    completion_rate = completed / (actionable_total or 1)

    # Duration stats
    durations = [r.get("duration_seconds", 0) for r in runs if r.get("duration_seconds")]
    avg_duration = sum(durations) / len(durations) if durations else 0
    max_duration = max(durations) if durations else 0
    outlier_threshold = avg_duration * 2

    # Streak analysis
    max_success_streak = 0
    max_fail_streak = 0
    current_success = 0
    current_fail = 0

    for r in runs:
        outcome = r.get("outcome")
        if outcome in ("session_exhausted", "timeout", "session_busy", "completed_no_pr"):
            continue  # non-actionable — don't break streaks
        if outcome == "completed":
            current_success += 1
            current_fail = 0
            max_success_streak = max(max_success_streak, current_success)
        elif outcome in ("blocked", "error"):
            current_fail += 1
            current_success = 0
            max_fail_streak = max(max_fail_streak, current_fail)
        else:
            current_success = 0
            current_fail = 0

    # Critical alerts
    critical_count = sum(1 for a in alerts if a.get("severity") == "CRITICAL")

    # Confidence level
    if total < 10:
        confidence = "low"
    elif total < 30:
        confidence = "medium"
    else:
        confidence = "high"

    # ── Verification analysis ──
    verification_entries = []
    if VERIFICATION_LOG_PATH.exists():
        for line in VERIFICATION_LOG_PATH.read_text().strip().split("\n"):
            if line.strip():
                try:
                    verification_entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    v_total = len(verification_entries)
    v_passed = sum(1 for e in verification_entries if e.get("verified"))
    v_pass_rate = v_passed / v_total if v_total else 0.0

    # Most failed tiers
    tier_fail_counts = defaultdict(int)
    for e in verification_entries:
        for tier in e.get("tiers_failed", []):
            tier_fail_counts[tier] += 1
    most_failed_tiers = sorted(tier_fail_counts.items(), key=lambda x: -x[1])[:5]

    # Suggest verification_accuracy_min based on actual data
    if v_total >= 10:
        suggested_verify_min = round(max(0.60, v_pass_rate - 0.10), 2)
    else:
        suggested_verify_min = 0.80  # default until enough data

    return {
        "confidence": confidence,
        "total_runs": total,
        "outcomes": dict(outcomes),
        "completion_rate": round(completion_rate, 3),
        "avg_duration_s": round(avg_duration),
        "max_duration_s": max_duration,
        "outlier_threshold_s": round(outlier_threshold),
        "outliers": sum(1 for d in durations if d > outlier_threshold),
        "max_success_streak": max_success_streak,
        "max_fail_streak": max_fail_streak,
        "critical_alerts": critical_count,
        "verification_total": v_total,
        "verification_pass_rate": round(v_pass_rate, 3),
        "most_failed_tiers": most_failed_tiers,
        "suggested_verification_accuracy_min": suggested_verify_min,
    }


def suggest_thresholds(analysis: dict) -> dict:
    """Suggest new thresholds based on real data."""
    total = analysis.get("total_runs", 0)
    rate = analysis.get("completion_rate", 0)

    # Phase 1->2: min_runs and unedited_ratio
    # If completion rate is high, can use tighter window
    if total >= 10:
        suggested_min_1 = max(10, min(20, total))
        suggested_ratio_1 = max(0.6, min(0.85, rate - 0.05))
    else:
        suggested_min_1 = 20  # default, not enough data
        suggested_ratio_1 = 0.75

    # Phase 2->3: based on streak data
    if total >= 20:
        suggested_min_2 = max(15, min(30, int(total * 0.7)))
        suggested_ratio_2 = max(0.6, min(0.80, rate - 0.10))
    else:
        suggested_min_2 = 30
        suggested_ratio_2 = 0.70

    # Phase 3->4: based on critical alert history
    if analysis.get("critical_alerts", 0) == 0 and total >= 10:
        suggested_consec_3 = max(10, min(20, int(total * 0.5)))
    else:
        suggested_consec_3 = 20

    # Demotion: based on max fail streak
    max_fail = analysis.get("max_fail_streak", 0)
    suggested_demotion = max(2, min(5, max_fail + 1))

    return {
        "phase_1_to_2": {
            "min_runs": suggested_min_1,
            "unedited_ratio": round(suggested_ratio_1, 2),
        },
        "phase_2_to_3": {
            "min_runs": suggested_min_2,
            "acceptance_ratio": round(suggested_ratio_2, 2),
        },
        "phase_3_to_4": {
            "min_runs": suggested_consec_3,
            "zero_critical_consecutive": suggested_consec_3,
        },
        "demotion_consecutive_failures": suggested_demotion,
    }


def display(analysis: dict, current: dict, suggested: dict):
    """Display analysis and comparison."""
    v_total = analysis.get('verification_total', 0)
    v_rate = analysis.get('verification_pass_rate', 0)
    v_suggest = analysis.get('suggested_verification_accuracy_min', 0.80)
    print(f"""
Trust Ladder Calibration
========================
  Confidence:    {analysis['confidence'].upper()} ({analysis.get('total_runs', 0)} runs)

  Run Analysis:
    Completion rate:    {analysis.get('completion_rate', 0):.0%}
    Avg duration:       {analysis.get('avg_duration_s', 0)}s
    Max success streak: {analysis.get('max_success_streak', 0)}
    Max fail streak:    {analysis.get('max_fail_streak', 0)}
    Critical alerts:    {analysis.get('critical_alerts', 0)}
    Outliers (>2x avg): {analysis.get('outliers', 0)}

  Verification (GROUND):
    Total verified:     {v_total}
    Pass rate:          {v_rate:.0%}
    Suggested min:      {v_suggest:.0%}""")
    most_failed = analysis.get('most_failed_tiers', [])
    if most_failed:
        print("    Most failed tiers:")
        for tier, count in most_failed:
            print(f"      Tier {tier}: {count} failures")
    print(f"""
  Outcomes:""")
    for k, v in sorted(analysis.get("outcomes", {}).items()):
        print(f"    {k:20s} {v}")

    current_t = current.get("trust_ladder", {}).get("thresholds", {})
    print(f"""
  Threshold Comparison:
  ---------------------
  {'':30s} {'CURRENT':>10s}  {'SUGGESTED':>10s}
  Phase 1->2 min_runs:       {current_t.get('phase_1_to_2', {}).get('min_runs', '?'):>10}  {suggested['phase_1_to_2']['min_runs']:>10}
  Phase 1->2 ratio:          {current_t.get('phase_1_to_2', {}).get('unedited_ratio', '?'):>10}  {suggested['phase_1_to_2']['unedited_ratio']:>10}
  Phase 2->3 min_runs:       {current_t.get('phase_2_to_3', {}).get('min_runs', '?'):>10}  {suggested['phase_2_to_3']['min_runs']:>10}
  Phase 2->3 ratio:          {current_t.get('phase_2_to_3', {}).get('acceptance_ratio', '?'):>10}  {suggested['phase_2_to_3']['acceptance_ratio']:>10}
  Phase 3->4 consecutive:    {current_t.get('phase_3_to_4', {}).get('zero_critical_consecutive', '?'):>10}  {suggested['phase_3_to_4']['zero_critical_consecutive']:>10}
  Demotion failures:         {current_t.get('demotion_consecutive_failures', '?'):>10}  {suggested['demotion_consecutive_failures']:>10}
""")


def apply_thresholds(config: dict, suggested: dict):
    """Write suggested thresholds to config."""
    config.setdefault("trust_ladder", {})["thresholds"] = suggested
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")
    print("  Thresholds applied to .brain/driver/config.json")


def main():
    parser = argparse.ArgumentParser(description="Trust Ladder Calibration")
    parser.add_argument("--apply", action="store_true", help="Apply suggested thresholds")
    args = parser.parse_args()

    runs = load_runs()
    alerts = load_alerts()
    config = load_config()

    analysis = analyze(runs, alerts)

    if analysis.get("confidence") == "none":
        print("No runs yet. Run some tasks first.")
        return

    suggested = suggest_thresholds(analysis)
    display(analysis, config, suggested)

    if args.apply:
        apply_thresholds(config, suggested)
    else:
        print("  Run with --apply to write these thresholds.")


if __name__ == "__main__":
    main()
