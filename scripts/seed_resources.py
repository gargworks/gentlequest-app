from app import create_app
from models import db, Resource

def seed_resources():
    app = create_app()
    with app.app_context():
        print("🌱 Seeding Resources...")
        
        # 1. Define Initial Content (Generic & High Impact)
        resources_data = [
            # Crisis Support
            {
                "title": "988 Suicide & Crisis Lifeline",
                "description": "24/7, free and confidential support for people in distress. Call or text 988.",
                "url": "https://988lifeline.org",
                "category": "crisis",
                "country": "USA",
                "tags": "crisis,suicide,help,urgent"
            },
            {
                "title": "Crisis Text Line",
                "description": "Text HOME to 741741 to connect with a Crisis Counselor.",
                "url": "https://www.crisistextline.org",
                "category": "crisis",
                "country": "USA",
                "tags": "crisis,text,anxiety,depression"
            },
            
            # CBT / Self-Help
            {
                "title": "Unboxing Your Thoughts (CBT Basics)",
                "description": "A beginner's guide to Cognitive Behavioral Therapy. Learn how to identify and challenge negative thought patterns.",
                "url": "https://www.apa.org/ptsd-guideline/patients-and-families/cognitive-behavioral",
                "category": "self_help",
                "tags": "cbt,thoughts,anxiety,basics"
            },
            {
                "title": "Sleep Hygiene 101",
                "description": "Evidence-based tips to improve your sleep quality. Quality sleep is the foundation of mental health.",
                "url": "https://www.sleepfoundation.org/sleep-hygiene",
                "category": "self_help",
                "tags": "sleep,insomnia,health,wellness"
            },
            {
                "title": "Box Breathing Guide",
                "description": "A simple, powerful technique to regain calm. Inhale 4s, Hold 4s, Exhale 4s, Hold 4s.",
                "url": "https://health.clevelandclinic.org/box-breathing-benefits/",
                "category": "self_help",
                "tags": "anxiety,breathing,panic,calm"
            },
            {
                "title": "5-4-3-2-1 Grounding Technique",
                "description": "Stop a panic attack in its tracks by engaging your five senses.",
                "url": "https://www.mayoclinichealthsystem.org/hometown-health/speaking-of-health/5-4-3-2-1-grounding-technique",
                "category": "self_help",
                "tags": "grounding,panic,anxiety,senses"
            },
            
            # Productivity / ADHD
            {
                "title": "Pomodoro Technique for ADHD",
                "description": "How to use 25-minute focus bursts to overcome executive dysfunction.",
                "url": "https://todoist.com/productivity-methods/pomodoro-technique",
                "category": "productivity",
                "tags": "adhd,focus,work,study"
            },
            {
                "title": "Body Doubling Explained",
                "description": "Why working alongside someone else helps you get things done.",
                "url": "https://add.org/body-doubling-adhd/",
                "category": "productivity",
                "tags": "adhd,body_doubling,motivation"
            }
        ]
        
        count = 0
        for r_data in resources_data:
            # Check for generic duplicates (by title)
            exists = Resource.query.filter_by(title=r_data['title']).first()
            if not exists:
                resource = Resource(
                    title=r_data['title'],
                    description=r_data['description'],
                    url=r_data['url'],
                    category=r_data['category'],
                    country=r_data.get('country'),
                    tags=r_data['tags']
                )
                db.session.add(resource)
                count += 1
            else:
                print(f"   Skipping '{r_data['title']}' (already exists)")
        
        db.session.commit()
        print(f"✅ Successfully seeded {count} new resources.")

if __name__ == "__main__":
    seed_resources()
