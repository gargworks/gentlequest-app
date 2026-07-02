"""
Integration tests for wiring crisis_v2's ClinicalCrisisDetector into the
live /api/chat path, behind ENABLE_CLINICAL_DETECTION (v1.5.0 M1 repair,
ADR-006).

Prior to this PR, `crisis_detector` (crisis_v2) was importable behind the
flag but never called from the chat routes — see
tests/test_clinical_detection_flag.py's module docstring for the PR #167
finding. This PR wires it into
`helpers.chat_helpers._maybe_escalate_with_clinical_detector`, called from
`_process_chat_message` right after the existing
`crisis_detection.detect_crisis_level` (v1, keyword-only) call.

INVARIANT under test throughout this file: the clinical layer is
escalation-only. It can raise the final risk_level above what the v1
detector alone produced; it can never lower it, and it can never suppress
a crisis the v1 detector already caught. See
`_maybe_escalate_with_clinical_detector`'s docstring in
helpers/chat_helpers.py for the enforcement (a `risk_hierarchy`-style
rank comparison, plus an explicit short-circuit when the v1 result is
already "crisis").

Three things are covered here, matching the v1.5.0 M1 brief:

1. Flag OFF (default/unset, and explicit "false") = current behavior.
   A message the v1 detector does not catch (a genuine coverage gap —
   crisis_detection.py has no vocabulary for lethal-means access, e.g.
   "pills", "gun") stays at whatever the v1 detector alone produces
   ("low"), through the real /api/chat endpoint.

2. Flag ON = the two documented keyword-bypass phrases from PR #167
   ("want it all to stop", "thinking about ending my life") still
   trigger a crisis response through the real /api/chat endpoint. Also:
   flag ON measurably changes behavior for a message only the clinical
   detector catches (proving the wiring is live, not inert) — the same
   "pills ready" message from (1) escalates to "high" when the flag is
   on.

3. The escalation-only invariant, tested explicitly two ways: (a) at the
   function level, direct calls to
   `_maybe_escalate_with_clinical_detector` proving a "crisis" input is
   never downgraded regardless of what the clinical detector would say
   about the same message in isolation; (b) through the real endpoint,
   using a message crisis_detection.py's v1 keyword list catches
   ("thinking about suicide" — v1 has this as a literal keyword) but
   which crisis_v2 does NOT flag at all in isolation (`risk_level="none"`,
   verified directly) — the flag being on must not downgrade this below
   "crisis".
"""

import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["PYTEST_CURRENT_TEST"] = "true"

# Imported at module level, matching tests/test_clinical_detection_flag.py's
# established pattern for this suite — a deferred import inside a test
# function can resolve to the wrong `app` module once other test files have
# altered sys.path ahead of this one.
import integrations as integrations_module  # noqa: E402
from app import create_app  # noqa: E402
from crisis_v2.clinical_detection import ClinicalCrisisDetector, RiskLevel  # noqa: E402
from helpers.chat_helpers import _maybe_escalate_with_clinical_detector  # noqa: E402
from models import db  # noqa: E402

BYPASS_PHRASES = ("want it all to stop", "thinking about ending my life")

# Not covered by ANY crisis_detection.py (v1) keyword list — no
# gun/weapon/pills/rope/knife vocabulary exists there at all — but matches
# crisis_v2's `method_access` indicator (weight 1.0, immediate_action=True).
# A genuine, real coverage gap the clinical layer closes when enabled.
CLINICAL_ONLY_MESSAGE = "I have pills ready for tonight"

# Caught by crisis_detection.py's v1 SUICIDE_KEYWORDS ("thinking about
# suicide" is a literal entry) but produces a clinical assessment of
# risk_level="none" in isolation (verified in
# test_invariant_message_produces_none_from_clinical_detector_alone below).
# The cleanest possible case for proving escalation-only: if the invariant
# were broken, this message is exactly where a downgrade would show up.
INVARIANT_MESSAGE = "I keep thinking about suicide"


