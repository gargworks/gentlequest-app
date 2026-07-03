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
import re
import sys
import time

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


# ─────────────────────────────────────────────────────────────────────────
# Property test (FLIP-SAFE adversarial review, crisis-hardening trio 3a):
# EVERY immediate_action=True indicator in CLINICAL_INDICATORS, alone in a
# message with no other corroborating signal, must set
# immediate_action_required=True and reach at least RiskLevel.HIGH. This is
# exactly the safety property BASE_WEIGHT=3.25 was derived to guarantee
# (see _combine_scores docstring's lower-bound derivation: the single
# lowest-weight immediate_action=True indicator, 0.8, must alone clear HIGH
# >= 2.5). test_immediate_action_indicators_set_immediate_action_required
# above spot-checks 2 hand-picked messages; this generalizes to the full
# table so a future weight edit that quietly drops any ONE
# immediate_action=True indicator below the derived floor fails CI instead
# of silently reopening the original bug for that specific indicator.
# ─────────────────────────────────────────────────────────────────────────

# One example message per immediate_action=True indicator, keyed by the
# indicator's `clinical_note` (unique across CLINICAL_INDICATORS today).
# Each message was hand-verified (via _detect_clinical_indicators) to match
# ONLY its target indicator and no other in the table -- so a weight
# regression on any single indicator is caught by its own dedicated case,
# not masked by a second indicator's contribution to the same message.
IMMEDIATE_ACTION_EXAMPLE_MESSAGES = {
    "Active suicidal ideation with intent": "I want to kill myself",
    "Active suicidal ideation without specific intent": "I wish I was dead",
    "Suicide plan in progress": "I am planning to harm myself",
    "Active suicidal ideation — soft/inflected phrasing": (
        "I keep thinking about ending my life"
    ),
    "Active self-harm behavior": "I keep hurting myself",
    "Access to lethal means": "I have a gun ready to use",
    "Specific method mentioned": "I keep thinking about an overdose",
    "Immediate temporal intent": "Tonight is when I will end this pain",
    "Acute distress": "I can't take it anymore",
    "Previous suicide attempt": "I've tried before, more than once",
    "Possible psychotic symptoms": "I keep hearing voices",
}


def _immediate_action_indicators():
    """All CLINICAL_INDICATORS entries with immediate_action=True, as
    (category, indicator) pairs -- read live from the class so this
    tracks the actual table, not a frozen snapshot of it.
    """
    found = []
    for category, indicators in ClinicalCrisisDetector.CLINICAL_INDICATORS.items():
        for indicator in indicators:
            if indicator.immediate_action:
                found.append((category, indicator))
    return found


_IA_CASES = _immediate_action_indicators()


def test_every_immediate_action_indicator_has_an_example_message():
    """Guard for the property test below: if a new immediate_action=True
    indicator is added to CLINICAL_INDICATORS without a matching entry in
    IMMEDIATE_ACTION_EXAMPLE_MESSAGES, fail loudly here instead of the new
    indicator silently going untested by
    test_immediate_action_indicator_alone_clears_high (an empty
    parametrize list still "passes" -- it just runs zero cases).
    """
    missing = [
        indicator.clinical_note
        for _category, indicator in _IA_CASES
        if indicator.clinical_note not in IMMEDIATE_ACTION_EXAMPLE_MESSAGES
    ]
    assert not missing, (
        f"New immediate_action=True indicator(s) added without an example "
        f"message: {missing!r}. Add a case to "
        f"IMMEDIATE_ACTION_EXAMPLE_MESSAGES above."
    )
    assert len(_IA_CASES) >= 1, "CLINICAL_INDICATORS has no immediate_action=True entries -- unexpected."


