import os
import sys
from sqlalchemy import text

# Add parent directory to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

def enable_vector_extension():
    app = create_app()
    with app.app_context():
        try:
            print(f"Connecting to database: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1]}") # Log host only for safety
            print("Attempting to enable vector extension...")
            # We use text() for raw SQL
            db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            db.session.commit()
            print("Successfully enabled vector extension.")
            
            # Verify
            result = db.session.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector';"))
            if result.fetchone():
                print("Verification successful: 'vector' extension is present.")
            else:
                print("Verification failed: 'vector' extension not found after creation.")
                
        except Exception as e:
            print(f"Error enabling vector extension: {e}")
            sys.exit(1)

if __name__ == "__main__":
    enable_vector_extension()
