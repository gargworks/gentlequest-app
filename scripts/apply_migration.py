import os
import sys

def get_db_url():
    """Get Database URL from env or default to local SQLite."""
    url = os.environ.get('DATABASE_URL')
    if not url:
        # Default to local instance db
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'instance', 'mental_health.db')
        return f"sqlite:///{db_path}"
    return url

def apply_migration(sql_file_path):
    database_url = get_db_url()
    
    print(f"Applying migration: {sql_file_path}")
    print(f"Target Database URL: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    
    with open(sql_file_path, 'r') as f:
        sql = f.read()

    if 'sqlite' in database_url.lower():
        import sqlite3
        db_path = database_url.replace('sqlite:///', '')
        print(f"Using SQLite: {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.executescript(sql)
            conn.commit()
            print("✅ Migration applied successfully using SQLite.")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "no such column" in str(e).lower():
                print(f"⚠️ Column already exists or table issue (ignored): {e}")
            else:
                print(f"❌ Migration failed: {e}")
                sys.exit(1)
        finally:
            if 'conn' in locals() and conn:
                conn.close()
                
    else:
        # PostgreSQL with psycopg (v3)
        dsn = database_url
        if dsn.startswith('postgres://'):
            dsn = dsn.replace('postgres://', 'postgresql://', 1)
            
        try:
            import psycopg
            print(f"Using PostgreSQL via psycopg.")
            
            with psycopg.connect(dsn) as conn:
                with conn.cursor() as cur:
                    try:
                        cur.execute(sql)
                        conn.commit()
                        print("✅ Migration applied successfully using PostgreSQL.")
                    except Exception as e:
                        if "duplicate column" in str(e).lower():
                            print(f"⚠️ Column already exists (ignored): {e}")
                            conn.rollback()
                        else:
                            raise e

        except ImportError:
            try:
                import psycopg2
                print(f"Using PostgreSQL via psycopg2.")
                conn = psycopg2.connect(dsn)
                cur = conn.cursor()
                try:
                    cur.execute(sql)
                    conn.commit()
                    print("✅ Migration applied successfully using PostgreSQL (psycopg2).")
                except Exception as e:
                    if "duplicate column" in str(e).lower():
                        print(f"⚠️ Column already exists (ignored): {e}")
                        conn.rollback()
                    else:
                        raise e
                finally:
                    cur.close()
                    conn.close()
            except ImportError:
                print("❌ psycopg or psycopg2 module not found. Please install one.")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python apply_migration.py <sql_file_path>")
        sys.exit(1)
        
    apply_migration(sys.argv[1])
