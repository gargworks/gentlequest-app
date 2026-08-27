# Production Deployment Checklist
## Pre-Launch, Launch Day, Post-Launch

## Pre-Launch (1 Week Before)

### Code Readiness
- [ ] All tests passing (`make test`)
- [ ] Code reviewed (self-review or peer)
- [ ] No critical bugs (P0/P1 issues resolved)
- [ ] Performance benchmarks met (AI <3s, API <500ms)
- [ ] Security scan clean (`python scripts/security_audit.py`)

### Database Readiness
- [ ] Migrations tested locally
- [ ] Seed data prepared (quests, resources, counselors)
- [ ] Backup strategy configured (`scripts/backup_database.sh`)
- [ ] Indexes created (`scripts/database_optimization.sql`)

### Environment Configuration
- [ ] All environment variables set in Render
- [ ] SECRET_KEY is not default
- [ ] SENDGRID_API_KEY configured (for alerts)
- [ ] CORS_ORIGINS restricted to production domains
- [ ] Rate limiting enabled

### Monitoring Setup
- [ ] Health check endpoint working (`/api/health`)
- [ ] Error tracking configured (Sentry optional)
- [ ] Alert thresholds set (error rate >5%, response time >5s)
- [ ] Daily health check cron job scheduled

### Documentation
- [ ] README updated (setup instructions)
- [ ] API documentation current
- [ ] Deployment guide reviewed
- [ ] Rollback procedure documented

## Launch Day

### Morning (9am-12pm)

**T-60min: Final Checks**
- [ ] Run validation: `./scripts/validate_deployment.sh`
- [ ] Verify tests pass: `make test`
- [ ] Check environment variables in Render
- [ ] Backup current database: `make backup`

**T-30min: Deploy**
- [ ] Run deployment script: `make deploy`
- [ ] Monitor Render logs (watch for errors)
- [ ] Wait for deployment complete (~3-5 minutes)

**T-0: Verify Deployment**
- [ ] Health check: `curl https://gentlequest.onrender.com/api/health`
- [ ] Smoke tests: `./scripts/validate_deployment.sh`
- [ ] Test critical paths (chat, mood, quests, resources, crisis)

### Afternoon (12pm-5pm)

**Hour 1-2: Initialize Production**
- [ ] Run migrations: `alembic upgrade head` (in Render Shell)
- [ ] Seed data: `python scripts/seed_quests.py` (in Render Shell)
- [ ] Seed resources: `python scripts/seed_resources.py`
- [ ] Configure counselors: Update and run `scripts/seed_counselors.py`
- [ ] Test crisis alerts: `python scripts/test_crisis_alerts.py`

**Hour 3-4: Monitor**
- [ ] Check error rate (should be <1%)
- [ ] Check response time (AI <3s, API <500ms)
- [ ] Test user flows (signup, chat, mood, quests)
- [ ] Verify crisis detection (send test message with keyword)

**Hour 5: First Outreach**
- [ ] Send first 5 outreach emails (test email system)
- [ ] Monitor email delivery (SendGrid dashboard)
- [ ] Track responses (HubSpot CRM)

### Evening (5pm-8pm)

**Final Monitoring**
- [ ] Review logs (any errors, warnings?)
- [ ] Check metrics (DAU, messages sent, crisis events)
- [ ] Verify backups running
- [ ] Document any issues

## Post-Launch (Week 1)

### Daily Tasks (Every Morning)
- [ ] Health check: `python scripts/daily_health_check.py`
- [ ] Review logs (errors, warnings, crisis events)
- [ ] Check pending alerts (CAPS dashboard)
- [ ] Monitor engagement (DAU, WAU)
- [ ] Test critical paths (chat, crisis detection)

### Week 1 Checklist
- [ ] Day 1: Monitor closely (hourly checks)
- [ ] Day 2: Review Day 1 data (any issues?)
- [ ] Day 3: Send 10 more outreach emails
- [ ] Day 4: Monitor engagement trends
- [ ] Day 5: Weekly report (if any pilots active)
- [ ] Day 6-7: Weekend monitoring (lighter, but check daily)

### Week 1 Metrics to Watch
- **Error Rate:** Target <1% (if >5%, investigate immediately)
- **Response Time:** AI <3s p95, API <500ms p95
- **Crisis Detection:** 100% (if any missed, CRITICAL issue)
- **User Signups:** Track from outreach emails
- **Engagement:** 40%+ weekly active (if pilots active)

## Emergency Procedures

### If Service Down
1. Check Render status (service running?)
2. Check logs (what error?)
3. Rollback if needed: `make rollback`
4. Notify users (if downtime >1 hour)

### If Crisis Alert Fails
1. Verify student safe (call CAPS immediately)
2. Investigate root cause (logs, SendGrid, Twilio)
3. Deploy hotfix (within 24 hours)
4. Notify all partners (transparency)

### If Data Breach
1. Isolate affected systems
2. Call lawyer (don't respond publicly)
3. Notify affected users (within 72 hours)
4. File insurance claim

## Success Criteria

**Launch Day:**
- ✅ Deployment successful (no rollback needed)
- ✅ All smoke tests pass
- ✅ Zero critical errors
- ✅ Crisis detection working (100%)

**Week 1:**
- ✅ Uptime >99% (< 1 hour downtime)
- ✅ Error rate <1%
- ✅ Response time <3s p95
- ✅ First outreach emails sent (10+)
- ✅ Zero crisis events missed

**Month 1:**
- ✅ First discovery calls (5+)
- ✅ First pilot proposals (2+)
- ✅ First pilot launched (1)
- ✅ System stable (no major issues)

**Deployment checklist complete. Pre-launch (1 week): Code, database, environment, monitoring, documentation. Launch day: Final checks, deploy, verify, initialize, monitor, first outreach. Post-launch (Week 1): Daily health checks, log review, engagement monitoring, weekly report. Emergency procedures: Service down (rollback), crisis alert fails (investigate, hotfix), data breach (isolate, notify). Success criteria: Launch day (deployment successful, smoke tests pass), Week 1 (uptime >99%, error <1%, response <3s), Month 1 (discovery calls, pilots, stable system).**
