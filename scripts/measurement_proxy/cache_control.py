"""PR-2: request-side cache_control parser + per-stream attribution.

Walks Anthropic-API request bodies to (1) enumerate every block carrying a
``cache_control`` annotation for the ``request_usage_counters.cache_control_blocks``
array, and (2) decompose per-turn input cost into the three measurement streams
defined in §1 of compounding_multiplier_wedge.md:

    - cached_system_prompt_effective  (10% of cache_read + 100% of cache_creation)
    - uncached_dynamic_reminder       (<system-reminder> blocks not in cache)
    - uncached_conversation_history   (messages[] not in cache, excluding reminders)

Per-stream decomposition is a heuristic (byte/4 token approximation on uncached
blocks, combined with response-side aggregates for cached cost). The heuristic
lands in ``high`` confidence when |decomposed − billed| / billed < 10%, else
``partial`` or ``fallback_aggregate`` per §4.1 turn-scoped fallback framing.
"""

from __future__ import annotations

import json
import re
from typing import Any


_SYSTEM_REMINDER_PATTERN = re.compile(r"<system-reminder[> ]", re.IGNORECASE)

HEURISTIC_RESOLUTION_FLOOR = 10
"""Below this response_input_tokens count, the byte/4 approximation cannot
resolve decomposer-vs-billing deltas meaningfully. Treated as high confidence
by rule — ratio math is dominated by quantization noise at this magnitude."""


