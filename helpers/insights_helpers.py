"""
Pure analytics helpers for /api/insights/* endpoints.

All functions are pure (no Flask context) except where they explicitly need
DB session access. They return plain dicts/lists ready for jsonify.
"""

import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

# Crisis keyword taxonomy for heatmap bucketing (must match crisis_helpers tiers).
CRISIS_KEYWORD_BUCKETS: Dict[str, List[str]] = {
    "hopelessness": ["hopeless", "worthless", "no point", "pointless", "nothing matters"],
    "self_harm": ["hurt myself", "cut myself", "self-harm"],
    "suicidal_ideation": ["kill myself", "end it", "suicide", "ending my life"],
    "isolation": ["alone", "no one", "nobody cares", "isolated"],
    "anxiety": ["panic", "anxious", "can't breathe", "overwhelmed"],
}


# -------------------------------------------------------------------------
# Weekly trend
# -------------------------------------------------------------------------

def compute_weekly_trend(
    mood_entries: List[Any],
    window_days: int = 7,
) -> Dict[str, Any]:
    """Compute mean, stdev, min, max, and daily buckets for the window.

    Args:
        mood_entries: iterable of objects with `.mood_level: int` and `.timestamp: datetime`
        window_days: 7, 30, or 90

    Returns:
        {
            "window_days": int,
            "count": int,
            "mean": float|None,
            "stdev": float|None,
            "min": int|None,
            "max": int|None,
            "daily": [{"date": "YYYY-MM-DD", "avg": float, "count": int}, ...]
        }
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now - timedelta(days=window_days)
    window = [e for e in mood_entries if e.timestamp and e.timestamp >= cutoff]

    if not window:
        return {
            "window_days": window_days,
            "count": 0,
            "mean": None,
            "stdev": None,
            "min": None,
            "max": None,
            "daily": [],
        }

    levels = [e.mood_level for e in window]
    mean = round(statistics.mean(levels), 2)
    stdev = round(statistics.pstdev(levels), 2) if len(levels) > 1 else 0.0

    # Daily buckets
    by_day: Dict[str, List[int]] = defaultdict(list)
    for e in window:
        key = e.timestamp.date().isoformat()
        by_day[key].append(e.mood_level)

    daily = [
        {
            "date": k,
            "avg": round(statistics.mean(v), 2),
            "count": len(v),
        }
        for k, v in sorted(by_day.items())
    ]

    return {
        "window_days": window_days,
        "count": len(window),
        "mean": mean,
        "stdev": stdev,
        "min": min(levels),
        "max": max(levels),
        "daily": daily,
    }


# -------------------------------------------------------------------------
# Crisis keyword heatmap
# -------------------------------------------------------------------------

def bucket_keyword(text: str) -> Optional[str]:
    """Return the first matching bucket name, or None."""
    if not text:
        return None
    t = text.lower()
    for bucket, keywords in CRISIS_KEYWORD_BUCKETS.items():
        for kw in keywords:
            if kw in t:
                return bucket
    return None


def compute_keyword_heatmap(
    messages: List[Any],
    window_days: int = 30,
) -> Dict[str, Any]:
    """Aggregate crisis-keyword frequency per day (calendar heatmap data).

    Privacy: only bucket names + dates + counts are returned — never raw text.

    Args:
        messages: iterable with `.content: str`, `.timestamp: datetime`, `.is_user: bool`

    Returns:
        {
            "window_days": int,
            "buckets": ["hopelessness", ...],
            "heatmap": [{"date": "...", "bucket": "...", "count": int}, ...],
            "totals_per_bucket": {"hopelessness": 3, ...}
        }
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now - timedelta(days=window_days)
    by_day_bucket: Counter = Counter()
    totals: Counter = Counter()

    for m in messages:
        if not getattr(m, "is_user", False):
            continue
        ts = getattr(m, "timestamp", None)
        if not ts or ts < cutoff:
            continue
        bucket = bucket_keyword(m.content or "")
        if not bucket:
            continue
        day = ts.date().isoformat()
        by_day_bucket[(day, bucket)] += 1
        totals[bucket] += 1

    heatmap = [
        {"date": day, "bucket": bucket, "count": count}
        for (day, bucket), count in sorted(by_day_bucket.items())
    ]

    return {
        "window_days": window_days,
        "buckets": list(CRISIS_KEYWORD_BUCKETS.keys()),
        "heatmap": heatmap,
        "totals_per_bucket": dict(totals),
    }


# -------------------------------------------------------------------------
# Quest mood correlation
# -------------------------------------------------------------------------

