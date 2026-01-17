"""Comprehensive system status check"""
import sys
import os
import requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

def check_status():
    app = create_app()
    
    print("🔍 SYSTEM STATUS CHECK")
    print("=" * 80)
    
    # Database
    try:
        with app.app_context():
            db.session.execute(text("SELECT 1")).scalar()
        print("✅ Database: Connected")
    except Exception as e:
        print(f"❌ Database: {e}")
    
    # Redis
    try:
        with app.app_context():
            if app.config.get('SESSION_TYPE') == 'redis':
                redis_client = app.config.get('SESSION_REDIS')
                if redis_client:
                    redis_client.ping()
                    print("✅ Redis: Connected")
                else:
                    print("⚠️  Redis: Not configured")
            else:
                print("ℹ️  Redis: Using filesystem sessions")
    except Exception as e:
        print(f"⚠️  Redis: {e}")
    
    # AI Providers
    gemini_key = os.getenv('GEMINI_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    pplx_key = os.getenv('PPLX_API_KEY')
    
    print(f"{'✅' if gemini_key else '❌'} Gemini API Key: {'Set' if gemini_key else 'Not set'}")
    print(f"{'✅' if openai_key else '⚠️ '} OpenAI API Key: {'Set' if openai_key else 'Not set'}")
    print(f"{'✅' if pplx_key else '⚠️ '} Perplexity API Key: {'Set' if pplx_key else 'Not set'}")
    
    # SendGrid
    sendgrid_key = os.getenv('SENDGRID_API_KEY')
    print(f"{'✅' if sendgrid_key else '⚠️ '} SendGrid: {'Configured' if sendgrid_key else 'Not configured'}")
    
    # Twilio
    twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
    print(f"{'✅' if twilio_sid else 'ℹ️ '} Twilio: {'Configured' if twilio_sid else 'Not configured (optional)'}")
    
    # Health endpoint
    try:
        response = requests.get('http://localhost:5055/api/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Endpoint: {data.get('status', 'unknown')}")
        else:
            print(f"⚠️  Health Endpoint: HTTP {response.status_code}")
    except Exception as e:
        print(f"⚠️  Health Endpoint: {e}")
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    check_status()
