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

2. Separately — and NOT fixed in this pass, on purpose — the detector's
   *aggregate* `risk_level` / `immediate_action_required` output has a
   deeper scoring bug: `_combine_scores` weights the indicator-derived
   `base` score by only 0.5, so even a single immediate_action=True
   indicator (weight 1.0, e.g. "kill myself") lands in RiskLevel.LOW, and
   weight <1.0 indicators (e.g. "hurt myself", weight 0.8) can round all
   the way down to RiskLevel.NONE. Verified against the module's own
   `verify_enterprise.py::verify_clinical_crisis` self-test cases: 4 of 5
   fail against current scoring. This is a scoring-architecture problem
   that needs deliberate clinical review, not a surgical patch, so it's
   flagged here (and in a comment above `_combine_scores`) rather than
   silently patched. Tests below therefore assert at the indicator-
   detection layer (what was actually fixed), not the aggregate
   risk_level — and deliberately do NOT assert immediate_action_required
   is True, because today it is not.

3. `crisis_detector` (crisis_v2) is not wired into the live /api/chat path.
   routes/chat.py's synchronous check calls crisis_detection.detect_crisis_level
   (the v1, keyword-only module) plus an LLM watchdog
   (helpers/crisis_helpers._run_crisis_watchdog); neither touches crisis_v2.
   integrations.process_chat_with_enterprise() is the only caller of
   crisis_detector, and nothing calls that function from the chat routes.
   So flipping ENABLE_CLINICAL_DETECTION changes /api/enterprise/status's
   reported flag and makes the class importable, but does not change any
   user-facing crisis handling today — confirmed by the last test below.
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
    """routes/chat.py never reads ENABLE_CLINICAL_DETECTION or
    integrations.crisis_detector (confirmed by inspection — see module
    docstring), so flipping the flag must not change /api/chat's status
    code or crisis-related response fields, and must never block the
    response. Parametrized over both flag states to prove identical
    behavior either way.
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
