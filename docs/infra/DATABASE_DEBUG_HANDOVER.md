# GentleQuest Database Debugging Guide
> **Authoritative Reference** — All context extracted from prior debugging session  
> **Last Updated:** 2026-01-15

---

## 1. System Context

### Application
**GentleQuest** — AI-powered mental health companion app

### Architecture
```
Flutter Web → Nginx → Gunicorn/Flask → Cloud SQL PostgreSQL
                                     ↘ Gemini LLM (Chat)
                                     ↘ pgvector (Memory)
```

### Infrastructure
| Component | Value |
|:----------|:------|
| **Cloud Project** | `gen-lang-client-0894185576` |
| **Region** | `us-central1` |
| **Cloud SQL Instance** | `gentlequest-db` (PostgreSQL 15) |
| **Database Name** | `gentlequest` |
| **Database User** | `gentlequest` |
| **Expected Password** | `gentlequest2026` |
| **Cloud Run Service** | `gentlequest-backend` |
| **Public URL** | `https://app.gentlequest.app` |

---

## 2. Credential Management

### DATABASE_URL Format
```
postgresql://gentlequest:gentlequest2026@/gentlequest?host=/cloudsql/gen-lang-client-0894185576:us-central1:gentlequest-db
```

**Components:**
- `postgresql://` — Driver prefix
- `gentlequest:gentlequest2026` — `user:password`
- `@/gentlequest` — Database name (Unix socket, no host)
- `?host=/cloudsql/...` — Cloud SQL socket path

### Where Credentials Are Set

| Location | Purpose | Notes |
|:---------|:--------|:------|
| `cloudbuild.yaml:42` | CI/CD deployment | ⚠️ Password hardcoded here |
| Cloud Run env vars | Runtime | Set via `gcloud run services update` |
| Cloud SQL user table | Database auth | Reset via Cloud Console or `gcloud sql users` |

---

## 3. Known Issue History

### Issue #1: Password Mismatch
- **Symptom:** `FATAL: password authentication failed for user 'gentlequest'`
- **Root Cause:** Cloud SQL user password didn't match `DATABASE_URL` in Cloud Run
- **Fix:** Reset Cloud SQL password to match env var

### Issue #2: DATABASE_URL Overwritten
- **Symptom:** `tables_initialized: false`, session history errors
- **Root Cause:** `gcloud run services update --set-env-vars KEY=VALUE` **replaces ALL vars**
- **Fix:** Always set all env vars together:
  ```bash
  gcloud run services update gentlequest-backend \
    --set-env-vars "ENVIRONMENT=production,DATABASE_URL=...,GEMINI_API_KEY=..."
  ```

### Issue #3: Frontend Proxy 503
- **Symptom:** `nucleus-hud` API calls return 503
- **Root Cause:** Next.js rewrite defaulted to `localhost`
- **Fix:** Set `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_APP_API_URL` env vars

---

## 4. Step-by-Step Debugging Plan

### Step 1: Verify Health Endpoint
```bash
curl https://app.gentlequest.app/api/health
```

**Expected:** `{"status": "healthy", "database": "healthy"}`

**If database is unhealthy → Continue to Step 2**

---

### Step 2: Check Cloud Run Logs
```bash
gcloud run services logs read gentlequest-backend \
  --region us-central1 --limit 50
```

**Look for:**
- `FATAL: password authentication failed for user 'gentlequest'`
- `could not connect to server`
- `timeout expired`

---

### Step 3: Verify Environment Variables
```bash
gcloud run services describe gentlequest-backend \
  --region us-central1 \
  --format='yaml(spec.template.spec.containers[0].env)'
```

**Confirm:**
- [ ] `DATABASE_URL` is present
- [ ] `DATABASE_URL` contains correct password
- [ ] `ENVIRONMENT=production`
- [ ] `GEMINI_API_KEY` is set

---

### Step 4: Test Cloud SQL Connectivity
```bash
# List users
gcloud sql users list --instance=gentlequest-db

# Describe instance
gcloud sql instances describe gentlequest-db --format='yaml(connectionName)'
```