@pytest.fixture
def restore_integrations_state():
    """integrations.py reads ENABLE_CLINICAL_DETECTION at *import* time.
    Tests that flip the env var must reload the module, and must restore
    both the env var and the module state afterward — otherwise a leftover
    reload leaks a non-None `crisis_detector` into whatever test file runs
    next in the same pytest session/process.
    """
    original_env = os.environ.get("ENABLE_CLINICAL_DETECTION")
    yield
    if original_env is None:
        os.environ.pop("ENABLE_CLINICAL_DETECTION", None)
    else:
        os.environ["ENABLE_CLINICAL_DETECTION"] = original_env
    importlib.reload(integrations_module)


@pytest.fixture
def chat_app():
    os.environ["PYTEST_CURRENT_TEST"] = "true"
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key",
            "RATE_LIMIT_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def chat_client(chat_app):
    return chat_app.test_client()


def _mock_ai_layer(monkeypatch):
    """Non-crisis messages proceed past Guardrail 1 into real AI-response
    generation (function-calling branch by default). Mock both the Gemini
    call and Layer 2 safety check so tests are fast, deterministic, and
    don't require GEMINI_API_KEY. Same pattern as
    tests/test_safety_guardrails.py.
    """
    monkeypatch.setattr(
        "providers.gemini.get_gemini_response_with_tools",
        lambda *a, **k: ("I hear you. Let's talk about what's going on.", []),
    )
    monkeypatch.setattr(
        "providers.safety.check_safety_llm",
        lambda *a, **k: (True, "Valid"),
    )


# ── (1) & (2) flag off/on behavior through the real /api/chat endpoint ──


@pytest.mark.parametrize(
    "flag_value,expected_risk_level",
    [(None, "low"), ("false", "low"), ("true", "high")],
)
def test_flag_controls_escalation_for_v1_coverage_gap_message(
    flag_value, expected_risk_level, chat_client, restore_integrations_state, monkeypatch,
):
    """The actual payoff of wiring the clinical detector in. With the flag
    off (default, unset, or explicit "false"), CLINICAL_ONLY_MESSAGE is
    invisible to server-side crisis detection — crisis_detection.py has no
    keyword coverage for lethal-means access at all, so it stays "low",
    identical to pre-PR behavior. With the flag on, the same message is
    correctly escalated to "high" through the real /api/chat code path —
    proving the wiring is live end-to-end, not just at the class/unit
    level (see tests/test_clinical_detection_scoring.py for that).
    """
    if flag_value is None:
        os.environ.pop("ENABLE_CLINICAL_DETECTION", None)
    else:
        os.environ["ENABLE_CLINICAL_DETECTION"] = flag_value
    importlib.reload(integrations_module)

    _mock_ai_layer(monkeypatch)

    resp = chat_client.post("/api/chat", json={"message": CLINICAL_ONLY_MESSAGE})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["risk_level"] == expected_risk_level
    assert data["crisis_level"] == expected_risk_level
    # "high" is below the crisis-block threshold ("crisis" only) — this
    # message doesn't cross Guardrail 1 either way. The point here is that
    # risk_level itself is now materially more accurate when the flag is
    # on, not that this specific message gets blocked.
    assert data["crisis_detected"] is False


@pytest.mark.parametrize("phrase", BYPASS_PHRASES)
def test_flag_on_bypass_phrases_trigger_crisis_through_chat_endpoint(
    phrase, chat_client, restore_integrations_state,
):
    """Both documented keyword-bypass incidents from PR #167, hit through
    the real /api/chat POST endpoint with ENABLE_CLINICAL_DETECTION=true —
    the chief's pre-flip sanity check. No AI-layer mocking needed: both
    phrases are already caught by crisis_detection.py's v1 keyword list
    (2026-05-21 audit), so Guardrail 1 short-circuits before any AI call.
    """
    os.environ["ENABLE_CLINICAL_DETECTION"] = "true"
    importlib.reload(integrations_module)

    resp = chat_client.post("/api/chat", json={"message": phrase})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["risk_level"] == "crisis"
    assert data["crisis_detected"] is True
    assert data["crisis_msg"]
    assert data["crisis_numbers"]


