#!/usr/bin/env python3
"""
scripts/simulate_sensor_data.py
Role: Dev Tool / Simulator
Function: Injects mock "Trend" and "Inbox" data into marketing_log.md for testing.
"""

import datetime
import os

MARKETING_LOG_PATH = "docs/marketing/marketing_log.md"

def inject_simulation():
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 1. Mock Trend (Perplexity Style)
    trend_row = f"| {date_str} | Trend 📡 | **Topic:** AI Coding Anxiety<br>**Insight:** Developers feel guilty using Copilot.<br>**Angle:** Use AI to *learn*, not just generate. | New Opportunity | <button onclick=\"copyToClipboard('Use AI to learn, not just generate.'); alert('Angle copied!');\">Draft Response</button> |"
    
    # 2. Mock Inbox (IndieHackers Style)
    inbox_row = f"| {date_str} | Inbox 📬 | **Source:** IndieHackers<br>**From:** @sarah_dev<br>**Message:** 'Does this work for Flutter web?' | Reply Needed | <button onclick=\"window.open('https://indiehackers.com/notifications')\">Open Thread</button> |"

    print(f"💉 Injecting Test Data into {MARKETING_LOG_PATH}...")
    
    with open(MARKETING_LOG_PATH, "a") as f:
        f.write("\n" + trend_row)
        f.write("\n" + inbox_row)
    
    print("✅ Injected 1 Trend and 1 Inbox Reply.")

if __name__ == "__main__":
    inject_simulation()
