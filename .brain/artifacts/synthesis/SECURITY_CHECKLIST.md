# SECURITY CHECKLIST - GentleQuest 2026
## Security Review and Audit Procedures

**Purpose:** Ensure security best practices and audit readiness  
**Valid Until:** December 2026  
**Last Updated:** January 16, 2026

---

## 1. SECRETS MANAGEMENT

### ✅ Verified Practices
- [ ] No secrets in source code
- [ ] No secrets in git history
- [ ] `.env` in `.gitignore`
- [ ] `key.properties` in `.gitignore`
- [ ] Secrets stored in Render dashboard
- [ ] `sync: false` for secrets in render.yaml

### Current Secrets Inventory
| Secret | Location | Rotation Schedule |
|--------|----------|-------------------|
| GEMINI_API_KEY | Render Dashboard | Quarterly |
| OPENAI_API_KEY | Render Dashboard | Quarterly |
| PPLX_API_KEY | Render Dashboard | Quarterly |
| DATABASE_URL | Render Dashboard | On compromise |
| REDIS_URL | Render Dashboard | On compromise |
| SECRET_KEY | Render Dashboard | On compromise |
| ADMIN_API_TOKEN | Render Dashboard | Quarterly |

### Rotation Procedure
```bash
# 1. Generate new secret in provider dashboard
# 2. Update in Render environment
# 3. Deploy to apply
# 4. Verify functionality
# 5. Revoke old secret
```

---

## 2. AUTHENTICATION & SESSIONS

### ✅ Session Security
- [ ] Sessions stored server-side (Redis/filesystem)
- [ ] Session ID is UUID (not sequential)
- [ ] SECRET_KEY is strong (32+ chars)
- [ ] Session expiry configured (14 days)
- [ ] No session data in cookies (ID only)

### ⚠️ Current Limitations
- No user authentication (session-based only)
- No email/password login
- No OAuth integration

### Session Configuration
```python
# app.py
app.config['SESSION_TYPE'] = 'redis'  # or 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=14)
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JS access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

---

## 3. INPUT VALIDATION

### ✅ Validated Inputs
- [ ] Message content length limited
- [ ] Session ID format validated (UUID)
- [ ] Mood value range checked (1-10)
- [ ] Country code validated
- [ ] JSON parsing with error handling

### Validation Patterns
```python
# Session ID validation
import uuid
def is_valid_session_id(sid):
    try:
        uuid.UUID(sid)
        return True
    except ValueError:
        return False

# Message length
MAX_MESSAGE_LENGTH = 10000
if len(message) > MAX_MESSAGE_LENGTH:
    return jsonify({"error": "Message too long"}), 400

# Mood value
if not 1 <= mood_value <= 10:
    return jsonify({"error": "Invalid mood value"}), 400
```

---

## 4. RATE LIMITING

### ✅ Rate Limits Configured
| Endpoint | Limit | Key |
|----------|-------|-----|
| Global | 5000/day, 1000/hour | IP |
| /api/chat | 120/min | session_id |
| /api/mood/* | 120/min | session_id |
| /api/community/react | 20/min, 200/day | session_id |
| /api/community/report | 10/min, 100/day | session_id |

### Implementation
```python
from flask_limiter import Limiter
limiter = Limiter(
    key_func=lambda: request.json.get('session_id', request.remote_addr),
    default_limits=["5000 per day", "1000 per hour"]
)
```

---

## 5. CORS CONFIGURATION

### ✅ Allowed Origins
```python
CORS_ORIGINS = [
    "https://gentlequest.onrender.com",
    "https://gentlequest.com",
    "https://www.gentlequest.com",
    "https://gentlequest.app",
    "https://www.gentlequest.app",
    "https://app.gentlequest.app"
]
```

### ⚠️ Local Development
```python
if os.getenv('ENVIRONMENT') == 'development':
    CORS_ORIGINS.append("http://localhost:*")
```

---

## 6. DATABASE SECURITY

### ✅ Database Practices
- [ ] Connection via SSL (Render default)
- [ ] Connection string in environment variable
- [ ] No raw SQL (use SQLAlchemy ORM)
- [ ] Parameterized queries only
- [ ] No database credentials in logs

### SQL Injection Prevention
```python
# GOOD - Parameterized
db.session.execute(
    text("SELECT * FROM users WHERE id = :id"),
    {"id": user_id}
)

