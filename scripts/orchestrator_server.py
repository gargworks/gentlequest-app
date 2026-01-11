import os
import asyncio
from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
import uvicorn
from pathlib import Path
import sys

# Ensure path is set up to find mcp_server_nucleus
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "mcp-server-nucleus" / "src"))

# Import the orchestrator logic
# Note: We import inside the function or after path setup
try:
    from scripts.orchestrator import run_orchestrator
except ImportError:
    # Fallback if scripts module not found (e.g. running from scripts dir)
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.orchestrator import run_orchestrator

app = FastAPI(title="Nucleus Cloud Orchestrator")

@app.get("/")
async def health_check():
    """Health check for Cloud Run."""
    return {"status": "healthy", "service": "nucleus-orchestrator"}

@app.post("/tick")
async def trigger_orchestrator(background_tasks: BackgroundTasks):
    """
    Trigger the orchestrator loop.
    Cloud Scheduler should hit this endpoint.
    """
    background_tasks.add_task(run_orchestrator_task)
    return {"status": "triggered"}

async def run_orchestrator_task():
    """Run the orchestrator and catch errors."""
    try:
        print("⏰ Orchestrator triggered via API")
        await run_orchestrator()
    except Exception as e:
        print(f"❌ Orchestrator failed: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
