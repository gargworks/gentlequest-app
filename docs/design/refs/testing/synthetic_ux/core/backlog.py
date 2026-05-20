"""
backlog.py — Layer 4: Aggregation and prioritized backlog generator.

Reads JSONL observations, scores each finding, detects systemic patterns,
and emits BACKLOG.md + run_summary.json.

Scoring: score = severity_weight × flow_position_bonus
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional

from .observation_log import Observation, load_observations

SEVERITY_WEIGHTS = {
    "BLOCKER": 40,
    "HIGH": 20,
    "MEDIUM": 8,
    "LOW": 2,
    "DELIGHT": -5,
}

FLOW_BONUSES = {
    "crisis": 1.8,
    "onboarding": 1.5,
    "core": 1.0,
    "secondary": 0.5,
    "settings": 0.3,
}

COST_PER_1K_INPUT = 0.003   # claude-sonnet-4-6 approximate
COST_PER_1K_OUTPUT = 0.015


def _score(obs: Observation) -> float:
    if not obs.layer3_user_mind:
        return 0.0
    verdict = obs.layer3_user_mind.design_verdict
    flow = obs.flow_position
    w = SEVERITY_WEIGHTS.get(verdict, 0)
    b = FLOW_BONUSES.get(flow, 1.0)
    return w * b


def _cost_usd(observations: list[Observation]) -> float:
    total = 0.0
    for obs in observations:
        for result in (obs.layer2_judge, obs.layer3_user_mind):
            if result:
                inp = getattr(result, "input_tokens", 0)
                out = getattr(result, "output_tokens", 0)
                total += (inp / 1000) * COST_PER_1K_INPUT
                total += (out / 1000) * COST_PER_1K_OUTPUT
    return round(total, 4)


def _verdict_counts(observations: list[Observation]) -> dict:
    counts: dict = {v: 0 for v in SEVERITY_WEIGHTS}
    uncertain = 0
    for obs in observations:
        if obs.layer3_user_mind:
            v = obs.layer3_user_mind.design_verdict
            counts[v] = counts.get(v, 0) + 1
        elif obs.layer2_judge and obs.layer2_judge.verdict == "UNCERTAIN":
            uncertain += 1
    counts["UNCERTAIN"] = uncertain
    return counts


_DRIFT_PHRASES = (
    "talk/chat screen",
    "talk/home screen",
    "talk screen",
    "talk/chat home",
    "chat screen is shown",
    "chat screen still displayed",
)


def _is_drift_finding(obs: Observation) -> bool:
    """A FAIL is suspected WALK_DRIFT if the judge reason or issues mention
    the Talk/chat screen as the rendered destination — i.e., the precondition
    likely was never reached, so the BLOCKER verdict is a framework artifact
    rather than an app bug."""
    judge = obs.layer2_judge
    if not judge or judge.verdict != "FAIL":
        return False
    haystack = " ".join([
        (judge.reason or "").lower(),
        " ".join(judge.issues or []).lower(),
    ])
    return any(p in haystack for p in _DRIFT_PHRASES)


def _pattern_alerts(observations: list[Observation], counts: dict) -> list[str]:
    alerts = []

    # WALK_DRIFT (must run first — clusters the dominant false-positive pattern)
    drift = [o for o in observations if _is_drift_finding(o)]
    if len(drift) >= 5:
        alerts.append(
            f"🧭 WALK_DRIFT: {len(drift)} UCs FAILed with Talk/chat screen rendered "
            "in place of the expected destination — likely a precondition/calibration "
            "issue in the walk executor, NOT N separate app bugs. See "
            "'Suspected WALK_DRIFT' section for the list; fix the precondition "
            "or tap coordinates before treating these as real findings."
        )

    # BLOCKERs in onboarding (exclude drift cases — they're noise)
    onboarding_blockers = [
        o for o in observations
        if o.flow_position == "onboarding"
        and o.layer3_user_mind
        and o.layer3_user_mind.design_verdict == "BLOCKER"
        and not _is_drift_finding(o)
    ]
    if len(onboarding_blockers) >= 2:
        alerts.append(
            f"🚨 CRITICAL: onboarding has {len(onboarding_blockers)} BLOCKERs "
            "— users won't reach core features"
        )

    # High abandon risk
    high_risk = [
        o for o in observations
        if o.layer3_user_mind and o.layer3_user_mind.abandon_risk_score > 60
    ]
    if len(high_risk) >= 3:
        alerts.append(
            f"⚠ CHURN RISK: {len(high_risk)} UCs with abandon_risk_score > 60 "
            "— Maya will silently stop using the app"
        )

    # Too many UNCERTAIN
    if counts.get("UNCERTAIN", 0) >= 4:
        alerts.append(
            f"🔍 COVERAGE GAP: {counts['UNCERTAIN']} UCs inconclusive "
            "— re-run with better screenshots or add manual checks"
        )

    return alerts


def _render_finding(obs: Observation, rank: int) -> str:
    mind = obs.layer3_user_mind
    judge = obs.layer2_judge
    if not mind:
        return ""

    lines = [
        f"**[{obs.uc_id}] {obs.uc_title}**",
    ]
    if mind.first_reaction and mind.first_reaction != "parse_error":
        lines.append(f'Maya: "{mind.first_reaction}"')
    if mind.unspoken_frustration and mind.unspoken_frustration.lower() != "none":
        lines.append(f'Unspoken: "{mind.unspoken_frustration}"')
    if mind.heuristic_violated and mind.heuristic_violated.lower() != "none":
        lines.append(f"Heuristic: {mind.heuristic_violated}")
    lines.append(f"Abandon risk: {mind.abandon_risk_score}/100")
    if judge and judge.verdict == "FAIL" and judge.issues:
        lines.append(f"Judge: FAIL — {judge.issues[0]}")
    if mind.refinement_suggestion:
        lines.append(f"→ Fix: {mind.refinement_suggestion}")
    return "\n".join(lines)


def generate_backlog(
    observations: list[Observation],
    output_dir: Path,
    product_name: str = "GentleQuest",
    run_id: Optional[str] = None,
) -> tuple[Path, Path]:
    """
    Score all observations and emit BACKLOG.md + run_summary.json.
    Returns (backlog_path, summary_path).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    scored = sorted(observations, key=_score, reverse=True)
    counts = _verdict_counts(observations)
    alerts = _pattern_alerts(observations, counts)
    cost = _cost_usd(observations)

    today = date.today().isoformat()
    n = len(observations)
    run_label = run_id or f"{product_name.lower()}-{today}"

    # ── BACKLOG.md ─────────────────────────────────────────────
    md_lines = [
        f"# {product_name} Synthetic QA Backlog — {today}",
        f"> Run: {n} UCs | "
        f"BLOCKER:{counts['BLOCKER']} "
        f"HIGH:{counts['HIGH']} "
        f"MEDIUM:{counts['MEDIUM']} "
        f"LOW:{counts['LOW']} "
        f"DELIGHT:{counts['DELIGHT']} "
        f"| ~${cost:.2f}",
        "",
    ]

    if alerts:
        md_lines += ["## Pattern Alerts", ""]
        for alert in alerts:
            md_lines.append(f"- {alert}")
        md_lines.append("")

    md_lines += ["## Prioritized Findings", ""]

    current_verdict = None
    verdict_order = ["BLOCKER", "HIGH", "MEDIUM", "LOW"]
    rendered_verdicts: set = set()
    drift_obs: list[Observation] = []

    for obs in scored:
        if not obs.layer3_user_mind:
            continue
        verdict = obs.layer3_user_mind.design_verdict
        if verdict == "DELIGHT":
            continue
        if verdict not in verdict_order:
            continue
        # Drift findings are demoted to their own section — they're framework
        # noise (wrong precondition), not real app bugs.
        if _is_drift_finding(obs):
            drift_obs.append(obs)
            continue
        if verdict not in rendered_verdicts:
            md_lines += [f"### {verdict}", ""]
            rendered_verdicts.add(verdict)
        finding = _render_finding(obs, 0)
        if finding:
            md_lines += [finding, ""]

    if drift_obs:
        md_lines += [
            "## Suspected WALK_DRIFT — fix framework before treating as bugs",
            "",
            "These UCs FAILed because the simulator landed on the Talk/chat "
            "screen instead of the precondition screen. The Maya findings "
            "below are not actionable until either (a) tap coordinates are "
            "recalibrated, or (b) a navigation precondition step is added.",
            "",
        ]
        for obs in drift_obs:
            judge = obs.layer2_judge
            reason = (judge.reason if judge else "") or ""
            md_lines.append(f"- **[{obs.uc_id}]** {obs.uc_title} — {reason[:140]}")
        md_lines.append("")

    # DELIGHTs at the bottom
    delights = [o for o in scored if o.layer3_user_mind and o.layer3_user_mind.design_verdict == "DELIGHT"]
    if delights:
        md_lines += ["## DELIGHT — protect these", ""]
        for obs in delights:
            if obs.layer3_user_mind:
                md_lines.append(f"**[{obs.uc_id}]** {obs.uc_title}")
                if obs.layer3_user_mind.unspoken_delight and obs.layer3_user_mind.unspoken_delight.lower() != "none":
                    md_lines.append(f'  → "{obs.layer3_user_mind.unspoken_delight}"')
                md_lines.append("")

    backlog_path = output_dir / "BACKLOG.md"
    backlog_path.write_text("\n".join(md_lines), encoding="utf-8")

    # ── run_summary.json ───────────────────────────────────────
    blocker_ids = [
        o.uc_id for o in observations
        if o.layer3_user_mind and o.layer3_user_mind.design_verdict == "BLOCKER"
    ]
    highest_risk = max(
        (o for o in observations if o.layer3_user_mind),
        key=lambda o: o.layer3_user_mind.abandon_risk_score,  # type: ignore[union-attr]
        default=None,
    )
    summary = {
        "run_id": run_label,
        "product": product_name,
        "date": today,
        "uc_count": n,
        "verdict_counts": counts,
        "pattern_alerts": alerts,
        "blocker_uc_ids": blocker_ids,
        "highest_risk_uc": highest_risk.uc_id if highest_risk else None,
        "highest_risk_score": highest_risk.layer3_user_mind.abandon_risk_score if highest_risk and highest_risk.layer3_user_mind else 0,
        "cost_usd": cost,
        "has_blockers": counts["BLOCKER"] > 0,
    }
    summary_path = output_dir / "run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return backlog_path, summary_path


def generate_backlog_from_jsonl(
    jsonl_path: Path,
    output_dir: Path,
    product_name: str = "GentleQuest",
) -> tuple[Path, Path]:
    observations = load_observations(jsonl_path)
    return generate_backlog(observations, output_dir, product_name)
