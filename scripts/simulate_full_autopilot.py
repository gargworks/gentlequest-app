#!/usr/bin/env python3
import requests
import json
import time
import sys
import os
from datetime import datetime

# Setup paths for direct brain imports
sys.path.append(os.path.join(os.getcwd(), 'mcp-server-nucleus', 'src'))
from mcp_server_nucleus.runtime.capabilities.marketing_engine import brain_synthesize_strategy

DASHBOARD_URL = "http://localhost:9999/api/ingest"

def log_step(step, emoji):
    print(f"\n{emoji} --- {step} ---")

def agent_action(agent_name, action_type, content):
    payload = {
        "type": f"{agent_name} {action_type}",
        "content": content
    }
    try:
        response = requests.post(DASHBOARD_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            print(f"✅ {agent_name}: Successfully logged to Dashboard.")
        else:
            print(f"❌ {agent_name}: Dashboard rejected request ({response.status_code}).")
    except Exception as e:
        print(f"❌ {agent_name}: Connection failed: {e}")

def simulate_consultant_loop():
    log_step("PHASE 1: THE LISTENER & SCOUT", "👂")
    print("Simulating Perplexity Agent browsing social history and web trends...")
    time.sleep(2)
    
    # 1. Consultant Feedback (Replies)
    reply_finding = (
        "**Consultant Report (Listener):**\n"
        "Found 2 replies to yesterday's 'Anti-Streak' post.\n"
        "- @DevDan: 'Actually I like this. Gamification gives me anxiety.'\n"
        "- @SarahCode: 'Is this open source?'\n"
        "**Recommendation:** Engage Dan, Reply to Sarah with repo link."
    )
    agent_action("Perplexity Agent", "📡 Insight", reply_finding)
    
    # 2. Consultant Trend Alert
    trend_finding = (
        "**Consultant Report (Trend Scout):**\n"
        "Warning: The 'AI Fatigue' narrative is saturating.\n"
        "**New Trend:** 'Local-First' is blowing up. People want owning data + AI privacy.\n"
        "**Strategy Shift:** Pivot generated content to emphasize 'Local-First Brain'."
    )
    agent_action("Perplexity Agent", "⚠️ Warning", trend_finding)

    log_step("PHASE 2: THE BRAIN (Strategy & Drafting)", "🧠")
    print("Nucleus Brain analyzing Consultant Feedback...")
    
    # 3. Brain Processing (Real Tool Call)
    # We trigger the actual strategy update based on the agent's specific finding
    brain_synthesize_strategy(os.getcwd(), focus_topic="Local-First Privacy Trend")
    
    # 4. Brain Drafting (Simulating the Writer component logic)
    # In a real continuous loop, this happens via event trigger. Here we simulate the output.
    draft_content = (
        "**DRAFT READY**\n"
        "Title: Your Brain, Local-First.\n"
        "Body: tired of sending your code to the cloud? \n"
        "Nucleus runs local. Your data stays on your machine.\n"
        "The only AI that keeps your secrets.\n"
        "#LocalFirst #Privacy #DevTools"
    )
    agent_action("Nucleus Brain", "📝 Draft", draft_content)
    
    log_step("PHASE 3: THE PUBLISHER (Execution & Polish)", "✍️")
    print("Simulating Perplexity Agent reviewing and publishing the draft...")
    time.sleep(2)
    
    # 5. Consultant Polish & Post
    # The agent decides to improve the draft before posting
    final_post_log = (
        "**POSTED** (Polished via Perplexity)\n"
        "Content Used: 'Tired of leaking code to the cloud? Nucleus runs 100% Local...'\n"
        "**Change Log:** Made it punchier. Added #OfflineFirst tag.\n"
        "**Status:** Live on Twitter."
    )
    agent_action("Perplexity Agent", "✅ Posted", final_post_log)

    log_step("SIMULATION COMPLETE", "🏁")
    print("The Dashboard now reflects the full 'Consultant' interaction cycle.")

if __name__ == "__main__":
    simulate_consultant_loop()
