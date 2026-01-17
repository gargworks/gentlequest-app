"""
Seed university counselor contacts
Run with: python scripts/seed_counselors.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

# Example counselor data - UPDATE with real contacts before production
COUNSELORS = [
    {
        'university_id': 1,
        'name': 'Dr. Jane Smith',
        'email': 'jsmith@university.edu',
        'phone': '+12345678901',
        'role': 'Director, Counseling Services',
        'alert_methods': 'email,sms'
    },
    {
        'university_id': 1,
        'name': 'Dr. John Doe',
        'email': 'jdoe@university.edu',
        'phone': None,
        'role': 'Crisis Counselor',
        'alert_methods': 'email'
    },
]

def main():
    app = create_app()
    
    with app.app_context():
        # Check if counselors already exist
        existing_count = db.session.execute(
            text("SELECT COUNT(*) FROM university_counselors")
        ).scalar()
        
        if existing_count > 0:
            print(f"⚠️  {existing_count} counselors already exist. Skipping seed.")
            print("   To re-seed, delete existing counselors first.")
            return
        
        # Insert counselors
        for counselor in COUNSELORS:
            db.session.execute(
                text("""
                    INSERT INTO university_counselors 
                    (university_id, name, email, phone, role, alert_methods)
                    VALUES (:university_id, :name, :email, :phone, :role, :alert_methods)
                """),
                counselor
            )
        
        db.session.commit()
        print(f"✅ Seeded {len(COUNSELORS)} counselors")
        print()
        print("⚠️  IMPORTANT: Update counselor contacts with real information before production!")
        print()
        
        # Show what was created
        for counselor in COUNSELORS:
            print(f"  • {counselor['name']} ({counselor['role']})")
            print(f"    Email: {counselor['email']}, Methods: {counselor['alert_methods']}")

if __name__ == '__main__':
    main()
