"""Check migration status"""
import subprocess
import sys

def check_migrations():
    print("🗄️  MIGRATION STATUS")
    print("=" * 80)
    
    try:
        # Check current version
        result = subprocess.run(['alembic', 'current'], capture_output=True, text=True)
        print("Current version:")
        print(result.stdout)
        
        # Check history
        result = subprocess.run(['alembic', 'history'], capture_output=True, text=True)
        print("\nMigration history:")
        print(result.stdout)
        
        # Check if migrations needed
        result = subprocess.run(['alembic', 'check'], capture_output=True, text=True)
        if result.returncode == 0:
            print("\n✅ Database is up to date")
        else:
            print("\n⚠️  Migrations needed")
            print(result.stdout)
        
    except Exception as e:
        print(f"❌ Error checking migrations: {e}")
        return False
    
    print("=" * 80)
    return True

if __name__ == '__main__':
    success = check_migrations()
    sys.exit(0 if success else 1)
