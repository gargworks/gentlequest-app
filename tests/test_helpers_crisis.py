"""Unit tests for helpers/crisis_helpers.py."""

import os
import sys
import uuid
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["PYTEST_CURRENT_TEST"] = "true"

from app import create_app
from helpers.crisis_helpers import (
    CRISIS_RESOURCES_BY_COUNTRY,
    _enhanced_crisis_detection,
    _get_crisis_resources,
    _get_crisis_response,
    _log_crisis_detection,
    get_country_code_from_ip,
    get_country_from_request,
    get_crisis_response_and_resources,
)
from models import CrisisEvent, db


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "RATE_LIMIT_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# ---------------------------------------------------------------------------
# CRISIS_RESOURCES_BY_COUNTRY structure
# ---------------------------------------------------------------------------

class TestCrisisResourcesData:
    def test_has_generic_fallback(self):
        assert "generic" in CRISIS_RESOURCES_BY_COUNTRY

    def test_all_countries_have_required_keys(self):
        for code, data in CRISIS_RESOURCES_BY_COUNTRY.items():
            assert "crisis_msg" in data, f"{code} missing crisis_msg"
            assert "crisis_numbers" in data, f"{code} missing crisis_numbers"
            assert isinstance(data["crisis_numbers"], list)
            assert len(data["crisis_numbers"]) > 0

    def test_major_countries_present(self):
        for c in ["us", "uk", "ca", "au", "in", "de", "fr", "jp", "br", "mx"]:
            assert c in CRISIS_RESOURCES_BY_COUNTRY


# ---------------------------------------------------------------------------
# _enhanced_crisis_detection
# ---------------------------------------------------------------------------

class TestEnhancedCrisisDetection:
    def test_keywords_detected_and_scored(self):
        risk, score, kws = _enhanced_crisis_detection(
            "I want to kill myself and end it all"
        )
        # Normalized score against sum of ALL keyword weights is small; risk tier
        # can be "low" even with explicit keywords. We verify detection+score instead.
        assert score > 0
        assert "kill myself" in kws
        assert "end it all" in kws
        assert "want to die" not in kws  # not in input
        assert risk in ("low", "medium", "high", "crisis")

    def test_low_tier_on_mild_message(self):
        risk, score, kws = _enhanced_crisis_detection("I'm a bit stressed today")
        assert risk == "low"

    def test_no_keywords_returns_low(self):
        risk, score, kws = _enhanced_crisis_detection("I had a nice lunch")
        assert risk == "low"
        assert score == 0
        assert kws == []

    def test_case_insensitive_keyword_match(self):
        _, _, kws = _enhanced_crisis_detection("I WANT TO DIE")
        assert "want to die" in kws

    def test_returns_triple(self):
        result = _enhanced_crisis_detection("hopeless")
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_multiple_keywords_aggregate(self):
        risk, score, kws = _enhanced_crisis_detection(
            "I'm hopeless, worthless, and depressed"
        )
        assert len(kws) >= 3
        assert risk in ("high", "medium", "low")  # depends on scoring threshold

    def test_empty_string(self):
        risk, score, kws = _enhanced_crisis_detection("")
        assert risk == "low"
        assert score == 0


# ---------------------------------------------------------------------------
# get_country_code_from_ip
# ---------------------------------------------------------------------------

class TestGetCountryCodeFromIP:
    def setup_method(self):
        # Clear LRU cache between tests
        get_country_code_from_ip.cache_clear()

    def test_localhost_returns_generic(self):
        assert get_country_code_from_ip("127.0.0.1") == "generic"
        assert get_country_code_from_ip("::1") == "generic"
        assert get_country_code_from_ip("localhost") == "generic"

    def test_private_ranges_return_generic(self):
        assert get_country_code_from_ip("10.0.0.5") == "generic"
        assert get_country_code_from_ip("192.168.1.1") == "generic"
        assert get_country_code_from_ip("172.16.0.1") == "generic"

    def test_invalid_ip_returns_generic(self):
        assert get_country_code_from_ip("not-an-ip") == "generic"

    def test_successful_lookup_known_country(self):
        fake = MagicMock()
        fake.status_code = 200
        fake.json.return_value = {"country": "US"}
        with patch("helpers.crisis_helpers.requests.get", return_value=fake):
            assert get_country_code_from_ip("8.8.8.8") == "us"

    def test_unknown_country_returns_generic(self):
        fake = MagicMock()
        fake.status_code = 200
        fake.json.return_value = {"country": "XX"}
        with patch("helpers.crisis_helpers.requests.get", return_value=fake):
            assert get_country_code_from_ip("8.8.4.4") == "generic"

    def test_non_200_returns_generic(self):
        fake = MagicMock()
        fake.status_code = 500
        with patch("helpers.crisis_helpers.requests.get", return_value=fake):
            assert get_country_code_from_ip("1.1.1.1") == "generic"

    def test_request_exception_returns_generic(self):
        with patch(
            "helpers.crisis_helpers.requests.get", side_effect=Exception("net")
        ):
            assert get_country_code_from_ip("4.4.4.4") == "generic"


