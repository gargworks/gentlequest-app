"""
user_mind.py — Layer 3: Synthetic user mind simulation.

Simulates Maya (24, Austin, mildly anxious) looking at the after-screenshot.
Speaks as Maya first, then as UX consultant.

Uses a static system prompt with cache_control to amortize ~80% of input
cost from the second call onward in a run.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

try:
    import anthropic
    _APIError = anthropic.APIError
except ImportError:
    anthropic = None  # type: ignore[assignment]
    _APIError = Exception  # type: ignore[assignment,misc]

from .observation_log import JudgeResult, MindResult

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 700

SYSTEM_PROMPT = """\
You are a dual-role synthetic UX evaluator. You will first simulate the inner \
experience of a real user, then step out and give a UX consultant critique. \
Your output must be a single JSON object with exactly the fields specified. \
Do not break character during the user simulation section."""

MAYA_PERSONA = """\
You are Maya.

Age: 24. Lives alone in Austin. Works remotely as a junior UX writer at a SaaS startup.
Mental health: mildly anxious, occasional spiral thoughts at night. Not in crisis — just \
someone who has tried therapy once and found it too expensive to continue. She downloaded \
GentleQuest tonight after seeing a TikTok about "AI wellness companions." She has \
medium-low trust in apps: she's been burned by notification spam before.

Tonight's emotional context: It's 9:48 PM. She had a stressful day — her manager moved \
up a deadline without warning. She opened GentleQuest 7 minutes ago. She has not spoken \
to anyone today except two Slack messages."""

RESPONSE_FORMAT = """\
Respond with ONLY this JSON object. No markdown, no preamble.

{
  "first_reaction": "<Maya's literal inner monologue, first person, 1-2 sentences>",
  "emotional_state": "<1 sentence, present tense, sensory/physiological — not abstract>",
  "expected": "<what Maya expected to see or happen based on what she just did>",
  "actual": "<what she actually sees>",
  "gap": "<the delta — 'none' or specific description of mismatch and its emotional weight>",
  "unspoken_frustration": "<what Maya would never say aloud but feels — or 'none'>",
  "unspoken_delight": "<small moment of pleasure she wouldn't consciously notice — or 'none'>",
  "continue_or_abandon": "continue" | "abandon" | "hesitate",
  "abandon_risk_score": <integer 0-100, 0=definitely continues, 100=closes app right now>,
  "heuristic_violated": "<H# — name — 1-sentence violation description — or 'none'>",
  "design_verdict": "BLOCKER" | "HIGH" | "MEDIUM" | "LOW" | "DELIGHT",
  "refinement_suggestion": "<specific widget/copy/interaction change, max 30 words>"
}

Field rules:
- first_reaction: Maya's voice, not a description of her
- emotional_state: use sensory language ("chest tightening", "relief washing over"), not abstract ("she felt good")
- gap: if no gap, name what Maya noticed positively instead
- abandon_risk_score: calibrated to Maya specifically — anxious 24yo, not a power user
- heuristic_violated: use Nielsen H1-H10 (H1 visibility, H2 real-world match, H3 user control, \
H4 consistency, H5 error prevention, H6 recognition over recall, H7 flexibility, \
H8 aesthetic/minimal, H9 error recovery, H10 help)
- design_verdict: BLOCKER=causes dropout/safety risk; HIGH=erodes trust; MEDIUM=survivable friction; \
LOW=minor polish; DELIGHT=unexpected positive worth protecting
- refinement_suggestion: name the specific widget, copy string, or interaction — not general guidance"""


def _encode_image(path: Path) -> str:
    import base64
    return base64.standard_b64encode(path.read_bytes()).decode("utf-8")


def simulate_mind(
    client: anthropic.Anthropic,
    after_path: Path,
    uc_spec: dict,
    judge_result: JudgeResult,
) -> MindResult:
    """Simulate Maya's experience of the after-screenshot."""

    persona_context = uc_spec.get("persona_context", "")

    # If the judge flagged a failure, prime Maya's state accordingly
    if judge_result.verdict == "FAIL" and judge_result.reason not in ("parse_error", ""):
        persona_context = (
            f"Maya just experienced a broken flow: {judge_result.reason}. "
            + persona_context
        )

    user_text = f"""\
== PERSONA BOOT ==
{MAYA_PERSONA}

USE CASE CONTEXT: {persona_context}

USE CASE: {uc_spec['id']} — {uc_spec['title']}
SCREEN: {uc_spec.get('screen', '')}
ACTION TAKEN: {uc_spec.get('defining_action', '')}

The screenshot above is what Maya sees RIGHT NOW on her phone.

Step completely into Maya's perspective. You are Maya looking at this screen.
Simulate her inner experience. Do not describe the screen from outside.

Then step out of Maya and become a senior UX consultant with 12 years in
consumer mental health products (2M+ users with anxiety disorders). Apply
Nielsen's heuristics. Assign severity honestly — DELIGHT is as valuable as BLOCKER.

{RESPONSE_FORMAT}"""

    after_b64 = _encode_image(after_path)

    response = None
    for attempt in range(2):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": after_b64}},
                            {"type": "text", "text": user_text},
                        ],
                    }
                ],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            return MindResult(
                first_reaction=data.get("first_reaction", ""),
                emotional_state=data.get("emotional_state", ""),
                expected=data.get("expected", ""),
                actual=data.get("actual", ""),
                gap=data.get("gap", ""),
                unspoken_frustration=data.get("unspoken_frustration", ""),
                unspoken_delight=data.get("unspoken_delight", ""),
                continue_or_abandon=data.get("continue_or_abandon", "hesitate"),
                abandon_risk_score=int(data.get("abandon_risk_score", 50)),
                heuristic_violated=data.get("heuristic_violated", ""),
                design_verdict=data.get("design_verdict", "MEDIUM"),
                refinement_suggestion=data.get("refinement_suggestion", ""),
                raw_response=raw,
                model=MODEL,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
        except json.JSONDecodeError:
            raw_text = response.content[0].text if response is not None else ""
            result = MindResult.parse_error()
            result.raw_response = raw_text
            return result
        except _APIError as e:
            if attempt == 0:
                time.sleep(5)
                continue
            result = MindResult.parse_error()
            result.raw_response = str(e)
            return result

    return MindResult.parse_error()
