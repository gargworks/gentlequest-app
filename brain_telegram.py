#!/usr/bin/env python3
"""
Brain Telegram Integration
===========================

Two-way integration between Nuclear Brain and Telegram:
1. ALERTS OUT: Critical events → Telegram notifications
2. COMMANDS IN: Telegram commands → Brain actions

Bot: @gentlequest_alerts_bot

Usage:
    python brain_telegram.py serve       # Start webhook server
    python brain_telegram.py alert "msg" # Send test alert
    
Commands (in Telegram):
    /status  - Get current Brain status
    /sprint <goal> - Start new sprint
    /tasks   - List pending tasks
    /idea <thought> - Quick capture shower thoughts
    /event <type> <msg> - Log custom event

Author: Nuclear Brain System
"""

import os
import json
import uuid
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from flask import Flask, request, jsonify

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

BRAIN_ROOT = Path(__file__).parent / ".brain"
EVENTS_FILE = BRAIN_ROOT / "ledger" / "events.jsonl"
STATE_FILE = BRAIN_ROOT / "ledger" / "state.json"

# Telegram config (from env or defaults)
TG_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7575125475")  # Your ID

# ═══════════════════════════════════════════════════════════════════
# TELEGRAM ALERTS (Brain → Telegram)
# ═══════════════════════════════════════════════════════════════════

def send_telegram_alert(message: str, parse_mode: str = "Markdown") -> bool:
    """Send alert to your Telegram"""
    if not TG_BOT_TOKEN:
        print("⚠️ TELEGRAM_BOT_TOKEN not set")
        return False
    
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TG_CHAT_ID,
                "text": message,
                "parse_mode": parse_mode
            },
            timeout=10
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ Telegram send failed: {e}")
        return False


def alert_critical_event(event: dict) -> bool:
    """Format and send CRITICAL event alert"""
    msg = f"""🚨 *CRITICAL EVENT*
    
*Type:* `{event.get('event_type', 'unknown')}`
*Agent:* {event.get('emitter', 'unknown')}
*Time:* {event.get('timestamp', 'now')[:19]}

*Details:*
{json.dumps(event.get('payload', {}), indent=2)[:500]}

→ Check Antigravity for action required"""
    
    return send_telegram_alert(msg)


def alert_sprint_started(sprint_name: str, focus: str) -> bool:
    """Alert when sprint starts"""
    msg = f"""🚀 *Sprint Started*
    
*Name:* {sprint_name}
*Focus:* {focus}

Agents are now active."""
    
    return send_telegram_alert(msg)


def alert_sprint_completed(sprint_name: str, tasks_done: int) -> bool:
    """Alert when sprint completes"""
    msg = f"""✅ *Sprint Complete*
    
*Name:* {sprint_name}
*Tasks:* {tasks_done} done

Review outputs in Antigravity."""
    
    return send_telegram_alert(msg)


# ═══════════════════════════════════════════════════════════════════
# BRAIN HELPERS
# ═══════════════════════════════════════════════════════════════════

def load_state() -> dict:
    """Load current state.json - returns defaults if file doesn't exist (e.g., on Render)"""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    
    # Return sensible defaults for production where .brain/ doesn't exist
    return {
        "current_sprint": {
            "name": "No local brain",
            "status": "REMOTE",
            "focus": "Brain files exist only on dev machine"
        },
        "counters": {"total_events": 0, "tasks_completed": 0},
        "active_agents": ["synthesizer"],
        "top_3_leverage_actions": [{"action": "Sync .brain to production or use local dev"}]
    }


def save_state(state: dict):
    """Save state.json - no-op if .brain/ doesn't exist"""
    try:
        if BRAIN_ROOT.exists():
            state["last_updated"] = datetime.now(timezone.utc).isoformat()
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=4)
    except Exception as e:
        print(f"Could not save state: {e}")


