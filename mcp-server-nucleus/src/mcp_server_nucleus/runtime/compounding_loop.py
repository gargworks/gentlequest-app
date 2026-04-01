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

    return {
        "cycle_id": cycle_id,
        "week_start": week_start,
        "days": days,
        "weekly_score_start": _compute_compounding_score(brain),
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
    
    # Calculate compounding score (rough metric)
    # Higher score = more engrams, more auto-writes, fewer errors
    auto_writes = hooks.get("outcomes", {}).get("ADD", 0)
    errors = hooks.get("outcomes", {}).get("ERROR", 0)
    efficiency = hooks.get("efficiency", 0) if isinstance(hooks.get("efficiency"), (int, float)) else 0
    
    compounding_score = min(100, int(
        (engram_count * 0.5) +
        (auto_writes * 2) +
        (efficiency * 50) -
        (errors * 5)
    ))
    
    response = {
        "day_of_week": day,
        "week_number": week,
        "today": today,
        "metrics": {
            "total_engrams": engram_count,
            "auto_writes_this_session": auto_writes,
            "error_count": errors,
            "compounding_score": compounding_score,
        },
        "recommendation": brief.get("recommendation", {}),
        "formatted": _format_loop_status(day, week, today, compounding_score, brief),
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


def _format_loop_status(day: str, week: int, today: Dict, score: int, brief: Dict) -> str:
    """Format the loop status as a readable output."""
    lines = []
    lines.append("=" * 60)
    lines.append("🔄 COMPOUNDING v0 LOOP STATUS")
    lines.append(f"   Week {week} | {day}")
    lines.append("=" * 60)
    
    lines.append(f"\n📅 TODAY'S ACTION: {today['action']}")
    lines.append("-" * 40)
    lines.append(f"  Task: {today['task']}")
    lines.append(f"  Output: {today['output']}")
    lines.append(f"  Engram to write: {today['engram_key']}")
    
    memory = brief.get("sections", {}).get("memory", {})
    hooks = brief.get("sections", {}).get("hook_health", {})
    
    lines.append(f"\n📊 COMPOUNDING METRICS")
    lines.append("-" * 40)
    lines.append(f"  Total engrams: {memory.get('count', 0)}")
    lines.append(f"  Auto-writes: {hooks.get('outcomes', {}).get('ADD', 0)}")
    lines.append(f"  Compounding score: {score}/100")
    
    # Score interpretation
    if score >= 80:
        interpretation = "🚀 EXCELLENT — Nucleus is compounding rapidly"
    elif score >= 50:
        interpretation = "📈 GOOD — Keep writing engrams daily"
    elif score >= 20:
        interpretation = "⚠️ SLOW — Need more consistent daily use"
    else:
        interpretation = "🔴 COLD — Nucleus isn't being used. Start with morning_brief!"
    lines.append(f"  {interpretation}")
    
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
                    cycle["days"][today_str]["score_at_end"] = _compute_compounding_score(brain)
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
    from .consolidation_ops import _garbage_collect_tasks, _archive_resolved_files
    from .engram_ops import _brain_query_engrams_impl
    
    brain = get_brain_path()
    week = _get_week_number()
    
    results = {
        "week": week,
        "dry_run": dry_run,
        "actions": [],
    }
    
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
                final_score = _compute_compounding_score(brain)

                cycle["weekly_score_end"] = final_score
                cycle["weekly_delta"] = final_score - cycle.get("weekly_score_start", 0)

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
