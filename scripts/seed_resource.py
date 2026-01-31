
import sys
import os
from app import create_app
from models import db, Resource

app = create_app()

with app.app_context():
    # Check if resource 1 exists
    r = Resource.query.get(1)
    if not r:
        print("Seeding Resource ID 1...")
        r = Resource(
            id=1,
            title="Understanding Anxiety",
            description="A guide to managing anxiety symptoms.",
            url="https://example.com/anxiety",
            category="anxiety",
            country="us",
            tags="anxiety,help,guide",
            is_active=True
        )
        db.session.add(r)
        db.session.commit()
        print("✅ Resource 1 created.")
    else:
        print("ℹ️ Resource 1 already exists.")
