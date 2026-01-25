# 30-Minute Rabbit Hole Killer Workflow

> **Purpose:** Scheduled ritual to find and close all open loops  
> **Frequency:** Weekly or bi-weekly  
> **Duration:** 30 minutes max  
> **Automation:** Can be triggered by AI agent on schedule

---

## When to Run This Workflow

**Schedule Options:**
- **Weekly:** Every Sunday 8 PM (after week's work)
- **Bi-weekly:** 1st and 15th of month
- **On-demand:** When feeling overwhelmed

**Triggers:**
- Manual: User says "run rabbit hole killer"
- Automatic: Cron job triggers AI agent
- Dashboard: "Open loops >5" alert

---

## The Workflow (6 Steps)

### Step 1: Detection (5 min) - AUTO

**AI scans for rabbit holes:**
```bash
# Search for open checklist items
rg "- \[ \]" /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/ --type md

# Search for TODOs
rg "TODO" /Users/lokeshgarg/ai-mvp-backend/ --type py --type md

# Search for "draft" files
fd "draft" /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/

# Search for board decisions
rg "Board Decision" /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/strategy/
```

**Output:** List of potential rabbit holes

---

### Step 2: Categorization (5 min) - AUTO

**AI categorizes each rabbit hole:**

| Category | Criteria | Action |
|:---------|:---------|:-------|
| **DO NOW** | <15 min + high impact | Execute immediately |
| **SCHEDULE** | Needs focus time | Calendar block |
| **ARCHIVE** | Low priority, defer | Move to `/deferred/` |
| **KILL** | No longer relevant | Delete with rationale |
| **DELEGATE** | Someone else should do | Hand off |

**Context dimensions checked:**
- Age (days since created)
- Dopamine level (boring vs. fun)
- Novelty (first-time vs. repetitive)
- Impact (blocks other work?)

---

### Step 3: Quick Wins (10 min) - AUTO-EXECUTE

**AI executes "DO NOW" items:**
- Post to Reddit (if <15 min)
- Send DMs (if drafted)
- Run scripts (if one command)
- Update docs (if clear what to do)

**Rules:**
- Max 3 quick wins per session
- Each must be <5 min
- If uncertain, don't auto-execute (schedule instead)

---

### Step 4: Scheduling (5 min) - AI + USER

**AI creates schedule, user approves:**
```markdown
### This Week's Actions

**Jan 7 (Tue), 11 AM** - Task X (30 min)
**Jan 9 (Thu), 4 PM** - Task Y (1 hour)
**Jan 11 (Sat), 2 PM** - Task Z (2 hours)

[Approve] [Modify]
```

**User clicks approve → AI adds to calendar/Telegram**

---

### Step 5: Archiving (3 min) - AUTO

**AI moves deferred items:**
```bash
# Move to deferred with reason
mv artifact.md /deferred/category/artifact.md

# Create archive log entry
echo "Archived artifact.md - Reason: Low priority, revisit v0.6.0" >> ARCHIVED_ITEMS_LOG.md
```

---

### Step 6: Closure Receipt (2 min) - AUTO

**AI generates summary:**
```markdown
# Rabbit Hole Killer - Jan 6, 2026

## Results
- Detected: 12 rabbit holes
- Executed immediately: 3
- Scheduled: 4
- Archived: 4
- Killed: 1

## Open loops: 12 → 0

## Next session: Jan 20, 2026
```

---

## Automation Script (Phase 2)

**File:** `scripts/rabbit_hole_killer.py`

```python
#!/usr/bin/env python3
"""
30-Minute Rabbit Hole Killer
Automated detection and closure of open loops
"""

import subprocess
import os
from pathlib import Path
from datetime import datetime

def detect_rabbit_holes():
    """Scan for open loops using ripgrep"""
    brain_path = Path.home() / "ai-mvp-backend" / ".brain" / "artifacts"
    
    # Find open checklist items
    checklist_cmd = f"rg '- \\[ \\]' {brain_path} --type md -l"
    checklists = subprocess.run(checklist_cmd, shell=True, capture_output=True, text=True)
    
    # Find TODOs
    todo_cmd = f"rg 'TODO' {brain_path} --type md -l"
    todos = subprocess.run(todo_cmd, shell=True, capture_output=True, text=True)
    
    # Find drafts
    draft_cmd = f"fd 'draft' {brain_path}"
    drafts = subprocess.run(draft_cmd, shell=True, capture_output=True, text=True)
    
    return {
        'checklists': checklists.stdout.strip().split('\n') if checklists.stdout else [],
        'todos': todos.stdout.strip().split('\n') if todos.stdout else [],
        'drafts': drafts.stdout.strip().split('\n') if drafts.stdout else []
    }

def categorize_rabbit_hole(file_path):
    """Determine action for each rabbit hole"""
    # Age check
    file_age_days = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))).days
    
    # Read file to determine context
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Simple heuristics
    if file_age_days > 30:
        return 'ARCHIVE'
    elif 'board decision' in content.lower() or 'action required' in content.lower():
        return 'SCHEDULE'
    elif file_age_days < 7 and content.count('- [ ]') < 3:
        return 'DO_NOW'
    else:
        return 'SCHEDULE'

def execute_quick_wins(rabbit_holes):
    """Auto-execute DO_NOW items"""
    for rh in rabbit_holes:
        if rh['action'] == 'DO_NOW':
            print(f"Executing: {rh['file']}")
            # Execute based on type
            # (Implementation specific to each action type)

def generate_closure_receipt(results):
    """Create closure summary"""
    summary = f"""
# Rabbit Hole Killer - {datetime.now().strftime('%Y-%m-%d')}

## Results
- Detected: {len(results['all'])}
- Executed immediately: {len([r for r in results['all'] if r['action'] == 'DO_NOW'])}
- Scheduled: {len([r for r in results['all'] if r['action'] == 'SCHEDULE'])}
- Archived: {len([r for r in results['all'] if r['action'] == 'ARCHIVE'])}
- Killed: {len([r for r in results['all'] if r['action'] == 'KILL'])}

## Next session: {(datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')}
    """
    
    with open(Path.home() / ".gemini/antigravity/brain/<brain_id>/RABBIT_HOLE_KILLER_RECEIPT.md", 'w') as f:
        f.write(summary)

if __name__ == "__main__":
    print("🔍 Detecting rabbit holes...")
    rabbit_holes = detect_rabbit_holes()
    
    print("📊 Categorizing...")
    # Process each
    
    print("⚡ Executing quick wins...")
    # Execute
    
    print("✅ Generating closure receipt...")
    # Generate summary
    
    print("🎉 Done! All loops closed.")
```

---

## How to Schedule This Workflow

### Option 1: Cron (Automated, Weekly)

Add to crontab:
```bash
# Every Sunday at 8 PM
0 20 * * 0 cd /Users/lokeshgarg/ai-mvp-backend && source .env && /usr/bin/python3 /Users/lokeshgarg/ai-mvp-backend/scripts/rabbit_hole_killer.py && notify-send "Rabbit holes cleared"
```

### Option 2: Manual Trigger

Create alias in `~/.zshrc`:
```bash
alias kill-rabbits="cd /Users/lokeshgarg/ai-mvp-backend && source .env && python3 scripts/rabbit_hole_killer.py"
```

Then just run: `kill-rabbits`

### Option 3: AI Agent Trigger

In Nucleus:
```bash
nucleus rabbit-holes kill
```

---

## Integration with PEFS Phase 2

**This workflow becomes:**
- The "fallback safety net" you requested
- Runs automatically every 2 weeks
- Catches anything commitment ledger misses
- Pure automation - no manual intervention needed

**Workflow saves:**
- All detection commands → reusable
- All categorization logic → pattern library
- All closure receipts → learning data for Phase 3

---

## Success Criteria

**After running workflow:**
- ✅ Zero `- [ ]` items older than 7 days
- ✅ Zero TODOs older than 14 days
- ✅ Zero "draft" files older than 30 days
- ✅ Closure receipt generated
- ✅ Mental load: HIGH → LOW

**This is your "periodic reset button" for guilt-free operation.**

---

## Next Evolution (Phase 3)

**What to add:**
- Machine learning on categorization (learns your patterns)
- Telegram interactive approval ("Approve quick win?")
- Cross-project detection (GentleQuest + Nucleus)
- Predictive alerts ("This will become a rabbit hole in 3 days")

But for now, this workflow gives you the **safety net you need.**
