#!/usr/bin/env python3
"""
Nucleus v0.5: RELEASING THE CRACKEN (Final Version)
Orchestrating a Gemini Flash Swarm to bypass Pro/Opus Quota Exhaustion.
"""

import os
import json
import subprocess
from pathlib import Path

# --- CONFIGURATION ---
PYTHON_BIN = "python3.11"
BRAIN_ROOT = Path("/Users/lokeshgarg/.brain_cracken")
SWARM_CONFIG = {
    "synthesizer": {
        "model": "gemini-2.0-flash",
        "system_prompt": "You are the Lead Synthesizer. Coordinate all agent tools via the master control plane."
    },
    "architect": {
        "model": "gemini-2.0-flash",
        "system_prompt": "You are the Lead Architect. Focus on system design, database schemas, and protocol compliance."
    },
    "researcher": {
        "model": "gemini-2.0-flash",
        "system_prompt": "You are the Lead Researcher. Focus on web search, competitor analysis, and market trends."
    }
}

def setup_cracken_swarm():
    print("="*60)
    print("🐙 NUCLEUS v0.5: RELEASING THE CRACKEN")
    print("="*60)
    
    # 1. Initialize Brain
    if not BRAIN_ROOT.exists():
        print(f"🧠 Initializing Master Brain at {BRAIN_ROOT}...")
        subprocess.run([PYTHON_BIN, "-m", "mcp_server_nucleus.cli", "init", str(BRAIN_ROOT), "--template", "solo"], check=True)
    else:
        print(f"🧠 Master Brain already exists at {BRAIN_ROOT}")

    # 2. Configure Recursive Mounts (Direct JSON Writing for Reliability)
    mounts = {}
    print("\n🔌 Configuring Recursive Namespacing for the Swarm...")
    
    for agent_id, config in SWARM_CONFIG.items():
        print(f"   [Configuring {agent_id}] -> Model: {config['model']}")
        
        # Build the mount configuration for stdio transport
        mounts[agent_id] = {
            "transport": "stdio",
            "command": PYTHON_BIN,
            "args": ["-m", "mcp_server_nucleus"],
            "env": {
                "NUCLEAR_BRAIN_PATH": str(BRAIN_ROOT / agent_id),
                "MODEL_OVERRIDE": config["model"],
                "SYSTEM_PROMPT_APPENDIX": config["system_prompt"]
            },
            "status": "configured"
        }
        
        # Ensure the child brain directory exists
        (BRAIN_ROOT / agent_id).mkdir(parents=True, exist_ok=True)

    # 3. Write mounts.json
    mounts_file = BRAIN_ROOT / "mounts.json"
    with open(mounts_file, "w") as f:
        json.dump(mounts, f, indent=2)
    
    print(f"\n✅ Created {mounts_file} with {len(mounts)} active mounts.")

def show_activation_snippet():
    abs_path = str(BRAIN_ROOT.absolute())
    print("\n" + "="*60)
    print("🚀 ACTIVATION SNIPPET (Copy to your AI Client Config)")
    print("="*60)
    print(f'''
"nucleus-cracken": {{
    "command": "{PYTHON_BIN}",
    "args": ["-m", "mcp_server_nucleus"],
    "env": {{
        "NUCLEAR_BRAIN_PATH": "{abs_path}"
    }}
}}
''')
    print("="*60)
    print("\n🔥 NEXT STEPS")
    print("1. Restart your IDE/AI Client.")
    print("2. Ask: 'Show me all tools' to see namespaces: synthesizer:*, architect:*, researcher:*.")
    print("3. Execute complex dev tasks using the combined power of Gemini Flash.")
    print("\n[CRACKEN RELEASED]")

if __name__ == "__main__":
    try:
        setup_cracken_swarm()
        show_activation_snippet()
    except Exception as e:
        print(f"❌ Failed to release the Cracken: {e}")