def approx_tokens(text: str) -> int:
    """Byte-length/4 heuristic. Crude but consistent across baseline/experimental."""
    if not text:
        return 0
    return max(1, len(text.encode("utf-8")) // 4)


def _block_text(block: Any) -> str:
    if isinstance(block, str):
        return block
    if not isinstance(block, dict):
        return ""
    kind = block.get("type")
    if kind == "text":
        return block.get("text") or ""
    if kind == "tool_use":
        return json.dumps(block.get("input") or {}, ensure_ascii=False)
    if kind == "thinking":
        return block.get("thinking") or ""
    if kind == "tool_result":
        content = block.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(_block_text(b) for b in content)
        if content is None:
            return ""
        return json.dumps(content, ensure_ascii=False)
    # Tool definitions (top-level entries in body["tools"]): no "type" field;
    # recognized by name + input_schema. Token cost = serialized definition.
    if "name" in block and "input_schema" in block:
        return json.dumps(
            {
                "name": block.get("name"),
                "description": block.get("description") or "",
                "input_schema": block.get("input_schema") or {},
            },
            ensure_ascii=False,
        )
    return ""


def parse_cache_control(body: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the schema-shaped ``cache_control_blocks`` list for a request body."""
    blocks: list[dict[str, Any]] = []
    idx = 0

    def _scan(role: str, content: Any) -> None:
        nonlocal idx
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("cache_control"):
                    blocks.append(
                        {
                            "block_index": idx,
                            "role": role,
                            "block_kind": block.get("type") or "text",
                            "cache_control_type": (block["cache_control"] or {}).get("type") or "ephemeral",
                            "approx_token_count": approx_tokens(_block_text(block)),
                        }
                    )
                idx += 1
        else:
            idx += 1

    _scan("system", body.get("system"))
    for msg in body.get("messages") or []:
        if isinstance(msg, dict):
            _scan(msg.get("role") or "user", msg.get("content"))

    for tool in body.get("tools") or []:
        if isinstance(tool, dict) and tool.get("cache_control"):
            blocks.append(
                {
                    "block_index": idx,
                    "role": "system",
                    "block_kind": "tool_use",
                    "cache_control_type": (tool["cache_control"] or {}).get("type") or "ephemeral",
                    "approx_token_count": approx_tokens(json.dumps(tool, ensure_ascii=False)),
                }
            )
            idx += 1
    return blocks


def _flatten_blocks(body: dict[str, Any]) -> list[dict[str, Any] | str]:
    """Flatten system + tools + messages into a single ordered block list.

    Anthropic cache_control semantics are prefix-boundary: a `cache_control`
    marker at position K in the flattened prompt caches blocks 0..K together.
    Only blocks after the LAST marker are truly uncached. This helper produces
    the ordered list the boundary-finder walks, in the wire-prefix order
    ``system → tools → messages`` so cache-boundary calculations match
    Anthropic's actual prompt assembly.

    Pre-2026-04-27 versions of this function omitted ``tools`` entirely, which
    caused decomposed_uncached to systematically undercount by the size of the
    tool array (10-50K tokens in MCP-using clients). That surfaced as
    fallback_aggregate attribution on the majority of turns
    (engram:phase1_baseline_analysis_20260427). Tools are now first-class
    blocks in the flat list and may individually carry ``cache_control``;
    their schema/description tokens count toward
    ``uncached_conversation_history`` when they sit after the cache boundary.

    String content (system as a bare string, or a message with `content: "..."`)
    becomes one atomic "block" represented as the string itself — cache_control
    cannot be applied to it.
    """
    flat: list[dict[str, Any] | str] = []
    sys_content = body.get("system")
    if isinstance(sys_content, str):
        flat.append(sys_content)
    elif isinstance(sys_content, list):
        flat.extend(b for b in sys_content if isinstance(b, (dict, str)))
    for tool in body.get("tools") or []:
        if isinstance(tool, dict):
            flat.append(tool)
    for msg in body.get("messages") or []:
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if isinstance(content, str):
            flat.append(content)
        elif isinstance(content, list):
            flat.extend(b for b in content if isinstance(b, (dict, str)))
    return flat


def _count_block(block: dict[str, Any] | str) -> tuple[int, int, int]:
    """Classify one block's token count as (reminder, history, tool_result)."""
    if isinstance(block, str):
        tokens = approx_tokens(block)
        if _SYSTEM_REMINDER_PATTERN.search(block):
            return tokens, 0, 0
        return 0, tokens, 0
    if not isinstance(block, dict):
        return 0, 0, 0
    text = _block_text(block)
    tokens = approx_tokens(text)
    if block.get("type") == "tool_result":
        return 0, tokens, tokens
    if _SYSTEM_REMINDER_PATTERN.search(text):
        return tokens, 0, 0
    return 0, tokens, 0


def compute_per_stream_attribution(
    body: dict[str, Any],
    response_input_tokens: int,
    cache_read_tokens: int,
    cache_creation_tokens: int,
) -> dict[str, Any]:
    """Decompose per-turn input cost into the 3 streams + confidence label.

    Honors Anthropic prefix-boundary cache semantics: the block at the largest
    index carrying `cache_control` defines the cache boundary; blocks at that
    index or earlier are cached (don't count toward uncached streams); blocks
    after are uncached and decomposed into reminder / history / tool_result.
    """
    cached_effective = cache_creation_tokens + (cache_read_tokens // 10)

    flat = _flatten_blocks(body)
    last_cc = -1
    for i, block in enumerate(flat):
        if isinstance(block, dict) and block.get("cache_control"):
            last_cc = i

    reminder_t = 0
    history_t = 0
    tool_result_t = 0
    for block in flat[last_cc + 1:]:
        r, h, tr = _count_block(block)
        reminder_t += r
        history_t += h
        tool_result_t += tr

    decomposed_uncached = reminder_t + history_t
    if response_input_tokens <= 0:
        confidence = "fallback_aggregate"
    elif response_input_tokens <= HEURISTIC_RESOLUTION_FLOOR:
        confidence = "high"
    elif decomposed_uncached == 0 and (cache_read_tokens > 0 or cache_creation_tokens > 0):
        confidence = "high"
    else:
        ratio = abs(decomposed_uncached - response_input_tokens) / response_input_tokens
        if ratio < 0.10:
            confidence = "high"
        elif ratio < 0.25:
            confidence = "partial"
        else:
            confidence = "fallback_aggregate"

    return {
        "cached_system_prompt_effective": cached_effective,
        "uncached_dynamic_reminder": reminder_t,
        "uncached_conversation_history": history_t,
        "tool_response_body_bytes": tool_result_t,
        "attribution_confidence": confidence,
    }
