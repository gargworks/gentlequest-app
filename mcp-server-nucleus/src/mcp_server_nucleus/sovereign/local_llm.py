"""Local/self-hosted LLM client — the Third Brother provider.

Connects to any OpenAI-compatible endpoint (Ollama, vLLM, llama.cpp,
text-generation-inference, LM Studio). This is where the fine-tuned
model runs after training on the archive pipeline data.

Env vars:
    NUCLEUS_LOCAL_ENDPOINT  — base URL (default: http://localhost:11434/v1)
    NUCLEUS_LOCAL_MODEL     — model name (default: nucleus-brother)
    NUCLEUS_LOCAL_API_KEY   — optional API key for vLLM/TGI auth
"""

import logging
import os
from typing import Optional

from ..runtime.llm_client import AnthropicResponse, LLMTier

logger = logging.getLogger("nucleus.llm.local")


class LocalLLM:
    DEFAULT_ENDPOINT = "http://localhost:11434/v1"  # Ollama default
    DEFAULT_MODEL = "nucleus-brother"

    def __init__(
        self,
        model_name: Optional[str] = None,
        system_instruction: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        tier: Optional[LLMTier] = None,
        job_type: Optional[str] = None,
        budget_mode: str = "balanced",
        **_ignored,
    ):
        self.endpoint = (
            endpoint
            or os.environ.get("NUCLEUS_LOCAL_ENDPOINT", self.DEFAULT_ENDPOINT)
        ).rstrip("/")
        self.model_name = model_name or os.environ.get(
            "NUCLEUS_LOCAL_MODEL", self.DEFAULT_MODEL
        )
        self.api_key = api_key or os.environ.get("NUCLEUS_LOCAL_API_KEY", "not-needed")
        self.system_instruction = system_instruction
        self.engine = "LOCAL"
        self.tier = tier
        self.budget_mode = budget_mode

        logger.info(f"🧬 LLM Client: Local/Third Brother → {self.model_name} @ {self.endpoint}")

    def generate_content(self, prompt, **kwargs) -> AnthropicResponse:
        """Generate text via OpenAI-compatible chat completions API."""
        import urllib.request
        import json as _json

        messages = []
        if isinstance(prompt, list):
            if self.system_instruction and not any(m.get("role") == "system" for m in prompt):
                messages.append({"role": "system", "content": self.system_instruction})
            messages.extend(prompt)
        else:
            if self.system_instruction:
                messages.append({"role": "system", "content": self.system_instruction})
            messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
        }

        url = f"{self.endpoint}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        req = urllib.request.Request(
            url,
            data=_json.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = _json.loads(resp.read().decode())
        except Exception as e:
            raise RuntimeError(
                f"Local LLM at {self.endpoint} unreachable: {e}\n"
                f"  Start Ollama: ollama serve && ollama run {self.model_name}\n"
                f"  Or set NUCLEUS_LOCAL_ENDPOINT to your vLLM/TGI endpoint."
            )

        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return AnthropicResponse(
            text=text,
            model=data.get("model", self.model_name),
            usage={
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            },
        )

    def generate_content_stream(self, prompt, **kwargs):
        """Streaming via OpenAI-compatible SSE endpoint."""
        import urllib.request
        import json as _json

        messages = []
        if isinstance(prompt, list):
            if self.system_instruction and not any(m.get("role") == "system" for m in prompt):
                messages.append({"role": "system", "content": self.system_instruction})
            messages.extend(prompt)
        else:
            if self.system_instruction:
                messages.append({"role": "system", "content": self.system_instruction})
            messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": True,
        }

        url = f"{self.endpoint}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        req = urllib.request.Request(
            url,
            data=_json.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )

        try:
            resp = urllib.request.urlopen(req, timeout=120)
            for line in resp:
                line = line.decode().strip()
                if not line or not line.startswith("data: "):
                    continue
                chunk_str = line[6:]
                if chunk_str == "[DONE]":
                    break
                chunk = _json.loads(chunk_str)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content
        except Exception as e:
            logger.warning(f"Local streaming failed: {e}")
            response = self.generate_content(prompt, **kwargs)
            yield response.text

    generate = generate_content
    stream_content = generate_content_stream

    @property
    def active_engine(self):
        return self.engine
