"""Load university configuration from JSON"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

def load_university_config(config_file):
    """Load university configuration from JSON file"""
    app = create_app()
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    with app.app_context():
        # Insert university
        db.session.execute(text("""
            INSERT INTO universities (id, name, domain, caps_email, caps_phone, waitlist_weeks, enrollment)
            VALUES (:id, :name, :domain, :email, :phone, :waitlist, :enrollment)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                caps_email = EXCLUDED.caps_email,
                caps_phone = EXCLUDED.caps_phone
        """), {
            'id': config['university_id'],
            'name': config['name'],
            'domain': config['domain'],
            'email': config['caps_contact']['email'],
            'phone': config['caps_contact']['phone'],
            'waitlist': config['waitlist']['average_weeks'],
            'enrollment': config['enrollment']
        })
        
        # Insert counselors
        for counselor in config['counselors']:
            db.session.execute(text("""
                INSERT INTO university_counselors (university_id, name, email, phone, role, alert_methods)
                VALUES (:uid, :name, :email, :phone, :role, :methods)
            """), {
                'uid': config['university_id'],
                'name': counselor['name'],
                'email': counselor['email'],
                'phone': counselor.get('phone'),
                'role': counselor['role'],
                'methods': ','.join(counselor['alert_methods'])
            })
        
        # Insert crisis resources
        for resource in config['crisis_resources']:
            db.session.execute(text("""
                INSERT INTO resources (title, description, url, category, university_id)
                VALUES (:title, :desc, :url, :category, :uid)
            """), {
                'title': resource['name'],
                'desc': resource.get('hours', resource.get('available', '')),
                'url': resource.get('url', resource.get('phone', '')),
                'category': resource['type'],
                'uid': config['university_id']
            })
        
        db.session.commit()
        print(f"✅ Loaded configuration for {config['name']}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/load_university_config.py config/university_configs/umich.json")
        sys.exit(1)
    
    load_university_config(sys.argv[1])