**Verify:** `connectionName` = `gen-lang-client-0894185576:us-central1:gentlequest-db`

---

### Step 5: Reset Cloud SQL Password (If Needed)
```bash
gcloud sql users set-password gentlequest \
  --instance=gentlequest-db \
  --password=gentlequest2026
```

> ⚠️ **CRITICAL:** Ensure this matches `cloudbuild.yaml` line 42

---

### Step 6: Restore All Env Vars (If Overwritten)
```bash
gcloud run services update gentlequest-backend \
  --region us-central1 \
  --set-env-vars 'ENVIRONMENT=production,DATABASE_URL=postgresql://gentlequest:gentlequest2026@/gentlequest?host=/cloudsql/gen-lang-client-0894185576:us-central1:gentlequest-db,GEMINI_API_KEY=YOUR_KEY_HERE'
```

---

### Step 7: Verify Recovery
```bash
# Check health
curl https://app.gentlequest.app/api/health

# Check memory
curl https://app.gentlequest.app/api/memory/status

# Check chat
curl -X POST https://app.gentlequest.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello"}'
```

---

## 5. Quick Reference Commands

| Action | Command |
|:-------|:--------|
| Check health | `curl https://app.gentlequest.app/api/health` |
| View logs | `gcloud run services logs read gentlequest-backend --region us-central1` |
| List env vars | `gcloud run services describe gentlequest-backend --region us-central1 --format='yaml(spec.template.spec.containers[0].env)'` |
| Reset SQL password | `gcloud sql users set-password gentlequest --instance=gentlequest-db --password=gentlequest2026` |
| Redeploy | `gcloud builds submit --config=cloudbuild.yaml` |

---

## 6. Current Status (2026-01-15 18:00 IST)

| Service | Status | Revision | Last Verified |
|:--------|:-------|:---------|:--------------|
| `gentlequest-backend` | ✅ Healthy | `gentlequest-backend-00026-xd6` | 2026-01-15 18:00 IST |
| `nucleus-hud` | ✅ Healthy | `nucleus-hud-00007-xxx` | 2026-01-15 18:00 IST |
| `nucleus-sovereign` | ✅ Healthy | `nucleus-sovereign-00007-k2x` | 2026-01-15 18:00 IST |

**Last Known Good Revision:** `gentlequest-backend-00025-xxx`

---

## 6a. Access Requirements

### GCP IAM Roles Needed
| Role | Purpose |
|:-----|:--------|
| `roles/run.admin` | Deploy and manage Cloud Run services |
| `roles/cloudsql.client` | Connect to Cloud SQL |
| `roles/secretmanager.secretAccessor` | Read secrets (future) |
| `roles/logging.viewer` | View Cloud Run logs |

### Console URLs
| Resource | URL |
|:---------|:----|
| **Cloud Run Dashboard** | https://console.cloud.google.com/run?project=gen-lang-client-0894185576 |
| **Cloud SQL Instance** | https://console.cloud.google.com/sql/instances/gentlequest-db?project=gen-lang-client-0894185576 |
| **Cloud Build History** | https://console.cloud.google.com/cloud-build/builds?project=gen-lang-client-0894185576 |
| **Cloud Logging** | https://console.cloud.google.com/logs?project=gen-lang-client-0894185576 |

### Verify Your Access
```bash
# Check current auth
gcloud auth list

# Verify IAM access to project
gcloud projects get-iam-policy gen-lang-client-0894185576 \
  --filter="bindings.members:$(gcloud auth list --format='value(account)')" \
  --format="table(bindings.role)"
```

### On-Call / Escalation
| Contact | Channel | When |
|:--------|:--------|:-----|
| @lokeshgarg | Telegram | Primary owner, all escalations |

---

## 6b. Monitoring & Alerting

### Current Status
| Component | Status | Notes |
|:----------|:-------|:------|
| Cloud Logging | ✅ Active | 30-day retention |
| Cloud Monitoring | ⚠️ Manual | No automated alerts configured |
| Error Alerting | ❌ None | See TASK-005 to implement |

