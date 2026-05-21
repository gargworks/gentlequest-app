"""Local/self-hosted LLM client — the Third Brother provider.

Connects to any OpenAI-compatible endpoint (Ollama, vLLM, llama.cpp,
text-generation-inference, LM Studio). This is where the fine-tuned
model runs after training on the archive pipeline data.

Env vars:
    NUCLEUS_LOCAL_ENDPOINT  — base URL (default: http://localhost:11434/v1)
    NUCLEUS_LOCAL_MODEL     — model name (default: nucleus-brother)
    NUCLEUS_LOCAL_API_KEY   — optional API key for vLLM/TGI auth
"""

import json as _json_top
import logging
import os
import re as _re_top
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..runtime.llm_client import AnthropicResponse, LLMTier

logger = logging.getLogger("nucleus.llm.local")


def _format_tools_for_prompt(tools: List[Dict[str, Any]]) -> str:
    """ReAct-style tool serialization for models lacking native tool-use.

    v14 Modelfile has no `{{ .Tools }}` block and weights weren't trained on
    tool-call JSON, so Ollama rejects `tools=` in the payload. We inject the
    specs into the system prompt and parse the assistant text for tool_call
    blocks. When v15+ ships with native support, swap this for the payload
    `tools` field.
    """
    lines = ["You have access to the following tools:", ""]
    for t in tools:
        fn = t.get("function", t)
        name = fn.get("name", "?")
        desc = fn.get("description", "")
        params = fn.get("parameters", {})
        lines.append(f"- {name}: {desc}")
        if params:
            lines.append(f"  parameters: {_json_top.dumps(params)}")
    lines.extend([
        "",
        "To call a tool, emit exactly one JSON block wrapped in <tool_call> tags:",
        '<tool_call>{"name": "<tool_name>", "arguments": {...}}</tool_call>',
        "Emit at most one tool_call per turn. If no tool is needed, respond normally.",
    ])
    return "\n".join(lines)


_TOOL_CALL_RE = _re_top.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", _re_top.DOTALL)


def _parse_tool_calls_from_text(text: str) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
    """Extract <tool_call>{...}</tool_call> blocks from assistant text.

    Returns (stripped_text, tool_calls_or_None). Malformed blocks are dropped.
    """
    matches = _TOOL_CALL_RE.findall(text)
    if not matches:
        return text, None
    tool_calls: List[Dict[str, Any]] = []
    for idx, raw in enumerate(matches):
        try:
            parsed = _json_top.loads(raw)
        except (ValueError, TypeError):
            continue
        tool_calls.append({
            "id": f"call_{idx}",
            "type": "function",
            "name": parsed.get("name", ""),
            "arguments": parsed.get("arguments", {}),
        })
    if not tool_calls:
        return text, None
    stripped = _TOOL_CALL_RE.sub("", text).strip()
    return stripped, tool_calls


