"""
ENABLE_CLINICAL_DETECTION flag + crisis_v2/clinical_detection.py coverage.

Added for v1.5.0 M1 (docs/V1_5_0_ADHD_UPDATE_SCOPE.md, Workstream 3b:
"Flip ENABLE_CLINICAL_DETECTION after verification"). No test previously
covered this flag or crisis_v2/clinical_detection.py at all.

Findings from the "manual verification pass against the two documented
keyword-bypass incidents" the brief requires before flipping the flag:

1. Both bypass phrases ("want it all to stop", "thinking about ending my
   life" — the same two incidents crisis_detection.py's 2026-05-21 audit
   fixed for the v1 keyword list) were NOT recognized by
   ClinicalCrisisDetector's pattern set before this change. Fixed with a
   targeted pattern addition in crisis_v2/clinical_detection.py (see the
   comment there) mirroring the v1 fix.

2. Separately, `_combine_scores` had a deeper scoring bug: it weighted
   the indicator-derived `base` score by only 0.5, so even a single
   immediate_action=True indicator (weight 1.0, e.g. "kill myself")
   landed in RiskLevel.LOW, and weight <1.0 indicators (e.g. "hurt
   myself", weight 0.8) could round all the way down to RiskLevel.NONE.
   Verified against the module's own `verify_enterprise.py::verify_clinical_crisis`
   self-test cases: 4 of 5 failed against that scoring. This class of test
   file originally deliberately did NOT assert `immediate_action_required`
   for that reason.

   UPDATE (v1.5.0 M1 repair, ADR-006, this PR): `_combine_scores` is
   fixed — see its docstring in crisis_v2/clinical_detection.py for the
   full derivation, and tests/test_clinical_detection_scoring.py for the
   converted self-test cases (3 of 5 now pass their literal bucket; the
   other 2 are proven mathematically unreachable via any
   `_combine_scores`-only reweighting, but the actual safety property —
   `immediate_action_required=True` for both — now holds). The tests
   below still assert at the indicator-detection layer for the bypass
   phrases specifically (that layer is unaffected by the scoring fix),
   but `immediate_action_required` is no longer universally False; see
   test_clinical_detection_scoring.py and
   test_clinical_detection_integration.py for aggregate-score coverage.

3. `crisis_detector` (crisis_v2) was not wired into the live /api/chat path
   as of PR #167 — routes/chat.py's synchronous check called only
   crisis_detection.detect_crisis_level (the v1, keyword-only module) plus
   an LLM watchdog (helpers/crisis_helpers._run_crisis_watchdog); neither
   touched crisis_v2. integrations.process_chat_with_enterprise() was the
   only caller of crisis_detector, and nothing called that function from
   the chat routes. So flipping ENABLE_CLINICAL_DETECTION changed
   /api/enterprise/status's reported flag and made the class importable,
   but did not change any user-facing crisis handling — confirmed by the
   last test below (still true, see its updated docstring).

   UPDATE (v1.5.0 M1 repair, ADR-006, this PR): `crisis_detector` is now
   wired into `helpers/chat_helpers._process_chat_message` behind the
   SAME flag, as an escalation-only layer on top of
   crisis_detection.detect_crisis_level — it can only raise risk_level,
   never lower it or suppress a crisis the v1 detector already caught.
   See `helpers/chat_helpers._maybe_escalate_with_clinical_detector` and
   tests/test_clinical_detection_integration.py (flag-off/on behavior
   through the real /api/chat path, and an explicit invariant test).
"""

import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["PYTEST_CURRENT_TEST"] = "true"

# Imported at module level (matching tests/test_app.py, test_journal.py,
# test_user_settings.py) rather than inside a test function/fixture body.
# A deferred `from app import create_app` inside a function can resolve to
# the wrong `app` module (backend/app/__init__.py, a different package)
# when the full suite runs and some other test file has already put
# `backend/` on sys.path ahead of this one — a pre-existing suite-hygiene
# issue also seen on tests/test_assessments_api.py and
# tests/test_safety_guardrails.py. Importing once at collection time here,
# like the other passing files do, avoids it.
import app as app_module  # noqa: E402
import integrations as integrations_module  # noqa: E402
from app import create_app  # noqa: E402
from crisis_v2.clinical_detection import ClinicalCrisisDetector  # noqa: E402
from models import db  # noqa: E402

BYPASS_PHRASES = ("want it all to stop", "thinking about ending my life")


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


# ── (a) flag off = old behavior ─────────────────────────────────────────


def test_flag_off_default_crisis_detector_is_none(restore_integrations_state):
    os.environ.pop("ENABLE_CLINICAL_DETECTION", None)
    importlib.reload(integrations_module)
    assert integrations_module.ENABLE_CLINICAL_DETECTION is False
    assert integrations_module.crisis_detector is None


def test_flag_explicitly_false_crisis_detector_is_none(restore_integrations_state):
    os.environ["ENABLE_CLINICAL_DETECTION"] = "false"
    importlib.reload(integrations_module)
    assert integrations_module.crisis_detector is None


# ── (b) flag on = clinical detector engaged ─────────────────────────────