### Manual Monitoring Commands
```bash
# View recent errors
gcloud run services logs read gentlequest-backend --region us-central1 --limit 50 | grep -i "error\|fatal\|exception"

# Check request latency (last hour)
gcloud logging read 'resource.type="cloud_run_revision" severity>=WARNING' --limit 20 --format json

# Verify Redis fallback is active
gcloud run services logs read gentlequest-backend --region us-central1 | grep -i "filesystem\|redis\|session"
```

### Expected Response Times
| Endpoint | Expected | Alert If |
|:---------|:---------|:---------|
| `/api/health` | < 500ms | > 2s |
| `/api/chat` | < 3s | > 10s |
| `/api/memory/status` | < 1s | > 5s |

---

## 6c. Database Backup & Recovery

### Backup Configuration
| Setting | Value |
|:--------|:------|
| **Automated Backups** | ✅ Enabled (Cloud SQL default) |
| **Backup Window** | 04:00-08:00 UTC |
| **Retention** | 7 days (default) |
| **Point-in-Time Recovery** | ✅ Enabled |

### Backup Commands
```bash
# List available backups
gcloud sql backups list --instance=gentlequest-db

# Create on-demand backup
gcloud sql backups create --instance=gentlequest-db --description="Pre-migration backup"

# Restore from backup (DESTRUCTIVE)
gcloud sql backups restore BACKUP_ID --restore-instance=gentlequest-db
```

### Point-in-Time Recovery
```bash
# Restore to specific time (creates new instance)
gcloud sql instances clone gentlequest-db gentlequest-db-recovery \
  --point-in-time="2026-01-15T12:00:00Z"
```

---

## 6d. Smoke Test Checklist

Run after **any** deployment or configuration change:

```bash
# 1. Health check
curl -s https://app.gentlequest.app/api/health | jq .
# Expected: {"status": "healthy", "database": "healthy"}

# 2. Memory system
curl -s https://app.gentlequest.app/api/memory/status | jq .
# Expected: {"status": "active", "tables_initialized": true}

# 3. Chat endpoint (basic)
curl -s -X POST https://app.gentlequest.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello"}' | jq '.response | length'
# Expected: > 0 (non-empty response)

# 4. Check logs for errors (last 5 min)
gcloud run services logs read gentlequest-backend --region us-central1 --limit 20 | grep -i "error\|fatal"
# Expected: No new errors

# 5. Verify current revision
gcloud run services describe gentlequest-backend --region us-central1 \
  --format='value(status.latestReadyRevisionName)'
# Expected: gentlequest-backend-00026-xd6 (or newer)
```

---

## 6e. Version Tracking

### Currently Deployed
| Service | Revision | Deployed | Deployed By |
|:--------|:---------|:---------|:------------|
| `gentlequest-backend` | `00026-xd6` | 2026-01-15 | Cloud Build |
| `nucleus-hud` | `00007-xxx` | 2026-01-15 | Cloud Build |
| `nucleus-sovereign` | `00007-k2x` | 2026-01-15 | Cloud Build |

### Safe Rollback Targets
| Service | Last Known Good | Notes |
|:--------|:----------------|:------|
| `gentlequest-backend` | `00025-xxx` | Before security headers |
| `nucleus-hud` | `00006-xxx` | Before proxy fix |

### Check Current Revision
```bash
gcloud run services describe gentlequest-backend --region us-central1 \
  --format='value(status.latestReadyRevisionName)'
```

---

## 6f. Incident Response

### If Database Auth Fails
**Severity:** P1 (User-facing, data inaccessible)

**Symptoms:**
- `/api/health` returns `{"database": "error"}`
- Logs show `FATAL: password authentication failed`

**Response (15 min SLA):**
1. **Verify env vars still exist:**
   ```bash
   gcloud run services describe gentlequest-backend --region us-central1 \
     --format='yaml(spec.template.spec.containers[0].env)'
   ```