@pytest.mark.parametrize("phrase", BYPASS_PHRASES)
def test_flag_off_bypass_phrases_still_trigger_crisis(
    phrase, chat_client, restore_integrations_state,
):
    """Same two phrases with the flag OFF — must be unaffected, since v1
    alone already catches them (2026-05-21 audit, independent of crisis_v2
    entirely). Confirms flag-off is truly current behavior for the
    phrases the brief specifically calls out.
    """
    os.environ.pop("ENABLE_CLINICAL_DETECTION", None)
    importlib.reload(integrations_module)

    resp = chat_client.post("/api/chat", json={"message": phrase})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["risk_level"] == "crisis"
    assert data["crisis_detected"] is True


# ── (3) escalation-only invariant ───────────────────────────────────────


def test_invariant_message_produces_none_from_clinical_detector_alone():
    """Sanity-check the premise of the endpoint-level invariant test below:
    INVARIANT_MESSAGE really does produce risk_level="none" from the
    clinical detector in isolation, with zero clinical indicators. This is
    what makes it the cleanest possible case for proving escalation-only —
    if the invariant were broken, downgrading here would be maximally
    visible (crisis -> none, not crisis -> some intermediate level).
    """
    detector = ClinicalCrisisDetector()
    assessment = detector.assess_risk(INVARIANT_MESSAGE, session_id="invariant-premise-check")
    assert assessment["risk_level"] == RiskLevel.NONE
    assert assessment["clinical_indicators"] == []


def test_invariant_crisis_never_downgraded_through_chat_endpoint(
    chat_client, restore_integrations_state,
):
    """INVARIANT_MESSAGE is caught by crisis_detection.py's v1 keyword list
    ("thinking about suicide" is a literal SUICIDE_KEYWORDS entry) but the
    clinical detector alone would say "none" for it (see previous test).
    With ENABLE_CLINICAL_DETECTION=true, the final response must still be
    "crisis" — the escalation-only design must never let a weak clinical
    read downgrade a crisis the simple detector already caught.
    """
    os.environ["ENABLE_CLINICAL_DETECTION"] = "true"
    importlib.reload(integrations_module)

    resp = chat_client.post("/api/chat", json={"message": INVARIANT_MESSAGE})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["risk_level"] == "crisis"
    assert data["crisis_detected"] is True


def test_invariant_at_function_level_crisis_input_always_returns_crisis():
    """Direct, fast, no-Flask-context test of
    `_maybe_escalate_with_clinical_detector` itself: whenever
    `simple_risk_level` is already "crisis", the function must return
    "crisis" — regardless of message content, session, or flag state.
    This is enforced by an explicit early-return in the function (see its
    docstring), not left as an incidental property of score comparison;
    this test exercises that directly.
    """
    # Message content is irrelevant once simple_risk_level == "crisis" —
    # use INVARIANT_MESSAGE (clinically reads as "none" in isolation) to
    # make the point sharply: even the weakest possible clinical read
    # cannot pull this down.
    result = _maybe_escalate_with_clinical_detector(
        INVARIANT_MESSAGE, "function-level-invariant", "crisis"
    )
    assert result == "crisis"


def test_invariant_at_function_level_escalates_when_clinical_is_stronger(
    restore_integrations_state,
):
    """Complementary case: when the flag is on and the clinical assessment
    IS more severe than the simple result, the function escalates (this is
    the actual feature, not just the safety rail). Uses
    CLINICAL_ONLY_MESSAGE ("I have pills ready for tonight"), which
    crisis_detection.py would classify as "low" on its own.
    """
    os.environ["ENABLE_CLINICAL_DETECTION"] = "true"
    importlib.reload(integrations_module)

    result = _maybe_escalate_with_clinical_detector(
        CLINICAL_ONLY_MESSAGE, "function-level-escalation", "low"
    )
    assert result == "high"


def test_invariant_at_function_level_flag_off_never_escalates(
    restore_integrations_state,
):
    """With the flag off, `_maybe_escalate_with_clinical_detector` must be
    a complete no-op — byte-for-byte the input risk_level back, even for a
    message that (if the flag were on) would escalate.
    """
    os.environ.pop("ENABLE_CLINICAL_DETECTION", None)
    importlib.reload(integrations_module)

    result = _maybe_escalate_with_clinical_detector(
        CLINICAL_ONLY_MESSAGE, "function-level-flag-off", "low"
    )
    assert result == "low"
