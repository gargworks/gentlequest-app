"""Compounding v0 Loop — The 7-Day Automated Workflow.

MDR_017: The system that makes Nucleus self-improving.

Design Thinking Output Reference:
  "Each cycle starts faster because memory improves context."
  — DT1_SWARM_SESSION_DELIVERABLES.md, Section F

The Loop:
  INPUT (Founder: 3-5 line intent)
    ↓
  NUCLEUS ACTION (Execute tool calls with bounded autonomy)
    ↓
  OUTPUT (One artifact)
    ↓
  ENGRAM OPS (Write stable deltas via ADUN)
    ↓
  NEXT SESSION (Retrieve engrams + rolling summary)
    ↓
  [REPEAT — compounding effect]

Daily Plan:
  Mon: Gap analysis → alive_moment_definition
  Tue: Build the gap → feature_x_implemented
  Wed: Test the build → feature_x_verified
  Thu: Reflect → week_N_synthesis
  Fri: Ship it → release_vX.Y.Z
  Sat: Review telemetry → telemetry_week_N
  Sun: Auto-consolidate → consolidation_week_N
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger("nucleus.compounding")


# ── Artery 7: Compounding cycle state machine ──────────────────

def _compute_compounding_score(brain: Path) -> int:
    """Compute compounding score from brain state.

    Extracted from inline computation for reuse by cycle state machine.
    """
    engram_count = 0
    auto_writes = 0
    errors = 0

    ledger = brain / "engrams" / "ledger.jsonl"
    if ledger.exists():
        try:
            for line in ledger.read_text().splitlines():
                try:
                    e = json.loads(line.strip())
                    if not e.get("deleted", False):
                        engram_count += 1
                except (json.JSONDecodeError, KeyError):
                    pass
        except OSError:
            pass

    metrics = brain / "engrams" / "hook_metrics.jsonl"
    if metrics.exists():
        try:
            for line in metrics.read_text().splitlines():
                try:
                    m = json.loads(line.strip())
                    outcome = m.get("outcome", "")
                    if outcome == "ADD":
                        auto_writes += 1
                    elif outcome == "ERROR":
                        errors += 1
                except (json.JSONDecodeError, KeyError):
                    pass
        except OSError:
            pass

    efficiency = auto_writes / max(auto_writes + errors, 1)

    return min(100, int(
        (engram_count * 0.5) +
        (auto_writes * 2) +
        (efficiency * 50) -
        (errors * 5)
    ))


def _compute_compounding_score_v2(brain: Path) -> Dict:
    """Multi-dimensional compounding score (5 dimensions × 100 pts).

    Dimensions:
      Knowledge Metabolism (30): engrams, auto-writes, updates
      Frontier Health (30): GROUND pass rate, ALIGN reviews, COMPOUND rate
      Velocity (20): this_week / last_week ratio
      Continuity (10): active days, session gaps
      Training Signal (10): new SFT + DPO pairs

    Returns dict with dimension scores, total, and band.
    """
    from datetime import timedelta
    dims = {}
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    week_ago_str = week_ago.strftime("%Y-%m-%d")

    # ── Knowledge Metabolism (max 30) ──
    recent_engrams = 0
    auto_writes_7d = 0
    update_writes = 0
    ledger = brain / "engrams" / "ledger.jsonl"
    if ledger.exists():
        try:
            for line in ledger.read_text().splitlines():
                try:
                    e = json.loads(line.strip())
                    ts = e.get("timestamp", "")[:10]
                    if ts >= week_ago_str and not e.get("deleted"):
                        recent_engrams += 1
                        if e.get("auto_written"):
                            auto_writes_7d += 1
                        if e.get("updated"):
                            update_writes += 1
                except (json.JSONDecodeError, KeyError):
                    pass
        except OSError:
            pass
    dims["knowledge_metabolism"] = min(30, round(
        recent_engrams * 0.3 + auto_writes_7d * 1.5 + update_writes * 2.0
    ))

    # ── Frontier Health (max 30) ──
    ground_rate = 0.0
    align_reviews = 0
    delta_positive_rate = 0.0
    try:
        from .hardening import safe_read_jsonl
        vlog = brain / "verification_log.jsonl"
        if vlog.exists():
            receipts = safe_read_jsonl(vlog)
            if receipts:
                passed = sum(1 for r in receipts if not r.get("tiers_failed"))
                ground_rate = passed / len(receipts)
        vpath = brain / "driver" / "human_verdicts.jsonl"
        if vpath.exists():
            verdicts = safe_read_jsonl(vpath)
            align_reviews = len([v for v in verdicts if v.get("verdict") != "pending"])
        dpath = brain / "deltas" / "deltas.jsonl"
        if dpath.exists():
            deltas = safe_read_jsonl(dpath)
            if deltas:
                pos = sum(1 for d in deltas if d.get("delta", {}).get("direction") == "positive")
                delta_positive_rate = pos / len(deltas)
    except Exception:
        pass
    dims["frontier_health"] = min(30, round(
        ground_rate * 15 + min(align_reviews, 5) * 2 + delta_positive_rate * 15
    ))

    # ── Velocity (max 20) ──
    v0_score = _compute_compounding_score(brain)
    cycle_path = brain / "meta" / "compounding_cycle.json"
    prev_score = 0
    if cycle_path.exists():
        try:
            cycle = json.loads(cycle_path.read_text())
            prev_cycles = cycle.get("previous_cycles", [])
            if prev_cycles:
                prev_score = prev_cycles[-1].get("score_end", 0)
        except Exception:
            pass
    ratio = v0_score / max(prev_score, 1) if prev_score > 0 else 1.0
    dims["velocity"] = min(20, round(ratio * 10))

    # ── Continuity (max 10) ──
    active_days = 0
    try:
        sessions_dir = brain / "sessions"
        if sessions_dir.exists():
            for sf in sessions_dir.glob("*.json"):
                try:
                    s = json.loads(sf.read_text())
                    ts = s.get("created_at", s.get("start_time", s.get("timestamp", "")))[:10]
                    if ts >= week_ago_str:
                        active_days += 1
                except Exception:
                    pass
    except Exception:
        pass
    active_days = min(active_days, 7)
    dims["continuity"] = min(10, round(active_days * 1.5))

    # ── Training Signal (max 10) ──
    sft_count = 0
    dpo_count = 0
    training_dir = brain / "training"
    turns_path = training_dir / "loop_turns.jsonl"
    prefs_path = training_dir / "preference_pairs.jsonl"
    if turns_path.exists():
        sft_count = sum(1 for line in turns_path.read_text(encoding="utf-8").splitlines() if line.strip())
    if prefs_path.exists():
        dpo_count = sum(1 for line in prefs_path.read_text(encoding="utf-8").splitlines() if line.strip())
    dims["training_signal"] = min(10, round(sft_count * 0.3 + dpo_count * 1.0))

    total = sum(dims.values())
    if total >= 80:
        band = "COMPOUNDING"
    elif total >= 60:
        band = "GROWING"
    elif total >= 40:
        band = "STALLING"
    elif total >= 20:
        band = "DECAYING"
    else:
        band = "COLD"

    return {
        "v2_score": total,
        "band": band,
        "dimensions": dims,
        "v0_score": v0_score,
    }


def _load_or_create_cycle(brain: Path, cycle_path: Path) -> dict:
    """Load existing cycle state or create a fresh one."""
    if cycle_path.exists():
        try:
            return json.loads(cycle_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass  # Corrupted — create fresh
    return _create_new_cycle(brain, cycle_id=1)


def _create_new_cycle(brain: Path, cycle_id: int) -> dict:
    """Create a new weekly cycle starting from this week's Monday."""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    week_start = monday.strftime("%Y-%m-%d")

    daily_actions = {
        0: "GAP_ANALYSIS", 1: "BUILD", 2: "TEST",
        3: "REFLECT", 4: "SHIP", 5: "AUDIT", 6: "CONSOLIDATE",
    }

    days = {}
    for i in range(7):
        day = monday + timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        days[day_str] = {
            "action": daily_actions[i],
            "planned": True,
            "completed": False,
            "score_at_start": None,
            "score_at_end": None,
        }

    v2 = _compute_compounding_score_v2(brain)
    return {
        "cycle_id": cycle_id,
        "week_start": week_start,
        "days": days,
        "weekly_score_start": v2["v2_score"],
        "weekly_score_start_v0": v2["v0_score"],
        "weekly_score_start_v2": v2,
        "weekly_score_end": None,
        "weekly_delta": None,
        "previous_cycles": [],
    }


