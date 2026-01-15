
import os
import discord
from discord.ext import commands
import subprocess
import asyncio
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nucleus-bot")

# Configuration
TOKEN = os.environ.get("DISCORD_TOKEN")
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "gentlequest-443904")
REGION = os.environ.get("GCP_REGION", "us-central1")
JOB_NAME = "nucleus-builder"

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Nucleus Bot Online: {bot.user}")
    print(f"Logged in as {bot.user}")

@bot.command(name="deploy")
async def deploy(ctx, plan: str = "IMPLEMENTATION_PLAN.md"):
    """Trigger a Nucleus Swarm deployment."""
    await ctx.send(f"🚀 **Initiating Deployment**\nPlan: `{plan}`\nTarget: `Cloud Run ({JOB_NAME})`")
    
    try:
        # Construct gcloud command
        cmd = [
            "gcloud", "run", "jobs", "execute", JOB_NAME,
            "--region", REGION,
            "--project", PROJECT_ID,
            "--args", f"--plan={plan},--force-vertex" 
            # Note: We pass --force-vertex to ensure cloud mode via args if script supports it
            # Currently execution_swarm.py takes --plan and --test. 
            # We might need to ensure arguments align.
        ]
        
        # Async execution
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            output = stdout.decode().strip()
            # Extract Execution ID if possible. 
            # Output usually: "Execution [nucleus-builder-xxxxx] has been successfully provisioned..."
            await ctx.send(f"✅ **Deployment Triggered Successfully!**\nLogs: `gcloud run jobs logs {JOB_NAME}`\nOutput: ```{output}```")
        else:
            error = stderr.decode().strip()
            await ctx.send(f"❌ **Deployment Failed**\nError: ```{error}```")
            
    except Exception as e:
        await ctx.send(f"⚠️ **Internal Bot Error**: {str(e)}")

@bot.command(name="status")
async def status(ctx):
    """Check status of latest execution."""
    await ctx.send("🔍 Checking latest execution status...")
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
             info = stdout.decode().strip().split()
             if info:
                 name = info[0]
                 # Status parsing might vary depending on output format
                 await ctx.send(f"**Latest Job**: `{name}`\n**Raw Status**: `{stdout.decode().strip()}`")
             else:
                 await ctx.send("No executions found.")
         else:
             await ctx.send(f"Error checking status: {stderr.decode()}")

    except Exception as e:
        await ctx.send(f"Error: {e}")

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set.")
        exit(1)
    bot.run(TOKEN)
