from app import create_app
from models import db, Quest, QuestProgress, UserProfile

app = create_app()
with app.app_context():
    quests = Quest.query.all()
    print(f"Total Quests: {len(quests)}")
    for q in quests:
        print(f"  ID: {q.id}, Title: {q.title}, Type: {q.quest_type}")
    
    progress = QuestProgress.query.all()
    print(f"\nTotal Progress Entries: {len(progress)}")
    for p in progress:
        print(f"  SID: {p.session_id}, QID: {p.quest_id}, Status: {p.status}")

    profiles = UserProfile.query.all()
    print(f"\nTotal Profiles: {len(profiles)}")
    for pr in profiles:
        print(f"  SID: {pr.session_id}, XP: {pr.xp}, Level: {pr.level}")
