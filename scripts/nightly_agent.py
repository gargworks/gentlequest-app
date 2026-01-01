#!/usr/bin/env python3
"""
Nightly Agent v2.1: 100% Knowledge University + Enhancements
- All 5 review loops (Critic, Strategist, Growth, Docs)
- Telegram notification of digest
- Expanded test coverage
- Event traceability
"""
import os
import subprocess
import json
import datetime
import sys
import requests
from pathlib import Path
from google import genai

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent

# Load .env file if it exists (for cron jobs)
ENV_FILE = PROJECT_ROOT / ".env"
if ENV_FILE.exists():
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if key not in os.environ:  # Don't override existing env vars
                    os.environ[key] = value

BRAIN_PATH = PROJECT_ROOT / ".brain"
LEDGER_PATH = BRAIN_PATH / "ledger"
AGENTS_PATH = BRAIN_PATH / "agents"
ARTIFACTS_PATH = BRAIN_PATH / "artifacts"
EVENTS_FILE = LEDGER_PATH / "events.jsonl"
DIGEST_PATH = LEDGER_PATH / "daily_digest.md"
KNOWLEDGE_INDEX_PATH = BRAIN_PATH / "knowledge_index.json"
IDEAS_INBOX_PATH = ARTIFACTS_PATH / "ideas" / "inbox.md"
MODEL_ID = "gemini-2.0-flash-exp"

# Telegram config (loaded from .env or environment)
TG_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7575125475")

# Test files (core tests that should always pass)
CORE_TESTS = [
    "test_clinical_assessments.py",
    "test_analytics_endpoints.py",
]

# Ensure paths exist
LEDGER_PATH.mkdir(parents=True, exist_ok=True)


def get_timestamp():
    return datetime.datetime.now().isoformat()


def emit_event(event_type: str, severity: str, payload: dict):
    """Emit an event to events.jsonl for traceability."""
    event = {
        "timestamp": get_timestamp(),
        "event_type": event_type,
        "emitter": "nightly_agent",
        "severity": severity,
        "payload": payload
    }
    with open(EVENTS_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")
    print(f"   📡 Emitted: {event_type} ({severity})")


def send_telegram_notification(message: str) -> bool:
    """Send notification to Telegram."""
    if not TG_BOT_TOKEN:
        print("   ⚠️ TELEGRAM_BOT_TOKEN not set, skipping notification")
        return False
    
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TG_CHAT_ID,
                "text": message
            },
            timeout=10
        )
        if resp.status_code == 200:
            print("   📱 Telegram notification sent!")
            return True
        else:
            print(f"   ⚠️ Telegram failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ⚠️ Telegram error: {e}")
        return False


def load_artifact(path: str) -> str:
    """Load an artifact file."""
    full_path = PROJECT_ROOT / path
    if full_path.exists():
        return full_path.read_text(encoding='utf-8')
    return ""


def get_unprocessed_ideas() -> tuple[int, list[str]]:
    """Read unprocessed ideas (unchecked items) from ideas inbox."""
    if not IDEAS_INBOX_PATH.exists():
        return 0, []
    
    try:
        content = IDEAS_INBOX_PATH.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Find unchecked items (- [ ])
        unprocessed = []
        for line in lines:
            if line.strip().startswith('- [ ]'):
                # Extract the idea text after the timestamp
                idea_text = line.strip()[6:]  # Remove "- [ ] "
                # Try to extract just the idea (after timestamp)
                if '**: ' in idea_text:
                    idea_text = idea_text.split('**: ', 1)[1]
                unprocessed.append(idea_text[:60])  # Truncate for digest
        
        return len(unprocessed), unprocessed[:5]  # Return count and top 5
    except Exception as e:
        print(f"   ⚠️ Error reading ideas: {e}")
        return 0, []


RESEARCH_QUEUE_PATH = ARTIFACTS_PATH / "research" / "queue.md"

