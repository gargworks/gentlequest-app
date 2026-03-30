"""
Tests for Frontier 3: COMPOUND — Quality Scoring & Verification Metadata
=========================================================================
Tests compute_quality_score in export_raft_training.py and the
verification metadata helpers in third_brother_driver.py.

No external dependencies — pure unit tests on scoring logic.
"""

import sys
import pytest
from pathlib import Path

# Add scripts/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from export_raft_training import compute_quality_score
from third_brother_driver import (
    _verification_flag,
    _verification_tier,
    _verification_quality,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(**overrides):
    """Build a minimal shadow-log entry for quality scoring."""
    entry = {
        "query": "x" * 30,           # > 20 chars → +0.2
        "response": "y" * 200,       # > 100 chars → +0.2
        "oracle_chunks": [{"content": "c", "source": "s"}],  # +0.2
        "outcome": "completed",       # +0.2
    }
    entry.update(overrides)
    return entry


def _make_response(verified=None, tier_reached=None):
    """Build a response dict with optional verification data."""
    resp = {"result": "I did the work"}
    if verified is not None:
        resp["verification"] = {
            "verified": verified,
            "tier_reached": tier_reached if tier_reached is not None else (2 if verified else 1),
            "tiers_passed": [0, 1] if verified else [0],
            "tiers_failed": [] if verified else [1],
            "signals": [],
        }
    return resp


# ===========================================================================
# compute_quality_score — verification signals
# ===========================================================================

class TestQualityScoring:
    def test_quality_boost_verified(self):
        """execution_verified=True → score increases by 0.2."""
        base = _make_entry()
        boosted = _make_entry(metadata={"execution_verified": True})
        base_score = compute_quality_score(base)
        boosted_score = compute_quality_score(boosted)
        assert boosted_score == round(min(base_score + 0.2, 1.0), 2)

    def test_quality_penalty_failed(self):
        """execution_verified=False → score decreases by 0.3."""
        base = _make_entry()
        penalized = _make_entry(metadata={"execution_verified": False})
        base_score = compute_quality_score(base)
        penalized_score = compute_quality_score(penalized)
        expected = round(max(base_score - 0.3, 0.0), 2)
        assert penalized_score == expected

    def test_platinum_overrides_all(self):
        """source='human_review' → score=1.0 regardless."""
        entry = _make_entry(
            query="short",  # too short → no +0.2
            response="x",   # too short → no +0.2
            metadata={"source": "human_review"},
        )
        assert compute_quality_score(entry) == 1.0

    def test_platinum_quality_overrides(self):
        """quality='platinum' → score=1.0 regardless."""
        entry = _make_entry(
            query="short",
            response="x",
            metadata={"quality": "platinum"},
        )
        assert compute_quality_score(entry) == 1.0

    def test_no_verification_unchanged(self):
        """No verification metadata → same score as baseline."""
        entry = _make_entry()
        # No metadata key at all → score based only on heuristics
        score = compute_quality_score(entry)
        # Base: query(0.2) + response(0.2) + oracle(0.2) + completed(0.2) + no error(0.2) = 1.0
        assert score == 1.0


# ===========================================================================
# _verification_quality helper
# ===========================================================================

class TestVerificationQualityHelper:
    def test_verification_quality_gold(self):
        """Verified pass + silver base → promoted to gold."""
        resp = _make_response(verified=True)
        assert _verification_quality(resp, "silver") == "gold"

    def test_verification_quality_copper(self):
        """Verified fail + gold base → demoted to copper."""
        resp = _make_response(verified=False)
        assert _verification_quality(resp, "gold") == "copper"

    def test_verification_quality_none(self):
        """No verification data → base quality unchanged."""
        resp = _make_response()  # no verification
        assert _verification_quality(resp, "silver") == "silver"

    def test_verification_quality_gold_stays_gold(self):
        """Verified pass + gold base → stays gold."""
        resp = _make_response(verified=True)
        assert _verification_quality(resp, "gold") == "gold"


# ===========================================================================
# _verification_flag and _verification_tier helpers
# ===========================================================================

class TestVerificationExtractors:
    def test_verification_flag_true(self):
        """Response with verified=True → returns True."""
        resp = _make_response(verified=True)
        assert _verification_flag(resp) is True

    def test_verification_flag_false(self):
        """Response with verified=False → returns False."""
        resp = _make_response(verified=False)
        assert _verification_flag(resp) is False

    def test_verification_flag_none(self):
        """Response without verification → returns None."""
        resp = _make_response()
        assert _verification_flag(resp) is None

    def test_verification_tier_extracts(self):
        """Response with tier_reached=2 → returns 2."""
        resp = _make_response(verified=True, tier_reached=2)
        assert _verification_tier(resp) == 2

    def test_verification_tier_none(self):
        """Response without verification → returns None."""
        resp = _make_response()
        assert _verification_tier(resp) is None
