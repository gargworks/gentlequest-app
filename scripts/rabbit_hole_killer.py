#!/usr/bin/env python3
"""
30-Minute Rabbit Hole Killer
Automated detection and closure of open loops

Usage:
    python3 rabbit_hole_killer.py
    nucleus rabbit-holes kill
"""

import subprocess
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

BRAIN_PATH = Path(os.getenv("NUCLEAR_BRAIN_PATH", "/Users/lokeshgarg/ai-mvp-backend/.brain"))
ARTIFACTS_PATH = BRAIN_PATH / "artifacts"

def detect_rabbit_holes() -> Dict[str, List[str]]:
    """Scan for open loops using ripgrep and fd"""
    results = {
        'checklists': [],
        'todos': [],
        'drafts': [],
        'decisions': []
    }
    
    # Find open checklist items
    try:
        result = subprocess.run(
            ["rg", r"- \[ \]", str(ARTIFACTS_PATH), "--type", "md", "-l"],
            capture_output=True,
            text=True
        )
        if result.stdout:
            results['checklists'] = result.stdout.strip().split('\n')
    except Exception as e:
        print(f"⚠️  Checklist scan failed: {e}")
    
    # Find TODOs
    try:
        result = subprocess.run(
            ["rg", "TODO", str(ARTIFACTS_PATH), "--type", "md", "-l"],
            capture_output=True,
            text=True
        )
        if result.stdout:
            results['todos'] = result.stdout.strip().split('\n')
    except Exception as e:
        print(f"⚠️  TODO scan failed: {e}")
    
    # Find draft files
    try:
        result = subprocess.run(
            ["fd", "draft", str(ARTIFACTS_PATH)],
            capture_output=True,
            text=True
        )
        if result.stdout:
            results['drafts'] = result.stdout.strip().split('\n')
    except Exception as e:
        print(f"⚠️  Draft scan failed: {e}")
    
    # Find board decisions
    try:
        result = subprocess.run(
            ["rg", "Board Decision", str(ARTIFACTS_PATH), "--type", "md", "-l"],
            capture_output=True,
            text=True
        )
        if result.stdout:
            results['decisions'] = result.stdout.strip().split('\n')
    except Exception as e:
        print(f"⚠️  Decision scan failed: {e}")
    
    return results

def categorize_file(file_path: str) -> Dict:
    """Determine action for each rabbit hole"""
    if not os.path.exists(file_path):
        return None
    
    # Calculate age
    file_age_days = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))).days
    
    # Read content
    try:
        with open(file_path, 'r') as f:
            content = f.read().lower()
    except:
        return None
    
    # Categorization logic
    action = 'SCHEDULE'  # default
    reason = ''
    
    if file_age_days > 30:
        action = 'ARCHIVE'
        reason = f'Stale ({file_age_days} days old)'
    elif 'board decision' in content or 'action required' in content:
        action = 'SCHEDULE'
        reason = 'Important decision needs attention'
    elif 'draft' in file_path.lower() and file_age_days > 14:
        action = 'KILL'
        reason = f'Draft never finalized ({file_age_days} days)'
    elif file_age_days < 7 and content.count('- [ ]') <= 2:
        action = 'DO_NOW'
        reason = 'Recent and small scope'
    
    return {
        'file': file_path,
        'age_days': file_age_days,
        'action': action,
        'reason': reason
    }

def generate_report(all_files: List[str]) -> Dict:
    """Process all files and generate closure report"""
    categorized = []
    
    for file in all_files:
        if file:  # skip empty strings
            cat = categorize_file(file)
            if cat:
                categorized.append(cat)
    
    # Count by action
    stats = {
        'total': len(categorized),
        'do_now': len([c for c in categorized if c['action'] == 'DO_NOW']),
        'schedule': len([c for c in categorized if c['action'] == 'SCHEDULE']),
        'archive': len([c for c in categorized if c['action'] == 'ARCHIVE']),
        'kill': len([c for c in categorized if c['action'] == 'KILL'])
    }
    
    return {
        'items': categorized,
        'stats': stats,
        'timestamp': datetime.now().isoformat()
    }

def save_report(report: Dict):
    """Save closure report as artifact"""
    output_file = Path.home() / ".gemini/antigravity/brain" / os.getenv("BRAIN_ID", "") / "RABBIT_HOLE_KILLER_RECEIPT.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    markdown = f"""# Rabbit Hole Killer - {datetime.now().strftime('%Y-%m-%d, %I:%M %p')}

## 📊 Detection Results

| Category | Count |
|:---------|:------|
| **Total detected** | {report['stats']['total']} |
| DO NOW (quick wins) | {report['stats']['do_now']} |
| SCHEDULE (needs time) | {report['stats']['schedule']} |
| ARCHIVE (defer) | {report['stats']['archive']} |
| KILL (no longer relevant) | {report['stats']['kill']} |

---

## 🎯 Actions Required

### DO NOW (Execute immediately)
"""
    
    for item in report['items']:
        if item['action'] == 'DO_NOW':
            markdown += f"- [ ] `{Path(item['file']).name}` - {item['reason']}\n"
    
    markdown += "\n### SCHEDULE\n"
    for item in report['items']:
        if item['action'] == 'SCHEDULE':
            markdown += f"- [ ] `{Path(item['file']).name}` - {item['reason']}\n"
    
    markdown += "\n### ARCHIVE\n"
    for item in report['items']:
        if item['action'] == 'ARCHIVE':
            markdown += f"- `{Path(item['file']).name}` - {item['reason']}\n"
    
    markdown += "\n### KILL\n"
    for item in report['items']:
        if item['action'] == 'KILL':
            markdown += f"- `{Path(item['file']).name}` - {item['reason']}\n"
    
    markdown += f"\n---\n\n**Next rabbit hole killer:** {(datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')}\n"
    
    with open(output_file, 'w') as f:
        f.write(markdown)
    
    print(f"\n📄 Report saved: {output_file}")
    return str(output_file)

def main():
    print("🐰 30-Minute Rabbit Hole Killer")
    print("=" * 50)
    
    print("\n🔍 Step 1: Detecting rabbit holes...")
    raw_results = detect_rabbit_holes()
    
    # Flatten all files
    all_files = []
    for category, files in raw_results.items():
        all_files.extend(files)
    
    # Remove duplicates
    all_files = list(set(all_files))
    
    print(f"   Found {len(all_files)} potential rabbit holes")
    
    print("\n📊 Step 2: Categorizing...")
    report = generate_report(all_files)
    
    print(f"""
   Results:
   - DO NOW: {report['stats']['do_now']}
   - SCHEDULE: {report['stats']['schedule']}
   - ARCHIVE: {report['stats']['archive']}
   - KILL: {report['stats']['kill']}
    """)
    
    print("\n💾 Step 3: Generating report...")
    report_path = save_report(report)
    
    print("\n✅ Done!")
    print(f"\nNext steps:")
    print(f"1. Review report: {report_path}")
    print(f"2. Execute DO NOW items")
    print(f"3. Schedule SCHEDULE items")
    print(f"4. Archive/Kill as recommended")
    
    return report

if __name__ == "__main__":
    main()
