#!/usr/bin/env python3
import json
import os
import sys
import subprocess
from pathlib import Path
import time

# --- Config ---
MCP_CONFIG_PATH = Path("/Users/lokeshgarg/.gemini/antigravity/mcp_config.json")

# Define the three brains
BRAINS = {
    "warm": "/Users/lokeshgarg/ai-mvp-backend/.brain",
    "prod": "/Users/lokeshgarg/ai-mvp-backend/.brain", # Alias for warm
    "cold": "/Users/lokeshgarg/dogfood-brain/.brain",
    "dogfood": "/Users/lokeshgarg/dogfood-brain/.brain", # Alias for cold/test
}

# --- Helpers ---
def load_config():
    if not MCP_CONFIG_PATH.exists():
        print(f"❌ Config not found at {MCP_CONFIG_PATH}")
        sys.exit(1)
    with open(MCP_CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(MCP_CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✅ Updated {MCP_CONFIG_PATH}")

def kill_servers():
    print("🔪 Killing running MCP servers...")
    try:
        subprocess.run(["pkill", "-f", "mcp_server_nucleus"], check=False)
        time.sleep(1) # Wait for death
    except Exception as e:
        print(f"⚠️ Error killing servers: {e}")

def switch_brain(mode):
    if mode not in BRAINS:
        print(f"❌ Uknown mode '{mode}'. Available: {', '.join(BRAINS.keys())}")
        sys.exit(1)
        
    target_path = BRAINS[mode]
    print(f"🔄 Switching to {mode.upper()} brain: {target_path}")

    # 1. Kill old servers
    kill_servers()

    # 2. Update Config
    config = load_config()
    try:
        # Navigate JSON structure safely
        config["mcpServers"]["nucleus"]["env"]["NUCLEAR_BRAIN_PATH"] = target_path
    except KeyError:
        print("❌ Could not find ['mcpServers']['nucleus']['env']['NUCLEAR_BRAIN_PATH'] in config")
        sys.exit(1)
    
    save_config(config)

    # 3. Special handling for COLD (Clean slate)
    if mode == "cold":
        brain_path = Path(target_path)
        if brain_path.exists():
            print(f"🧹 Cleaning cold brain at {brain_path}...")
            import shutil
            shutil.rmtree(brain_path) 
            print("   (Deleted old cold data)")
    
    print("\n" + "="*40)
    print(f"🚀 SUCCESS! Switched to {mode.upper()}.")
    print("⚠️  ACTION REQUIRED: RESTART ANTIGRAVITY NOW")
    print("="*40 + "\n")

# --- Main ---
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python switch_brain.py [warm|cold]")
        sys.exit(1)
    
    switch_brain(sys.argv[1])
