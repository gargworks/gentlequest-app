"""Auto-correction detector — turns inline chat corrections into DPO pairs.

Two-stage gate to avoid noisy false positives:
  1. Cheap regex heuristic — flags candidate "user is correcting TB" turns
  2. LLM judge — only fires on flagged turns, returns yes/no/partial

When confirmed, the caller writes a record_correction() with TB's last
output as `context` and the user's new message as `correction`. The
DPO pair lands in the same archive that explicit /align bad uses.
"""
import json
import re
import urllib.request
from typing import Optional

OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_JUDGE_MODEL = "third-brother:latest"

_CORRECTION_REGEX = re.compile(
    r"^\s*(no[,.\s]|wrong|actually|that(?:'?s| is)\s+(?:not|incorrect|wrong)|"
    r"not\s+(?:quite|really|exactly|right)|let me correct|correction[:,]|"
    r"you('?re| are)\s+wrong|incorrect[,.\s]|fix:|"
    r"you (got|have) (it|that) wrong)",
    re.IGNORECASE
)

_JUDGE_PROMPT = """Did the user's new message correct or push back on TB's previous response?

TB's previous response:
{tb_last}

User's new message:
{user_new}

Answer with ONE word: yes, no, or partial."""


def heuristic_is_correction(user_turn: str) -> bool:
    """Cheap regex pass. Returns True if turn looks like it might be a correction."""
    if not user_turn:
        return False
    return bool(_CORRECTION_REGEX.search(user_turn[:200]))


def llm_confirm_correction(user_new: str, tb_last: str,
                           model: str = DEFAULT_JUDGE_MODEL,
                           timeout: int = 30) -> Optional[str]:
    """Call LLM judge. Returns 'yes' | 'no' | 'partial' | None on error."""
    prompt = _JUDGE_PROMPT.format(
        tb_last=(tb_last or "")[:400],
        user_new=(user_new or "")[:400],
    )
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 8, "temperature": 0.0},
    }).encode()
    req = urllib.request.Request(
        OLLAMA_API_URL, data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            raw = (data.get("response") or "").strip().lower()
            think_end = raw.find("</think>")
            after = raw[think_end + 8:].strip() if think_end >= 0 else raw
            for source in (after, raw):
                for token in ("partial", "yes", "no"):
                    if token in source[:200]:
                        return token
            return None
    except Exception:
        return None


def detect_correction(user_new: str, tb_last: str,
                      model: str = DEFAULT_JUDGE_MODEL,
                      use_llm: bool = False) -> Optional[str]:
    """Two-stage detect. Returns 'yes' | 'partial' | 'heuristic' | None.

    Heuristic gate first (cheap). LLM judge optionally confirms — but v14
    judge is unreliable, so default is heuristic-only (use_llm=False). Bias
    toward capture: false positives filter at training time; missed
    corrections lose signal forever.

    Returns:
      - 'yes' / 'partial' — LLM-confirmed (use_llm=True path)
      - 'heuristic'       — regex fired, no LLM confirmation requested
      - None              — heuristic missed, or LLM judge said 'no'
    """
    if not heuristic_is_correction(user_new):
        return None
    if not use_llm:
        return "heuristic"
    verdict = llm_confirm_correction(user_new, tb_last, model=model)
    return verdict if verdict in ("yes", "partial") else None
