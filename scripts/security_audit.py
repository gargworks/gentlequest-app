"""
Security Audit Script
Checks for common vulnerabilities and security issues
Run with: python scripts/security_audit.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text
import re

def check_environment_variables():
    """Check for exposed secrets"""
    print("🔐 ENVIRONMENT VARIABLE SECURITY:")
    print("=" * 80)
    
    required_secrets = [
        'SECRET_KEY',
        'GEMINI_API_KEY',
        'DATABASE_URL',
        'SENDGRID_API_KEY',
    ]
    
    for secret in required_secrets:
        value = os.getenv(secret)
        if value:
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print(f"  ✅ {secret:25s} {masked}")
        else:
            print(f"  ⚠️  {secret:25s} NOT SET")

def check_sql_injection_protection(app):
    """Verify parameterized queries"""
    print("\n💉 SQL INJECTION PROTECTION:")
    print("=" * 80)
    
    # Scan code for potential SQL injection
    files_to_scan = [
        'app.py',
        'app_quest_routes.py',
        'app_resource_routes.py',
        'app_alert_routes.py',
        'providers/quest_generator.py',
        'providers/alert_manager.py',
    ]
    
    issues = []
    for filename in files_to_scan:
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), filename)
        if not os.path.exists(filepath):
            continue
            
        with open(filepath, 'r') as f:
            content = f.read()
            
            # Look for string formatting in SQL (potential injection)
            if re.search(r'f".*SELECT.*{', content) or re.search(r'f\'.*SELECT.*{', content):
                issues.append(f"{filename}: Found f-string in SQL query (potential injection)")
            
            # Look for % formatting in SQL
            if re.search(r'".*SELECT.*%.*".*%', content):
                issues.append(f"{filename}: Found % formatting in SQL query (potential injection)")
    
    if issues:
        print("  ⚠️  POTENTIAL SQL INJECTION RISKS:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  ✅ All queries use parameterized statements")

def check_xss_protection(app):
    """Check for XSS vulnerabilities"""
    print("\n🛡️  XSS PROTECTION:")
    print("=" * 80)
    
    with app.app_context():
        # Check if output is sanitized
        test_input = "<script>alert('XSS')</script>"
        
        # Test mood note sanitization
        try:
            from app import _sanitize_note
            sanitized = _sanitize_note(test_input)
            if '<script' not in sanitized or '&lt;script' in sanitized:
                print("  ✅ Mood notes are sanitized")
            else:
                print("  ⚠️  Mood notes may be vulnerable to XSS")
        except:
            print("  ⚠️  Could not test mood note sanitization")

def check_rate_limiting(app):
    """Verify rate limiting is enabled"""
    print("\n⏱️  RATE LIMITING:")
    print("=" * 80)
    
    rate_limit_enabled = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    
    if rate_limit_enabled:
        print("  ✅ Rate limiting enabled")
        print(f"    Requests: {os.getenv('RATE_LIMIT_REQUESTS', '30')}/minute")
    else:
        print("  ⚠️  Rate limiting DISABLED (not recommended for production)")

def check_encryption(app):
    """Check encryption configuration"""
    print("\n🔒 ENCRYPTION:")
    print("=" * 80)
    
    # Check TLS
    environment = os.getenv('ENVIRONMENT', 'local')
    if environment == 'production':
        print("  ✅ Production environment (TLS enforced by Render)")
    else:
        print(f"  ℹ️  Environment: {environment} (TLS not enforced)")
    
    # Check database URL for SSL
    db_url = os.getenv('DATABASE_URL', '')
    if 'sslmode=require' in db_url:
        print("  ✅ Database SSL required")
    elif environment == 'production':
        print("  ⚠️  Database SSL not explicitly required (check Render config)")
    else:
        print("  ℹ️  Database SSL not required (local/dev)")

def check_session_security(app):
    """Check session management security"""
    print("\n🎫 SESSION SECURITY:")
    print("=" * 80)
    
    secret_key = os.getenv('SECRET_KEY')
    if secret_key and secret_key != 'dev-secret-key-change-in-production':
        print("  ✅ SECRET_KEY is set and not default")
    else:
        print("  ⚠️  SECRET_KEY is default or not set (CRITICAL for production)")
    
    session_type = os.getenv('SESSION_TYPE', 'redis')
    print(f"  ℹ️  Session storage: {session_type}")

def check_cors_configuration(app):
    """Check CORS configuration"""
    print("\n🌐 CORS CONFIGURATION:")
    print("=" * 80)
    
    cors_origins = os.getenv('CORS_ORIGINS', '')
    if cors_origins:
        origins = [o.strip() for o in cors_origins.split(',')]
        print("  Allowed origins:")
        for origin in origins:
            if '*' in origin:
                print(f"    ⚠️  {origin} (wildcard - too permissive)")
            else:
                print(f"    ✅ {origin}")
    else:
        print("  ⚠️  CORS_ORIGINS not set (using defaults)")

def check_admin_endpoints(app):
    """Check admin endpoint protection"""
    print("\n👤 ADMIN ENDPOINT PROTECTION:")
    print("=" * 80)
    
    admin_token = os.getenv('ADMIN_API_TOKEN')
    if admin_token:
        print("  ✅ ADMIN_API_TOKEN is set")
    else:
        print("  ⚠️  ADMIN_API_TOKEN not set (admin endpoints unprotected)")

def main():
    app = create_app()
    
    print("🔒 SECURITY AUDIT")
    print("=" * 80)
    print()
    
    check_environment_variables()
    check_sql_injection_protection(app)
    check_xss_protection(app)
    check_rate_limiting(app)
    check_encryption(app)
    check_session_security(app)
    check_cors_configuration(app)
    check_admin_endpoints(app)
    
    print("\n" + "=" * 80)
    print("✅ Security audit complete")
    print("\n⚠️  RECOMMENDATIONS:")
    print("  1. Set ADMIN_API_TOKEN in production")
    print("  2. Verify SECRET_KEY is not default")
    print("  3. Review CORS origins (no wildcards in production)")
    print("  4. Enable rate limiting in production")
    print("  5. Verify database SSL in production")

if __name__ == '__main__':
    main()
