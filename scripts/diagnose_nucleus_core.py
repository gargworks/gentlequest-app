import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path("/Users/lokeshgarg/ai-mvp-backend")
sys.path.append(str(project_root / "mcp-server-nucleus" / "src"))

# Set environment variables
os.environ["NUCLEUS_BRAIN_PATH"] = str(project_root / ".brain")
os.environ["NUCLEAR_BRAIN_PATH"] = str(project_root / ".brain")
os.environ["FORCE_VERTEX"] = "0" # Use API key for simpler diagnostic

# Force standard levels for debugging
logging.basicConfig(level=logging.INFO)

from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
from mcp_server_nucleus.runtime.factory import ContextFactory

def main():
    try:
        print("🔍 Testing DualEngineLLM (Full Inference: RESEARCH)...")
        model = DualEngineLLM(job_type="RESEARCH")
        print(f"✅ LLM Initialized. Engine: {model.engine}, Tier: {model.tier}, Model: {model.model_name}")
        
        print("📡 Attempting generate_content...")
        response = model.generate_content("Hello, this is a diagnostic test. Please respond with 'OK'.")
        if response:
            print(f"✅ Inference Success! Response: {response.text}")
        else:
            print("❌ Inference returned None.")
        
    except Exception as e:
        print(f"❌ Diagnostic Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
