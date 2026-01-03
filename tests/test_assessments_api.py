import pytest
import json
import sys
import os

# Allow import from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from unittest.mock import patch

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    # Use SQLite for tests unless ENV override
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    
    with app.test_client() as client:
        yield client

def test_get_phq9_questions(client):
    """Test fetching PHQ-9 questions"""
    response = client.get("/api/assessment/phq9/questions")
    assert response.status_code == 200
    data = response.get_json()
    assert data["type"] == "phq9"
    assert len(data["questions"]) == 9
    assert len(data["options"]) == 4

def test_get_gad7_questions(client):
    """Test fetching GAD-7 questions"""
    response = client.get("/api/assessment/gad7/questions")
    assert response.status_code == 200
    data = response.get_json()
    assert data["type"] == "gad7"
    assert len(data["questions"]) == 7

@patch('app.save_assessment_result')
def test_submit_phq9_success(mock_save, client):
    """Test successful PHQ-9 submission"""
    mock_save.return_value = 123
    payload = {
        "responses": [0, 1, 2, 3, 0, 1, 2, 3, 0]
    }
    response = client.post(
        "/api/assessment/phq9",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-Session-ID": "test_session_123"}
    )
    
    # If DB init failed, this might 500. Logic should handle it.
    # In sqlite memory, table init runs on startup.
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["assessment_type"] == "phq9"
    assert data["total_score"] == 12
    assert "id" in data
    assert data["severity"] == "moderate"

@patch('app.save_assessment_result')
def test_submit_gad7_success(mock_save, client):
    """Test successful GAD-7 submission"""
    mock_save.return_value = 456
    payload = {
        "responses": [3, 3, 3, 3, 3, 3, 3] # Max score
    }
    response = client.post(
        "/api/assessment/gad7",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-Session-ID": "test_session_456"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["assessment_type"] == "gad7"
    assert data["total_score"] == 21
    assert data["severity"] == "severe"

def test_submit_invalid_responses(client):
    """Test submission with wrong number of responses"""
    payload = {
        "responses": [0, 0] # Too few
    }
    response = client.post(
        "/api/assessment/phq9",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-Session-ID": "test_session_123"}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_submit_invalid_values(client):
    """Test submission with out of range values"""
    payload = {
        "responses": [0, 1, 2, 3, 0, 1, 2, 3, 5] # 5 is invalid
    }
    response = client.post(
        "/api/assessment/phq9",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-Session-ID": "test_session_123"}
    )
    assert response.status_code == 400

@patch('app.get_assessment_history')
@patch('app.save_assessment_result')
def test_assessment_history(mock_save, mock_get_history, client):
    """Test retrieving assessment history"""
    session_id = "history_user_1"
    
    # Mock history response
    mock_get_history.return_value = [{
        "id": 1,
        "assessment_type": "phq9",
        "total_score": 12,
        "severity": "moderate",
        "created_at": "2025-01-01T12:00:00"
    }]
    # Since we are mocking app.save_assessment_result, we mock it here too
    mock_save.return_value = 1
    
    # 1. Submit a result
    payload = {"responses": [0]*9}
    client.post(
        "/api/assessment/phq9",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-Session-ID": session_id}
    )
    
    # 2. Get history
    response = client.get(
        "/api/assessment/history",
        headers={"X-Session-ID": session_id}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert "history" in data
    assert len(data["history"]) >= 1
    assert data["history"][0]["assessment_type"] == "phq9"
