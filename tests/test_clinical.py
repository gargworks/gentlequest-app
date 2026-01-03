import sys
import os
import unittest
import json
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db, Config

class TestClinicalAssessments(unittest.TestCase):
    def setUp(self):
        # Patch Config to forcedly use SQLite
        # create_app uses Config.DATABASE_URL to set SQLALCHEMY_DATABASE_URI
        self.original_db_url = getattr(Config, 'DATABASE_URL', None)
        self.original_uri = getattr(Config, 'SQLALCHEMY_DATABASE_URI', None)
        
        Config.DATABASE_URL = 'sqlite:///:memory:'
        Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        Config.TESTING = True
        
        # Configure app for testing
        self.app = create_app()
        self.client = self.app.test_client()
        
        # Setup DB context
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        # Create all tables (in memory)
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        
        # Restore Config
        if self.original_db_url:
            Config.DATABASE_URL = self.original_db_url
        if self.original_uri:
            Config.SQLALCHEMY_DATABASE_URI = self.original_uri

    def test_phq9_flow(self):
        print("\n🧪 Testing PHQ-9 Flow...")
        
        # 1. Get Questions
        print("   GET /api/assessment/phq9/questions")
        rv = self.client.get('/api/assessment/phq9/questions')
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['questions']), 9)
        print("   ✅ Fetched 9 questions")

        # 2. Submit Assessment (Moderate Depression)
        print("   POST /api/assessment/phq9 (Score 15)")
        payload = {
            "session_id": "test-session-123",
            "responses": [2, 2, 1, 2, 1, 2, 2, 2, 1] # Sum = 15
        }
        rv = self.client.post('/api/assessment/phq9', json=payload)
        self.assertEqual(rv.status_code, 200)
        
        res = rv.get_json()
        print(f"   Response: {res}")
        self.assertTrue(res['success'])
        self.assertEqual(res['total_score'], 15)
        # API returns snake_case for severity identifiers
        self.assertIn("moderately_severe", res['severity'])
        print(f"   ✅ Score verified: {res['total_score']} ({res['severity']})")

    def test_gad7_flow(self):
        print("\n🧪 Testing GAD-7 Flow...")
        
        # 1. Get Questions
        print("   GET /api/assessment/gad7/questions")
        rv = self.client.get('/api/assessment/gad7/questions')
        self.assertEqual(rv.status_code, 200)
        
        # 2. Submit Assessment (Severe Anxiety)
        print("   POST /api/assessment/gad7 (Score 21)")
        payload = {
            "session_id": "test-session-123",
            "responses": [3] * 7 # Max score 21
        }
        rv = self.client.post('/api/assessment/gad7', json=payload)
        self.assertEqual(rv.status_code, 200)
        
        res = rv.get_json()
        print(f"   Response: {res}")
        self.assertEqual(res['total_score'], 21)
        self.assertEqual(res['severity'], "severe")
        print(f"   ✅ Score verified: {res['total_score']} ({res['severity']})")

if __name__ == '__main__':
    unittest.main()
