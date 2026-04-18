"""
Rule-based quest matcher: picks 3 daily quests based on recent mood + keyword signals.

Pure functions (no Flask/DB) — caller passes pre-queried data, we return quest
IDs or type preferences. Writes live in `routes/quests.py`.
"""

from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Quest type priority when multiple signals match
QUEST_TYPE_PRIORITY: List[str] = [
    "breathing",      # anxiety, panic
    "grounding",      # dissociation, high variability
    "gratitude",      # low mood
    "journaling",     # emotional processing
    "movement",       # activation
    "social",         # isolation
    "sleep",          # insomnia
    "check_in",       # default baseline
]

# Mood → quest-type mapping
_MOOD_TO_TYPES: Dict[str, List[str]] = {
    "low": ["gratitude", "social", "movement"],
    "moderate": ["journaling", "check_in", "movement"],
    "high": ["check_in", "gratitude"],
    "anxious": ["breathing", "grounding"],
    "unstable": ["grounding", "breathing", "journaling"],
}


def classify_mood_state(
    mood_entries: List[Any],
    window_days: int = 7,
) -> str:
    """Classify the session's current mood state.

    Returns one of: "low", "moderate", "high", "unstable".
    "anxious" is returned by classify_from_keywords instead.
    """
    if not mood_entries:
        return "moderate"

    now = datetime.utcnow()
    cutoff = now - timedelta(days=window_days)
    window = [
        e for e in mood_entries
        if getattr(e, "timestamp", None) and e.timestamp >= cutoff
    ]

    if not window:
        return "moderate"

    levels = [e.mood_level for e in window]
    mean = sum(levels) / len(levels)

    # High variability trumps mean
    if len(levels) >= 3:
        spread = max(levels) - min(levels)
        if spread >= 3:
            return "unstable"

    if mean <= 2.0:
        return "low"
    if mean >= 4.0:
        return "high"
    return "moderate"


def classify_from_keywords(messages: List[Any]) -> Optional[str]:
    """Return a mood state override if recent messages show strong signals."""
    from helpers.insights_helpers import bucket_keyword

    if not messages:
        return None

    counts: Counter = Counter()
    for m in messages[-30:]:  # Only last 30 user messages
        if not getattr(m, "is_user", False):
            continue
        bucket = bucket_keyword(getattr(m, "content", "") or "")
        if bucket:
            counts[bucket] += 1

    if counts.get("anxiety", 0) >= 2:
        return "anxious"
    if counts.get("isolation", 0) >= 2:
        return "low"
    if counts.get("hopelessness", 0) >= 2:
        return "low"
    return None


def pick_quest_types(
    mood_entries: List[Any],
    messages: List[Any],
    n: int = 3,
) -> List[str]:
    """Return a prioritized list of `n` quest types for this session."""
    override = classify_from_keywords(messages)
    state = override or classify_mood_state(mood_entries)
    preferred = list(_MOOD_TO_TYPES.get(state, ["check_in"]))

    # Pad with defaults from the priority list
    for t in QUEST_TYPE_PRIORITY:
        if t not in preferred:
            preferred.append(t)

    return preferred[:n]


def select_daily_quests(
    quests: List[Any],
    quest_types: List[str],
    completed_today_ids: Optional[List[int]] = None,
    n: int = 3,
) -> List[Any]:
    """Pick up to `n` quests matching the preferred type list.

    Algorithm:
    1. Prefer one quest per type in order.
    2. Skip any quest already completed today.
    3. If fewer than `n` matched, fill with any remaining quest (by id order).
    """
    completed_set = set(completed_today_ids or [])
    available = [q for q in quests if q.id not in completed_set]
    by_type: Dict[str, List[Any]] = {}
    for q in available:
        by_type.setdefault(getattr(q, "quest_type", "check_in"), []).append(q)

    picked: List[Any] = []
    used_ids: set = set()
    for t in quest_types:
        bucket = by_type.get(t, [])
        if bucket and bucket[0].id not in used_ids:
            picked.append(bucket[0])
            used_ids.add(bucket[0].id)
            if len(picked) >= n:
                return picked

    # Fill remainder
    for q in available:
        if q.id not in used_ids:
            picked.append(q)
            used_ids.add(q.id)
            if len(picked) >= n:
                break
    return picked[:n]


def compute_streak(completion_dates: List[datetime]) -> Dict[str, int]:
    """Compute current + longest streak from a list of completion timestamps.

    A streak day counts if there's ≥1 completion on that calendar date.
    Consecutive calendar days (UTC) extend the streak.
    """
    if not completion_dates:
        return {"current": 0, "longest": 0}

    dates = sorted({d.date() for d in completion_dates if d})
    if not dates:
        return {"current": 0, "longest": 0}

    # Compute longest run of consecutive days
    longest = 1
    run = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    # Current streak: from most recent date backward, requires today or yesterday as anchor
    today = datetime.utcnow().date()
    last = dates[-1]
    if (today - last).days > 1:
        current = 0
    else:
        current = 1
        for i in range(len(dates) - 1, 0, -1):
            if (dates[i] - dates[i - 1]).days == 1:
                current += 1
            else:
                break

    return {"current": current, "longest": longest}


# Achievement rules (simple, idempotent — caller is responsible for de-dup via stored badges)
ACHIEVEMENTS: Dict[str, Dict[str, Any]] = {
    "first_quest": {
        "title": "Getting Started",
        "description": "Complete your first quest",
        "condition": lambda stats: stats.get("total_completed", 0) >= 1,
    },
    "seven_day_streak": {
        "title": "Consistency",
        "description": "7-day streak",
        "condition": lambda stats: stats.get("current_streak", 0) >= 7,
    },
    "thirty_day_streak": {
        "title": "Committed",
        "description": "30-day streak",
        "condition": lambda stats: stats.get("current_streak", 0) >= 30,
    },
    "ten_quests": {
        "title": "Dedicated",
        "description": "10 quests completed",
        "condition": lambda stats: stats.get("total_completed", 0) >= 10,
    },
    "mood_lifter": {
        "title": "Mood Lifter",
        "description": "A quest gave you a +2 mood boost",
        "condition": lambda stats: stats.get("max_mood_delta", 0) >= 2,
    },
}


def check_achievements(
    stats: Dict[str, Any],
    already_earned: Optional[List[str]] = None,
) -> List[str]:
    """Return list of NEW achievement keys earned (not already in `already_earned`)."""
    earned = set(already_earned or [])
    new: List[str] = []
    for key, spec in ACHIEVEMENTS.items():
        if key in earned:
            continue
        try:
            if spec["condition"](stats):
                new.append(key)
        except Exception:
            continue
    return new


__all__ = [
    "ACHIEVEMENTS",
    "QUEST_TYPE_PRIORITY",
    "check_achievements",
    "classify_from_keywords",
    "classify_mood_state",
    "compute_streak",
    "pick_quest_types",
    "select_daily_quests",
]
