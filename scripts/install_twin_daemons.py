#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

# Create macOS launchd agents for morning and evening routines
LAUNCH_AGENT_DIR = Path.home() / "Library" / "LaunchAgents"
LAUNCH_AGENT_DIR.mkdir(parents=True, exist_ok=True)

python_exe = "/opt/homebrew/bin/python3" # System python or use current sys.executable
script_path = "/Users/lokeshgarg/ai-mvp-backend/scripts/twin_routine.py"

# --- MORNING PLIST (Runs at 08:00) ---
morning_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>dev.nucleusos.twin.morning</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{script_path}</string>
        <string>morning</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>"""

# --- EVENING PLIST (Runs at 23:59) ---
evening_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>dev.nucleusos.twin.evening</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{script_path}</string>
        <string>evening</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>23</integer>
        <key>Minute</key>
        <integer>59</integer>
    </dict>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>"""

m_path = LAUNCH_AGENT_DIR / "dev.nucleusos.twin.morning.plist"
e_path = LAUNCH_AGENT_DIR / "dev.nucleusos.twin.evening.plist"

with open(m_path, "w") as f:
    f.write(morning_plist)
with open(e_path, "w") as f:
    f.write(evening_plist)

# Load them into the kernel
subprocess.run(["launchctl", "unload", str(m_path)], stderr=subprocess.DEVNULL)
subprocess.run(["launchctl", "unload", str(e_path)], stderr=subprocess.DEVNULL)

subprocess.run(["launchctl", "load", str(m_path)])
subprocess.run(["launchctl", "load", str(e_path)])

print("✅ Twin Daemons installed.")
print(f"   Morning Routine: 08:00 AM")
print(f"   Evening Routine: 11:59 PM")
