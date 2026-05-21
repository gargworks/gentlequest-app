"""nucleus audit-plans — CLI wrapper around the plan_audit lever.

Lets anyone (not just this laptop's TB driver) point Nucleus at a
folder of plan-markdown files and get a rot report. Reuses the lever's
classifier so CLI output matches what the daily heartbeat sees.

Usage:
    python3 scripts/audit_plans_cli.py [PLANS_DIR] [--results PATH] [--json]

Defaults:
    PLANS_DIR  = ~/.claude/plans
    --results  = <cwd>/.nucleus/audit/results.json (created if missing)

Exit codes:
    0  no rotting plans found
    1  ≥1 rotting plan
    2  lever error (bad results.json, unreadable plan dir, etc.)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))

from scripts.levers.plan_audit import PlanAuditLever  # noqa: E402


def _format_human(detail: dict, outcome: str) -> str:
    lines = [f"outcome: {outcome}"]
    total = detail.get("plans_total", 0)
    rotting = detail.get("plans_rotting", 0)
    lines.append(f"plans:   {total} total, {rotting} rotting")
    by_bucket = detail.get("by_bucket", {})
    if by_bucket:
        lines.append("buckets:")
        for bucket, count in sorted(by_bucket.items(), key=lambda kv: -kv[1]):
            lines.append(f"  {bucket:24s} {count}")
    top_rot = detail.get("top_rot", [])
    if top_rot:
        lines.append("top rot (newest first):")
        for entry in top_rot:
            lines.append(
                f"  [{entry['bucket']:22s}] {entry['name']} "
                f"(age {entry['age_days']}d)"
            )
    skip = detail.get("skip_reasons", {})
    if skip:
        lines.append(f"skip_reasons: {len(skip)}")
        for name, reason in skip.items():
            lines.append(f"  {name}: {reason}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit a folder of plan-markdown files for rot."
    )
    parser.add_argument(
        "plans_dir", nargs="?", default="~/.claude/plans",
        help="Directory of *.md plan files (default: ~/.claude/plans)",
    )
    parser.add_argument(
        "--results", default=None,
        help="Path to audit results.json (default: <cwd>/.nucleus/audit/results.json)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Emit raw observation JSON instead of human report",
    )
    args = parser.parse_args()

    cwd = Path.cwd()
    if args.results:
        results_path = Path(args.results).expanduser()
    else:
        brain_results = cwd / ".brain" / "audit" / "results.json"
        nucleus_results = cwd / ".nucleus" / "audit" / "results.json"
        results_path = brain_results if brain_results.exists() else nucleus_results
    results_path.parent.mkdir(parents=True, exist_ok=True)
    if not results_path.exists():
        results_path.write_text("{}", encoding="utf-8")

    manifest = {
        "inputs": {
            "plan_dirs": [args.plans_dir],
            "audit_results_path": str(results_path),
            "max_report": 10,
            "stale_threshold_seconds": 60,
        }
    }

    obs = PlanAuditLever().run(manifest, brain_path=cwd / ".brain")
    outcome = obs.get("outcome", "unknown")
    detail = obs.get("detail", {})

    if args.json:
        print(json.dumps({"outcome": outcome, "detail": detail}, indent=2))
    else:
        print(_format_human(detail, outcome))

    if outcome == "error":
        return 2
    if outcome == "found" and detail.get("plans_rotting", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