def emit_event(emitter: str, event_type: str, payload: dict, severity: str = "NOTABLE") -> str:
    """Emit event to events.jsonl - sends Telegram alert if file doesn't exist"""
    event = {
        "event_id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "emitter": emitter,
        "event_type": event_type,
        "severity": severity,
        "payload": payload,
        "metadata": {"source": "telegram"}
    }
    
    try:
        if BRAIN_ROOT.exists():
            with open(EVENTS_FILE, 'a') as f:
                f.write(json.dumps(event) + '\n')
    except Exception:
        pass
    
    return event["event_id"]


# ═══════════════════════════════════════════════════════════════════
# TELEGRAM COMMANDS (Telegram → Brain)
# ═══════════════════════════════════════════════════════════════════

def handle_status_command() -> str:
    """Handle /status command"""
    state = load_state()
    sprint = state.get("current_sprint", {})
    counters = state.get("counters", {})
    
    status = sprint.get("status", "UNKNOWN")
    status_emoji = "🟢" if status == "ACTIVE" else "✅" if status == "COMPLETE" else "🔴"
    
    return f"""{status_emoji} *Brain Status*

*Sprint:* {sprint.get('name', 'None')}
*Status:* {status}
*Focus:* {sprint.get('focus', 'N/A')[:50]}

*Stats:*
• Events: {counters.get('total_events', 0)}
• Tasks Done: {counters.get('tasks_completed', 0)}
• Active Agents: {', '.join(state.get('active_agents', ['none']))}

*Top Action:*
{state.get('top_3_leverage_actions', [{}])[0].get('action', 'Check Antigravity')}"""


def handle_sprint_command(goal: str) -> str:
    """Handle /sprint <goal> command"""
    if not goal:
        return "❌ Usage: /sprint <goal description>"
    
    sprint_id = f"sprint-{uuid.uuid4().hex[:8]}"
    state = load_state()
    
    # Create new sprint
    new_sprint = {
        "id": sprint_id,
        "name": f"Sprint: {goal[:30]}",
        "started": datetime.now(timezone.utc).isoformat(),
        "ends": (datetime.now(timezone.utc) + timedelta(hours=72)).isoformat(),
        "focus": goal,
        "status": "ACTIVE",
        "objectives": [goal],
        "tasks": []
    }
    
    state["current_sprint"] = new_sprint
    state["active_agents"] = ["synthesizer"]
    save_state(state)
    
    # Emit event
    emit_event(
        emitter="founder",
        event_type="sprint_started",
        payload={"sprint_id": sprint_id, "goal": goal}
    )
    
    return f"""✅ *Sprint Created*

*ID:* `{sprint_id}`
*Goal:* {goal}

Sprint logged. Open Antigravity and tell Synthesizer to delegate tasks."""


def handle_tasks_command() -> str:
    """Handle /tasks command"""
    state = load_state()
    sprint = state.get("current_sprint", {})
    tasks = sprint.get("tasks", [])
    
    if not tasks:
        return "📋 *No active tasks*\n\nStart a sprint: /sprint <goal>"
    
    task_list = ""
    for t in tasks[:5]:  # Max 5
        status_emoji = "✅" if t.get("status") == "complete" else "🔄" if t.get("status") == "assigned" else "⏳"
        task_list += f"{status_emoji} [{t.get('agent', '?')}] {t.get('task', 'Unknown')[:40]}\n"
    
    return f"""📋 *Sprint Tasks*

{task_list}
Total: {len(tasks)} tasks"""


def handle_event_command(args: str) -> str:
    """Handle /event <type> <message> command"""
    parts = args.split(" ", 1)
    if len(parts) < 2:
        return "❌ Usage: /event <type> <message>\nExample: /event idea New feature concept"
    
    event_type = parts[0]
    message = parts[1]
    
    event_id = emit_event(
        emitter="founder",
        event_type=f"founder_{event_type}",
        payload={"message": message}
    )
    
    return f"✅ Event logged: `{event_id}`"


