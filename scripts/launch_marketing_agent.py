#!/usr/bin/env python3
import sys
import os
import subprocess
import webbrowser
import time

# Configuration
CHEATSHEET_PATH = ".agent/workflows/marketing_autopilot_cheatsheet.md"
PERPLEXITY_URL = "https://www.perplexity.ai/"

PROMPTS = {
    "listener": {
        "start_marker": "## 👂 The Listener",
        "end_marker": "## 🧠 The Brain"
    },
    "publisher": {
        "start_marker": "## ✍️ The Publisher",
        "end_marker": "## 📡 The Scout"
    },
    "scout": {
        "start_marker": "## 📡 The Scout",
        "end_marker": "```\n\n" # End of the last block
    }
}

def copy_to_clipboard(text):
    """Copy text to clipboard on macOS."""
    process = subprocess.Popen(
        'pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE
    )
    process.communicate(text.encode('utf-8'))

def extract_prompt(role):
    """Extract the specific prompt block from the cheatsheet."""
    try:
        with open(CHEATSHEET_PATH, 'r') as f:
            content = f.read()
            
        role_config = PROMPTS.get(role)
        if not role_config:
            print(f"❌ Unknown role: {role}. Available: listener, publisher, scout")
            sys.exit(1)

        start = content.find(role_config["start_marker"])
        end = content.find(role_config["end_marker"])
        
        if start == -1 or end == -1:
            print("❌ Could not parse cheatsheet markers.")
            sys.exit(1)
            
        # Extract the code block inside the section
        section = content[start:end]
        code_start = section.find("```text") + 7
        code_end = section.rfind("```")
        
        prompt = section[code_start:code_end].strip()
        return prompt

    except FileNotFoundError:
        print(f"❌ Cheatsheet not found at {CHEATSHEET_PATH}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 launch_marketing_agent.py [listener|publisher|scout]")
        sys.exit(1)
        
    role = sys.argv[1].lower()
    print(f"🚀 Preparing {role.upper()} Agent...")
    
    # 1. Extract Prompt
    prompt = extract_prompt(role)
    
    # 2. Copy to Clipboard
    copy_to_clipboard(prompt)
    print("✅ Prompt copied to clipboard!")
    
    # 3. Open Browser
    print(f"🌐 Opening Perplexity...")
    webbrowser.open(PERPLEXITY_URL)
    
    print("\n👉 ACTION REQUIRED: Context window is open. Just press CMD+V (Paste).")

if __name__ == "__main__":
    main()