def test_flag_on_crisis_detector_engaged(restore_integrations_state):
    os.environ["ENABLE_CLINICAL_DETECTION"] = "true"
    importlib.reload(integrations_module)
    assert integrations_module.ENABLE_CLINICAL_DETECTION is True
    assert isinstance(integrations_module.crisis_detector, ClinicalCrisisDetector)


def test_flag_on_enterprise_status_reports_clinical_detection_true(
    restore_integrations_state,
):
    os.environ["ENABLE_CLINICAL_DETECTION"] = "true"
    importlib.reload(integrations_module)

    app = create_app()
    app.config.update({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    client = app.test_client()
    resp = client.get("/api/enterprise/status")
    assert resp.status_code == 200
    assert resp.get_json()["features"]["clinical_detection"] is True


# ── the two documented bypass phrases are caught ────────────────────────


@pytest.mark.parametrize("phrase", BYPASS_PHRASES)
def test_bypass_phrase_registers_high_priority_indicator(phrase):
    """The two documented keyword-bypass incidents must register as a
    clinical indicator with immediate_action=True — the same severity
    class as "kill myself" / "end my life". This is the pattern-detection
    layer this change fixed; see module docstring re: the separate,
    unfixed aggregate risk_level scoring bug.
    """
    detector = ClinicalCrisisDetector()
    assessment = detector.assess_risk(message=phrase, session_id=f"test-{hash(phrase)}")
    indicators = assessment["clinical_indicators"]
    assert indicators, f"{phrase!r} produced zero clinical indicators"
    assert any(
        ind.immediate_action and ind.category == "active_ideation" for ind in indicators
    ), f"{phrase!r} was not recognized as active suicidal ideation"


def test_bypass_phrases_caught_through_flag_gated_singleton(restore_integrations_state):
    """Same assertion, but through the actual flag-gated
    integrations.crisis_detector singleton — proves the fix is reachable
    end-to-end from the flag, not just at the class level."""
    os.environ["ENABLE_CLINICAL_DETECTION"] = "true"
    importlib.reload(integrations_module)
    detector = integrations_module.crisis_detector
    for phrase in BYPASS_PHRASES:
        assessment = detector.assess_risk(message=phrase, session_id=f"test-{hash(phrase)}")
        assert any(
            ind.immediate_action for ind in assessment["clinical_indicators"]
        ), f"{phrase!r} not caught via integrations.crisis_detector"


@pytest.mark.parametrize(
    "phrase",
    [
        "ending it with my boyfriend",
        "the meeting is ending",
        "I want the pain to stop",
    ],
)
def test_new_pattern_does_not_false_positive_on_similar_benign_phrases(phrase):
    """Guard the new pattern against the obvious false-positive neighbors
    of the bypass-phrase fix (breakup/meeting "ending", generic "stop")."""
    detector = ClinicalCrisisDetector()
    assessment = detector.assess_risk(message=phrase, session_id="test-fp")
    assert not any(
        ind.category == "active_ideation" and "soft/inflected" in ind.clinical_note
        for ind in assessment["clinical_indicators"]
    ), f"{phrase!r} false-positived on the new bypass-phrase pattern"


# ── Hard constraint: crisis flow never blocks, flag on or off ──────────


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


@pytest.mark.parametrize("flag_value", ["true", "false"])
def test_flag_flip_does_not_change_or_block_chat_endpoint(
    flag_value, chat_client, restore_integrations_state, monkeypatch
):
    """UPDATED (v1.5.0 M1 repair, ADR-006, this PR): routes/chat.py's
    dependency chain (via helpers/chat_helpers._process_chat_message) now
    DOES read ENABLE_CLINICAL_DETECTION / integrations.crisis_detector —
    see the module docstring's item 3 update. This specific test still
    holds, but for a narrower reason than its original docstring claimed:
    "want it all to stop" is already caught by crisis_detection.py's v1
    keyword list (risk_level="crisis" before the clinical layer even
    runs), and the clinical escalation layer is escalation-only — it
    short-circuits and never even consults the clinical detector once the
    simple detector has already said "crisis" (nothing can escalate past
    it). So for THIS phrase specifically, flipping the flag provably
    cannot change the response, in either flag state. It does NOT mean
    the flag is inert for /api/chat in general — see
    test_clinical_detection_integration.py for a message the v1 detector
    misses entirely, where the flag flip visibly changes risk_level
    through the real endpoint.
    """
    os.environ["ENABLE_CLINICAL_DETECTION"] = flag_value
    importlib.reload(integrations_module)

    # Patched on the module object captured at collection time (`app_module`,
    # imported above), not via the string form `monkeypatch.setattr("app.X",
    # ...)` — the string form re-resolves "app" through sys.modules at patch
    # time, which is exactly what the pre-existing full-suite pollution
    # (see module docstring / import comment) corrupts.
    monkeypatch.setattr(
        app_module,
        "_get_ai_response_with_failover",
        lambda *a, **k: ("I understand you're going through a difficult time...", "gemini"),
    )

    resp = chat_client.post(
        "/api/chat",
        json={"message": "want it all to stop"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "crisis_detected" in data
    assert "crisis_msg" in data
    assert "crisis_numbers" in data
    # v1 keyword list already catches this phrase (2026-05-21 audit) —
    # unaffected by the crisis_v2 flag either way.
    assert data["risk_level"] == "crisis"
