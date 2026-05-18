"""Cross-encoder rerank pass for RAG results.

Takes RRF-fused candidates and rescores via joint query+doc relevance scoring
using a local LLM. Wraps brain_rag.search_brain output to produce a refined
top-N list.

Disabled by default — adds ~2-5s per query with warm TB model. Toggle on
for quality-critical retrieval (deep questions, ambiguous queries).
"""
import json
import re
import urllib.request
from typing import List, Dict, Optional

OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_RERANK_MODEL = "third-brother:latest"
SCORE_PROMPT = """Rate how relevant this snippet is to answering the query. Reply with ONE digit 0-9 only.

Query: {query}

Snippet:
{snippet}

Score (0-9):"""


def _score_pair(query: str, snippet: str, model: str = DEFAULT_RERANK_MODEL,
                timeout: int = 30) -> Optional[float]:
    """Score one query-snippet pair via LLM. Returns 0.0-1.0 or None on error."""
    prompt = SCORE_PROMPT.format(query=query, snippet=snippet[:1500])
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
            text = data.get("response", "").strip()
            think_end = text.find("</think>")
            if think_end >= 0:
                text = text[think_end + 8:].strip()
            m = re.search(r"\d", text)
            if not m:
                return None
            return int(m.group()) / 9.0
    except Exception:
        return None


def rerank(query: str, results: List[Dict], top_n: int = 8,
           model: str = DEFAULT_RERANK_MODEL) -> List[Dict]:
    """Rerank RAG results via LLM cross-encoder scoring.

    Mutates each result with `rerank_score` (0-1, None if scoring failed) and
    sorts by it (falling back to original score for ties or failures).
    Returns top_n.
    """
    if not results:
        return []

    for r in results:
        r["rerank_score"] = _score_pair(query, r.get("content", ""), model=model)

    def sort_key(r):
        rs = r.get("rerank_score")
        return (rs if rs is not None else -1, r.get("score", 0))

    results.sort(key=sort_key, reverse=True)
    return results[:top_n]
