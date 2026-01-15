
import os
import sys
import logging
import asyncio
import subprocess
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("nucleus-op")

# Configuration
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
PROJECT_ID = "gen-lang-client-0894185576"
REGION = os.environ.get("GCP_REGION", "us-central1")
JOB_NAME = "nucleus-builder"

# ═══════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message."""
    user = update.effective_user
    await update.message.reply_text(
        f"🤖 **Nucleus Operator Active**\nHello {user.first_name}!\n\n"
        "Commands:\n"
        "/deploy <plan> - Trigger Cloud Run Job\n"
        "/status - Check latest execution status\n"
        "/ping - Check bot connectivity"
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if bot is alive."""
    await update.message.reply_text("🏓 Pong! I am online.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check Cloud Run Job execution status."""
    await update.message.reply_text("🔍 Checking latest execution status...")
    
    try:
        cmd = [
            "gcloud", "run", "jobs", "executions", "list",
            "--job", JOB_NAME,
            "--region", REGION,
            "--project", PROJECT_ID,
            "--limit", "1",
            "--format", "value(name,status.conditions[0].status,creationTimestamp)"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            output = stdout.decode().strip()
            if output:
                # Simple parsing (Name, Status, Time are tab separated usually in value format but here depends)
                # value(a,b,c) outputs tab separated
                parts = output.split()
                name = parts[0]
                state = parts[1] if len(parts) > 1 else "Unknown"
                time_val = parts[2] if len(parts) > 2 else "?"
                
                emoji = "✅" if "True" in state else "❌" if "False" in state else "⏳"
                if state == "Unknown": emoji = "❓"

                await update.message.reply_text(
                    f"{emoji} **Job Status**\n"
                    f"Name: `{name}`\n"
                    f"State: `{state}`\n"
                    f"Time: `{time_val}`"
                )
            else:
                await update.message.reply_text("⚠️ No executions found.")
        else:
            await update.message.reply_text(f"❌ Error fetching status:\n`{stderr.decode()}`")

    except Exception as e:
        logger.error(f"Status error: {e}")
        await update.message.reply_text(f"⚠️ Internal Error: {e}")

async def deploy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger a Nucleus Swarm deployment."""
    # Parse arguments
    args = context.args
    plan = args[0] if args else "IMPLEMENTATION_PLAN_MOCK.md"
    
    await update.message.reply_text(
        f"🚀 **Initiating Deployment**\n"
        f"Target: `Cloud Run ({JOB_NAME})`\n"
        f"Plan: `{plan}`"
    )
    
    try:
        # Construct gcloud command
        # Arguments must be passed as a single string for --args if using execution_swarm.py parsing
        # execution_swarm.py uses argparse: --plan PLAN --test
        # Cloud Run passed arguments: --args="--plan=X"
        
        cmd = [
            "gcloud", "run", "jobs", "execute", JOB_NAME,
            "--region", REGION,
            "--project", PROJECT_ID,
            f"--args=--plan={plan}"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            output = stdout.decode().strip()
            # Extract basic info
            msg = f"✅ **Triggered Successfully!**\n\n`{output}`\n\nTrack with /status"
            if len(msg) > 4000: msg = msg[:4000] + "..."
            await update.message.reply_text(msg)
        else:
            error = stderr.decode().strip()
            await update.message.reply_text(f"❌ **Deployment Failed**\n`{error}`")
            
    except Exception as e:
        logger.error(f"Deploy error: {e}")
        await update.message.reply_text(f"⚠️ **Internal Bot Error**: {e}")

# ═══════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════

def main():
    """Start the bot."""
    if not TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable not set.")
        print("Please set it directly or in your .env file.")
        sys.exit(1)

    print(f"🤖 Starting Nucleus Operator...")
    print(f"   Mode: POLLING (Local Dev Friendly)")
    print(f"   Project: {PROJECT_ID}")
    
    # Create Application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("deploy", deploy))

    # Run
    print("✅ Bot is polling. Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()
