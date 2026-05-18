"""Haiku grounding verifier — post-pass quality gate for high-stakes turns.

Cheap (~$0.001/turn) post-generation check that asks Haiku: "Does this
answer make claims unsupported by the retrieved context?" Used in
/quality verified tier. Off by default; opt-in via TB_VERIFIER=haiku
or per-turn payload flag.

Returns a structured verdict, never blocks the response — callers append
a banner if unsupported claims are found, but the original answer still
ships. v15 training will weight verifier-gated pairs as gold.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from .sonnet_principal import compose_with_sonnet


# Phase 3 (2026-05-10): bumped per "comprehensive" direction. Verifier
# (Haiku 4.5 = 200K context) has plenty of room.
_MAX_ANSWER_CHARS = int(os.environ.get("TB_VERIFIER_MAX_ANSWER", "8000"))   # was 3000
_MAX_CHUNK_CHARS = int(os.environ.get("TB_VERIFIER_MAX_CHUNK", "2000"))    # was 600
_MAX_CHUNKS = int(os.environ.get("TB_VERIFIER_MAX_CHUNKS", "30"))          # was 8


def _format_chunks(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return "(no retrieved chunks)"
    lines = []
    for i, c in enumerate(chunks[:_MAX_CHUNKS], start=1):
        src = c.get("source") or "unknown"
        body = (c.get("content") or "")[:_MAX_CHUNK_CHARS]
        lines.append(f"[{i}] source={src}\n{body}")
    return "\n\n".join(lines)


def _extract_verdict(text: str) -> Dict[str, Any]:
    """Best-effort parse of the verifier's reply. Verdict defaults to 'ok'
    if the parse fails — the verifier is a quality signal, not a gate, so
    parser failures shouldn't punish the answer."""
    text = (text or "").strip()
    # Try a fenced or inline JSON block first
    m = re.search(r"\{[^{}]*\"verdict\"[^{}]*\}", text)
    if m:
        try:
            obj = json.loads(m.group(0))
            verdict = (obj.get("verdict") or "").strip().lower()
            if verdict in ("ok", "supported", "grounded"):
                verdict = "ok"
            elif verdict in ("unsupported", "ungrounded", "fail", "bad"):
                verdict = "unsupported"
            else:
                verdict = "ok"
            claims = obj.get("claims_unsupported") or obj.get("claims") or []
            if not isinstance(claims, list):
                claims = [str(claims)]
            return {
                "verdict": verdict,
                "claims_unsupported": [str(c)[:200] for c in claims[:5]],
                "raw": text[:500],
            }
        except Exception:
            pass
    # Fallback: look for a yes/no signal in plain prose
    low = text.lower()
    if any(s in low for s in ["unsupported", "not in brain", "fabricat",
                              "no evidence", "hallucinat"]):
        return {"verdict": "unsupported", "claims_unsupported": [],
                "raw": text[:500]}
    return {"verdict": "ok", "claims_unsupported": [], "raw": text[:500]}


def verify_grounding(answer: str, retrieved_chunks: List[Dict[str, Any]],
                     query: str = "",
                     timeout: int = 60) -> Dict[str, Any]:
    """Ask Haiku whether `answer` is supported by `retrieved_chunks`.

    Returns:
        {
          "verdict": "ok" | "unsupported",
          "claims_unsupported": [str, ...],
          "duration_ms": int,
          "ok": bool,           # False on subprocess error
          "raw": str,           # truncated raw verifier output
        }
    """
    t0 = time.time()
    answer = (answer or "").strip()[:_MAX_ANSWER_CHARS]
    if not answer:
        return {"verdict": "ok", "claims_unsupported": [],
                "duration_ms": 0, "ok": True, "raw": ""}

    chunks_text = _format_chunks(retrieved_chunks or [])
    # Phase 3.5 fix-3 (2026-05-10): inject today's date into verifier
    # prompt too. Without it, Haiku-as-verifier doesn't know the current
    # date and may incorrectly flag temporal claims by the principal
    # (e.g. principal correctly says 'today is Sunday 2026-05-10'; Haiku
    # internally guesses Saturday and flags the principal as wrong).
    today_str = datetime.now(timezone.utc).astimezone().strftime(
        "%Y-%m-%d (%A)"
    )
    prompt = (
        "You are a grounding verifier. Decide whether the ANSWER below is "
        "supported by the retrieved CHUNKS. An answer is 'supported' if "
        "every concrete factual claim (names, dates, numbers, biographical "
        "details, quoted preferences) appears in or follows directly from "
        "the chunks. Generic advice or general-knowledge phrasing does not "
        "need to be in the chunks — only concrete, specific claims do.\n"
        "\n"
        f"TODAY = {today_str}. Use this when reasoning about temporal "
        "claims; chunks carry [|when] tags showing when their content was "
        "originally written/sent.\n"
        "\n"
        "Respond with a single JSON object on one line:\n"
        '{"verdict": "ok" or "unsupported", '
        '"claims_unsupported": ["<short claim>", ...]}\n'
        "\n"
        f"QUERY: {query[:300]}\n"
        "\n"
        "ANSWER:\n"
        f"{answer}\n"
        "\n"
        "RETRIEVED CHUNKS:\n"
        f"{chunks_text}\n"
        "\n"
        "JSON:"
    )

    text, dur_ms, meta = compose_with_sonnet(
        prompt=prompt,
        query_summary="grounding-verifier",
        tb_advice="",
        timeout=timeout,
        model="haiku",
    )
    if text.startswith("[SONNET_PRINCIPAL_ERROR]"):
        return {"verdict": "ok", "claims_unsupported": [],
                "duration_ms": dur_ms, "ok": False, "raw": text[:500]}
    parsed = _extract_verdict(text)
    return {
        "verdict": parsed["verdict"],
        "claims_unsupported": parsed["claims_unsupported"],
        "duration_ms": dur_ms,
        "ok": True,
        "raw": parsed["raw"],
    }


def banner_for_verdict(verdict: Dict[str, Any]) -> str:
    """Render a one-line banner appended to the answer when the verifier
    flagged unsupported claims. Returns empty string if verdict is ok."""
    if verdict.get("verdict") != "unsupported":
        return ""
    claims = verdict.get("claims_unsupported") or []
    if claims:
        joined = "; ".join(claims[:3])
        return f"\n\n— [VERIFIER: unsupported claims — {joined}]"
    return "\n\n— [VERIFIER: some claims may not be grounded in retrieved context]"
