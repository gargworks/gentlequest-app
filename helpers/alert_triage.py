"""
Counselor alert triage state machine.

States:
- new           — alert just created, no counselor action yet
- acknowledged  — counselor saw it, working on it
- resolved      — outcome logged, no further action needed
- escalated    — handed up the chain (e.g. to psychiatrist, emergency services)

Legal transitions:
    new          -> acknowledged, resolved, escalated
    acknowledged -> resolved, escalated
    resolved     -> (terminal)
    escalated    -> resolved

Any other transition is rejected.
"""

from typing import Dict, Set

ALERT_STATES: Set[str] = {"new", "acknowledged", "resolved", "escalated"}

# triage_state -> set of allowed next states
_TRANSITIONS: Dict[str, Set[str]] = {
    "new":          {"acknowledged", "resolved", "escalated"},
    "acknowledged": {"resolved", "escalated"},
    "resolved":     set(),
    "escalated":    {"resolved"},
}


def is_valid_transition(current: str, target: str) -> bool:
    """True if `current → target` is a legal state transition."""
    if target not in ALERT_STATES:
        return False
    if current not in _TRANSITIONS:
        return False
    return target in _TRANSITIONS[current]


def next_states(current: str) -> Set[str]:
    """Return the set of valid next states from `current`."""
    return set(_TRANSITIONS.get(current, set()))


def is_terminal(state: str) -> bool:
    """True if `state` has no outgoing transitions."""
    return not _TRANSITIONS.get(state, set())


__all__ = ["ALERT_STATES", "is_terminal", "is_valid_transition", "next_states"]
