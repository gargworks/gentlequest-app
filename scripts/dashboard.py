#!/usr/bin/env python3
"""
DASHBOARD.md Generator
======================
Reads .brain/ledger/state.json and generates an up-to-date DASHBOARD.md

Usage:
    python scripts/dashboard.py
"""

import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
STATE_FILE = ROOT / ".brain" / "ledger" / "state.json"
DASHBOARD_FILE = ROOT / "DASHBOARD.md"

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def generate_dashboard():
    state = load_state()
    sprint = state.get("current_sprint", {})
    actions = state.get("top_3_leverage_actions", [])
    
    # Format actions
    action_lines = ""
    for i, action in enumerate(actions[:3], 1):
        action_lines += f"{i}. **{action.get('action', 'TBD')}**\n"
        action_lines += f"   - Agent: {action.get('agent', '?')}\n"
        action_lines += f"   - Impact: {action.get('impact', 'TBD')}\n\n"
    
    # Sprint status
    status = sprint.get("status", "UNKNOWN")
    ends = sprint.get("ends", "?")[:10]
    
    # Check if overdue
    try:
        end_date = datetime.fromisoformat(sprint.get("ends", "").replace("Z", "+00:00"))
        if datetime.now(end_date.tzinfo) > end_date:
            status = "OVERDUE"
    except:
        pass
    
    dashboard = f"""# 🎯 DASHBOARD — Your Single Entry Point

> **Open this file first. Every time.**
> Auto-generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 🔥 RIGHT NOW

| What | Status |
|------|--------|
| **Sprint** | {sprint.get('name', 'None')} |
| **Status** | {status} |
| **Ends** | {ends} |
| **Focus** | {sprint.get('focus', 'N/A')[:50]} |

---

## ⚡ TOP 3 ACTIONS

{action_lines}
---

## 📍 QUICK LINKS

| Need | Go To |
|------|-------|
| **What to work on?** | [backlog.md](backlog.md) |
| **Full system map?** | [.brain/NUCLEUS_HUB.md](.brain/NUCLEUS_HUB.md) |
| **Creds & Secrets?** | [docs/ADMIN_OPS.md](docs/ADMIN_OPS.md) |
| **Product Roadmap?** | [docs/IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md) |
| **Investor Narrative?** | [docs/STRATEGIC_AI_CAPABILITIES_ROADMAP.md](docs/STRATEGIC_AI_CAPABILITIES_ROADMAP.md) |
| **Capture an idea?** | Telegram: `/idea <thought>` |
| **Check live status?** | Telegram: `/status` |

---

## 🔄 REFRESH THIS

```bash
python scripts/dashboard.py
```

---

## 🧠 THE RULE

**Before ANY work session:**
1. Open `DASHBOARD.md`
2. Pick ONE action
3. Do it
4. Update backlog.md
5. Close laptop

That's it. No rabbit holes.
"""
    
    with open(DASHBOARD_FILE, "w") as f:
        f.write(dashboard)
    
    print(f"✅ DASHBOARD.md updated at {datetime.now().strftime('%H:%M')}")
    print(f"   Sprint: {sprint.get('name', 'None')} ({status})")
    print(f"   Top Action: {actions[0].get('action', 'None') if actions else 'None'}")

if __name__ == "__main__":
    generate_dashboard()
