"""
judge.py — Layer 2: Behavioral judge.

For each UC, takes before + after screenshots and asks Claude Vision:
"Did the right thing happen?"

Returns PASS / FAIL / UNCERTAIN with confidence and reason.
"""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path

import anthropic

from .observation_log import JudgeResult

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 400

PROMPT_TEMPLATE = """\
You are a behavioral QA oracle for a Flutter iOS app called {product_name}.

You have been given two screenshots:
- Image 1: the BEFORE state — captured immediately before a user action
- Image 2: the AFTER state — captured after the action completed

USE CASE: {uc_id} — {uc_title}
SCREEN: {screen}
ACTION TAKEN: {defining_action}

EXPECTED AFTER STATE:
{after_state_description}

JUDGE CRITERIA (all must be true for a PASS):
{criteria_list}

Your task: determine whether the right thing happened.

Respond with ONLY a JSON object. No markdown, no preamble, no explanation outside the JSON.

{{
  "verdict": "PASS" | "FAIL" | "UNCERTAIN",
  "confidence": <integer 0-100>,
  "reason": "<1-3 sentences referencing what you see in the screenshots>",
  "issues": ["<specific issue 1>", "<specific issue 2>"]
}}

Rules:
- PASS: all judge criteria visually confirmed in Image 2
- FAIL: at least one criterion clearly not met, OR Image 2 shows an error state / wrong screen
- UNCERTAIN: Image 2 is ambiguous (loading state, partially rendered, criteria not visually verifiable)
- confidence reflects how clearly the screenshots support the verdict
- issues array is empty on PASS; 1+ items on FAIL/UNCERTAIN
- Do not invent problems. If the after state looks correct, say PASS."""


def _encode_image(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode("utf-8")


def judge_uc(
    client: anthropic.Anthropic,
    before_path: Path,
    after_path: Path,
    uc_spec: dict,
    product_name: str,
) -> JudgeResult:
    """Call Claude Vision to judge whether a UC succeeded."""

    criteria = "\n".join(
        f"{i+1}. {c}" for i, c in enumerate(uc_spec.get("judge_criteria", []))
    )

    prompt = PROMPT_TEMPLATE.format(
        product_name=product_name,
        uc_id=uc_spec["id"],
        uc_title=uc_spec["title"],
        screen=uc_spec.get("screen", ""),
        defining_action=uc_spec.get("defining_action", ""),
        after_state_description=uc_spec.get("after_state", {}).get("description", ""),
        criteria_list=criteria,
    )

    before_b64 = _encode_image(before_path)
    after_b64 = _encode_image(after_path)

    response = None
    for attempt in range(2):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": before_b64}},
                            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": after_b64}},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )
            raw = response.content[0].text.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            return JudgeResult(
                verdict=data["verdict"],
                confidence=int(data.get("confidence", 50)),
                reason=data.get("reason", ""),
                raw_response=raw,
                issues=data.get("issues", []),
                model=MODEL,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
        except json.JSONDecodeError as e:
            raw_text = response.content[0].text if response is not None else ""
            return JudgeResult(
                verdict="UNCERTAIN",
                confidence=0,
                reason="parse_error",
                raw_response=raw_text,
                issues=[str(e)],
                model=MODEL,
            )
        except anthropic.APIError as e:
            if attempt == 0:
                time.sleep(5)
                continue
            return JudgeResult(
                verdict="JUDGE_ERROR",
                confidence=0,
                reason=str(e),
                raw_response="",
                issues=[str(e)],
                model=MODEL,
            )

    return JudgeResult(verdict="JUDGE_ERROR", confidence=0, reason="max retries", raw_response="", issues=[])