def run_research_queue() -> int:
    """Process pending research tasks via run_research.py script.
    
    Returns the number of tasks processed.
    """
    print("🔬 Processing research queue...")
    
    # Check if queue file exists and has pending tasks
    if not RESEARCH_QUEUE_PATH.exists():
        print("   No research queue found.")
        return 0
    
    content = RESEARCH_QUEUE_PATH.read_text()
    pending_count = content.count('- [ ]')
    
    if pending_count == 0:
        print("   No pending research tasks.")
        return 0
    
    print(f"   Found {pending_count} pending research task(s)...")
    
    # Run the research processor script
    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "run_research.py")],
            capture_output=True,
            text=True,
            timeout=600,  # 10 min max for all research
            cwd=str(PROJECT_ROOT)
        )
        
        # Count completed (check for "completed" in output)
        completed = result.stdout.count("✅ Saved to:")
        print(f"   ✅ Completed {completed} research task(s)")
        
        emit_event("research_queue_processed", "ROUTINE", {
            "pending": pending_count,
            "completed": completed
        })
        
        return completed
    except subprocess.TimeoutExpired:
        print("   ⚠️ Research processing timed out")
        return 0
    except Exception as e:
        print(f"   ❌ Error processing research: {e}")
        return 0


def load_agent_prompt(agent_name: str) -> str:
    """Load an agent definition from .brain/agents/{agent_name}.md"""
    agent_file = AGENTS_PATH / f"{agent_name}.md"
    if agent_file.exists():
        return agent_file.read_text(encoding='utf-8')[:3000]
    return ""


