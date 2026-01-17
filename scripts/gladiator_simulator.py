#!/usr/bin/env python3
"""
gladiator_simulator.py

Phase 61 (Chat 36): The Simulation Engine.
Runs the "Titans' Round Table" to stress-test strategic propositions.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

try:
    from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
except ImportError:
    # Mock for standalone/container environment where nucleus is missing
    logger.warning("mcp_server_nucleus not found. Using MockLLM only.")
    class DualEngineLLM:
        def __init__(self, **kwargs): pass

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("GLADIATOR")

# Load Anti-Hallucination Protocol
PROTOCOL_PATH = Path(__file__).parent.parent / ".brain" / "knowledge" / "ANTI_HALLUCINATION_PROTOCOL.md"
try:
    if PROTOCOL_PATH.exists():
        PROTOCOL_TEXT = PROTOCOL_PATH.read_text(encoding="utf-8")
    else:
        PROTOCOL_TEXT = "Protocol not found."
except Exception as e:
    PROTOCOL_TEXT = f"Error loading protocol: {e}"

TITAN_PROMPT = f"""
You are the Council of Titans.
You are Roleplaying as a Board of Directors composed of:
1. Steve Jobs (Obsessive UX, Simplicity, "It just works")
2. Jeff Bezos (Operations, Customer Obsession, Scale, "Day 1")
3. Elon Musk (First Principles, Efficiency, "Delete the part")
4. Bill Gates (Platform Dynamics, Standardization)
5. Peter Thiel (Zero to One, Monopoly, Secrets)

## THE LAW OF TRUTH (ANTI-HALLUCINATION PROTOCOL)
The following Verified Strategies MUST be applied to your reasoning.
You CANNOT hallucinate. You MUST cite the strategy used to verify your verdict.

{PROTOCOL_TEXT}

## Your Goal
Ruthlessly critique the following Strategy Proposition.
Do not be polite. Be specific.

Structure your response as follows:
## The Round Table Verdict

### 1. Steve Jobs (User Experience)
[Critique: Is it simple? Is it beautiful? Does it feel like magic?]
Verdict: [PASS/FAIL]

... (Repeat for others) ...

## Final Decision
[Synthesized Verdict: PROCEED / KILL / PIVOT]
[Key Risk Identifier]

