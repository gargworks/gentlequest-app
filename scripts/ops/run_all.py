#!/usr/bin/env python3
"""
Run All Phases - Autonomous Session Orchestrator
=================================================
Executes all phases in sequence with error handling.

Usage:
    python scripts/ops/run_all.py
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
STATE_FILE = ROOT / "autonomous_state.json"
OPS_DIR = Path(__file__).parent

PHASE_SCRIPTS = {
    1: "verify_foundation.py",
    2: "consolidate.py",
    3: "stress_test.py",
}

def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def run_phase(phase_num: int) -> bool:
    """Run a single phase script."""
    script = OPS_DIR / PHASE_SCRIPTS.get(phase_num, "")
    if not script.exists():
        print(f"⚠️ No script for Phase {phase_num}")
        return True  # Skip
    
    print(f"\n{'='*50}")
    print(f"🚀 Running Phase {phase_num}: {script.name}")
    print('='*50)
    
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(ROOT),
            timeout=3600  # 1 hour max per phase
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"❌ Phase {phase_num} timed out")
        return False
    except Exception as e:
        print(f"❌ Phase {phase_num} error: {e}")
        return False

def main():
    print("🛫 AUTONOMOUS SESSION STARTING")
    print(f"Time: {datetime.now().isoformat()}")
    
    state = load_state()
    start_phase = state.get("current_phase", 1)
    
    # Skip Phase 0 (setup already done)
    if start_phase == 0:
        state["phases"]["0"]["status"] = "COMPLETE"
        start_phase = 1
        state["current_phase"] = 1
        save_state(state)
    
    # Run phases 1-3
    for phase in range(start_phase, 4):
        success = run_phase(phase)
        
        state = load_state()
        state["current_phase"] = phase
        state["phases"][str(phase)]["status"] = "COMPLETE" if success else "FAILED"
        save_state(state)
        
        if not success:
            print(f"\n⚠️ Phase {phase} failed. Continuing...")
    
    print("\n" + "="*50)
    print("✅ AUTONOMOUS SESSION COMPLETE")
    print("="*50)
    
    # Final status
    subprocess.run([sys.executable, str(OPS_DIR / "master_controller.py"), "status"])

if __name__ == "__main__":
    main()