def handle_idea_command(idea: str) -> str:
    """Handle /idea <your shower thought> command - quick capture for ideas"""
    if not idea:
        return "❌ Usage: /idea <your thought>\nExample: /idea Add voice notes to Luna"
    
    # Get ideas inbox path
    ideas_folder = BRAIN_ROOT / "artifacts" / "ideas"
    inbox_file = ideas_folder / "inbox.md"
    
    # Create folder if needed (will fail gracefully on production)
    try:
        ideas_folder.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    
    # Format the idea entry
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = f"\n- [ ] **{timestamp}**: {idea}\n"
    
    # Append to inbox
    try:
        if BRAIN_ROOT.exists():
            # Create file with header if it doesn't exist
            if not inbox_file.exists():
                inbox_file.write_text("# 💡 Ideas Inbox\n\nShower thoughts and quick captures from Telegram.\n\n---\n")
            
            with open(inbox_file, 'a') as f:
                f.write(entry)
            
            # Also emit as event for ledger tracking
            emit_event(
                emitter="founder",
                event_type="idea_captured",
                payload={"idea": idea},
                severity="ROUTINE"
            )
            
            return f"💡 *Idea Captured!*\n\n_{idea}_\n\nSaved to ideas inbox. Review in Antigravity."
        else:
            # Production: no local brain, just acknowledge
            return f"💡 *Idea Noted!*\n\n_{idea}_\n\n⚠️ No local brain on production. Sync needed for persistence."
    except Exception as e:
        return f"❌ Failed to save idea: {str(e)[:50]}"


def process_telegram_message(message: dict) -> str:
    """Process incoming Telegram message and return response"""
    text = message.get("text", "")
    
    if text.startswith("/status"):
        return handle_status_command()
    
    elif text.startswith("/sprint"):
        goal = text.replace("/sprint", "").strip()
        return handle_sprint_command(goal)
    
    elif text.startswith("/tasks"):
        return handle_tasks_command()
    
    elif text.startswith("/event"):
        args = text.replace("/event", "").strip()
        return handle_event_command(args)
    
    elif text.startswith("/idea"):
        idea = text.replace("/idea", "").strip()
        return handle_idea_command(idea)
    
    elif text.startswith("/help"):
        return """🧠 *Brain Commands*

/status - Get current status
/sprint <goal> - Start new sprint
/tasks - List current tasks
/idea <thought> - 💡 Quick capture (shower thoughts!)
/event <type> <msg> - Log event

Example:
`/idea Add voice notes to Luna`"""
    
    else:
        return "❓ Unknown command. Try /help"


# ═══════════════════════════════════════════════════════════════════
# FLASK WEBHOOK SERVER
# ═══════════════════════════════════════════════════════════════════

app = Flask(__name__)

@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    """Handle incoming Telegram updates"""
    try:
        data = request.get_json()
        message = data.get("message", {})
        chat_id = str(message.get("chat", {}).get("id", ""))
        
        # Security: Only respond to authorized chat
        if chat_id != TG_CHAT_ID:
            return jsonify({"ok": False, "error": "Unauthorized"}), 403
        
        response_text = process_telegram_message(message)
        
        # Send response back
        send_telegram_alert(response_text)
        
        return jsonify({"ok": True})
    
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/brain/alert", methods=["POST"])
def brain_alert_endpoint():
    """Manual alert endpoint"""
    data = request.get_json() or {}
    message = data.get("message", "Test alert from Brain")
    success = send_telegram_alert(message)
    return jsonify({"ok": success})


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python brain_telegram.py serve        # Start webhook server")
        print("  python brain_telegram.py alert <msg>  # Send test alert")
        print("  python brain_telegram.py status       # Print status")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "serve":
        print("🤖 Starting Telegram webhook server on :5001")
        print(f"   Bot: @gentlequest_alerts_bot")
        print(f"   Chat ID: {TG_CHAT_ID}")
        app.run(host="0.0.0.0", port=5001, debug=True)
    
    elif cmd == "alert":
        msg = " ".join(sys.argv[2:]) or "🧪 Test alert from Nuclear Brain"
        if send_telegram_alert(msg):
            print("✅ Alert sent!")
        else:
            print("❌ Failed to send alert")
    
    elif cmd == "status":
        print(handle_status_command())
    
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
