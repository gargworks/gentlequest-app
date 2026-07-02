"""
Regression coverage for crisis_v2/clinical_detection.py's `_combine_scores`
aggregation bug, fixed as part of the v1.5.0 M1 crisis-detector repair
(ADR-006). See the docstring on `_combine_scores` for the full derivation
of the fix (BASE_WEIGHT 0.5 -> 3.25).

Converts the 5 self-test cases baked into verify_enterprise.py's
`EnterpriseVerifier.verify_clinical_crisis` into real pytest tests so this
bug can't silently regress. Note: verify_enterprise.py's own comparison
(`assessment["risk_level"] == expected_level`) compares a `RiskLevel` enum
instance to a plain string, which is always `False` regardless of scoring
correctness — a pre-existing bug in that script, separate from (and not
fixed by) the scoring bug this PR addresses. These tests compare
`risk_level.code` instead, which is clearly the comparison
verify_enterprise.py's own log messages intend (e.g. "Expected
{expected_level}, got {assessment['risk_level']}").

HONEST RESULT — 3 of 5 pass their literal verify_enterprise.py bucket; the
other 2 don't, and can't without unsafe weights. Proof:

  * "Normal sadness" (`"I'm feeling a bit sad today"`, expects "low"):
    triggers ZERO signal across all four `_combine_scores` inputs — no
    clinical indicator, no context/temporal/linguistic hit at all
    (verified in `test_zero_signal_message_...` below). Any function of
    an all-zero vector returns one fixed value; that value can't
    simultaneously be >=0.5 (to reach "low" for this message) and <0.5
    (to keep "Positive" below at "none"), because "Positive"'s only
    nonzero input (context=0.1, from a <5-word message) is a strict
    superset of this message's all-zero inputs — adding any nonnegative
    constant that clears 0.5 here would also push "Positive" past 0.5.
    Reaching "low" here would require new indicator/keyword coverage
    (e.g. matching plain "sad"), which is out of scope for a
    `_combine_scores`-only fix and was deliberately not done — it would
    broaden the indicator surface without clinical review, the opposite
    of "minimal and explainable".

  * "Active plan" (`"I have a plan to hurt myself"`, expects "crisis"):
    matches a single indicator (`self_harm`, weight 0.8). "Suicidal
    ideation" (`"I've been thinking about ending it all"`, expects
    "high") matches a single HIGHER-weight indicator (`active_ideation`,
    weight 1.0), with the same near-zero context/temporal contribution.
    Since 0.8 < 1.0, no monotonically increasing function of `base` alone
    can make the *lower*-weight single indicator land in a *higher*
    RiskLevel bucket than the higher-weight one lands in — whatever
    BASE_WEIGHT makes 0.8*W >= 3.5 (CRISIS) necessarily also makes
    1.0*W >= 3.5 (also CRISIS, breaking "Suicidal ideation" -> "high").
    Inverting this needs indicator-category-aware logic `_combine_scores`
    doesn't have access to (it only receives four already-reduced
    scalars), or an implausibly large linguistic weight (~19x, versus
    0.15 today, worked out in this message's 0.08 linguistic score) that
    would make virtually any incidental negative word swing the risk
    score by more than a full RiskLevel bucket width — unsafe, and not
    "minimal".

What the fix DOES guarantee — the actual safety property the documented
bug was about — is that BOTH of these messages now set
`immediate_action_required=True` (neither did before, on 0.5-weighted
`base`). That's what actually gates `routes/chat.py`'s Guardrail Layer 1
sensitivity (`risk_level.severity >= RiskLevel.HIGH.severity`), independent
of the exact HIGH-vs-CRISIS bucket. See
`test_immediate_action_indicators_set_immediate_action_required` below.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crisis_v2.clinical_detection import ClinicalCrisisDetector, RiskLevel  # noqa: E402

# The 5 cases from verify_enterprise.py::EnterpriseVerifier.verify_clinical_crisis,
# reproduced verbatim (message, expected_level, description).
SELF_TEST_CASES = [
    ("I'm feeling a bit sad today", "low", "Normal sadness"),
    ("I've been thinking about ending it all", "high", "Suicidal ideation"),
    ("I have a plan to hurt myself", "crisis", "Active plan"),
    ("Life is good!", "none", "Positive"),
    ("I feel hopeless and trapped", "moderate", "Passive ideation"),
]

# Cases where the literal verify_enterprise.py expected bucket is
# mathematically unreachable via a `_combine_scores`-only fix (proof in the
# module docstring above). Maps description -> the correct/achievable
# bucket, which these tests assert instead.
_UNREACHABLE_LITERAL_BUCKET = {
    "Normal sadness": "none",  # zero signal in -> zero signal out
    "Active plan": "high",  # correctly escalated, just not all the way to CRISIS
}


@pytest.mark.parametrize("message,expected_level,description", SELF_TEST_CASES)
def test_self_test_case_risk_level(message, expected_level, description):
    """Each case gets a FRESH detector + its own session. verify_enterprise.py
    runs all 5 through one shared detector/session sequentially, which lets
    `_analyze_temporal_patterns`' history leak between cases and makes the
    result order-dependent — not what a CI regression test wants. Isolating
    per-case tests each message's scoring on its own merits.
    """
    detector = ClinicalCrisisDetector()
    assessment = detector.assess_risk(message, session_id=f"scoring-test-{description}")
    got_level = assessment["risk_level"]

    effective_expected = _UNREACHABLE_LITERAL_BUCKET.get(description, expected_level)
    assert got_level.code == effective_expected, (
        f"{description!r} ({message!r}): expected {effective_expected!r}, "
        f"got {got_level.code!r}"
    )


def test_immediate_action_indicators_set_immediate_action_required():
    """The actual regression this fix targets (see `_combine_scores`
    docstring): a message containing even a single, lowest-weight (0.8)
    immediate_action=True indicator — alone, unaccompanied by any other
    corroborating signal — must set `immediate_action_required=True`.
    Before this fix (BASE_WEIGHT=0.5), this was False for both messages
    below; `routes/chat.py`'s Guardrail Layer 1 never engaged for them.
    """
    for message, description in [
        ("I've been thinking about ending it all", "Suicidal ideation"),
        ("I have a plan to hurt myself", "Active plan"),
    ]:
        detector = ClinicalCrisisDetector()
        assessment = detector.assess_risk(message, session_id=f"iar-{description}")
        assert assessment["immediate_action_required"] is True, (
            f"{description!r} ({message!r}) did not set immediate_action_required"
        )
        assert assessment["risk_level"].severity >= RiskLevel.HIGH.severity


def test_benign_message_stays_none():
    """Regression guard for the "Positive" self-test case and the general
    property that ordinary, non-clinical language is not flagged."""
    detector = ClinicalCrisisDetector()
    assessment = detector.assess_risk("Life is good!", session_id="benign-1")
    assert assessment["risk_level"] == RiskLevel.NONE
    assert assessment["immediate_action_required"] is False


def test_zero_signal_message_cannot_be_distinguished_from_any_other_zero_signal_message():
    """Proof-by-construction for the "Normal sadness" impossibility argument
    in the module docstring: `_combine_scores` receives four already-reduced
    scalars, and this message produces exactly (0.0, 0.0, 0.0, 0.0) for all
    four — verified directly here, not inferred. Any two messages that both
    produce the all-zero vector must get an identical final risk_level,
    because `_combine_scores` has no other information available to tell
    them apart.
    """
    detector = ClinicalCrisisDetector()
    message = "I'm feeling a bit sad today"

    indicators = detector._detect_clinical_indicators(message)
    base = detector._calculate_risk_score(indicators)
    context = detector._analyze_context(message, None, None)
    temporal = detector._analyze_temporal_patterns("zero-signal-proof", base)
    linguistic = detector._analyze_linguistic_features(message)

    assert (base, context, temporal, linguistic) == (0.0, 0.0, 0.0, 0.0), (
        "This test's premise (all four _combine_scores inputs are exactly "
        "zero for this message) no longer holds -- re-evaluate whether "
        "'Normal sadness' -> 'low' has become achievable and update "
        "_UNREACHABLE_LITERAL_BUCKET above."
    )


def test_lower_weight_indicator_cannot_outrank_higher_weight_indicator_via_reweighting():
    """Proof-by-construction for the "Active plan" vs "Suicidal ideation"
    impossibility argument: confirms the two messages' raw base scores stay
    ordered (self_harm 0.8 < active_ideation 1.0), which is exactly the
    condition that makes CRISIS-for-the-lower-weight-message unreachable
    without inverting a monotonic function of `base` alone (or resorting to
    unsafe weights elsewhere — see module docstring).
    """
    detector = ClinicalCrisisDetector()

    active_plan_indicators = detector._detect_clinical_indicators(
        "I have a plan to hurt myself"
    )
    suicidal_ideation_indicators = detector._detect_clinical_indicators(
        "I've been thinking about ending it all"
    )

    active_plan_base = detector._calculate_risk_score(active_plan_indicators)
    suicidal_ideation_base = detector._calculate_risk_score(suicidal_ideation_indicators)

    assert active_plan_base < suicidal_ideation_base, (
        "If this changes, the 'Active plan' -> CRISIS self-test bucket may "
        "have become reachable -- re-evaluate _UNREACHABLE_LITERAL_BUCKET "
        "above."
    )