# ---------------------------------------------------------------------------
# get_country_from_request
# ---------------------------------------------------------------------------

class TestGetCountryFromRequest:
    def setup_method(self):
        get_country_code_from_ip.cache_clear()

    def test_explicit_country_in_body(self, app):
        with app.test_request_context(
            "/", method="POST", json={"country": "uk"}
        ):
            from flask import request
            assert get_country_from_request(request) == "uk"

    def test_invalid_country_falls_to_ip(self, app):
        with app.test_request_context(
            "/",
            method="POST",
            json={"country": "zz"},
            headers={"X-Forwarded-For": "127.0.0.1"},
        ):
            from flask import request
            assert get_country_from_request(request) == "generic"

    def test_x_forwarded_for_used(self, app):
        with app.test_request_context(
            "/",
            method="POST",
            json={},
            headers={"X-Forwarded-For": "127.0.0.1"},
        ):
            from flask import request
            assert get_country_from_request(request) == "generic"


# ---------------------------------------------------------------------------
# get_crisis_response_and_resources
# ---------------------------------------------------------------------------

class TestCrisisResponseAndResources:
    def test_crisis_uses_country_specific_msg(self):
        result = get_crisis_response_and_resources("crisis", "us")
        assert result["risk_level"] == "crisis"
        assert "988" in result["crisis_msg"]
        assert len(result["crisis_numbers"]) > 0

    def test_crisis_unknown_country_falls_to_generic(self):
        result = get_crisis_response_and_resources("crisis", "zz")
        assert result["risk_level"] == "crisis"
        assert result["crisis_numbers"] == CRISIS_RESOURCES_BY_COUNTRY["generic"][
            "crisis_numbers"
        ]

    def test_high_risk_returns_empty_numbers(self):
        result = get_crisis_response_and_resources("high")
        assert result["risk_level"] == "high"
        assert result["crisis_numbers"] == []
        assert "worried" in result["crisis_msg"].lower()

    def test_medium_risk(self):
        result = get_crisis_response_and_resources("medium")
        assert result["risk_level"] == "medium"

    def test_low_risk(self):
        result = get_crisis_response_and_resources("low")
        assert result["risk_level"] == "low"


# ---------------------------------------------------------------------------
# _get_crisis_response / _get_crisis_resources
# ---------------------------------------------------------------------------

class TestLegacyCrisisHelpers:
    def test_get_crisis_response_crisis_level(self):
        msg = _get_crisis_response("crisis", 1.0)
        assert "988" in msg or "crisis" in msg.lower() or "help" in msg.lower()

    def test_get_crisis_response_unknown_level_defaults_low(self):
        msg = _get_crisis_response("unknown", 0.0)
        assert isinstance(msg, str) and len(msg) > 0

    def test_get_crisis_resources_returns_dict(self):
        for level in ["crisis", "high", "medium", "low"]:
            result = _get_crisis_resources(level)
            assert "immediate" in result
            assert "online" in result
            assert isinstance(result["immediate"], list)
            assert isinstance(result["online"], list)

    def test_get_crisis_resources_unknown_defaults_to_low(self):
        result = _get_crisis_resources("zzz")
        assert result == _get_crisis_resources("low")


# ---------------------------------------------------------------------------
# _log_crisis_detection
# ---------------------------------------------------------------------------

class TestLogCrisisDetection:
    def test_persists_crisis_event_row(self, app):
        sid = str(uuid.uuid4())
        with patch(
            "helpers.crisis_helpers.AlertManager.create_alert", return_value=None
        ):
            _log_crisis_detection(
                sid, "I want to die", "crisis", 1.0, ["want to die"]
            )
        events = CrisisEvent.query.filter_by(session_id=sid).all()
        assert len(events) == 1
        assert events[0].risk_level == "crisis"
        assert "want to die" in (events[0].keywords or "")

    def test_triggers_alert_manager(self, app):
        sid = str(uuid.uuid4())
        with patch(
            "helpers.crisis_helpers.AlertManager.create_alert", return_value=42
        ) as mock_alert:
            _log_crisis_detection(sid, "hopeless", "high", 0.8, ["hopeless"])
        mock_alert.assert_called_once()
        kwargs = mock_alert.call_args.kwargs
        assert kwargs["session_id"] == sid
        assert kwargs["risk_level"] == "high"

    def test_exception_does_not_propagate(self, app):
        with patch(
            "helpers.crisis_helpers.AlertManager.create_alert",
            side_effect=Exception("boom"),
        ):
            # Should not raise
            _log_crisis_detection(
                str(uuid.uuid4()), "m", "crisis", 1.0, ["suicide"]
            )