2. **If `DATABASE_URL` missing:** Re-run Section 4 Step 6 (full env var restore)
3. **If `DATABASE_URL` present but wrong password:** Re-run Section 4 Step 5 (reset password)
4. **Verify fix:** Run Smoke Test Checklist (Section 6d)
5. **If unresolved in 15 min:** Escalate to @lokeshgarg

### If 502/503 Errors
**Severity:** P2 (Degraded service)

**Response:**
1. Check if cold start: Wait 60s and retry
2. Check current revision: `gcloud run services describe...`
3. If regression: Rollback to last known good (Section 11)
4. If `start.sh` issue: Verify `netcat-openbsd` in Dockerfile

---

**This document is the authoritative source.** Do not reference the original "Debugging Database Password Mismatch" conversation unless explicitly needed.

---

## 7. Open Tasks & Backlog

> **Source:** Deep extraction from [conversation:7c654df4-b83e-43f9-8620-f15868ec39d1]  
> **Extracted:** 2026-01-15 18:30 IST

---

### 🔴 Must Do (Blocking / High Risk)

#### TASK-001: Redeploy `nucleus-hud` to Complete Frontend Proxy Fix
- **Status:** IN PROGRESS (marked `[/]` in task.md:1212)
- **Description:** The `nucleus-hud` service needs redeployment after the `next.config.ts` fix to use environment variables for the rewrite destination.
- **Why It Matters:** Until redeployed, the 503 error for `/api/status` may recur on cold starts or new instances.
- **Commands:**
  ```bash
  gcloud builds submit --config=cloudbuild.yaml
  # OR manually:
  gcloud run deploy nucleus-hud --image gcr.io/gen-lang-client-0894185576/nucleus-hud --region us-central1
  ```
- **Files:** `cloudbuild.yaml`, `tools/nucleus-hud/next.config.ts`

#### TASK-002: Verify SSL Certificate for `app.gentlequest.app`
- **Status:** OPEN (task.md:857)
- **Description:** Google Managed Certificate for the custom domain needs verification.
- **Why It Matters:** Without active SSL, users will see browser warnings.
- **Commands:**
  ```bash
  gcloud run domain-mappings describe --domain=app.gentlequest.app --region=us-central1
  ```
- **Expected:** Status = `ACTIVE`, Certificate = `PROVISIONED`

#### TASK-003: Monitor for Recurring Database Auth Failures
- **Status:** OBSERVATION (walkthrough.md:30)
- **Description:** After password reset, monitor `gentlequest-backend` logs for any recurring `password authentication failed` errors.
- **Why It Matters:** Silent failures could indicate config drift or deployment overwrites.
- **Commands:**
  ```bash
  gcloud run services logs read gentlequest-backend --region us-central1 --limit 100 | grep -i "password"
  ```

---

### 🟡 Should Do (Tech Debt / Hardening)

#### TASK-004: Migrate to Secret Manager
- **Status:** DOCUMENTED (secrets_protocol.md:49-61)
- **Description:** Migrate from Cloud Run Environment Variables to Secret Manager for sensitive credentials.
- **Why It Matters:** Environment variables can be accidentally overwritten by `gcloud run services update --set-env-vars`. Secret Manager provides audit trails and version control.
- **Commands:**
  ```bash
  printf "gentlequest2026" | gcloud secrets create gentlequest-db-pass --data-file=-
  gcloud secrets add-iam-policy-binding gentlequest-db-pass \
    --member=serviceAccount:gen-lang-client-0894185576@appspot.gserviceaccount.com \
    --role=roles/secretmanager.secretAccessor
  ```
- **Files:** `cloudbuild.yaml` (add `--set-secrets` flag)

#### TASK-005: Implement Connection Failure Monitoring
- **Status:** IMPLICIT (inferred from recurring issues)
- **Description:** Add alerting for database connection failures using Cloud Monitoring.
- **Why It Matters:** The password mismatch issue went undetected until manual verification. Proactive alerting would catch this earlier.
- **Commands:**
  ```bash
  gcloud monitoring policies create --policy-from-file=db_alert_policy.yaml
  ```

