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
    
    from mcp_server_nucleus import (
        brain_satellite_view,
        brain_metrics,
        brain_commitment_health,
        brain_open_loops,
        brain_list_tasks,
        brain_read_events,
        brain_emit_event
    )
    from mcp_server_nucleus.runtime.event_stream import EventTypes, EventSeverity
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def get_brain_path():
    """Get the brain path from environment"""
    return Path(os.getenv("NUCLEAR_BRAIN_PATH", PROJECT_ROOT / ".brain"))

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
