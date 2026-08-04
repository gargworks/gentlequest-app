#!/usr/bin/env python3
"""
GentleQuest Qualified Activation Proof — Standalone Gate-Read Evaluation Script.

Evaluates the activation proof experiment against hard gates and generates
metrics/activation_proof_verdict.md.

Usage:
    .venv/bin/python scripts/activation_proof_gate_read.py
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Repository root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_PATH = PROJECT_ROOT / "metrics" / "activation_proof_state.json"
VERDICT_PATH = PROJECT_ROOT / "metrics" / "activation_proof_verdict.md"


def load_state():
    if not STATE_PATH.exists():
        return {
            "t0_timestamp": None,
            "target_qualified_sessions": 50,
            "max_elapsed_days": 7,
            "gate_criteria": {
                "cta_ctr_min": 0.15,
                "first_value_actions_min": 3,
                "first_value_conversion_min": 0.10,
                "downstream_human_signal_min": 1,
            },
            "status": "awaiting_t0",
        }
    with open(STATE_PATH, "r") as f:
        return json.load(f)


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def write_verdict_report(
    verdict,
    t0_str,
    elapsed_days,
    landing_sessions,
    counts,
    cta_ctr,
    first_value_conversion,
    gate_results,
):
    date_str = datetime.utcnow().strftime("%Y-%m-%d")

    cta_ctr_pct = round(cta_ctr * 100, 1)
    fva_conv_pct = round(first_value_conversion * 100, 1)

    g1_tag = "PASS" if gate_results.get("cta_ctr", False) else "FAIL"
    g2_tag = "PASS" if gate_results.get("first_value_actions", False) else "FAIL"
    g3_tag = "PASS" if gate_results.get("first_value_conversion", False) else "FAIL"
    g4_tag = "PASS" if gate_results.get("downstream_human_signal", False) else "FAIL"

    g4_actual = gate_results.get("downstream_actual", 0)

    report_lines = [
        f"# Activation Proof Verdict — {date_str}",
        f"**Verdict:** {verdict}",
        f"**t0:** {t0_str}  **elapsed_days:** {elapsed_days}  **qualified_sessions:** {landing_sessions}",
        "## Funnel counts",
        f"- landing_sessions: {counts.get('landing_sessions', 0)}",
        f"- cta_clicks: {counts.get('cta_clicks', 0)} (CTR: {cta_ctr_pct}%)",
        f"- web_app_opens: {counts.get('web_app_opens', 0)}",
        f"- compliance_passed: {counts.get('compliance_passed', 0)}",
        f"- first_value_actions: {counts.get('first_value_actions', 0)} (conversion: {fva_conv_pct}%)",
        f"- returning_users: {counts.get('returning_users', 0)}",
        "## Gate evaluation",
        f"- [{g1_tag}] CTA CTR >= 15%: actual {cta_ctr_pct}%",
        f"- [{g2_tag}] first_value_actions >= 3: actual {counts.get('first_value_actions', 0)}",
        f"- [{g3_tag}] first_value_conversion >= 10%: actual {fva_conv_pct}%",
        f"- [{g4_tag}] downstream human signal >= 1: actual {g4_actual}",
        "## Next action",
        "- BREAKTHROUGH: send 10 additional matched creator emails into the same measured journey.",
        "- PARTIAL: allow one message/destination iteration; keep original stop date.",
        "- KILL: preserve GentleQuest as portfolio asset; stop new SEO + outreach; do not build new acquisition system.",
        "",
    ]

    VERDICT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(VERDICT_PATH, "w") as f:
        f.write("\n".join(report_lines))


def main():
    # 1. Load state & auto-trigger t0 if eligible
    from scripts.analytics_dashboard import update_activation_proof_t0
    update_activation_proof_t0()

    state = load_state()
    t0_timestamp = state.get("t0_timestamp")
    target_qualified_sessions = state.get("target_qualified_sessions", 50)
    max_elapsed_days = state.get("max_elapsed_days", 7)
    gate_criteria = state.get("gate_criteria", {})

    # 2. Check if t0_timestamp is null
    if not t0_timestamp:
        state["status"] = "awaiting_t0"
        save_state(state)
        write_verdict_report(
            verdict="NOT_STARTED",
            t0_str="None",
            elapsed_days=0,
            landing_sessions=0,
            counts={
                "landing_sessions": 0,
                "cta_clicks": 0,
                "web_app_opens": 0,
                "compliance_passed": 0,
                "first_value_actions": 0,
                "returning_users": 0,
            },
            cta_ctr=0.0,
            first_value_conversion=0.0,
            gate_results={
                "cta_ctr": False,
                "first_value_actions": False,
                "first_value_conversion": False,
                "downstream_human_signal": False,
                "downstream_actual": 0,
            },
        )
        print("Experiment not started — no cta_impression events detected yet. Run after the CTA is deployed and instrumentation is live.")
        sys.exit(0)

    # 3. Compute elapsed days
    try:
        t0_dt = datetime.fromisoformat(t0_timestamp.replace("Z", "+00:00"))
    except Exception:
        t0_dt = datetime.utcnow()

    now = datetime.now(timezone.utc) if t0_dt.tzinfo else datetime.utcnow()
    elapsed_days = max(0, (now - t0_dt).days)

    # 4. Get qualified-human funnel counts from PRODUCTION API
    # (was: local Flask app + SQLite — issue #191: local DB has no production data)
    import urllib.request
    PRODUCTION_API = os.environ.get("GQ_API_URL", "https://app.gentlequest.app")
    funnel_url = f"{PRODUCTION_API}/api/metrics/funnel"

    try:
        req = urllib.request.Request(funnel_url, headers={"User-Agent": "gq-funnel-snapshot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            funnel_data = json.loads(resp.read())
    except Exception as e:
        print(f"ERROR: Could not fetch funnel from {funnel_url}: {e}")
        funnel_data = {"counts": {}}

    # Downstream human signal — also from production API
    feedback_count = 0
    creator_reply_count = 0
    try:
        feedback_url = f"{PRODUCTION_API}/api/metrics/feedback-count"
        req2 = urllib.request.Request(feedback_url, headers={"User-Agent": "gq-funnel-snapshot/1.0"})
        with urllib.request.urlopen(req2, timeout=10) as resp:
            fb_data = json.loads(resp.read())
            feedback_count = fb_data.get("count", 0)
    except Exception:
        pass  # Endpoint may not exist — fallback to 0

    counts = funnel_data.get("counts", {})
    landing_sessions = counts.get("landing_sessions", 0)
    cta_clicks = counts.get("cta_clicks", 0)
    first_value_actions = counts.get("first_value_actions", 0)
    returning_users = counts.get("returning_users", 0)
    cta_ctr = funnel_data.get("cta_ctr", 0.0)
    first_value_conversion = funnel_data.get("first_value_conversion", 0.0)

    downstream_actual = returning_users + feedback_count + creator_reply_count

    # 5. Check if gate is readable: elapsed_days >= 7 OR landing_sessions >= 50
    gate_readable = (elapsed_days >= max_elapsed_days) or (landing_sessions >= target_qualified_sessions)

    if not gate_readable:
        state["status"] = "pending"
        save_state(state)
        write_verdict_report(
            verdict="PENDING",
            t0_str=t0_timestamp,
            elapsed_days=elapsed_days,
            landing_sessions=landing_sessions,
            counts=counts,
            cta_ctr=cta_ctr,
            first_value_conversion=first_value_conversion,
            gate_results={
                "cta_ctr": cta_ctr >= gate_criteria.get("cta_ctr_min", 0.15),
                "first_value_actions": first_value_actions >= gate_criteria.get("first_value_actions_min", 3),
                "first_value_conversion": first_value_conversion >= gate_criteria.get("first_value_conversion_min", 0.10),
                "downstream_human_signal": downstream_actual >= gate_criteria.get("downstream_human_signal_min", 1),
                "downstream_actual": downstream_actual,
            },
        )
        print(f"Gate not ready: {elapsed_days} days elapsed, {landing_sessions} qualified sessions (need 7 days OR 50 sessions).")
        sys.exit(0)

    # 6. Evaluate against hard gates
    g1_pass = cta_ctr >= gate_criteria.get("cta_ctr_min", 0.15)
    g2_pass = first_value_actions >= gate_criteria.get("first_value_actions_min", 3)
    g3_pass = first_value_conversion >= gate_criteria.get("first_value_conversion_min", 0.10)
    g4_pass = downstream_actual >= gate_criteria.get("downstream_human_signal_min", 1)

    all_gates_pass = g1_pass and g2_pass and g3_pass and g4_pass

    # 7. Verdict logic
    if landing_sessions < 10 or first_value_actions < 2:
        verdict = "KILL"
    elif g1_pass and (1.0 - first_value_conversion) > 0.80 and not all_gates_pass:
        verdict = "KILL"
    elif all_gates_pass:
        verdict = "BREAKTHROUGH"
    elif first_value_actions >= 2:
        verdict = "PARTIAL"
    else:
        verdict = "KILL"

    # 8. Write verdict report
    write_verdict_report(
        verdict=verdict,
        t0_str=t0_timestamp,
        elapsed_days=elapsed_days,
        landing_sessions=landing_sessions,
        counts=counts,
        cta_ctr=cta_ctr,
        first_value_conversion=first_value_conversion,
        gate_results={
            "cta_ctr": g1_pass,
            "first_value_actions": g2_pass,
            "first_value_conversion": g3_pass,
            "downstream_human_signal": g4_pass,
            "downstream_actual": downstream_actual,
        },
    )

    # 9. Update state status
    state["status"] = verdict.lower()
    save_state(state)

    print(f"Activation Proof Verdict: {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
