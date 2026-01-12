#!/usr/bin/env python3
"""
Nucleus Marketing Autopilot (Phase 49)
--------------------------------------
The central nervous system for GentleQuest/Nucleus marketing.
Replaces manual copy-pasta workflows with a robust CLI.

Commands:
    listen      - Ingest raw intelligence from clipboard or file
    scout       - Run AI trend analysis (WebOps)
    strategize  - Update strategy.md based on logs (Wraps auto_strategy_sync)
    draft       - Generate content drafts from open opportunities
    publish     - Review and mark drafts as published
    daemon      - Run the full loop continuously

Usage:
    python3 scripts/marketing_autopilot.py [command] [options]
"""

import sys
import os
import argparse
import logging
import json
import time
from datetime import datetime
from pathlib import Path

# --- CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("MarketingAutopilot")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs" / "marketing"
LOG_PATH = DOCS_DIR / "marketing_log.md"
DRAFTS_PATH = DOCS_DIR / "drafts.md"
STRATEGY_PATH = DOCS_DIR / "strategy.md"

# Ensure docs exist
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Add Nucleus to path
sys.path.append(str(PROJECT_ROOT / "mcp-server-nucleus" / "src"))

# LLM Helper
def get_llm():
    if os.environ.get("MARKETING_TEST_MODE"):
        class MockLLM:
            def generate_content(self, prompt):
                class MockResponse:
                    text = "Mock Response"
                return MockResponse()
        return MockLLM()
        
    try:
        from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
        return DualEngineLLM()
    except ImportError:
        logger.error("❌ Failed to import Nucleus LLM Client")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM: {e}")
        sys.exit(1)

# --- COMMANDS ---

def cmd_listen(args):
    """Ingest intelligence into marketing_log.md"""
    logger.info("👂 Listening for Intelligence...")
    
    content = ""
    # Check if piping input
    if not sys.stdin.isatty():
        content = sys.stdin.read().strip()
    else:
        print("📋 Paste your intelligence below (Ctrl+D to finish):")
        try:
            content = sys.stdin.read().strip()
        except EOFError:
            pass
            
    if not content:
        logger.warning("Empty input. Exiting.")
        return

    # Parse basic structure (heuristic)
    platform = "Inbox/Manual"
    if "Twitter" in content or "X.com" in content: platform = "Twitter/X"
    elif "Reddit" in content: platform = "Reddit"
    elif "IndieHackers" in content: platform = "IndieHackers"
    
    # Append to Log
    date_str = datetime.now().strftime("%Y-%m-%d")
    sanitized_content = content.replace("\n", "<br>").replace("|", "\\|")[:500] + "..." if len(content) > 500 else content.replace("\n", "<br>").replace("|", "\\|")
    
    row = f"| {date_str} | {platform} | {sanitized_content} | New Opportunity | |"
    
    with open(LOG_PATH, "a") as f:
        f.write("\n" + row)
        
    logger.info(f"✅ Logged to {LOG_PATH.name}")


def cmd_scout(args):
    """Run AI Trend Scout"""
    logger.info("📡 Scouting Trends...")
    
    if os.environ.get("MARKETING_TEST_MODE"):
        logger.info("🧪 Test Mode: Mocking Trends...")
        trends = [
            {"topic": "Mock Trend 1", "insight": "AI is taking over", "action": "Write about it"},
            {"topic": "Mock Trend 2", "insight": "Devs love CLI", "action": "Build more CLIs"},
            {"topic": "Mock Trend 3", "insight": "Python 3.14 is futuristic", "action": "Upgrade now"}
        ]
        with open(LOG_PATH, "a") as f:
            for t in trends:
                date_str = datetime.now().strftime("%Y-%m-%d")
                content = f"**Trend:** {t['topic']}<br>**Insight:** {t['insight']}<br>**Action:** {t['action']}"
                row = f"| {date_str} | Trend 🧪 | {content} | New Opportunity | |"
                f.write("\n" + row)
                logger.info(f"   Logged (Mock): {t['topic']}")
        return

    llm = get_llm()
    
    # ... (Rest of real logic)
    prompt = """
    Act as a Tech Trend Scout.
    Identify 3 rising trends in: "SaaS Marketing", "AI Development", "Developer Burnout".
    Format as JSON list: [{"topic": "...", "insight": "...", "action": "..."}]
    """
    
    logger.info("   Asking Gemini...")
    try:
        response = llm.generate_content(prompt)
        text = response.text.strip()
        # Strip code blocks
        if text.startswith("```json"): text = text[7:-3]
        elif text.startswith("```"): text = text[3:-3]
        
        trends = json.loads(text)
        
        with open(LOG_PATH, "a") as f:
            for t in trends:
                date_str = datetime.now().strftime("%Y-%m-%d")
                content = f"**Trend:** {t['topic']}<br>**Insight:** {t['insight']}<br>**Action:** {t['action']}"
                row = f"| {date_str} | Trend 📡 | {content} | New Opportunity | |"
                f.write("\n" + row)
                logger.info(f"   Logged: {t['topic']}")
                
    except Exception as e:
        logger.error(f"Scouting failed: {e}")