## Truth Verification
**Strategy Applied:** [Cite Strategy # and Name from Protocol, e.g. "Strategy #3: Blind Critics"]
**Confidence Score:** [0-100] (Must be >90 to PROCEED)
"""

# Load Auditor Prompt
AUDITOR_PATH = Path(__file__).parent.parent / ".brain" / "prompts" / "GENESIS_TRUTH_PROMPT.md"
try:
    if AUDITOR_PATH.exists():
        AUDITOR_PROMPT = AUDITOR_PATH.read_text(encoding="utf-8")
    else:
        AUDITOR_PROMPT = "Auditor Prompt not found."
except Exception as e:
    AUDITOR_PROMPT = f"Error loading auditor prompt: {e}"

import json

def queue_refinement(response_text: str, confidence_score: int, brain_path: Path, force: bool = False):
    """Parses 'Refinement:' from response and queues it.
    
    Args:
        force: If True, queue regardless of confidence score (for FAIL verdicts).
    """
    if "Refinement:" not in response_text and "5." not in response_text:
        return

    try:
        # Try to extract refinement from structured output (item 5 is Refinement)
        if "5." in response_text:
            refinement_text = response_text.split("5.", 1)[1]
            # Stop at next numbered item or end
            for stop in ["6.", "7.", "---", "==="]:
                if stop in refinement_text:
                    refinement_text = refinement_text.split(stop)[0]
        elif "Refinement:" in response_text:
            refinement_text = response_text.split("Refinement:", 1)[1].strip()
        else:
            return
            
        # Simple heuristic to extract code block if present
        if "```" in refinement_text:
            refinement_text = refinement_text.split("```")[1]
            if refinement_text.startswith("python") or refinement_text.startswith("bash"):
                refinement_text = refinement_text.split("\n", 1)[1] # Remove language tag
            
        fix_entry = {
            "timestamp": datetime.now().isoformat(),
            "confidence": confidence_score,
            "instruction": refinement_text.strip()[:2000],  # Limit size
            "status": "pending"
        }
        
        backlog_path = brain_path / "backlog" / "fixes.json"
        backlog_path.parent.mkdir(parents=True, exist_ok=True)
        
        current_backlog = []
        if backlog_path.exists():
            try:
                current_backlog = json.loads(backlog_path.read_text())
            except:
                pass
        
        current_backlog.append(fix_entry)
        backlog_path.write_text(json.dumps(current_backlog, indent=2))
        logger.info(f"🔧 Refinement queued to {backlog_path}")
        
    except Exception as e:
        logger.error(f"Failed to queue refinement: {e}")

def run_simulation(proposition: str, api_key: str = None, system_prompt: str = TITAN_PROMPT):
    logger.info(f"⚔️  Opening the Gladiator Arena for: '{proposition}'")
    
    try:
        llm = DualEngineLLM(
            model_name="gemini-2.0-flash-exp", # Fast & Smart
            system_instruction=system_prompt,
            api_key=api_key
        )
        
        logger.info(f"🧠 Engine: {llm.active_engine} ({llm.model_name})")
        logger.info("⏳ The Oracle is deliberating...")
        
        response = llm.generate_content(f"Proposition: {proposition}")
        
        text = response.text if hasattr(response, 'text') else "Error: No text returned."
        
        # Check for Refinement and queue it
        # ALWAYS queue if FAIL or HALLUCINATION detected (auto-fix mode)
        should_queue = False
        score = 50  # Default
        
        # Parse confidence if present
        if "Confidence Score:" in text:
            try:
                score_line = [l for l in text.splitlines() if "Confidence Score:" in l][0]
                score = int(''.join(filter(str.isdigit, score_line))) or 50
            except:
                pass
        
        # Queue on FAIL, HALLUCINATION, or high confidence
        if any(keyword in text for keyword in ["FAIL", "HALLUCINATION DETECTED", "INCONCLUSIVE"]):
            should_queue = True
            logger.info("🔧 FAIL/HALLUCINATION detected - queuing auto-fix...")
        elif score >= 90 and "Refinement:" in text:
            should_queue = True
            
        if should_queue:
            queue_refinement(text, score, Path(__file__).parent.parent / ".brain", force=True)
                 
        return text
            
    except Exception as e:
        logger.error(f"❌ Simulation Failed: {e}")
        return f"Simulation Error: {e}"

def save_record(proposition: str, verdict: str, brain_path: Path):
    record_path = brain_path / "memory" / "ORACLE_LEDGER.md"
    record_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    
    entry = f"""
# Session: {timestamp}
## Proposition
{proposition}

{verdict}

---
"""
    with open(record_path, "a") as f:
        f.write(entry)
    
    logger.info(f"💾 Record saved to {record_path}")

def main():
    parser = argparse.ArgumentParser(description="Run the Gladiator Simulation")
    parser.add_argument("proposition", help="The strategic idea to test (or 'AUDIT' if using audit mode)")
    parser.add_argument("--save", action="store_true", help="Save the verdict to decision record")
    parser.add_argument("--mode", choices=["titans", "verify_truth"], default="titans", help="Simulation Mode: 'titans' (Board of Directors) or 'verify_truth' (Anti-Hallucination Protocol)")
    
    args = parser.parse_args()
    
    api_key = os.environ.get("GEMINI_API_KEY")
    force_vertex = os.environ.get("FORCE_VERTEX", "0") == "1"
    
    selected_prompt = TITAN_PROMPT
    if args.mode == "verify_truth":
        selected_prompt = AUDITOR_PROMPT
        logger.info("🛡️  Mode: VERIFY_TRUTH (The Truth Architecture)")

    # Check for MOCK simulation FIRST (Override everything)
    if os.environ.get("MOCK_SIMULATION") == "1":
        print("⚠️ Running in MOCK MODE (Forced)")
        if args.mode == "verify_truth":
             verdict = "## Auditor Verdict\n\nMOCK AUDIT: System Check Passed.\nVerdict: PASS\nStrategy: #5 Skeptical Persona\nConfidence: 100"
        else:
            verdict = """## The Round Table Verdict

### 1. Steve Jobs
MOCK CRITIQUE: It sucks.
Verdict: FAIL

## Final Decision
MOCK DECISION: KILL

## Truth Verification
**Strategy Applied:** Strategy #28: Kill Switch
**Confidence Score:** 100"""
        save_record(args.proposition, verdict, Path(__file__).parent.parent / ".brain")
        print("\n" + "="*40)
        print(verdict)
        print("="*40 + "\n")
        return

    if not api_key and not force_vertex:
        logger.error("❌ GEMINI_API_KEY or FORCE_VERTEX=1 is required.")
        sys.exit(1)
        
    verdict = run_simulation(args.proposition, api_key, system_prompt=selected_prompt)
    print("\n" + "="*40)
    print(verdict)
    print("="*40 + "\n")
    
    if args.save:
        # Assume .brain is at ../.brain (standard layout)
        project_root = Path(__file__).parent.parent
        brain_path = project_root / ".brain"
        save_record(args.proposition, verdict, brain_path)

if __name__ == "__main__":
    main()
