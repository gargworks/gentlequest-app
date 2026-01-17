"""
Nucleus LLM Client
==================
Dual-Engine LLM Client.
Primary: google-genai (v1.0+)
Fallback: google-generativeai (Legacy)

MDR_010 Compliant: Ensures high availability and reliability.
"""

import os
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Configure logger
logger = logging.getLogger("nucleus.llm")

HAS_GENAI = False
HAS_LEGACY = False

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    pass

try:
    import google.generativeai as genai_legacy
    HAS_LEGACY = True
except ImportError:
    pass

class DualEngineLLM:
    """
    Unified LLM Client wrapper.
    Transparently falls back to legacy SDK if V1 is not available.
    """
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp", system_instruction: Optional[str] = None, api_key: Optional[str] = None):
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.client = None
        self.engine = "NONE"
        
        # 0. Check for FORCE_VERTEX switch (Production/Enterprise Mode)
        force_vertex = os.environ.get("FORCE_VERTEX", "0") == "1"
        
        if not self.api_key and not force_vertex:
            raise ValueError("GEMINI_API_KEY is required (or set FORCE_VERTEX=1).")
            
        # 1. Try V1 (Primary)
        if HAS_GENAI:
            try:
                if force_vertex:
                    # Enterprise Mode: Use GCP Credentials (ADC)
                    # Requires GOOGLE_APPLICATION_CREDENTIALS or gcloud auth
                    project_id = os.environ.get("GCP_PROJECT_ID", os.environ.get("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0894185576"))
                    location = os.environ.get("GCP_LOCATION", "us-central1")
                    
                    logger.info(f"🏢 LLM Client: FORCE_VERTEX enabled. Connecting to Vertex AI ({project_id})...")
                    self.client = genai.Client(
                        vertexai=True, 
                        project=project_id, 
                        location=location
                    )
                else:
                    # Personal Mode: Use API Key
                    self.client = genai.Client(api_key=self.api_key, http_options={'api_version': 'v1alpha'})
                    
                self.engine = "NEW"
                logger.info(f"✅ LLM Client: Initialized google-genai (V1) for {model_name} [Vertex={force_vertex}]")
                return
            except Exception as e:
                logger.warning(f"⚠️ LLM Client: V1 Init failed ({e}). Trying Legacy...")

        # 2. Try Legacy (Fallback)
        if HAS_LEGACY:
            try:
                genai_legacy.configure(api_key=self.api_key)
                # Map newer model names to legacy compatible ones if needed
                if "2.0" in model_name:
                    logger.warning(f"⚠️ Legacy SDK may not support {model_name}. Using gemini-1.5-flash.")
                    self.model_name = "gemini-1.5-flash"
                
                self.model = genai_legacy.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_instruction
                )
                self.engine = "LEGACY"
                logger.info(f"✅ LLM Client: Initialized google-generativeai (Legacy) for {self.model_name}")
                return
            except Exception as e:
                logger.error(f"❌ LLM Client: Legacy Init failed: {e}")
                
        if self.engine == "NONE":
            raise ImportError("Could not initialize any Gemini SDK. Install google-genai or google-generativeai.")

    def _log_interaction(self, prompt: str, response: Any):
        """
        Automatic Capture (Brain Consolidation - Phase 1).
        Saves the raw interaction to disk for later mining/consolidation.
        """
        try:
            brain_path = Path(os.environ.get("NUCLEAR_BRAIN_PATH", ".brain"))
            raw_path = brain_path / "raw"
            raw_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = raw_path / f"llm_interaction_{timestamp}.json"
            
            # Extract text from response (Best effort)
            response_text = "Unknown"
            if hasattr(response, 'text'):
                response_text = response.text
                
            data = {
                "timestamp": datetime.now().isoformat(),
                "engine": self.engine,
                "model": self.model_name,
                "prompt": str(prompt)[:5000], # Truncate massive prompts 
                "response_text": response_text
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to log interaction: {e}")

    def generate_content(self, prompt: str, **kwargs) -> Any:
        try:
            if self.engine == "NEW":
                config_args = {}
                if self.system_instruction:
                    config_args['system_instruction'] = self.system_instruction
                    
                if 'tools' in kwargs:
                    tools_raw = kwargs['tools']
                    if isinstance(tools_raw, dict) and "function_declarations" in tools_raw:
                        config_args['tools'] = [tools_raw] 
                    else:
                        config_args['tools'] = tools_raw

                if 'tool_config' in kwargs:
                     config_args['tool_config'] = kwargs['tool_config']
                
                config = types.GenerateContentConfig(**config_args)
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                self._log_interaction(prompt, response)
                return response

            elif self.engine == "LEGACY":
                # Legacy SDK logic
                generation_config = {}
                # Legacy doesn't support tools same way here, basic text only for now or map tools manually
                # For Marketing Autopilot, we mostly use text.
                
                response = self.model.generate_content(prompt, generation_config=generation_config)
                self._log_interaction(prompt, response)
                return response

        except Exception as e:
            logger.error(f"❌ LLM Generate Content Failed ({self.engine}): {e}")
            raise

    def embed_content(self, text: str, task_type: str = "retrieval_document", title: Optional[str] = None) -> Dict[str, Any]:
        try:
            if self.engine == "NEW":
                normalized_task_type = task_type.replace("retrieval_", "RETRIEVAL_").upper()
                config = {'task_type': normalized_task_type}
                if title:
                    config['title'] = title
                
                response = self.client.models.embed_content(
                    model=self.model_name,
                    contents=text,
                    config=config
                )
                if hasattr(response, 'embeddings') and response.embeddings:
                    return {'embedding': response.embeddings[0].values}
                return {'embedding': []}
                
            elif self.engine == "LEGACY":
                # Legacy SDK
                # task_type mapping
                # content
                result = genai_legacy.embed_content(
                    model="models/text-embedding-004", # Hardcoded or passed in
                    content=text,
                    task_type=task_type,
                    title=title
                )
                return result

        except Exception as e:
             logger.error(f"❌ LLM Embed Content Failed ({self.engine}): {e}")
             raise

    @property
    def active_engine(self):
        return self.engine