# BAD - String concatenation
# NEVER DO THIS
# f"SELECT * FROM users WHERE id = {user_id}"
```

---

## 7. API SECURITY

### ✅ HTTPS Enforcement
- [ ] HTTPS only in production
- [ ] HSTS header set
- [ ] Secure cookies

### Response Headers
```python
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    return response
```

---

## 8. ERROR HANDLING

### ✅ Safe Error Responses
- [ ] No stack traces in production
- [ ] No internal details in error messages
- [ ] Generic error messages to client
- [ ] Detailed logs server-side only

### Error Response Pattern
```python
@app.errorhandler(500)
def internal_error(error):
    # Log detailed error server-side
    app.logger.error(f"Internal error: {error}")
    
    # Return generic message to client
    return jsonify({
        "error": "Internal server error",
        "code": "INTERNAL_ERROR"
    }), 500
```

---

## 9. LOGGING & MONITORING

### ✅ Logging Practices
- [ ] No PII in logs
- [ ] No secrets in logs
- [ ] No full request bodies in logs
- [ ] Session IDs logged (for debugging)
- [ ] Error details logged server-side

### What to Log
```
✅ Request method, path, status code
✅ Session ID (anonymized)
✅ Error messages and stack traces
✅ Rate limit events
✅ AI provider fallbacks
❌ Full message content
❌ User personal data
❌ API keys or secrets
```

### Sentry Configuration
```python
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN_BACKEND'),
    traces_sample_rate=0,  # Disabled in prod
    send_default_pii=False  # No PII
)
```

---

## 10. DEPENDENCY SECURITY

### ✅ Dependency Practices
- [ ] Pin exact versions in requirements.txt
- [ ] Regular dependency updates
- [ ] Check for vulnerabilities

### Vulnerability Check
```bash
# Python
pip install safety
safety check -r requirements.txt

# Flutter
flutter pub outdated
```

### Known Vulnerabilities (as of Jan 2026)
| Package | Issue | Status |
|---------|-------|--------|
| urllib3 | LibreSSL warning | Informational |

---

## 11. DATA PRIVACY (GDPR/HIPAA Considerations)

### ✅ Data Minimization
- [ ] Only collect necessary data
- [ ] No IP addresses stored (currently)
- [ ] Messages retained 30 days max
- [ ] Sessions retained 14 days max

### ⚠️ Not Yet Implemented
- User data export endpoint
- User data deletion endpoint
- Consent management
- Privacy policy in app

### Data Retention
```python
MESSAGE_RETENTION_DAYS = 30
SESSION_RETENTION_DAYS = 14
ANALYTICS_RETENTION_DAYS = 90
ERROR_LOG_RETENTION_DAYS = 14
```

---

## 12. CRISIS DETECTION SECURITY

### ✅ Crisis Handling
- [ ] Keywords not logged
- [ ] User message content not stored in crisis logs
- [ ] Resources are country-specific
- [ ] No false information in resources

### Resource Verification
All crisis hotlines should be verified quarterly:
- IN: iCall (9152987821)
- US: 988 Lifeline
- UK: Samaritans (116 123)
- [etc.]

---

## 13. DEPLOYMENT SECURITY

### ✅ Deployment Practices
- [ ] No sensitive files in Docker image
- [ ] .dockerignore configured
- [ ] Build logs don't expose secrets
- [ ] Health check doesn't expose internals

### .dockerignore
```
.env
.env.*
*.secret
key.properties
.git
tests/
```

---

## 14. PRE-DEPLOYMENT CHECKLIST

### Before Every Deploy
- [ ] No secrets in code changes
- [ ] Tests pass
- [ ] No new high-severity vulnerabilities
- [ ] Rate limits appropriate
- [ ] Error handling in place

### Before Major Release
- [ ] Full security review
- [ ] Dependency audit
- [ ] Penetration test (if applicable)
- [ ] Crisis resources verified
- [ ] Backup verified

---

## 15. INCIDENT RESPONSE

### If Secrets Compromised
1. Rotate affected secrets immediately
2. Check logs for unauthorized access
3. Invalidate all sessions (if SECRET_KEY)
4. Deploy with new secrets
5. Document incident

### If Data Breach Suspected
1. Preserve logs
2. Identify scope
3. Notify affected users (if applicable)
4. Report to authorities (if required)
5. Post-mortem and fix

---

## SECURITY REVIEW SCHEDULE

| Review Type | Frequency | Next Due |
|-------------|-----------|----------|
| Secret rotation | Quarterly | Apr 2026 |
| Dependency audit | Monthly | Feb 2026 |
| Full security review | Quarterly | Apr 2026 |
| Crisis hotline verification | Quarterly | Apr 2026 |
