from app import create_app
from models import db
from sqlalchemy import text
import os

app = create_app()
with app.app_context():
    print(f"DB URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Root: {os.getcwd()}")
    try:
        res = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
        print(f"Tables: {[r[0] for r in res]}")
        
        # Check resources table
        if 'resources' in [r[0] for r in res]:
            count = db.session.execute(text("SELECT COUNT(*) FROM resources")).scalar()
            print(f"Resources count: {count}")
    except Exception as e:
        print(f"Error: {e}")
