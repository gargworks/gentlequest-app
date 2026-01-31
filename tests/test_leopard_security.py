"""
Security Test Suite for Leopard (Hidden Mode)
Ensures that the "High Status" features remain hidden from standard users/API calls.
"""
import pytest
import json
import os
import sys

# Ensure the project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app

@pytest.fixture
def app():
    """Create test application"""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'RATE_LIMIT_ENABLED': False
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

class TestLeopardSecurity:
    """Security tests for the hidden Leopard mode"""

    def test_default_profile_does_not_leak_leopard(self, client):
        """Standard profile fetch should NOT return leopard status/unlock info"""
        # Create a session
        session_resp = client.get('/api/get_or_create_session')
        session_id = json.loads(session_resp.data)['session_id']
        headers = {'X-Session-ID': session_id}

        # Get profile
        response = client.get('/api/user/profile', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)

        # SECURITY ASSERTIONS
        # 1. No 'leopard_check' field
        assert 'leopard_mode' not in data
        assert 'is_high_status' not in data
        # 2. No weird metadata leaking
        assert 'leopard_unlock_date' not in data.get('metadata', {})

    def test_resources_do_not_contain_leopard_assets(self, client):
        """Resource list should NOT show 'High Status' or 'Protocol' items"""
        session_resp = client.get('/api/get_or_create_session')
        session_id = json.loads(session_resp.data)['session_id']
        headers = {'X-Session-ID': session_id}

        response = client.get('/api/resources', headers=headers)
        if response.status_code == 200:
            data = json.loads(response.data)
            for resource in data.get('resources', []):
                # Ensure no restricted tags leak
                tags = resource.get('tags', [])
                assert 'leopard' not in tags
                assert 'high_status' not in tags

    def test_gate_endpoint_security(self, client):
        """Hypothetical restricted endpoint - ensures 404/403 if it ever existed"""
        # This confirms we haven't accidentally exposed a management route
        response = client.get('/api/leopard/status')
        # Should be 404 because it shouldn't exist in the public API
        assert response.status_code == 404