def cmd_strategize(args):
    """Run Strategy Sync"""
    logger.info("🧠 Syncing Strategy...")
    import subprocess
    script_path = PROJECT_ROOT / "scripts" / "auto_strategy_sync.py"
    subprocess.run([sys.executable, str(script_path)], check=True)


def cmd_draft(args):
    """Generate Drafts from Log"""
    logger.info("✍️  Generating Drafts...")
    
    # 1. Read Strategy
    if STRATEGY_PATH.exists():
        strategy_context = STRATEGY_PATH.read_text()[-2000:] # Last 2k chars
    else:
        strategy_context = "Focus on GentleQuest (ADHD/Anti-Burnout) and Nucleus (AI Agent DevTool)."

    # 2. Read Log for "New Opportunity"
    if not LOG_PATH.exists():
        logger.warning("No log found.")
        return

    log_lines = LOG_PATH.read_text().splitlines()
    opportunities = [line for line in log_lines if "| New Opportunity |" in line]
    
    if not opportunities:
        logger.info("No new opportunities found.")
        return
        
    logger.info(f"   Found {len(opportunities)} opportunities.")
    
    if os.environ.get("MARKETING_TEST_MODE"):
        logger.info("🧪 Test Mode: Mocking Draft Generation...")
        new_drafts = []
        for opp in opportunities[-3:]:
             draft = "This is a MOCK draft generated in test mode. #Mock #AI"
             new_drafts.append(f"\n\n---\n**Source**: {opp[:50]}...\n{draft}")
        
        if new_drafts:
            with open(DRAFTS_PATH, "a") as f:
                f.write("\n".join(new_drafts))
            logger.info(f"✅ Appended {len(new_drafts)} MOCK drafts to {DRAFTS_PATH.name}")
        return

    llm = get_llm()
    
    new_drafts = []
    
    for opp in opportunities[-3:]: # Process last 3 max to save tokens
        prompt = f"""
        CONTEXT:
        {strategy_context}
        
        OPPORTUNITY (Log Row):
        {opp}
        
        TASK:
        Write a short social media draft (Twitter/LinkedIn style) capitalizing on this opportunity.
        Be contrarian, authentic, and helpful. No hashtags unless necessary.
        Format:
        ### Draft [Platform]
        [Content]
        """
        
        try:
            logger.info("   Drafting...")
            resp = llm.generate_content(prompt)
            draft = resp.text.strip()
            
            new_drafts.append(f"\n\n---\n**Source**: {opp[:50]}...\n{draft}")
            
            # TODO: Mark log row as "Drafted" (Requires complex file editing, skipping for V1)
            
        except Exception as e:
            logger.error(f"Draft validation error: {e}")

    if new_drafts:
        with open(DRAFTS_PATH, "a") as f:
            f.write("\n".join(new_drafts))
        logger.info(f"✅ Appended {len(new_drafts)} drafts to {DRAFTS_PATH.name}")


def cmd_publish(args):
    """Read Drafts and Mark Published"""
    if not DRAFTS_PATH.exists():
        logger.warning("No drafts found.")
        return
        
    print(f"\n📄 Current Drafts in {DRAFTS_PATH.name}:")
    print(DRAFTS_PATH.read_text())
    print("\n👉 Action: Manually post these, then run 'python3 scripts/marketing_autopilot.py clean_drafts' (To Be Implemented)")