def compute_quest_correlation(
    intervention_outcomes: List[Any],
) -> Dict[str, Any]:
    """For each intervention type, compute avg mood delta (after - before).

    Args:
        intervention_outcomes: iterable with
            `.exercise_type: Optional[str]`,
            `.mood_before: Optional[int]`,
            `.mood_after: Optional[int]`

    Returns:
        {
            "overall_delta": float|None,
            "per_type": [{"type": "breathing", "n": 3, "avg_delta": 0.8}, ...]
        }
    """
    by_type: Dict[str, List[int]] = defaultdict(list)
    all_deltas: List[int] = []

    for o in intervention_outcomes:
        before = getattr(o, "mood_before", None)
        after = getattr(o, "mood_after", None)
        if before is None or after is None:
            continue
        delta = after - before
        etype = getattr(o, "exercise_type", None) or "unknown"
        by_type[etype].append(delta)
        all_deltas.append(delta)

    per_type = sorted(
        [
            {
                "type": t,
                "n": len(ds),
                "avg_delta": round(statistics.mean(ds), 2) if ds else 0.0,
            }
            for t, ds in by_type.items()
        ],
        key=lambda d: d["avg_delta"],
        reverse=True,
    )

    return {
        "overall_delta": round(statistics.mean(all_deltas), 2) if all_deltas else None,
        "n": len(all_deltas),
        "per_type": per_type,
    }


# -------------------------------------------------------------------------
# Personalized next-step CTAs
# -------------------------------------------------------------------------

def compute_next_steps(
    weekly_trend: Dict[str, Any],
    keyword_heatmap: Dict[str, Any],
    quest_correlation: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Return 3 prioritized CTAs based on patterns.

    Rules (in priority order):
    1. If any suicidal_ideation/self_harm keywords in window → crisis resource CTA
    2. If weekly mean < 2.5 → reach-out CTA + best quest-type (by avg_delta) CTA
    3. If stdev > 1.5 → grounding CTA
    4. Fallback → maintain positive habits
    """
    ctas: List[Dict[str, str]] = []

    totals = keyword_heatmap.get("totals_per_bucket", {})
    if totals.get("suicidal_ideation") or totals.get("self_harm"):
        ctas.append({
            "type": "crisis_resource",
            "title": "Urgent support available 24/7",
            "description": "We noticed some concerning themes. Please reach out — you're not alone.",
            "action": "/api/crisis/resources",
        })

    mean = weekly_trend.get("mean")
    if mean is not None and mean < 2.5:
        ctas.append({
            "type": "reach_out",
            "title": "Consider talking to someone you trust",
            "description": "Your mood has been low this week. Connection helps.",
            "action": "/resources/support-lines",
        })
        # Recommend best-performing quest type
        per_type = quest_correlation.get("per_type", [])
        if per_type and per_type[0]["avg_delta"] > 0:
            best = per_type[0]
            ctas.append({
                "type": "quest_recommendation",
                "title": f"Try a {best['type']} exercise",
                "description": (
                    f"Others have seen a +{best['avg_delta']} mood lift from this "
                    f"(n={best['n']})."
                ),
                "action": f"/api/quests/today?type={best['type']}",
            })

    stdev = weekly_trend.get("stdev") or 0
    if stdev > 1.5 and len(ctas) < 3:
        ctas.append({
            "type": "grounding",
            "title": "Try a quick grounding exercise",
            "description": "Your mood has swung a lot this week — 2 minutes of grounding can steady it.",
            "action": "/api/quests/today?type=grounding",
        })

    # Fallback: positive reinforcement
    if not ctas:
        ctas.append({
            "type": "maintain",
            "title": "Keep up your positive habits",
            "description": "You're doing well — consistency compounds.",
            "action": "/api/quests/today",
        })

    return ctas[:3]


# -------------------------------------------------------------------------
# Correlation helpers (exposed for convenience)
# -------------------------------------------------------------------------

def pearson_correlation(xs: List[float], ys: List[float]) -> Optional[float]:
    """Simple Pearson r. Returns None for insufficient or degenerate data."""
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    try:
        return round(statistics.correlation(xs, ys), 3)
    except (AttributeError, statistics.StatisticsError):
        # Python <3.10 fallback
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        den_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
        den_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5
        if den_x == 0 or den_y == 0:
            return None
        return round(num / (den_x * den_y), 3)


__all__ = [
    "CRISIS_KEYWORD_BUCKETS",
    "bucket_keyword",
    "compute_keyword_heatmap",
    "compute_next_steps",
    "compute_quest_correlation",
    "compute_weekly_trend",
    "pearson_correlation",
]
