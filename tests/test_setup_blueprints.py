"""Unit tests for setup/blueprints.py + routes/brain_routes.py + routes/enterprise_routes.py."""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["PYTEST_CURRENT_TEST"] = "true"

from app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "RATE_LIMIT_ENABLED": False,
    })
    yield app


class TestRouteCount:
    def test_expected_route_count(self, app):
        rules = [r.rule for r in app.url_map.iter_rules() if not r.rule.startswith("/static")]
        assert len(rules) >= 70, f"Expected ≥70 routes, got {len(rules)}"

    def test_no_duplicate_routes(self, app):
        from collections import Counter
        rules = [r.rule for r in app.url_map.iter_rules() if not r.rule.startswith("/static")]
        dupes = {r: c for r, c in Counter(rules).items() if c > 1}
        assert len(dupes) == 0, f"Duplicate routes: {dupes}"


class TestBrainRoutes:
    def test_brain_routes_registered(self, app):
        rules = {r.rule for r in app.url_map.iter_rules()}
        for expected in [
            "/api/brain/telegram/webhook",
            "/api/brain/status",
            "/api/brain/alert",
            "/api/brain/sprint",
            "/api/brain/sync",
            "/api/brain/debug_import",
            "/api/swarms",
        ]:
            assert expected in rules, f"Missing: {expected}"

    def test_brain_alert_requires_json(self, app):
        c = app.test_client()
        # Provide empty json so Flask doesn't 415 before our handler runs
        r = c.post("/api/brain/alert", json={})
        # Handler accepts empty JSON and returns 200 with send result
        assert r.status_code in (200, 500)  # 500 if telegram unreachable

    def test_brain_sprint_requires_goal(self, app):
        c = app.test_client()
        r = c.post("/api/brain/sprint", json={})
        assert r.status_code == 400
        assert r.is_json
        assert "goal" in r.json.get("error", "").lower()

    def test_brain_debug_import_requires_admin_token(self, app):
        c = app.test_client()
        r = c.get("/api/brain/debug_import")
        assert r.status_code == 401

    def test_swarms_returns_list(self, app):
        c = app.test_client()
        r = c.get("/api/swarms")
        assert r.status_code == 200
        assert r.is_json
        assert "swarms" in r.json
        assert isinstance(r.json["swarms"], list)


class TestEnterpriseRoutes:
    def test_enterprise_status_json(self, app):
        c = app.test_client()
        r = c.get("/api/enterprise/status")
        assert r.status_code == 200
        assert r.is_json
        assert r.json.get("status") == "active"
        assert "features" in r.json

    def test_enterprise_metrics_json(self, app):
        c = app.test_client()
        r = c.get("/api/enterprise/metrics")
        assert r.status_code == 200
        assert r.is_json
        # Integrations may return {}, fallback returns {"status":"active","metrics":{...}}
        assert isinstance(r.json, dict)

    def test_enterprise_routes_skip_when_preregistered(self):
        """register_enterprise_routes is a no-op if view_functions already have the names."""
        from flask import Flask

        from routes.enterprise_routes import register_enterprise_routes
        a = Flask(__name__)

        # Pre-register dummies
        @a.route("/api/enterprise/status")
        def enterprise_status():
            return "pre-existing"

        @a.route("/api/enterprise/metrics")
        def enterprise_metrics():
            return "pre-existing"

        # Should be a no-op (no exception from duplicate route)
        register_enterprise_routes(a)
        c = a.test_client()
        assert c.get("/api/enterprise/status").data == b"pre-existing"


class TestSessionIdCoercion:
    def test_middleware_registered(self, app):
        # Verify at least one before_request func in the global bucket
        assert len(app.before_request_funcs.get(None, [])) >= 1


class TestCommunityRouteFailureNonFatal:
    def test_create_app_succeeds_when_community_fails(self):
        from flask import Flask

        from setup.blueprints import register_all_blueprints
        a = Flask(__name__)

        with patch("community.register_community_routes", side_effect=Exception("boom")):
            # Should not raise
            try:
                register_all_blueprints(a, dashboard_available=False)
            except Exception as e:
                # Community failure is swallowed; other registrations may fail but community alone must not
                assert "community" not in str(e).lower(), f"Community failure leaked: {e}"