#### TASK-006: Clean Up Stale Environment Variables After Updates
- **Status:** IMPLICIT (caused DATABASE_URL overwrite issue)
- **Description:** Create a script or workflow to ensure all required env vars are preserved when using `gcloud run services update`.
- **Why It Matters:** Using `--set-env-vars` replaces ALL variables and has caused repeated issues.
- **Commands:**
  ```bash
  # Always use --update-env-vars instead of --set-env-vars for additions:
  gcloud run services update SERVICE --update-env-vars KEY=VALUE
  ```

#### TASK-007: Remove Hardcoded Password from `cloudbuild.yaml`
- **Status:** IMPLICIT (cloudbuild.yaml:42)
- **Description:** The `DATABASE_URL` in `cloudbuild.yaml` contains the password in plaintext. Replace with Secret Manager reference or Cloud Build substitution.
- **Why It Matters:** Secrets in version control are a security risk.
- **Files:** `cloudbuild.yaml:42`

---

### 🟢 Nice to Have (Future Enhancements)

#### TASK-008: Implement "Nightly Auditor" for User Retention
- **Status:** OPEN (task.md:847)
- **Description:** Build automated nightly checks for user engagement metrics (part of Stage GTM).
- **Why It Matters:** User #1 retention hook for GentleQuest.
- **Files:** `scripts/nightly_agent.py`

#### TASK-009: Validate "Time Saved" Metric (>2 hours/day)
- **Status:** OPEN (task.md:848)
- **Description:** Implement and validate the "Time Saved" metric for Nucleus users.
- **Why It Matters:** Key differentiator for product positioning.
- **Files:** `commitment_ledger.py` (already has `estimated_time_saved_minutes`)

#### TASK-010: Complete `.nuke` Protocol for Agent Transfer
- **Status:** OPEN (task.md:823)
- **Description:** Define the Universal Agent Transfer Format for digital legacy/migration.
- **Why It Matters:** Part of "Digital Immortality" vision (Phase 60).
- **Files:** `.brain/swarms/`

#### TASK-011: Implement `TimeCapsule` (Crypto-locked Graph Storage)
- **Status:** RESEARCH (task.md:825)
- **Description:** Research and implement crypto-locked storage for agent graphs.
- **Why It Matters:** Long-term data preservation and security.

#### TASK-012: Map `hud.gentlequest.app` Domain
- **Status:** DOCUMENTED (task.md:1195)
- **Description:** Complete domain mapping for the HUD service.
- **Why It Matters:** Cleaner URL for frontend access.
- **Commands:**
  ```bash
  gcloud run domain-mappings create --service nucleus-hud --domain hud.gentlequest.app --region us-central1
  ```

#### TASK-013: Deprecation Warning - `google.generativeai` Package
- **Status:** TECH DEBT (FutureWarning in scripts)
- **Description:** Several scripts still import from deprecated `google.generativeai`. Full migration to `google.genai` was marked complete but warnings persist.
- **Why It Matters:** Package may stop working in future versions.
- **Files:** `llm_client.py:32`

#### TASK-014: Archive Marathon Test Task
- **Status:** MINOR (BOOK_OF_WORK task-dc8bdba9)
- **Description:** Close/archive the auto-created marathon test task.
- **Why It Matters:** Backlog hygiene.

#### TASK-015: Test Critic LLM Loop with Real API Key
- **Status:** DEFERRED (MDR_SECOND_PASS_AUDIT.md:178)
- **Description:** The MDR_002 Critic "text → retry" loop needs testing with a real Gemini API key in test environment.
- **Why It Matters:** Verifies the self-correction loop actually works end-to-end.

---

## 9. Edge Cases

### Cold Start Behavior
- **Cold Start Time:** ~30s (Cloud Run) or ~65s (with full app init)
- **Impact:** First request after idle may timeout
- **Mitigation:** Pre-warming via scheduled health checks or Cloud Run `min-instances=1`

