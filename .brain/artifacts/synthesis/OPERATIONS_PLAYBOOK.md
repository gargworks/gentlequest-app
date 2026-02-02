# OPERATIONS PLAYBOOK - GentleQuest 2026
## Deploy, Rollback, Debug, Monitor Procedures

**Purpose:** Step-by-step operational procedures for autonomous execution  
**Valid Until:** December 2026  
**Last Updated:** January 16, 2026

---

## 1. DEPLOYMENT PROCEDURES

### 1.1 Deploy to Render (Primary)

**Pre-flight Checklist:**
```bash
# 1. Verify local tests pass
cd /Users/lokeshgarg/ai-mvp-backend
python3 -m pytest tests/ -v

# 2. Verify Flutter web builds
cd ai_buddy_web
flutter build web --release

# 3. Check for uncommitted changes
git status
```

**Deploy Steps:**
```bash
# 1. Commit changes
git add .
git commit -m "feat: description of change"

# 2. Push to main (auto-deploys on Render)
git push origin main

# 3. Monitor deploy in Render dashboard
# URL: https://dashboard.render.com/
# Service: gentlequest (srv-d2r3i1fdiees73dqtov0)

# 4. Verify health endpoint
curl https://gentlequest.onrender.com/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "database": "connected",
  "redis": "connected"
}
```

### 1.2 Deploy to GCP Cloud Run (Alternative)

```bash
# Trigger Cloud Build
gcloud builds submit --config=cloudbuild.yaml

# Or manual deploy
gcloud run deploy gentlequest-backend \
  --image gcr.io/PROJECT_ID/gentlequest-backend \
  --region us-central1 \
  --allow-unauthenticated
```

### 1.3 Deploy Flutter Web Only

```bash
cd ai_buddy_web
flutter build web --release

# Copy to backend static folder (if serving from Flask)
cp -r build/web/* ../static/

# Commit and push
git add .
git commit -m "chore: update flutter web build"
git push origin main
```

---

## 2. ROLLBACK PROCEDURES

### 2.1 Rollback on Render

**Option A: Revert commit**
```bash
# Find last good commit
git log --oneline -10

# Revert to specific commit
git revert HEAD
git push origin main
```

**Option B: Render Dashboard**
1. Go to https://dashboard.render.com/
2. Select `gentlequest` service
3. Click "Deploys" tab
4. Find last successful deploy
5. Click "Redeploy" on that version

### 2.2 Database Rollback

**WARNING:** Database rollbacks are destructive. Take backup first.

```bash
# Connect to Render PostgreSQL
psql $DATABASE_URL

# Backup current state
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# If schema migration failed, restore:
psql $DATABASE_URL < backup_YYYYMMDD.sql
```

### 2.3 Emergency: Disable Feature

If a feature is causing issues, use feature flags:

```python
# In app.py, wrap problematic code:
if os.getenv('FEATURE_X_ENABLED', 'true') == 'true':
    # problematic code
else:
    # safe fallback
```

Then set `FEATURE_X_ENABLED=false` in Render environment.

---

## 3. DEBUGGING PROCEDURES

### 3.1 Debug Chat/AI Issues

**Symptoms:** AI not responding, wrong responses, timeouts

**Steps:**
```bash
# 1. Check AI provider status
curl https://gentlequest.onrender.com/api/health

# 2. Check Render logs
# Dashboard → gentlequest → Logs

# 3. Test AI provider directly
curl -X POST https://gentlequest.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "session_id": "debug-session"}'

# 4. Check API key validity
# Verify GEMINI_API_KEY in Render environment vars
```

**Common Fixes:**
- Rotate API key if quota exceeded
- Check failover chain: Gemini → OpenAI → Perplexity
- Increase timeout in `api_service.dart` (currently 30s)

### 3.2 Debug Database Issues

**Symptoms:** Data not saving, connection errors

```bash
# 1. Verify connection
psql $DATABASE_URL -c "SELECT 1;"

# 2. Check table existence
psql $DATABASE_URL -c "\dt"

# 3. Check recent errors
psql $DATABASE_URL -c "SELECT * FROM error_logs ORDER BY created_at DESC LIMIT 10;"

# 4. Verify connection pool
# Check Render logs for "connection pool exhausted"
```

**Common Fixes:**
- Restart service to reset connection pool
- Increase pool size in SQLAlchemy config
- Check for long-running queries

### 3.3 Debug Flutter/UI Issues

**Symptoms:** UI not updating, blank screens, crashes

