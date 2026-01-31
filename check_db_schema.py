from app import create_app
from models import db
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Tables found: {tables}")
    
    expected = ['quests', 'quest_progress', 'user_profiles']
    missing = [t for t in expected if t not in tables]
    
    if missing:
        print(f"❌ Missing tables: {missing}")
        exit(1)
    else:
        print("✅ All Quest tables present.")
        exit(0)
