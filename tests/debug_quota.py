import os
import sys
from pathlib import Path

# Add src to path
CURRENT_DIR = Path(__file__).parent
SERVER_SRC = CURRENT_DIR.parent / "mcp-server-nucleus" / "src"
sys.path.append(str(SERVER_SRC))

# Mock valid keys to test precedence
os.environ["GEMINI_API_KEY"] = "fake-key"
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "fake-creds.json" 

try:
    from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
    client = DualEngineLLM(api_key="fake-key")
    print(f"✅ CLIENT ENGINE: {client.active_engine}")
    
    # Check what library is being used
    if client.engine == "NEW":
        print("Using: google-genai (V1) -> Likely AI Studio if API Key is used")
    elif client.engine == "LEGACY":
        print("Using: google-generativeai (Legacy) -> Likely AI Studio")
        
except Exception as e:
    print(f"Error: {e}")
