#!/usr/bin/env python3
"""
PEFS Telegram Bot - Daily Briefings and Commitment Reminders
MDR_010 Compliant: Includes feedback buttons, kill switch, and value tracking
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server-nucleus" / "src"))

from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from mcp_server_nucleus import commitment_ledger

BRAIN_PATH = Path(os.getenv("NUCLEAR_BRAIN_PATH", "/Users/lokeshgarg/ai-mvp-backend/.brain"))
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Your personal chat ID


# ============================================================
# MDR_010: CALLBACK HANDLERS FOR FEEDBACK
# ============================================================

async def handle_feedback(update: Update, context) -> None:
    """Handle inline button callbacks for Did I Help? feedback"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("feedback_"):
        # Format: feedback_{score}_{notification_type}
        parts = data.split("_")
        score = int(parts[1])
        notification_type = parts[2] if len(parts) > 2 else "daily"
        
        # Record feedback
        entry = commitment_ledger.record_feedback(
            BRAIN_PATH,
            notification_type=notification_type,
            score=score
        )
        
        if score >= 4:
            response = "✅ Glad it helped! This counts as high-impact."
        elif score >= 2:
            response = "📝 Noted. I'll try to be more useful."
        else:
            response = "😔 Sorry about that. I'll learn from this."
        
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(response)
    
    elif data == "stop_notifications":
        # Kill Switch activated
        commitment_ledger.pause_notifications(BRAIN_PATH)
        await query.edit_message_text(
            "🛑 Notifications paused. Reply /resume to restart."
        )
    
    elif data == "continue_notifications":
        commitment_ledger.record_interaction(BRAIN_PATH)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("👍 Great! I'll keep sending briefings.")


async def handle_resume(update: Update, context) -> None:
    """Handle /resume command to restart notifications"""
    commitment_ledger.resume_notifications(BRAIN_PATH)
    commitment_ledger.record_interaction(BRAIN_PATH)
    await update.message.reply_text("✅ Notifications resumed!")


async def handle_any_message(update: Update, context) -> None:
    """Record any user message as an interaction"""
    commitment_ledger.record_interaction(BRAIN_PATH)


# ============================================================
# MAIN BRIEFING (MDR_010 ENHANCED)
# ============================================================

async def send_daily_briefing():
    """Send morning briefing with commitment summary and feedback buttons"""
    
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        return
    
    # Check kill switch first
    kill_status = commitment_ledger.check_kill_switch(BRAIN_PATH)
    
    if kill_status["action"] == "paused":
        print("⏸️ Notifications paused by user. Skipping briefing.")
        return
    
    bot = Bot(token=BOT_TOKEN)
    ledger = commitment_ledger.load_ledger(BRAIN_PATH)
    stats = ledger.get("stats", {})
    
    open_comms = [c for c in ledger.get("commitments", []) if c["status"] == "open"]
    red_tier = [c for c in open_comms if c["tier"] == "red"]
    
    # Build message
    if not open_comms:
        message = """☀️ Good morning, Chairman!

✅ Zero open loops. Enjoy your guilt-free day!

🧠 Brain Health: OPTIMAL
"""
        keyboard = [
            [
                InlineKeyboardButton("👍 Helpful", callback_data="feedback_5_daily"),
                InlineKeyboardButton("👎 Not useful", callback_data="feedback_1_daily")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await bot.send_message(chat_id=CHAT_ID, text=message, reply_markup=reply_markup)
        commitment_ledger.increment_notifications(BRAIN_PATH)
        return
    
    # Mental load calculation
    if red_tier:
        mental_load = "🔴 HIGH"
    elif stats.get("yellow_tier", 0) > 2:
        mental_load = "🟡 MEDIUM"
    else:
        mental_load = "🟢 LOW"
    
    # MDR_010: Kill Switch escalation check
    if kill_status["action"] == "escalate":
        message = f"""⚠️ Chairman, I haven't heard from you in {kill_status['days_inactive']} days.

Is PEFS adding noise? Should I pause notifications?
"""
        keyboard = [
            [
                InlineKeyboardButton("🛑 STOP - Pause notifications", callback_data="stop_notifications"),
                InlineKeyboardButton("✅ Continue", callback_data="continue_notifications")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await bot.send_message(chat_id=CHAT_ID, text=message, reply_markup=reply_markup)
        commitment_ledger.increment_notifications(BRAIN_PATH)
        return
    
    message = f"""☀️ Good morning, Chairman!

🎯 TODAY'S CRITICAL PATH:
• {stats.get('red_tier', 0)} commitment(s) need closure (aging >7 days)
• {stats.get('total_open', 0)} total open loops

🧠 BRAIN HEALTH:
• Mental load estimate: {mental_load}
• Last scan: {ledger.get('last_scan', 'Never')[:10] if ledger.get('last_scan') else 'Never'}
"""
    
    if red_tier:
        message += "\n🚨 RED TIER (needs attention):\n"
        for comm in red_tier[:3]:  # Show max 3
            desc = comm['description'][:50] + "..." if len(comm['description']) > 50 else comm['description']
            message += f"• {desc} ({comm['age_days']}d)\n"
        
        if len(red_tier) > 3:
            message += f"• ...and {len(red_tier) - 3} more\n"
    
    # Weekly Challenge
    challenge = commitment_ledger.load_challenge(BRAIN_PATH)
    if challenge and challenge.get("status") == "active":
        message += f"\n🏆 CHALLENGE: {challenge['title']}\n"
        message += f"• Goal: {challenge['description']}\n"
        message += f"• Reward: {challenge['reward']}\n"

    # Sunday Weekly Summary with Time Saved (MDR_010 Enhanced)
    if datetime.now().weekday() == 6:  # Sunday
        weekly = commitment_ledger.get_weekly_summary(BRAIN_PATH)
        
        message += "\n📊 WEEKLY SUMMARY:\n"
        message += f"• Velocity: {weekly['velocity_7d']} items closed\n"
        message += f"• Avg Speed: {weekly['avg_days_to_close']} days\n"
        message += f"• ⏰ Time Saved: ~{weekly['estimated_time_saved_hours']}h this week\n"
        message += f"• Value Ratio: {weekly['value_ratio'].get('verdict', 'N/A')}\n"
        
        if weekly['manual_overrides'] > 0:
            message += f"• ⚠️ Friction: {weekly['friction_score']} ({weekly['manual_overrides']} overrides)\n"
    
    # MDR_010: "Did I Help?" feedback buttons
    keyboard = [
        [
            InlineKeyboardButton("👍 Helpful", callback_data="feedback_5_daily"),
            InlineKeyboardButton("🤷 Meh", callback_data="feedback_3_daily"),
            InlineKeyboardButton("👎 Noise", callback_data="feedback_1_daily")
        ],
        [InlineKeyboardButton("🔍 View All Commitments", url=f"file://{BRAIN_PATH}/commitments/ledger.json")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, reply_markup=reply_markup)
        commitment_ledger.increment_notifications(BRAIN_PATH)
        print(f"✅ Briefing sent to {CHAT_ID}")
    except Exception as e:
        print(f"❌ Failed to send briefing: {e}")


def run_bot():
    """Run the bot with callback handlers for interactive mode"""
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CallbackQueryHandler(handle_feedback))
    application.add_handler(CommandHandler("resume", handle_resume))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message))
    
    print("🤖 Bot running with MDR_010 compliance...")
    application.run_polling()


def main():
    """Main entry point - just send daily briefing"""
    asyncio.run(send_daily_briefing())


if __name__ == "__main__":
    # If run with --interactive, start the full bot
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        run_bot()
    else:
        main()
