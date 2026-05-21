#!/usr/bin/env python3
"""
Nucleus Health Check & Analytics
=================================
Periodic health check script that generates analytics dashboard
and emits health events.

Usage:
    python3 scripts/nucleus_health_check.py [--emit-event]
    
Cron:
    0 9 * * * cd /path/to/ai-mvp-backend && python3 scripts/nucleus_health_check.py --emit-event
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add MCP server to path
PROJECT_ROOT = Path(__file__).parent.parent
SERVER_SRC = PROJECT_ROOT / "mcp-server-nucleus" / "src"
sys.path.insert(0, str(SERVER_SRC))

try:
    import warnings
    warnings.filterwarnings('ignore', category=FutureWarning, module='google.generativeai')

    # Top-level brain_* exports were removed during the orchestration refactor;
    # the functions now live behind nucleus_orchestration action handlers + their
    # underlying runtime impls. This script wires directly to the impls so it
    # can run standalone without the MCP server up.
    from mcp_server_nucleus import commitment_ledger
    from mcp_server_nucleus.runtime.satellite_ops import (
        _get_satellite_view,
        _format_satellite_cli,
    )
    from mcp_server_nucleus.runtime.task_ops import _list_tasks
    from mcp_server_nucleus.runtime.event_ops import _emit_event, _read_events
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def get_brain_path():
    """Get the brain path from environment"""
    return Path(os.getenv("NUCLEUS_BRAIN_PATH", PROJECT_ROOT / ".brain"))


# ── Adapter shims preserving the original brain_* API used below ──
# These mirror the orchestration tool handlers (_h_satellite, _h_metrics, etc.)
# so the rest of this script keeps the call shapes it was written against.

def brain_satellite_view(detail_level: str = "standard") -> str:
    view = _get_satellite_view(detail_level)
    return _format_satellite_cli(view)


def brain_metrics() -> str:
    metrics = commitment_ledger.calculate_metrics(get_brain_path())
    output = (
        f"## 📊 Coordination Metrics (Last 7 Days)\n\n"
        f"**🚀 Velocity:** {metrics['velocity_7d']} items closed\n"
        f"**⏱️ Speed:** {metrics['avg_days_to_close']} days avg\n\n"
        f"**📈 Closure Rates by Type:**\n"
    )
    if metrics["closure_rates"]:
        for t, rate in metrics["closure_rates"].items():
            output += f"- {t}: {rate}\n"
    else:
        output += "(No closed items yet)\n"
    output += (
        f"\n**🧠 Current Load:**\n"
        f"- Total Open: {metrics['current_load']['total']}\n"
        f"- Red Tier: {metrics['current_load']['red']}\n"
    )
    return output


def brain_commitment_health() -> str:
    ledger = commitment_ledger.load_ledger(get_brain_path())
    stats = ledger.get("stats", {})
    total = stats.get("total_open", 0)
    green = stats.get("green_tier", 0)
    yellow = stats.get("yellow_tier", 0)
    red = stats.get("red_tier", 0)
    by_type = stats.get("by_type", {})
    if red > 0:
        mental_load, advice = "🔴 HIGH", "Focus on red-tier items first"
    elif yellow > 2:
        mental_load, advice = "🟡 MEDIUM", "Clear yellow items before they go red"
    elif total == 0:
        mental_load, advice = "✨ ZERO", "No open loops - guilt-free operation!"
    else:
        mental_load, advice = "🟢 LOW", "Looking good, maintain momentum"
    type_str = ", ".join([f"{t}: {c}" for t, c in by_type.items()]) if by_type else "(none)"
    last_scan = ledger.get("last_scan", "Never")
    last_scan_short = last_scan[:16] if last_scan and last_scan != "Never" else "Never"
    return (
        f"## 🎯 Commitment Health\n\n"
        f"**Open loops:** {total}\n"
        f"- 🟢 Green: {green}\n- 🟡 Yellow: {yellow}\n- 🔴 Red: {red}\n\n"
        f"**By type:** {type_str}\n\n"
        f"**Mental load:** {mental_load}\n"
        f"**Advice:** {advice}\n\n"
        f"**Last scan:** {last_scan_short}"
    )


def brain_open_loops(type_filter=None, tier_filter=None) -> str:
    ledger = commitment_ledger.load_ledger(get_brain_path())
    open_comms = [c for c in ledger["commitments"] if c["status"] == "open"]
    if type_filter:
        open_comms = [c for c in open_comms if c.get("type") == type_filter]
    if tier_filter:
        open_comms = [c for c in open_comms if c.get("tier") == tier_filter]
    if not open_comms:
        return "✅ No open loops! Guilt-free operation."
    by_type = {}
    for c in open_comms:
        t = c.get("type", "unknown")
        by_type.setdefault(t, []).append(c)
    type_emoji = {"task": "🔧", "todo": "☑️", "draft": "📝", "decision": "🤔"}
    output = f"## 📋 Open Loops ({len(open_comms)} total)\n\n"
    for t, items in by_type.items():
        output += f"### {type_emoji.get(t, '📌')} {t.upper()} ({len(items)})\n\n"
        items.sort(key=lambda x: ({"red": 0, "yellow": 1, "green": 2}.get(x.get("tier"), 3), -x.get("age_days", 0)))
        for c in items[:5]:
            te = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(c.get("tier"), "⚪")
            output += (
                f"{te} **{c['description'][:50]}**\n"
                f"   {c.get('age_days', 0)}d old | Suggested: {c.get('suggested_action')}\n"
                f"   ID: `{c['id']}`\n\n"
            )
        if len(items) > 5:
            output += f"   ...and {len(items) - 5} more\n\n"
    return output


def brain_list_tasks(status="PENDING"):
    return _list_tasks(status=status)


def brain_read_events(limit=10):
    return _read_events(limit=limit)


def brain_emit_event(emitter: str, event_type: str, data: dict, description: str = "") -> str:
    return _emit_event(event_type, emitter, data, description)

def collect_metrics():
    """Collect all health metrics"""
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "satellite": None,
        "metrics": None,
        "health": None,
        "open_loops": None,
        "tasks": None,
        "events": None,
        "consolidation": None,
    }
    
    try:
        # Get satellite view  
        sat = brain_satellite_view(detail_level='standard')
        metrics["satellite"] = sat
    except Exception as e:
        metrics["satellite"] = f"Error: {e}"
    
    try:
        # Get metrics
        met = brain_metrics()
        metrics["metrics"] = met
    except Exception as e:
        metrics["metrics"] = f"Error: {e}"
    
    try:
        # Get health
        health = brain_commitment_health()
        metrics["health"] = health
    except Exception as e:
        metrics["health"] = f"Error: {e}"
    
    try:
        # Get open loops
        loops = brain_open_loops()
        metrics["open_loops"] = loops
    except Exception as e:
        metrics["open_loops"] = f"Error: {e}"
    
    try:
        # Get tasks
        tasks = brain_list_tasks(status='PENDING')
        metrics["tasks"] = {"count": len(tasks), "items": [t["description"][:60] for t in tasks[:5]]}
    except Exception as e:
        metrics["tasks"] = f"Error: {e}"
    
    try:
        # Get recent events
        events = brain_read_events(limit=10)
        metrics["events"] = events
    except Exception as e:
        metrics["events"] = f"Error: {e}"

    try:
        # Get Brain Consolidation Status (MDR_010)
        brain_path = get_brain_path()
        raw_path = brain_path / "raw"
        if raw_path.exists():
            files = list(raw_path.glob("*.json"))
            count = len(files)
            size_mb = sum(f.stat().st_size for f in files) / (1024 * 1024)
            metrics["consolidation"] = {
                "raw_file_count": count,
                "raw_size_mb": round(size_mb, 2),
                "status": "accumulating" if count > 50 else "clean"
            }
        else:
            metrics["consolidation"] = {"status": "missing_dir"}
    except Exception as e:
        metrics["consolidation"] = f"Error: {e}"
    
    return metrics

def analyze_health(metrics):
    """Analyze metrics and determine health status"""
    status = {
        "overall": "healthy",
        "issues": [],
        "recommendations": []
    }
    
    # Parse health data
    health_text = metrics.get("health", "")
    if isinstance(health_text, str):
        if "🔴 Red: " in health_text and not "Red: 0" in health_text:
            status["overall"] = "warning"
            status["issues"].append("Red-tier commitments exist")
            status["recommendations"].append("Address red-tier items immediately")
        
        if "Mental load:** 🔴" in health_text:
            status["overall"] = "critical"
            status["issues"].append("High mental load")
            status["recommendations"].append("Close or delegate items to reduce load")
    
    # Check event activity
    events_data = metrics.get("events", "")
    if isinstance(events_data, str) and len(events_data.strip()) < 50:
        status["recommendations"].append("Event stream empty - consider emitting events for automation")
    
    return status

def generate_report(metrics, health):
    """Generate human-readable report"""
    report = []
    report.append("=" * 60)
    report.append("🧠 NUCLEUS HEALTH CHECK")
    report.append("=" * 60)
    report.append(f"Timestamp: {metrics['timestamp']}")
    report.append(f"Overall Status: {health['overall'].upper()}")
    report.append("")
    
    # Satellite view
    report.append("📍 SATELLITE VIEW:")
    if isinstance(metrics['satellite'], str):
        report.append(metrics['satellite'][:500])
    report.append("")
    
    # Metrics
    report.append("📊 METRICS:")
    if isinstance(metrics['metrics'], str):
        report.append(metrics['metrics'][:500])
    report.append("")
    
    # Health
    report.append("🏥 HEALTH:")
    if isinstance(metrics['health'], str):
        report.append(metrics['health'][:500])
    report.append("")
    
    # Open loops
    report.append("📋 OPEN LOOPS:")
    if isinstance(metrics['open_loops'], str):
        report.append(metrics['open_loops'][:500])
    report.append("")
    
    # Tasks
    report.append("✓ TASKS:")
    if isinstance(metrics['tasks'], dict):
        report.append(f"  Pending: {metrics['tasks']['count']}")
        for item in metrics['tasks'].get('items', []):
            report.append(f"  - {item}")
    report.append("")
    
    # Consolidation (MDR_010)
    report.append("💿 CONSOLIDATION (Brain Protocol):")
    cons = metrics.get('consolidation')
    if isinstance(cons, dict):
        report.append(f"  Raw Files: {cons.get('raw_file_count', 0)}")
        report.append(f"  Total Size: {cons.get('raw_size_mb', 0)} MB")
        report.append(f"  Status: {cons.get('status', 'unknown').upper()}")
    elif cons:
        report.append(str(cons))
    report.append("")

    # Issues & Recommendations
    if health['issues']:
        report.append("⚠️  ISSUES:")
        for issue in health['issues']:
            report.append(f"  - {issue}")
        report.append("")
    
    if health['recommendations']:
        report.append("💡 RECOMMENDATIONS:")
        for rec in health['recommendations']:
            report.append(f"  - {rec}")
        report.append("")
    
    report.append("=" * 60)
    
    return "\n".join(report)

def save_report(report, metrics):
    """Save report to .brain/meta/health_checks/"""
    brain_path = get_brain_path()
    health_dir = brain_path / "meta" / "health_checks"
    health_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save text report
    report_file = health_dir / f"health_check_{timestamp}.txt"
    report_file.write_text(report)
    
    # Save JSON metrics
    metrics_file = health_dir / f"health_check_{timestamp}.json"
    metrics_file.write_text(json.dumps(metrics, indent=2, default=str))
    
    return report_file, metrics_file

def emit_health_event(health, metrics):
    """Emit health check event"""
    try:
        brain_emit_event(
            emitter='health_check',
            event_type='health_status',
            data={
                'status': health['overall'],
                'issues_count': len(health['issues']),
                'timestamp': metrics['timestamp']
            },
            description=f"Health check: {health['overall']}"
        )
        print("✅ Health event emitted")
    except Exception as e:
        print(f"⚠️  Could not emit event: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Nucleus Health Check')
    parser.add_argument('--emit-event', action='store_true', help='Emit health event to event stream')
    parser.add_argument('--save', action='store_true', default=True, help='Save report to disk')
    args = parser.parse_args()
    
    print("🔍 Collecting metrics...")
    metrics = collect_metrics()
    
    print("📊 Analyzing health...")
    health = analyze_health(metrics)
    
    print("📝 Generating report...")
    report = generate_report(metrics, health)
    
    # Print report
    print(report)
    
    # Save report
    if args.save:
        report_file, metrics_file = save_report(report, metrics)
        print(f"\n📁 Saved to:")
        print(f"  - {report_file}")
        print(f"  - {metrics_file}")
    
    # Emit event
    if args.emit_event:
        emit_health_event(health, metrics)

if __name__ == "__main__":
    main()