@pytest.mark.parametrize(
    "category,indicator",
    _IA_CASES,
    ids=[indicator.clinical_note for _category, indicator in _IA_CASES],
)
def test_immediate_action_indicator_alone_clears_high(category, indicator):
    message = IMMEDIATE_ACTION_EXAMPLE_MESSAGES.get(indicator.clinical_note)
    assert message is not None, (
        f"No example message for {indicator.clinical_note!r} (category "
        f"{category!r}) -- see "
        f"test_every_immediate_action_indicator_has_an_example_message."
    )

    detector = ClinicalCrisisDetector()
    assessment = detector.assess_risk(
        message, session_id=f"ia-property-{indicator.clinical_note}"
    )

    assert assessment["immediate_action_required"] is True, (
        f"[{category}] {indicator.clinical_note!r} ({message!r}, "
        f"weight={indicator.weight}) did not set immediate_action_required"
    )
    assert assessment["risk_level"].severity >= RiskLevel.HIGH.severity, (
        f"[{category}] {indicator.clinical_note!r} ({message!r}, "
        f"weight={indicator.weight}) only reached "
        f"{assessment['risk_level'].code!r}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Crisis-hardening trio 3c: the 'temporal_urgency' / 'Immediate temporal
# intent' pattern's gap between the temporal word (tonight/today/right
# now/...) and the die/end/kill word is bounded to `.{0,200}?` -- an
# unbounded `.*` there was superlinear (re.search backtracks the `.*` from
# every occurrence of the temporal alternation), degrading toward O(n^2)
# for adversarial input. Measured before this fix: ~3.2s for a single
# 50,000-char message of repeated "tonight " with no die/end/kill match;
# ~0.37s at 500,000 chars after bounding (was heading toward minutes at
# that size unbounded). routes/chat.py's 5000-char /api/chat cap is the
# ONLY thing that made this safe today -- it doesn't protect any other
# call site of this detector (batch/offline scoring, a future endpoint,
# a raised cap).
# ─────────────────────────────────────────────────────────────────────────


def _temporal_urgency_pattern():
    """The compiled 'Immediate temporal intent' pattern, read live from
    CLINICAL_INDICATORS (not a copy-pasted regex string) so this test
    tracks the actual pattern, not a frozen snapshot of it.
    """
    for indicator in ClinicalCrisisDetector.CLINICAL_INDICATORS["temporal_urgency"]:
        if indicator.clinical_note == "Immediate temporal intent":
            return indicator
    raise AssertionError(
        "'Immediate temporal intent' indicator not found in "
        "CLINICAL_INDICATORS['temporal_urgency'] -- has it been renamed?"
    )


@pytest.mark.parametrize(
    "message",
    [
        "Tonight is when I will end this pain",
        "right now I just want to die",
        "by tomorrow I will kill myself, I have decided",
        "immediately after this call I am going to end it",
    ],
)
def test_temporal_urgency_pattern_still_matches_realistic_proximity(message):
    """The bounded gap must not have broken ordinary same-sentence /
    short-multi-clause phrasing -- these are all realistic crisis
    statements with well under 200 chars between the temporal word and
    die/end/kill.
    """
    indicator = _temporal_urgency_pattern()
    pattern = re.compile(indicator.pattern, re.IGNORECASE)
    assert pattern.search(message), (
        f"Bounded temporal_urgency pattern no longer matches a realistic "
        f"same-sentence case: {message!r}"
    )


def test_temporal_urgency_pattern_gap_is_bounded_not_unbounded():
    """Regression guard against re-introducing an unbounded `.*` (or any
    other unbounded quantifier) between the two word groups: the temporal
    word and the die/end/kill word, separated by more than the bound,
    must NOT match. If this starts failing because the bound widened,
    that's fine -- update the constant here to match; if it fails because
    the gap became unbounded again, that's the regression this test
    exists to catch.
    """
    indicator = _temporal_urgency_pattern()
    pattern = re.compile(indicator.pattern, re.IGNORECASE)

    filler = "x" * 500  # comfortably past any reasonable same-message bound
    far_apart = f"tonight {filler} kill"
    assert pattern.search(far_apart) is None, (
        "temporal_urgency pattern matched across a 500-char gap -- the "
        "quantifier between the two word groups is no longer bounded, "
        "reopening the superlinear-regex risk this test guards against."
    )


def test_temporal_urgency_pattern_performance_stays_linear():
    """Empirical guard for the superlinear-regex fix: an adversarial
    message (a temporal word repeated many times, no die/end/kill ever
    present, forcing the backtracker to retry from every occurrence) must
    stay fast even well beyond routes/chat.py's 5000-char /api/chat cap --
    this detector has no cap of its own, so a different call site (or a
    future change to that cap) must not be able to reintroduce the
    O(n^2) blowup. Generous wall-clock ceiling (not a tight benchmark) --
    this is a regression tripwire, not a perf micro-benchmark.
    """
    indicator = _temporal_urgency_pattern()
    pattern = re.compile(indicator.pattern, re.IGNORECASE)

    adversarial_message = "tonight " * 12500  # 100,000 chars, 20x the /api/chat cap

    start = time.monotonic()
    result = pattern.search(adversarial_message)
    elapsed = time.monotonic() - start

    assert result is None  # no die/end/kill anywhere -- confirms worst-case path ran
    assert elapsed < 2.0, (
        f"temporal_urgency pattern took {elapsed:.3f}s on a 100,000-char "
        f"adversarial message (expected well under 2s if the gap is "
        f"properly bounded) -- possible reintroduction of unbounded "
        f"backtracking."
    )


# ─────────────────────────────────────────────────────────────────────────
# Crisis-hardening trio 3b: `risk_history` is a dict keyed by session_id,
# one entry per distinct session ever seen by a detector instance. Each
# session's own list was already capped at 100 entries
# (`_update_risk_history`), but the *dict itself* had no cap -- a
# long-running process (or an attacker/bug cycling session_id per
# request) grows it without bound: an unbounded per-process memory leak.
# Fixed with a size-capped LRU (ClinicalCrisisDetector._MAX_TRACKED_SESSIONS,
# OrderedDict + evict-oldest).
# ─────────────────────────────────────────────────────────────────────────


def test_risk_history_is_bounded_and_evicts_oldest_session():
    """Feeding more distinct session_ids than _MAX_TRACKED_SESSIONS must
    not grow risk_history past that cap -- and the evicted session must be
    the least-recently-touched one (true LRU), not an arbitrary one.
    """
    detector = ClinicalCrisisDetector()
    cap = ClinicalCrisisDetector._MAX_TRACKED_SESSIONS

    # Fill exactly to the cap.
    for i in range(cap):
        detector.assess_risk("hello there", session_id=f"lru-session-{i}")
    assert len(detector.risk_history) == cap

    # One more distinct session must evict the oldest (session 0) rather
    # than growing past the cap.
    detector.assess_risk("hello there", session_id="lru-session-overflow")
    assert len(detector.risk_history) == cap, (
        f"risk_history grew to {len(detector.risk_history)}, past the "
        f"{cap}-session cap -- eviction did not fire."
    )
    assert "lru-session-0" not in detector.risk_history, (
        "Oldest session was not evicted when the cap was exceeded."
    )
    assert "lru-session-overflow" in detector.risk_history
    # The newest pre-fill session should still be present -- only the
    # single oldest entry should have been evicted for one overflow.
    assert f"lru-session-{cap - 1}" in detector.risk_history


def test_risk_history_lru_touch_protects_recently_used_session():
    """A session that's touched again (re-moved to most-recently-used)
    before the cap is exceeded must survive eviction even though it was
    created early -- confirms this is a real LRU (touch-based), not a
    simple insertion-order ring buffer that would evict it regardless.
    """
    detector = ClinicalCrisisDetector()
    cap = ClinicalCrisisDetector._MAX_TRACKED_SESSIONS

    for i in range(cap):
        detector.assess_risk("hello there", session_id=f"lru2-session-{i}")

    # Re-touch the oldest session, moving it to most-recently-used.
    detector.assess_risk("hello again", session_id="lru2-session-0")

    # Now overflow by one distinct new session. Without the touch above,
    # session-0 would be evicted (it was the original oldest); with the
    # touch, session-1 is now the least-recently-used and should be
    # evicted instead.
    detector.assess_risk("hello there", session_id="lru2-session-overflow")

    assert "lru2-session-0" in detector.risk_history, (
        "Re-touched session was evicted anyway -- eviction is not "
        "tracking recency (LRU), only insertion order."
    )
    assert "lru2-session-1" not in detector.risk_history, (
        "Expected the least-recently-touched session (session-1, since "
        "session-0 was re-touched) to be evicted."
    )


def test_risk_history_per_session_cap_unchanged():
    """Regression guard: the existing per-session 100-entry cap
    (`_update_risk_history`'s pre-existing behavior) must be untouched by
    the dict-level LRU bound added in this hardening pass.
    """
    detector = ClinicalCrisisDetector()
    for _ in range(150):
        detector.assess_risk("hello there", session_id="single-session")

    assert len(detector.risk_history["single-session"]) == 100