def _save_cycle(cycle: dict, path: Path):
    """Atomic JSON write with temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w') as f:
        json.dump(cycle, f, indent=2)
    tmp.rename(path)


def _get_day_of_week() -> str:
    """Get current day of week."""
    return datetime.now().strftime("%A")


def _get_week_number() -> int:
    """Get current ISO week number."""
    return datetime.now().isocalendar()[1]


def _compounding_loop_status_impl() -> Dict:
    """
    Get the current status of the Compounding v0 Loop.
    
    Shows:
    - What day of the loop we're on
    - What the founder should do today
    - Progress metrics (engrams written this week, tasks completed)
    - Compounding score (Day 7 output quality vs Day 1)
    """
    from .common import get_brain_path
    from .morning_brief_ops import _morning_brief_impl
    
    brain = get_brain_path()
    day = _get_day_of_week()
    week = _get_week_number()
    
    # Day-specific actions from the design thinking deliverables
    day_actions = {
        "Monday": {
            "action": "GAP_ANALYSIS",
            "task": "Identify what's missing to make Nucleus feel alive",
            "engram_key": "alive_moment_definition",
            "output": "1-page gap analysis",
        },
        "Tuesday": {
            "action": "BUILD",
            "task": "Implement the top gap from yesterday's analysis",
            "engram_key": "feature_x_implemented",
            "output": "Working PR or script",
        },
        "Wednesday": {
            "action": "TEST",
            "task": "Verify yesterday's build with tests and smoke tests",
            "engram_key": "feature_x_verified",
            "output": "Test report",
        },
        "Thursday": {
            "action": "REFLECT",
            "task": "Synthesize learnings from this week so far",
            "engram_key": f"week_{week}_synthesis",
            "output": "Weekly learning summary",
        },
        "Friday": {
            "action": "SHIP",
            "task": "Deploy and release the week's work",
            "engram_key": f"release_v1_0_X",
            "output": "Deployed version",
        },
        "Saturday": {
            "action": "AUDIT",
            "task": "Review telemetry and tool usage metrics",
            "engram_key": f"telemetry_week_{week}",
            "output": "Telemetry report",
        },
        "Sunday": {
            "action": "CONSOLIDATE",
            "task": "Auto-consolidate engrams and prune stale memory",
            "engram_key": f"consolidation_week_{week}",
            "output": "Clean ledger",
        },
    }
    
    today = day_actions.get(day, day_actions["Monday"])
    
    # Get morning brief data for metrics
    brief = _morning_brief_impl()
    memory = brief.get("sections", {}).get("memory", {})
    tasks = brief.get("sections", {}).get("tasks", {})
    hooks = brief.get("sections", {}).get("hook_health", {})
    
    # Calculate week's engram writes
    engram_count = memory.get("count", 0)
    
    # Score v2: multi-dimensional (knowledge, frontier, velocity, continuity, training)
    v2 = _compute_compounding_score_v2(brain)
    compounding_score = v2["v2_score"]

    auto_writes = hooks.get("outcomes", {}).get("ADD", 0)
    errors = hooks.get("outcomes", {}).get("ERROR", 0)

    response = {
        "day_of_week": day,
        "week_number": week,
        "today": today,
        "metrics": {
            "total_engrams": engram_count,
            "auto_writes_this_session": auto_writes,
            "error_count": errors,
            "compounding_score": compounding_score,
            "band": v2["band"],
            "dimensions": v2["dimensions"],
            "v0_score": v2["v0_score"],
        },
        "recommendation": brief.get("recommendation", {}),
        "formatted": _format_loop_status(day, week, today, compounding_score, brief, v2),
    }

    # ── Artery 7: Track cycle state ──
    if not os.environ.get("NUCLEUS_DISABLE_ARTERY_7"):
        try:
            cycle_path = brain / "meta" / "compounding_cycle.json"
            cycle = _load_or_create_cycle(brain, cycle_path)

            today_str = datetime.now().strftime("%Y-%m-%d")
            today_entry = cycle.get("days", {}).get(today_str, {})

            # Record score at day start if not yet recorded
            if today_entry and today_entry.get("score_at_start") is None:
                today_entry["score_at_start"] = compounding_score
                cycle["days"][today_str] = today_entry
                _save_cycle(cycle, cycle_path)

            # Build cycle context for response
            prev = cycle.get("previous_cycles", [])
            days_completed = sum(
                1 for d in cycle.get("days", {}).values() if d.get("completed")
            )
            avg_delta = (
                sum(p.get("delta", 0) for p in prev) / len(prev) if prev else 0
            )
            current_delta = compounding_score - cycle.get("weekly_score_start", 0)

            response["cycle"] = {
                "cycle_id": cycle.get("cycle_id"),
                "week_start": cycle.get("week_start"),
                "days_completed": days_completed,
                "days_total": len(cycle.get("days", {})),
                "weekly_score_start": cycle.get("weekly_score_start"),
                "current_score": compounding_score,
                "current_delta": current_delta,
                "trend": "accelerating" if current_delta > avg_delta else "steady" if not prev else "decelerating",
                "previous_delta": prev[-1].get("delta") if prev else None,
            }
        except Exception:
            pass  # Never let cycle tracking break status

    return response


def _format_loop_status(day: str, week: int, today: Dict, score: int, brief: Dict, v2: Dict = None) -> str:
    """Format the loop status as a readable output."""
    lines = []
    band = (v2 or {}).get("band", "")
    lines.append("=" * 60)
    lines.append(f"🔄 COMPOUNDING LOOP STATUS [{band}]")
    lines.append(f"   Week {week} | {day}")
    lines.append("=" * 60)

    lines.append(f"\n📅 TODAY'S ACTION: {today['action']}")
    lines.append("-" * 40)
    lines.append(f"  Task: {today['task']}")
    lines.append(f"  Output: {today['output']}")
    lines.append(f"  Engram to write: {today['engram_key']}")

    memory = brief.get("sections", {}).get("memory", {})
    hooks = brief.get("sections", {}).get("hook_health", {})

    lines.append(f"\n📊 COMPOUNDING SCORE: {score}/100 ({band})")
    lines.append("-" * 40)
    if v2 and v2.get("dimensions"):
        dims = v2["dimensions"]
        lines.append(f"  Knowledge Metabolism: {dims.get('knowledge_metabolism', 0)}/30")
        lines.append(f"  Frontier Health:      {dims.get('frontier_health', 0)}/30")
        lines.append(f"  Velocity:             {dims.get('velocity', 0)}/20")
        lines.append(f"  Continuity:           {dims.get('continuity', 0)}/10")
        lines.append(f"  Training Signal:      {dims.get('training_signal', 0)}/10")
    lines.append(f"  Total engrams: {memory.get('count', 0)}")
    lines.append(f"  Auto-writes: {hooks.get('outcomes', {}).get('ADD', 0)}")

    # Band interpretation
    interp = {
        "COMPOUNDING": "🚀 EXCELLENT — Nucleus is compounding rapidly",
        "GROWING": "📈 GOOD — Keep writing engrams daily",
        "STALLING": "⚠️ STALLING — Need more consistent daily use",
        "DECAYING": "🔴 DECAYING — Activity dropping. Resume daily loop.",
        "COLD": "🔴 COLD — Nucleus isn't being used. Start with morning_brief!",
    }
    lines.append(f"  {interp.get(band, interp['COLD'])}")
    
    lines.append(f"\n🎯 MORNING BRIEF RECOMMENDATION")
    lines.append("-" * 40)
    rec = brief.get("recommendation", {})
    if rec:
        lines.append(f"  Action: {rec.get('action', '?')}")
        lines.append(f"  Task: {rec.get('task', 'No task')[:70]}")
    
    lines.append("=" * 60)
    return "\n".join(lines)


def _end_of_day_capture_impl(
    summary: str,
    key_decisions: List[str] = None,
    blockers: List[str] = None,
) -> Dict:
    """
    Capture end-of-day learnings as engrams.
    
    This is the ENGRAM OPS step of the Compounding Loop.
    Run this at the end of each work session to persist learnings.
    
    Args:
        summary: What was accomplished today (2-3 sentences)
        key_decisions: List of decisions made (auto-written as engrams)
        blockers: List of blockers encountered (for tomorrow's context)
    
    Returns:
        Dict with written engrams and next-day priming info.
    """
    from .common import get_brain_path
    from .engram_ops import _brain_write_engram_impl
    from .event_ops import _emit_event
    
    brain = get_brain_path()
    day = _get_day_of_week()
    week = _get_week_number()
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    written_engrams = []
    
    # Write daily summary engram
    summary_key = f"daily_summary_{timestamp}"
    result = _brain_write_engram_impl(
        key=summary_key,
        value=summary,
        context="Decision",
        intensity=7,
    )
    written_engrams.append({"key": summary_key, "result": result})
    
    # Write each key decision as a separate engram
    if key_decisions:
        for i, decision in enumerate(key_decisions):
            decision_key = f"decision_{timestamp}_{i+1}"
            result = _brain_write_engram_impl(
                key=decision_key,
                value=decision,
                context="Decision",
                intensity=8,
            )
            written_engrams.append({"key": decision_key, "result": result})
    
    # Write blockers for tomorrow's context
    if blockers:
        blocker_key = f"blockers_{timestamp}"
        result = _brain_write_engram_impl(
            key=blocker_key,
            value="; ".join(blockers),
            context="Decision",
            intensity=9,  # High intensity so it surfaces tomorrow
        )
        written_engrams.append({"key": blocker_key, "result": result})
    
    # Emit event for the capture
    _emit_event("end_of_day_captured", "compounding_loop", {
        "day": day,
        "week": week,
        "summary_length": len(summary),
        "decisions_count": len(key_decisions) if key_decisions else 0,
        "blockers_count": len(blockers) if blockers else 0,
    })
    
    # ── Artery 7: Mark today as completed in cycle state ──
    if not os.environ.get("NUCLEUS_DISABLE_ARTERY_7"):
        try:
            cycle_path = brain / "meta" / "compounding_cycle.json"
            if cycle_path.exists():
                cycle = json.loads(cycle_path.read_text())
                today_str = datetime.now().strftime("%Y-%m-%d")
                if today_str in cycle.get("days", {}):
                    cycle["days"][today_str]["completed"] = True
                    v2_eod = _compute_compounding_score_v2(brain)
                    cycle["days"][today_str]["score_at_end"] = v2_eod["v2_score"]
                    cycle["days"][today_str]["score_v2"] = v2_eod
                    _save_cycle(cycle, cycle_path)
        except Exception:
            pass  # Never let cycle tracking break EOD capture

    return {
        "success": True,
        "day": day,
        "week": week,
        "engrams_written": len(written_engrams),
        "details": written_engrams,
        "next_step": "Run brain_morning_brief tomorrow to see these learnings applied.",
    }


def _session_start_inject_impl() -> Dict:
    """
    Session-start auto-injection of top engrams.
    
    This is the NEXT SESSION step of the Compounding Loop.
    Automatically retrieves and injects the most relevant context
    at the start of each session.
    
    Returns:
        Dict with injected context ready to be used.
    """
    from .common import get_brain_path
    from .morning_brief_ops import _retrieve_top_engrams, _retrieve_tasks
    
    brain = get_brain_path()
    
    # Get top 10 engrams by scoring
    memory = _retrieve_top_engrams(brain, limit=10)
    tasks = _retrieve_tasks(brain)
    
    # Format as injection context
    context_lines = []
    
    context_lines.append("=== SESSION START CONTEXT ===")
    context_lines.append("")
    
    # Top memories
    engrams = memory.get("engrams", [])
    if engrams:
        context_lines.append("📝 KEY MEMORIES:")
        for e in engrams[:5]:
            context_lines.append(f"  • {e['key']}: {e['value'][:100]}")
        context_lines.append("")
    
    # Current tasks
    in_progress = tasks.get("in_progress", [])
    pending = tasks.get("pending", [])
    
    if in_progress:
        context_lines.append("🔵 IN PROGRESS:")
        for t in in_progress[:3]:
            context_lines.append(f"  • [{t['id']}] {t['description'][:80]}")
        context_lines.append("")
    
    if pending:
        context_lines.append("⚪ PENDING:")
        for t in pending[:3]:
            context_lines.append(f"  • [{t['id']}] {t['description'][:80]}")
        context_lines.append("")
    
    context_lines.append("=== END CONTEXT ===")
    
    return {
        "injected": True,
        "engram_count": len(engrams),
        "task_count": len(in_progress) + len(pending),
        "context": "\n".join(context_lines),
        "top_engrams": engrams[:5],
        "active_tasks": in_progress[:3],
    }


def _weekly_consolidation_impl(dry_run: bool = True) -> Dict:
    """
    Weekly consolidation — Sunday's automated task.
    
    What it does:
    1. Archive old engrams with TTL expiry
    2. Compute NOOP ratio and flag if > 50%
    3. Generate weekly synthesis engram
    4. Clean up stale tasks
    
    Args:
        dry_run: If True, preview without making changes
    
    Returns:
        Dict with consolidation results.
    """
    from .common import get_brain_path
    from .consolidation_ops import _garbage_collect_tasks, _archive_resolved_files, _rotate_all_jsonl
    from .engram_ops import _brain_query_engrams_impl

    brain = get_brain_path()
    week = _get_week_number()

    results = {
        "week": week,
        "dry_run": dry_run,
        "actions": [],
    }

    # 0. Rotate oversized JSONL files
    if not dry_run:
        try:
            rotation = _rotate_all_jsonl()
            rotated = [r for r in rotation if r.get("rotated")]
            if rotated:
                results["actions"].append({
                    "action": "rotate_jsonl",
                    "rotated_files": [r["file"] for r in rotated],
                    "total_archived_lines": sum(r["archived_lines"] for r in rotated),
                })
        except Exception as e:
            results["actions"].append({"action": "rotate_jsonl", "error": str(e)})

    # 1. Archive old tasks
    try:
        gc_result = _garbage_collect_tasks(max_age_hours=168, dry_run=dry_run)  # 7 days
        results["actions"].append({
            "action": "garbage_collect_tasks",
            "archived": gc_result.get("archived_count", 0),
            "kept": gc_result.get("kept_count", 0),
        })
    except Exception as e:
        results["actions"].append({
            "action": "garbage_collect_tasks",
            "error": str(e),
        })
    
    # 2. Archive resolved files
    try:
        archive_result = _archive_resolved_files()
        results["actions"].append({
            "action": "archive_resolved_files",
            "archived": archive_result.get("archived_count", 0),
        })
    except Exception as e:
        results["actions"].append({
            "action": "archive_resolved_files",
            "error": str(e),
        })
    
    # 3. Compute NOOP ratio from hook metrics
    try:
        from .engram_hooks import get_hook_metrics_summary
        hooks = get_hook_metrics_summary(brain)
        outcomes = hooks.get("outcomes", {})
        total = sum(outcomes.values())
        noops = outcomes.get("NOOP", 0)
        noop_ratio = noops / total if total > 0 else 0
        
        results["noop_ratio"] = noop_ratio
        if noop_ratio > 0.5:
            results["warning"] = f"NOOP ratio is {noop_ratio:.0%} — tighten write triggers"
    except Exception as e:
        results["noop_ratio"] = None
        results["noop_error"] = str(e)
    
    # 4. Generate weekly synthesis (summary of top engrams this week)
    try:
        from .morning_brief_ops import _retrieve_top_engrams
        top = _retrieve_top_engrams(brain, limit=20)
        engrams = top.get("engrams", [])
        
        if engrams and not dry_run:
            from .engram_ops import _brain_write_engram_impl
            synthesis = "; ".join([e["key"] for e in engrams[:10]])
            _brain_write_engram_impl(
                key=f"week_{week}_synthesis",
                value=f"Week {week} top themes: {synthesis}",
                context="Strategy",
                intensity=8,
            )
            results["actions"].append({
                "action": "weekly_synthesis",
                "written": True,
                "themes_count": len(engrams[:10]),
            })
    except Exception as e:
        results["actions"].append({
            "action": "weekly_synthesis",
            "error": str(e),
        })

    # ── Artery 7: Close compounding cycle + write spiral engram ──
    if not os.environ.get("NUCLEUS_DISABLE_ARTERY_7"):
        try:
            cycle_path = brain / "meta" / "compounding_cycle.json"
            if cycle_path.exists():
                cycle = json.loads(cycle_path.read_text())
                v2 = _compute_compounding_score_v2(brain)
                final_score = v2["v2_score"]

                cycle["weekly_score_end"] = final_score
                cycle["weekly_score_end_v0"] = v2["v0_score"]
                cycle["weekly_delta"] = final_score - cycle.get("weekly_score_start", 0)
                cycle["v2_score"] = v2

                completed = sum(
                    1 for d in cycle.get("days", {}).values() if d.get("completed")
                )

                # Archive this cycle
                prev = cycle.get("previous_cycles", [])
                prev.append({
                    "cycle_id": cycle["cycle_id"],
                    "delta": cycle["weekly_delta"],
                    "week_start": cycle["week_start"],
                    "days_completed": completed,
                    "score_start": cycle.get("weekly_score_start", 0),
                    "score_end": final_score,
                })

                results["actions"].append({
                    "action": "close_cycle",
                    "cycle_id": cycle["cycle_id"],
                    "delta": cycle["weekly_delta"],
                    "days_completed": completed,
                })

                # Write spiral engram (visible compound curve)
                if not dry_run and prev:
                    try:
                        avg_delta = sum(p.get("delta", 0) for p in prev) / len(prev)

                        # Sparkline from last 12 cycles
                        deltas_12 = [p.get("delta", 0) for p in prev[-12:]]
                        bars = "▁▂▃▄▅▆▇█"
                        max_d = max(abs(d) for d in deltas_12) if deltas_12 else 1
                        sparkline = "".join(
                            bars[min(int(((d - min(0, min(deltas_12))) / max(max_d, 1)) * 7), 7)]
                            for d in deltas_12
                        ) if deltas_12 else ""

                        spiral_text = (
                            f"Week {cycle['cycle_id']}: "
                            f"score {cycle.get('weekly_score_start', '?')}->{final_score} "
                            f"(d{cycle['weekly_delta']:+d}). "
                            f"Avg: d{avg_delta:+.1f}/wk. {sparkline}"
                        )

                        from .memory_pipeline import MemoryPipeline
                        pipeline = MemoryPipeline(brain_path=brain)
                        pipeline.process(
                            text=spiral_text,
                            context="Strategy",
                            intensity=8,
                            source_agent="compounding_loop",
                            key=f"spiral_week_{cycle['cycle_id']}",
                        )

                        results["actions"].append({
                            "action": "spiral_engram",
                            "written": True,
                            "delta": cycle["weekly_delta"],
                            "avg_delta": round(avg_delta, 1),
                            "sparkline": sparkline,
                        })
                    except Exception:
                        pass  # Spiral engram is nice-to-have

                # Create new cycle
                new_cycle = _create_new_cycle(brain, cycle["cycle_id"] + 1)
                new_cycle["previous_cycles"] = prev[-52:]  # Keep 1 year
                _save_cycle(new_cycle, cycle_path)

                results["actions"].append({
                    "action": "new_cycle",
                    "cycle_id": new_cycle["cycle_id"],
                })
        except Exception as e:
            results["actions"].append({
                "action": "close_cycle",
                "error": str(e),
            })

    return results