### Redis Fallback
- **Condition:** If `K_SERVICE` env var is set (Cloud Run), Redis is skipped
- **Fallback:** Filesystem-based session storage is used
- **Status:** Working (LAUNCH_CONTROL.md verified)

### pgvector Extension
- **Database:** Cloud SQL PostgreSQL 15
- **Extension:** `pgvector` (active for RAG/memory)
- **Check:** If memory fails, verify extension is enabled:
  ```sql
  SELECT * FROM pg_extension WHERE extname = 'vector';
  ```

---

## 10. Known Pitfalls

### Pitfall #1: `gcloud run services update --set-env-vars` Replaces ALL Variables
- **Risk:** Setting one env var deletes all others
- **Symptom:** `DATABASE_URL` disappears, causing auth failures
- **Fix:** Use `--update-env-vars` for additions or set all vars together:
  ```bash
  gcloud run services update SERVICE --set-env-vars "VAR1=val1,VAR2=val2,VAR3=val3"
  ```

### Pitfall #2: 502 Bad Gateway on Deploy
- **Cause:** Nginx starts before Gunicorn is ready (~65s app init)
- **Fix (Already Applied):** `start.sh` reordered: Gunicorn → wait port 5055 via `nc -z` → Nginx
- **File:** `Dockerfile` added `netcat-openbsd` package

### Pitfall #3: Password in Version Control
- **Location:** `cloudbuild.yaml:42` contains `DATABASE_URL` with plaintext password
- **Risk:** Git history exposes credentials
- **Mitigation:** See TASK-007 (migrate to Secret Manager or Cloud Build substitutions)

### Pitfall #4: `postgres://` vs `postgresql://` Prefix
- **Issue:** Some Python libraries require `postgresql://` not `postgres://`
- **Check:** `app.py` auto-converts `postgres://` → `postgresql://` on load
- **File:** `app.py:307-308`

---

## 11. Rollout & Backout Plans

### Rollout (New Deployment)
```bash
# Build and deploy all services
gcloud builds submit --config=cloudbuild.yaml

# Verify health
curl https://app.gentlequest.app/api/health
```

### Backout (Rollback to Previous Revision)
```bash
# List revisions
gcloud run revisions list --service gentlequest-backend --region us-central1

# Rollback to specific revision
gcloud run services update-traffic gentlequest-backend \
  --to-revisions=gentlequest-backend-00025-xxx=100 \
  --region us-central1
```

### Emergency: Reset Database Password
```bash
# 1. Reset Cloud SQL password
gcloud sql users set-password gentlequest --instance=gentlequest-db --password=NEW_PASSWORD

# 2. Update Cloud Run (preserving all vars)
gcloud run services describe gentlequest-backend --region us-central1 \
  --format='value(spec.template.spec.containers[0].env)' > /tmp/env_backup.txt

# 3. Rebuild DATABASE_URL and update
gcloud run services update gentlequest-backend --region us-central1 \
  --set-env-vars "DATABASE_URL=postgresql://gentlequest:NEW_PASSWORD@/gentlequest?host=/cloudsql/..."
```

---

## 12. Summary

| Priority | Count | Status |
|:---------|:------|:-------|
| 🔴 Must Do | 3 | In progress / Verification |
| 🟡 Should Do | 4 | Tech debt |
| 🟢 Nice to Have | 8 | Future enhancements |
| **Total** | **15** | |

**Handover Target:** This thread (current conversation)

---

## 13. Information NOT Recoverable

The following types of information from the source conversation **cannot be recovered** from the archived artifacts:

1. **Real-time debugging session details** — Exact commands typed, trial-and-error iterations, and intermediate outputs during live debugging
2. **Ephemeral error messages** — Full stack traces and logs that weren't explicitly captured
3. **User decision rationale** — Why certain approaches were chosen over others during live discussion
4. **Timing details** — Exact sequence and duration of debugging steps
5. **Chat context** — Conversational flow, questions asked, and incremental discoveries
6. **Credentials tested but not documented** — Any passwords or configs tried but not saved
7. **Browser/UI state** — Screenshots or recordings of Cloud Console interactions

