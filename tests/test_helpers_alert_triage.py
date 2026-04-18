"""Unit tests for helpers/alert_triage.py (pure state machine)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from helpers.alert_triage import (
    ALERT_STATES,
    is_terminal,
    is_valid_transition,
    next_states,
)


class TestAlertStates:
    def test_exactly_four_states(self):
        assert ALERT_STATES == {"new", "acknowledged", "resolved", "escalated"}


class TestValidTransitions:
    @pytest.mark.parametrize("src,target", [
        ("new", "acknowledged"),
        ("new", "resolved"),
        ("new", "escalated"),
        ("acknowledged", "resolved"),
        ("acknowledged", "escalated"),
        ("escalated", "resolved"),
    ])
    def test_legal_transitions(self, src, target):
        assert is_valid_transition(src, target) is True

    @pytest.mark.parametrize("src,target", [
        ("resolved", "new"),
        ("resolved", "acknowledged"),
        ("resolved", "escalated"),
        ("acknowledged", "new"),
        ("new", "new"),
        ("escalated", "acknowledged"),
        ("escalated", "new"),
    ])
    def test_illegal_transitions(self, src, target):
        assert is_valid_transition(src, target) is False

    def test_unknown_target(self):
        assert is_valid_transition("new", "banana") is False

    def test_unknown_source(self):
        assert is_valid_transition("banana", "acknowledged") is False


class TestNextStates:
    def test_new_has_three_options(self):
        assert next_states("new") == {"acknowledged", "resolved", "escalated"}

    def test_resolved_terminal(self):
        assert next_states("resolved") == set()

    def test_escalated_can_resolve(self):
        assert next_states("escalated") == {"resolved"}

    def test_unknown_returns_empty(self):
        assert next_states("banana") == set()


class TestIsTerminal:
    def test_resolved_is_terminal(self):
        assert is_terminal("resolved") is True

    def test_new_is_not_terminal(self):
        assert is_terminal("new") is False

    def test_acknowledged_is_not_terminal(self):
        assert is_terminal("acknowledged") is False

    def test_escalated_is_not_terminal(self):
        assert is_terminal("escalated") is False

    def test_unknown_is_terminal(self):
        # Unknown states have no outgoing transitions; treat as terminal
        assert is_terminal("banana") is True