def cmd_daemon(args):
    """Run the loop"""
    logger.info("🤖 Starting Autopilot Daemon...")
    while True:
        cmd_scout(args)
        cmd_draft(args)
        logger.info("😴 Sleeping 4 hours...")
        time.sleep(14400)

def main(parser=None):
    if parser is None:
        parser = argparse.ArgumentParser(description="Nucleus Marketing Autopilot")
        parser.add_argument("--test", action="store_true", help="Run in mock/test mode")
        subparsers = parser.add_subparsers(dest="command", help="Command to run")
        
        subparsers.add_parser("listen", help="Ingest intelligence")
        subparsers.add_parser("scout", help="Find trends")
        subparsers.add_parser("strategize", help="Update strategy")
        subparsers.add_parser("draft", help="Generate drafts")
        subparsers.add_parser("publish", help="Review drafts")
        subparsers.add_parser("extract", help="Mine raw logs for marketing insights")
        subparsers.add_parser("daemon", help="Run continuous loop")
    
    args = parser.parse_args()
    
    # Global Test Mode
    if hasattr(args, 'test') and args.test:
        logger.info("⚠️ RUNNING IN TEST MODE (Mocking LLM)")
        os.environ["MARKETING_TEST_MODE"] = "1"

    if args.command == "listen": cmd_listen(args)
    elif args.command == "scout": cmd_scout(args)
    elif args.command == "strategize": cmd_strategize(args)
    elif args.command == "draft": cmd_draft(args)
    elif args.command == "publish": cmd_publish(args)
    elif args.command == "daemon": cmd_daemon(args)
    elif args.command == "extract": cmd_extract(args)
    else: parser.print_help()

def cmd_extract(args):
    """Extract Marketing Gold from Brain/Raw"""
    logger.info("⛏️  Mining Brain for Marketing Gold...")
    
    brain_path = Path(os.environ.get("NUCLEAR_BRAIN_PATH", ".brain"))
    raw_path = brain_path / "raw"
    insights_path = DOCS_DIR / "insights.md"
    
    if not raw_path.exists():
        logger.warning(f"No raw brain logs found at {raw_path}")
        return

    # Find recent logs (last 24h)
    logs = sorted(list(raw_path.glob("*.json")), reverse=True)[:10] # Process last 10 interactions for now
    
    if not logs:
        logger.info("No logs to process.")
        return
        
    logger.info(f"   Processing {len(logs)} recent interactions...")
    
    llm = get_llm()
    
    for log_file in logs:
        try:
            data = json.loads(log_file.read_text())
            prompt = data.get("prompt", "")
            response = data.get("response_text", "")
            
            combined_text = f"PROMPT: {prompt}\n\nRESPONSE: {response}"
            
            # Simple keyword check to save tokens
            keywords = ["protocol", "agentic", "neural", "system", "architecture", "vision", "mission"]
            if not any(k in combined_text.lower() for k in keywords):
                continue

            if os.environ.get("MARKETING_TEST_MODE"):
                result = "Found interesting concept: Neural Pathways. This refers to the preserved context between sessions."
                logger.info("🧪 Test Mode: Mocking Extraction...")
            else:
                extraction_prompt = f"""
                Analyze this raw LLM interaction from the Nucleus Brain.
                Extract any "Marketing Gold":
                - Unique phrases or jargon (e.g., "Neural Pathways", "Safety Sandwich")
                - Key architectural insights
                - Blog post kernels
                
                If nothing interesting, return "None".
                
                RAW DATA:
                {combined_text[:10000]}
                """
                
                resp = llm.generate_content(extraction_prompt)
                result = resp.text.strip()
            
            if result != "None" and len(result) > 10:
                with open(insights_path, "a") as f:
                    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    entry = f"\n\n## Insight ({date_str})\n**Source**: {log_file.name}\n\n{result}"
                    f.write(entry)
                logger.info(f"   💎 Found Gold in {log_file.name}")
                
        except Exception as e:
            logger.error(f"Failed to process {log_file.name}: {e}")
            
    logger.info(f"✅ Extraction complete. Check {insights_path}")

if __name__ == "__main__":
    main()
