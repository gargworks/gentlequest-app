import os
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys

# Check for Gemini Key
if not os.environ.get("GOOGLE_API_KEY"):
    print("❌ GOOGLE_API_KEY not found. Please set it to run the Autopilot.")
    sys.exit(1)

# Import Gemini
try:
    import google.generativeai as genai
except ImportError:
    print("❌ 'google-generativeai' package not installed. Run: pip install google-generativeai")
    sys.exit(1)

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash-8b') # Fast, efficient model

BRAIN_PATH = os.environ.get("NUCLEAR_BRAIN_PATH", ".brain")
POLL_INTERVAL = 5  # Seconds

async def run_autopilot():
    print(f"🚀 Nucleus Autopilot (Gemini Edition) starting...")
    print(f"   Brain Path: {BRAIN_PATH}")
    print(f"   Watching for 'user_input' events...")

    # We spawn a dedicated server instance for the Autopilot
    server_params = StdioServerParameters(
        command="python3.11", 
        args=["-m", "mcp_server_nucleus"],
        env={**os.environ, "NUCLEAR_BRAIN_PATH": BRAIN_PATH}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected to Nucleus Brain (System Layer)")

            last_processed_idx = -1 
            
            # Fast-forward
            try:
                events = await session.call_tool("brain_read_events", arguments={"limit": 50})
                if events:
                    last_processed_idx = len(events)
                    print(f"⏩  Skipping {len(events)} existing events.")
            except Exception as e:
                print(f"⚠️  Could not read initial events: {e}")

            while True:
                try:
                    # 1. READ EVENTS
                    events = await session.call_tool("brain_read_events", arguments={"limit": 10})
                    
                    # Naive "New Event" check for prototype
                    if events:
                        last_event = events[-1]
                        
                        # Only trigger if it's a NEW user input (simple check relative to startup for now)
                        # In prod, track event UUIDs
                        if last_event.get("type") == "user_input" and last_event.get("status", "pending") == "pending":
                             print(f"🔔 Detected User Input: {last_event.get('description')}")
                             
                             # 2. ACTIVATE SYNTHESIZER
                             print("🧠 Waking Synthesizer (Gemini)...")
                             prompt_text = await session.get_prompt("activate_synthesizer")
                             
                             # 3. CALL GEMINI
                             # Construct the prompt
                             full_prompt = f"{prompt_text}\n\n[NEW EVENT]\n{last_event.get('data', {}).get('content', 'Unknown')}\n\nAnalyze and Output JSON tool calls."

                             print("💭 Thinking...")
                             response = model.generate_content(full_prompt)
                             
                             reply = response.text
                             print(f"🤖 Synthesizer: {reply[:100]}...")
                             
                             # 4. EXECUTE DECISIONS (Parsing required in next step)
                             # Mark handled...
                             
                    await asyncio.sleep(POLL_INTERVAL)
                    
                except Exception as loop_err:
                    print(f"⚠️  Loop Error: {loop_err}")
                    await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(run_autopilot())
    except KeyboardInterrupt:
        print("\n🛑 Autopilot disconnected.")