```bash
# 1. Check browser console
# Open DevTools → Console tab

# 2. Check network requests
# DevTools → Network tab → filter by "api"

# 3. Rebuild with verbose logging
cd ai_buddy_web
flutter build web --release --dart-define=DEBUG=true

# 4. Check provider state
# Add debug prints in provider methods
```

**Common Fixes:**
- Clear browser cache (service worker)
- Check CORS configuration
- Verify API base URL in `api_config.dart`

### 3.4 Debug Rate Limiting

**Symptoms:** 429 errors, "Too many requests"

```bash
# 1. Check current limits
# In app.py: 5000/day, 1000/hour globally
# Chat/mood: 120/min

# 2. Check Redis for rate limit keys
redis-cli -u $REDIS_URL
KEYS "LIMITER:*"

# 3. Clear rate limit for session
redis-cli -u $REDIS_URL DEL "LIMITER:sid:SESSION_ID"
```

---

## 4. MONITORING PROCEDURES

### 4.1 Health Checks

**Endpoints to monitor:**
```
GET /api/health      → Overall health
GET /api/ping        → Lightweight keep-alive
GET /api/metrics     → Prometheus metrics
```

**Automated monitoring:**
- GitHub Actions workflow pings /api/ping every 13 mins
- Keeps Render free tier from sleeping

### 4.2 Log Analysis

**Render Logs Location:**
- Dashboard → gentlequest → Logs

**Key log patterns to watch:**
```
[ERROR] - Any error
[CRISIS] - Crisis detection triggered
[RATE_LIMIT] - Rate limit hit
[AI_FALLBACK] - Primary AI failed, using fallback
[DB_ERROR] - Database connection issue
```

### 4.3 Performance Metrics

**Key metrics:**
- Response time < 2s for chat
- Error rate < 1%
- AI fallback rate < 5%

**Prometheus endpoint:**
```
curl https://gentlequest.onrender.com/api/metrics
```

---

## 5. COMMON SCENARIOS

### 5.1 "Site is down"

```bash
# 1. Check Render status
# https://status.render.com/

# 2. Check if service is sleeping (free tier)
curl https://gentlequest.onrender.com/api/ping
# First request may take 30-60s to wake

# 3. Check deploy status in Render dashboard

# 4. If deploy failed, rollback to previous version
```

### 5.2 "AI responses are slow"

```bash
# 1. Check AI provider status
# https://status.openai.com/
# https://status.cloud.google.com/

# 2. Check if using fallback provider (slower)
# Look for [AI_FALLBACK] in logs

# 3. Consider increasing timeout or adding caching
```

### 5.3 "Users can't log in / sessions lost"

```bash
# 1. Check Redis connection
redis-cli -u $REDIS_URL ping

# 2. Check session configuration
# SESSION_RETENTION_DAYS=14

# 3. Verify SECRET_KEY hasn't changed
# Changing SECRET_KEY invalidates all sessions
```

### 5.4 "Database full / slow queries"

```bash
# 1. Check database size
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size(current_database()));"

# 2. Run retention cleanup
psql $DATABASE_URL -c "DELETE FROM messages WHERE created_at < NOW() - INTERVAL '30 days';"

# 3. Vacuum database
psql $DATABASE_URL -c "VACUUM ANALYZE;"
```

---

## 6. ENVIRONMENT QUICK REFERENCE

| Variable | Purpose | Where to Set |
|----------|---------|--------------|
| DATABASE_URL | PostgreSQL connection | Render Dashboard |
| REDIS_URL | Redis connection | Render Dashboard |
| GEMINI_API_KEY | Primary AI | Render Dashboard |
| OPENAI_API_KEY | Fallback AI | Render Dashboard |
| SECRET_KEY | Session encryption | Render Dashboard |
| SENTRY_DSN_BACKEND | Error tracking | Render Dashboard |

---

## 7. EMERGENCY CONTACTS

- **Render Status:** https://status.render.com/
- **Google Cloud Status:** https://status.cloud.google.com/
- **OpenAI Status:** https://status.openai.com/
- **Sentry Dashboard:** https://sentry.io/

---

## QUICK COMMANDS CHEATSHEET

```bash
# Deploy
git push origin main

# Check health
curl https://gentlequest.onrender.com/api/health

# View logs
# Render Dashboard → Logs

# Restart service
# Render Dashboard → Manual Deploy

# Database backup
pg_dump $DATABASE_URL > backup.sql

# Clear rate limits
redis-cli -u $REDIS_URL FLUSHDB

# Local development
cd /Users/lokeshgarg/ai-mvp-backend
python3 app.py  # Backend on :5055
cd ai_buddy_web && flutter run -d chrome  # Frontend
```