@dataclass
class LocalLLMResponse:
    """Response wrapper that surfaces tool_calls alongside text.

    Superset of AnthropicResponse — adds tool_calls for Qwen3-style
    function-calling. When tools are NOT passed, behaves identically
    (tool_calls is None, text populated).
    """
    text: str
    model: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    tool_calls: Optional[List[Dict[str, Any]]] = None  # OpenAI-format tool_calls
    finish_reason: Optional[str] = None  # "stop" | "tool_calls" | ...


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
        """Generate text via OpenAI-compatible chat completions API.

        Text-only. For tool-calling use generate_with_tools() — v14 rejects
        `tools` in the payload (Modelfile lacks `{{ .Tools }}` template).
        """
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
            with urllib.request.urlopen(req, timeout=kwargs.get("timeout", 120)) as resp:
                data = _json.loads(resp.read().decode())
        except Exception as e:
            raise RuntimeError(
                f"Local LLM at {self.endpoint} unreachable: {e}\n"
                f"  Start Ollama: ollama serve && ollama run {self.model_name}\n"
                f"  Or set NUCLEUS_LOCAL_ENDPOINT to your vLLM/TGI endpoint."
            )

        message = data["choices"][0]["message"]
        text = message.get("content") or ""
        usage = data.get("usage", {})
        return AnthropicResponse(
            text=text,
            model=data.get("model", self.model_name),
            usage={
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            },
        )

    def generate_with_tools(self, prompt, tools: List[Dict], **kwargs) -> LocalLLMResponse:
        """Single-turn generation with tool-calling. Returns LocalLLMResponse.

        Uses ReAct-in-prompt (Path B) for models lacking native tool-use:
        tools are serialized into the system prompt; assistant text is parsed
        for <tool_call>{...}</tool_call> blocks. v14 Modelfile has no
        `{{ .Tools }}` template and weights weren't trained on tool-call JSON,
        so native Ollama tool-use returns HTTP 400. When v15+ lands with
        tool-use training, flip `native_tool_use=True` in kwargs to send
        `tools` in the payload instead.

        Does NOT execute tool calls — that's the caller's job (see
        tb_context_injector.py).
        """
        import urllib.request
        import json as _json

        native = bool(kwargs.get("native_tool_use", False))

        messages = []
        if isinstance(prompt, list):
            messages.extend(prompt)
            has_system = any(m.get("role") == "system" for m in messages)
        else:
            if self.system_instruction:
                messages.append({"role": "system", "content": self.system_instruction})
            messages.append({"role": "user", "content": prompt})
            has_system = any(m.get("role") == "system" for m in messages)

        if not native:
            tool_block = _format_tools_for_prompt(tools)
            if has_system:
                for m in messages:
                    if m.get("role") == "system":
                        m["content"] = (m.get("content") or "") + "\n\n" + tool_block
                        break
            else:
                sys_msg = self.system_instruction or ""
                sys_msg = (sys_msg + "\n\n" + tool_block) if sys_msg else tool_block
                messages.insert(0, {"role": "system", "content": sys_msg})
        elif self.system_instruction and not has_system:
            messages.insert(0, {"role": "system", "content": self.system_instruction})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
        }
        if native:
            payload["tools"] = tools
            tool_choice = kwargs.get("tool_choice")
            if tool_choice is not None:
                payload["tool_choice"] = tool_choice

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
            with urllib.request.urlopen(req, timeout=kwargs.get("timeout", 120)) as resp:
                data = _json.loads(resp.read().decode())
        except Exception as e:
            raise RuntimeError(
                f"Local LLM at {self.endpoint} unreachable: {e}\n"
                f"  Start Ollama: ollama serve && ollama run {self.model_name}"
            )

        choice = data["choices"][0]
        message = choice.get("message", {})
        usage = data.get("usage", {})
        text = message.get("content") or ""
        finish_reason = choice.get("finish_reason")

        tool_calls = None
        if native:
            raw_tool_calls = message.get("tool_calls")
            if raw_tool_calls:
                tool_calls = []
                for tc in raw_tool_calls:
                    fn = tc.get("function", {})
                    args_str = fn.get("arguments", "{}")
                    try:
                        args = _json.loads(args_str) if isinstance(args_str, str) else args_str
                    except (ValueError, TypeError):
                        args = {"_raw": args_str}
                    tool_calls.append({
                        "id": tc.get("id", ""),
                        "type": tc.get("type", "function"),
                        "name": fn.get("name", ""),
                        "arguments": args,
                    })
        else:
            stripped, parsed_calls = _parse_tool_calls_from_text(text)
            if parsed_calls:
                text = stripped
                tool_calls = parsed_calls
                finish_reason = "tool_calls"

        return LocalLLMResponse(
            text=text,
            model=data.get("model", self.model_name),
            usage={
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            },
            tool_calls=tool_calls,
            finish_reason=finish_reason,
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
