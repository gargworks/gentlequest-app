#!/usr/bin/env python3
"""
Swarm Relay (Phase 5.4)
=======================
The "Meta-Orchestrator" that chains the Genesis Swarm (Planning) 
and Execution Swarm (Building) into a continuous pipeline.

Usage:
    python scripts/swarm_relay.py --mission "Create helloworld.py"
    python scripts/swarm_relay.py --mission "Test Relay" --test
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path

# ANSI Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

APP_DIR = Path(__file__).parent.parent
GENESIS_SCRIPT = APP_DIR / "scripts" / "genesis_swarm.py"
EXECUTION_SCRIPT = APP_DIR / "scripts" / "execution_swarm.py"
PLAN_FILE = APP_DIR / "IMPLEMENTATION_PLAN.md"

def print_step(step, msg):
    print(f"\n{CYAN}🔹 [RELAY] Step {step}: {msg}{RESET}")

def run_command(cmd, desc):
    print(f"{YELLOW}>> Running: {' '.join(cmd)}{RESET}")
    start = time.time()
    result = subprocess.run(cmd, cwd=APP_DIR, capture_output=True, text=True)
    duration = time.time() - start
    
    if result.returncode != 0:
        print(f"❌ {desc} Failed ({duration:.2f}s)")
        print(result.stderr)
        return False, result.stdout
    else:
        print(f"{GREEN}✅ {desc} Complete ({duration:.2f}s){RESET}")
        return True, result.stdout

def main():
    parser = argparse.ArgumentParser(description="Swarm Relay: Idea -> Code")
    parser.add_argument("--mission", required=True, help="The goal describing what to build")
    parser.add_argument("--test", action="store_true", help="Run in mock/test mode")
    
    args = parser.parse_args()
    
    print(f"{GREEN}🚀 Swarm Relay Initiated{RESET}")
    print(f"   Mission: {args.mission}")
    print(f"   Test Mode: {args.test}")

    # ============================================================
    # PHASE 1: GENESIS SWARM (PLANNING)
    # ============================================================
    print_step(1, "Genesis Swarm (Planning)")
    
    genesis_cmd = [sys.executable, str(GENESIS_SCRIPT), "--mission", args.mission]
    if args.test:
        genesis_cmd.append("--test")
        
    success, output = run_command(genesis_cmd, "Genesis Swarm")
    if not success:
        print("🛑 Relay Halted at Genesis Phase.")
        sys.exit(1)
        
    # Check for Plan
    target_plan = APP_DIR / ("IMPLEMENTATION_PLAN_MOCK.md" if args.test else "IMPLEMENTATION_PLAN.md")
    
    if not target_plan.exists():
        print(f"❌ Error: Plan file not found at {target_plan}")
        sys.exit(1)
        
    print(f"📄 Plan Created: {target_plan.name}")
    
    # Optional: Print Plan Summary could go here
    
    # ============================================================
    # PHASE 2: HANDOFF (INTERSTITIAL)
    # ============================================================
    print_step(2, "Handoff to Execution Swarm")
    if not args.test:
        # In real mode, we might want a pause or auto-continue. 
        # For now, we auto-continue as per "Autonomous Relay" goal.
        print("Wait 2s before engaging builders...")
        time.sleep(2)

    # ============================================================
    # PHASE 3: EXECUTION SWARM (BUILDING)
    # ============================================================
    print_step(3, "Execution Swarm (Building)")
    
    execution_cmd = [sys.executable, str(EXECUTION_SCRIPT), "--plan", str(target_plan.name)]
    if args.test:
        execution_cmd.append("--test")
        
    success, output = run_command(execution_cmd, "Execution Swarm")
    
    if success:
        print(f"\n{GREEN}✨ Relay Mission Accomplished!{RESET}")
        if args.test:
             print("Output Summary:")
             print(output)
    else:
        print(f"\n❌ Relay Failed at Execution Phase.")
        sys.exit(1)

if __name__ == "__main__":
    main()
