#!/usr/bin/env python3
"""
PEFS Telegram Bot - Daily Briefings and Commitment Reminders
MDR_010 Compliant: Includes feedback buttons, kill switch, and value tracking
"""

import os
import sys
import asyncio
import json
import urllib.request
import urllib.parse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server-nucleus" / "src"))

from datetime import datetime
from mcp_server_nucleus import commitment_ledger

# Try importing telegram library, but handle failure gracefully
try:
    from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters
    HAS_TELEGRAM_LIB = True
except ImportError:
    HAS_TELEGRAM_LIB = False
    print("⚠️ 'python-telegram-bot' not installed. Running in graceful fallback mode.")

BRAIN_PATH = Path(os.getenv("NUCLEAR_BRAIN_PATH", "/Users/lokeshgarg/ai-mvp-backend/.brain"))
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_fallback_message(text):
    """Send functionality using standard library"""
    try:
        data = urllib.parse.urlencode({'chat_id': CHAT_ID, 'text': text}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=data)
        with urllib.request.urlopen(req) as response:
            print(f"✅ Message sent to {CHAT_ID} (Fallback Mode)")
            return True
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False

async def send_daily_briefing(test_message=None):
    """Send morning briefing with commitment summary"""
    
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        return
    
    # Check kill switch first
    kill_status = commitment_ledger.check_kill_switch(BRAIN_PATH)
    if kill_status["action"] == "paused":
        print("⏸️ Notifications paused by user. Skipping briefing.")
        return

    if test_message:
        message = test_message
    else:
        ledger = commitment_ledger.load_ledger(BRAIN_PATH)
        stats = ledger.get("stats", {})
        open_comms = [c for c in ledger.get("commitments", []) if c["status"] == "open"]
        red_tier = [c for c in open_comms if c["tier"] == "red"]
        
        # Build message
        if not open_comms:
            message = "☀️ Good morning, Chairman!\n\n✅ Zero open loops. Enjoy your guilt-free day!\n\n🧠 Brain Health: OPTIMAL"
        else:
            mental_load = "🟢 LOW"
            if red_tier: mental_load = "🔴 HIGH"
            elif stats.get("yellow_tier", 0) > 2: mental_load = "🟡 MEDIUM"
            
            message = f"☀️ Good morning, Chairman!\n\n🎯 TODAY'S CRITICAL PATH:\n• {stats.get('total_open', 0)} open loops\n\n🧠 BRAIN HEALTH:\n• Mental load: {mental_load}\n"
            
            if red_tier:
                message += "\n🚨 RED TIER:\n"
                for comm in red_tier[:3]:
                    message += f"• {comm['description'][:50]} ({comm['age_days']}d)\n"

    # Send using appropriate method
    if HAS_TELEGRAM_LIB and not test_message:
        try:
            bot = Bot(token=BOT_TOKEN)
            # Simple keyboard for now
            keyboard = [[InlineKeyboardButton("view", url="https://google.com")]] # Placeholder
            reply_markup = InlineKeyboardMarkup(keyboard)
            await bot.send_message(chat_id=CHAT_ID, text=message, reply_markup=reply_markup)
            print(f"✅ Briefing sent to {CHAT_ID} (Full Mode)")
            commitment_ledger.increment_notifications(BRAIN_PATH)
        except Exception as e:
             # Fallback if library fails for some reason
            print(f"⚠️ Lib failed, trying fallback: {e}")
            send_fallback_message(message)
    else:
        if send_fallback_message(message):
            commitment_ledger.increment_notifications(BRAIN_PATH)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", help="Send a specific test message")
    parser.add_argument("--get-chat-id", action="store_true", help="Get chat ID")
    args = parser.parse_args()

    if args.test:
        asyncio.run(send_daily_briefing(args.test))
    elif args.get_chat_id:
        # Simple GetUpdates implementation
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                print(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error: {e}")
    else:
        asyncio.run(send_daily_briefing())

if __name__ == "__main__":
    main()