def run_knowledge_indexer():
    """Run the knowledge indexer to update the index."""
    print("📚 Updating knowledge index...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from knowledge_indexer import build_index, INDEX_OUTPUT
        index = build_index()
        with open(INDEX_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        print(f"   ✅ Indexed {index['total_files']} files, {index['total_rules_extracted']} rules")
        return index
    except Exception as e:
        print(f"   ⚠️ Knowledge indexer failed: {e}")
        return None


def run_tests():
    """Runs pytest on core test files."""
    print("🧪 Running tests...")
    try:
        result = subprocess.run(
            ["/opt/homebrew/bin/pytest"] + CORE_TESTS + ["--tb=short", "-q"],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(PROJECT_ROOT)
        )
        passed = result.returncode == 0
        
        # Count tests
        output = result.stdout + result.stderr
        test_count = "22"  # Default
        for line in output.split('\n'):
            if 'passed' in line:
                test_count = line.split()[0] if line.split() else "22"
                break
        
        emit_event(
            "tests_completed",
            "ROUTINE" if passed else "NOTABLE",
            {"passed": passed, "test_count": test_count}
        )
        return output, passed, test_count
    except Exception as e:
        return str(e), False, "0"


def run_critic_review(client, knowledge_index):
    """Use the CRITIC agent to review recent changes."""
    print("🔍 Critic Agent reviewing...")
    
    critic_prompt = load_agent_prompt("critic")
    if not critic_prompt:
        return "Critic agent definition not found."
    
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--since=24.hours.ago", "-n", "10"],
            capture_output=True, text=True, timeout=10, cwd=str(PROJECT_ROOT)
        )
        recent_commits = result.stdout if result.stdout else "No recent commits."
        
        rules = []
        if knowledge_index:
            for file_info in knowledge_index.get('files', []):
                if file_info.get('path') == 'DEVELOPMENT_RULES.md':
                    rules = file_info.get('extracted_rules', [])[:10]
                    break
        
        rules_text = "\n".join([f"- [{r['section']}] {r['rule']}" for r in rules]) if rules else "No rules loaded."
        
        prompt = f"""
You are the Critic Agent. {critic_prompt[:1500]}

TASK: Quick daily code review.

RECENT COMMITS:
{recent_commits}

DEVELOPMENT RULES TO CHECK:
{rules_text}

OUTPUT (be concise):
1. Status: ✅ APPROVED / ⚠️ CONCERNS / 🔴 BLOCKED
2. Key observation (1 bullet)
"""
        
        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        review = response.text
        
        severity = "CRITICAL" if "BLOCKED" in review else ("NOTABLE" if "CONCERNS" in review else "ROUTINE")
        emit_event("critic_review_completed", severity, {"has_concerns": "CONCERNS" in review})
        
        return review
    except Exception as e:
        return f"Critic error: {e}"


def run_strategist_review(client):
    """Use the MUSK METHOD to ask 'Are we building the right thing?'"""
    print("♟️ Strategist (Musk Method) reviewing...")
    
    musk_method = load_artifact(".brain/artifacts/strategy/musk_method.md")
    if not musk_method:
        return "Musk Method not found."
    
    try:
        state = {}
        state_file = LEDGER_PATH / "state.json"
        if state_file.exists():
            state = json.loads(state_file.read_text())
        
        current_sprint = state.get("current_sprint", {}).get("name", "Unknown")
        
        prompt = f"""
Apply the Musk Method to evaluate our current work.

CURRENT SPRINT: {current_sprint}

MUSK METHOD KEY PRINCIPLES (from musk_method.md):
- "The best part is no part"
- Focus on simple .brain/ folder + cloud backup
- Delete everything unnecessary

OUTPUT (2 lines max):
1. Alignment: 🟢 ALIGNED / 🟡 DRIFT / 🔴 WRONG
2. One sentence verdict
"""
        
        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        review = response.text
        
        severity = "NOTABLE" if "DRIFT" in review or "WRONG" in review else "ROUTINE"
        emit_event("strategist_review_completed", severity, {"aligned": "ALIGNED" in review})
        
        return review
    except Exception as e:
        return f"Strategist error: {e}"


def run_growth_nudge(client):
    """Check interview_guide.md and nudge about user interviews."""
    print("📈 Growth check (interviews)...")
    
    interview_guide = load_artifact(".brain/artifacts/research/interview_guide.md")
    if not interview_guide:
        return "Interview guide not found."
    
    try:
        prompt = f"""
Check interview progress.

INTERVIEW GUIDE:
{interview_guide[:1500]}

TODAY: {datetime.datetime.now().strftime("%B %d, %Y")}
DEADLINE: January 10, 2025
GOAL: 5 interviews

OUTPUT (2 lines):
1. Progress: X/5 (based on table)
2. Today's action: [specific action]
"""
        
        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        nudge = response.text
        
        emit_event("growth_nudge_completed", "ROUTINE", {})
        
        return nudge
    except Exception as e:
        return f"Growth error: {e}"


def run_doc_drift_check(client):
    """Check if README.md matches the actual codebase."""
    print("📄 Checking doc drift...")
    
    try:
        readme_path = PROJECT_ROOT / "README.md"
        app_path = PROJECT_ROOT / "app.py"
        
        if not readme_path.exists() or not app_path.exists():
            return "README or app.py not found."
        
        readme = readme_path.read_text()[:2000]
        app_code = app_path.read_text()[:1500]
        
        prompt = f"""
Compare README.md with app.py.

README (snippet):
{readme[:1000]}

APP.PY (snippet):
{app_code[:800]}

OUTPUT (1 line):
PASS or DRIFT: [one specific issue]
"""
        
        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        result = response.text
        
        has_drift = "DRIFT" in result
        emit_event("doc_drift_check_completed", "NOTABLE" if has_drift else "ROUTINE", {"has_drift": has_drift})
        
        return result
    except Exception as e:
        return f"Doc drift error: {e}"


def run_synthesizer_digest(client, test_count, test_passed, critic_review, strategist_review, growth_nudge, doc_drift, research_count=0):
    """Generate the final daily digest."""
    print("📋 Synthesizer generating digest...")
    
    status_emoji = "✅" if test_passed else "❌"
    
    # Get unprocessed ideas
    ideas_count, ideas_list = get_unprocessed_ideas()
    ideas_text = f"- Ideas: {ideas_count} unprocessed - " + "; ".join(ideas_list[:3]) if ideas_count > 0 else "- Ideas: None pending"
    
    # Research info
    research_text = f"- Research: {research_count} tasks completed overnight" if research_count > 0 else "- Research: None queued"
    
    prompt = f"""
Create a concise founder daily digest.

INPUTS:
- Tests: {status_emoji} {test_count} tests {'passed' if test_passed else 'failed'}
- Critic: {critic_review[:200]}
- Strategist: {strategist_review[:200]}
- Growth: {growth_nudge[:150]}
- Docs: {doc_drift[:100]}
{ideas_text}
{research_text}

OUTPUT FORMAT:
# 🌙 Nightly Report

## Status
Tests: [emoji] | Critic: [status] | Strategy: [status]

## Key Findings
• [Most important finding]
• [Second finding]

## Ideas Inbox
[If any ideas pending, list them. Otherwise say "Clear"]

## Today's Action
[Single most important thing to do today]

Keep under 120 words.
"""
    
    response = client.models.generate_content(model=MODEL_ID, contents=prompt)
    return response.text


def create_telegram_summary(test_passed, test_count, critic_review, strategist_review, growth_nudge):
    """Create a short Telegram-friendly summary."""
    test_emoji = "✅" if test_passed else "❌"
    
    # Extract key statuses
    critic_status = "✅" if "APPROVED" in critic_review else ("⚠️" if "CONCERNS" in critic_review else "🔴")
    strategy_status = "🟢" if "ALIGNED" in strategist_review else ("🟡" if "DRIFT" in strategist_review else "🔴")
    
    # Sanitize growth nudge for Telegram (remove markdown chars)
    growth_text = growth_nudge.replace('*', '').replace('_', '').replace('`', '')[:80]
    
    # Get unprocessed ideas count
    ideas_count, _ = get_unprocessed_ideas()
    ideas_line = f"\n💡 Ideas: {ideas_count} unprocessed" if ideas_count > 0 else ""
    
    # Use plain text, no markdown to avoid 400 errors
    return f"""🌙 Nightly Agent Report

{test_emoji} Tests: {test_count} passed
{critic_status} Critic: {'Clean' if 'APPROVED' in critic_review else 'Review needed'}
{strategy_status} Strategy: {'Aligned' if 'ALIGNED' in strategist_review else 'Drift detected'}{ideas_line}

📈 Growth: {growth_text}

Full digest in daily_digest.md"""


def main():
    print("🌙 Nightly Agent v2.1 Starting...")
    print(f"   Time: {get_timestamp()}")
    print(f"   Mode: 100% Knowledge University + Telegram")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        return

    client = genai.Client(api_key=api_key)
    
    emit_event("nightly_run_started", "ROUTINE", {"version": "2.1", "time": get_timestamp()})

    # 0. Update Knowledge Index
    knowledge_index = run_knowledge_indexer()
    
    # 1. Run Tests
    test_output, test_passed, test_count = run_tests()
    
    # 2. Critic Review
    critic_review = run_critic_review(client, knowledge_index)
    
    # 3. Strategist Review
    strategist_review = run_strategist_review(client)
    
    # 4. Growth Nudge
    growth_nudge = run_growth_nudge(client)
    
    # 5. Doc Drift Check
    doc_drift = run_doc_drift_check(client)
    
    # 5.5. Process Research Queue (via Gemini CLI)
    research_count = run_research_queue()
    
    # 6. Generate Synthesized Digest
    digest = run_synthesizer_digest(
        client, test_count, test_passed,
        critic_review, strategist_review, growth_nudge, doc_drift, research_count
    )
    
    # 7. Save Digest
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    header = f"\n\n---\n\n## 🌙 Nightly Report: {today}\n"
    
    with open(DIGEST_PATH, "a") as f:
        f.write(header + digest)
    
    # 8. Send Telegram Notification
    print("📱 Sending Telegram notification...")
    tg_summary = create_telegram_summary(test_passed, test_count, critic_review, strategist_review, growth_nudge)
    send_telegram_notification(tg_summary)
    
    emit_event("nightly_run_completed", "ROUTINE", {
        "version": "2.1",
        "tests_passed": test_passed,
        "telegram_sent": bool(TG_BOT_TOKEN)
    })
        
    print(f"✅ Finished. Full digest at {DIGEST_PATH}")


if __name__ == "__main__":
    main()
