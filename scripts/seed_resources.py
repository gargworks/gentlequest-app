"""
Seed initial resources for GentleQuest
Run with: python scripts/seed_resources.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

RESOURCES = [
    {
        'title': 'National Suicide Prevention Lifeline',
        'description': '24/7 crisis support. Call 988 or chat online for immediate help.',
        'url': 'https://988lifeline.org',
        'category': 'crisis',
        'country': 'us',
        'tags': 'crisis,suicide,24/7,hotline'
    },
    {
        'title': 'Crisis Text Line',
        'description': 'Text HOME to 741741 for 24/7 crisis support via text message.',
        'url': 'https://www.crisistextline.org',
        'category': 'crisis',
        'country': 'us',
        'tags': 'crisis,text,24/7,support'
    },
    {
        'title': 'Understanding Anxiety',
        'description': 'Learn about anxiety symptoms, causes, and evidence-based coping strategies from NIMH.',
        'url': 'https://www.nimh.nih.gov/health/topics/anxiety-disorders',
        'category': 'self_help',
        'country': None,
        'tags': 'anxiety,education,coping,nimh'
    },
    {
        'title': 'Sleep Hygiene Tips',
        'description': 'Evidence-based strategies for better sleep quality and healthy sleep habits.',
        'url': 'https://www.sleepfoundation.org/sleep-hygiene',
        'category': 'self_help',
        'country': None,
        'tags': 'sleep,wellness,tips,hygiene'
    },
    {
        'title': 'Cognitive Distortions Guide',
        'description': 'Identify and challenge unhelpful thinking patterns like catastrophizing and all-or-nothing thinking.',
        'url': None,
        'category': 'self_help',
        'country': None,
        'tags': 'cbt,thinking,mental-health,distortions'
    },
    {
        'title': 'Breathing Exercises for Anxiety',
        'description': 'Quick breathing techniques to reduce stress and anxiety in moments of overwhelm.',
        'url': None,
        'category': 'self_help',
        'country': None,
        'tags': 'breathing,relaxation,stress,anxiety'
    },
    {
        'title': 'Grounding Techniques',
        'description': '5-4-3-2-1 and other grounding exercises to manage anxiety and panic attacks.',
        'url': None,
        'category': 'self_help',
        'country': None,
        'tags': 'grounding,anxiety,techniques,panic'
    },
    {
        'title': 'Journaling for Mental Health',
        'description': 'How to use journaling to process emotions, reduce stress, and gain clarity.',
        'url': None,
        'category': 'self_help',
        'country': None,
        'tags': 'journaling,writing,coping,emotions'
    },
    {
        'title': 'Progressive Muscle Relaxation',
        'description': 'Step-by-step guide to PMR for stress reduction and better sleep.',
        'url': None,
        'category': 'self_help',
        'country': None,
        'tags': 'relaxation,stress,body,sleep'
    },
    {
        'title': 'Mindfulness Basics',
        'description': 'Introduction to mindfulness meditation for beginners - simple practices for daily life.',
        'url': None,
        'category': 'self_help',
        'country': None,
        'tags': 'mindfulness,meditation,beginner,practice'
    },
]

def main():
    app = create_app()
    
    with app.app_context():
        # Check if resources already exist
        existing_count = db.session.execute(
            text("SELECT COUNT(*) FROM resources")
        ).scalar()
        
        if existing_count > 0:
            print(f"⚠️  {existing_count} resources already exist. Skipping seed.")
            print("   To re-seed, delete existing resources first.")
            return
        
        # Insert resources
        for resource in RESOURCES:
            db.session.execute(
                text("""
                    INSERT INTO resources (title, description, url, category, country, tags)
                    VALUES (:title, :description, :url, :category, :country, :tags)
                """),
                resource
            )
        
        db.session.commit()
        print(f"✅ Seeded {len(RESOURCES)} resources")
        print()
        
        # Show what was created
        for resource in RESOURCES:
            print(f"  • {resource['title']} ({resource['category']})")

if __name__ == '__main__':
    main()
