# GentleQuest Infrastructure Hardening Checklist
> **Generated:** 2026-01-15 19:15 IST  
> **Source:** DATABASE_DEBUG_HANDOVER.md  
> **Duration:** ~2 weeks

---

## Week 1: Critical Path

### Day 1-2: Verification
- [ ] **1.** `curl https://nucleus.gentlequest.app/api/health` → Confirm `{"database": "healthy"}`
- [ ] **2.** `gcloud run domain-mappings describe --domain=nucleus.gentlequest.app --region=us-central1` → Confirm SSL = ACTIVE
- [ ] **3.** `gcloud run services logs read gentlequest-backend --region us-central1 --limit 50 | grep -i "password"` → Confirm 0 auth failures

### Day 3-4: Frontend Completion
- [ ] **4.** `gcloud builds submit --config=cloudbuild.yaml` → Redeploy all services
- [ ] **5.** `curl -u admin:nucleus https://nucleus-hud-999376128638.us-central1.run.app/api/health` → Verify proxy returns JSON

### Day 5-7: Secret Manager Migration
- [ ] **6.** Open `cloudbuild.yaml:42` → Note hardcoded password
- [ ] **7.** `printf "gentlequest2026" | gcloud secrets create gentlequest-db-pass --data-file=-`
- [ ] **8.** `gcloud secrets add-iam-policy-binding gentlequest-db-pass --member=serviceAccount:gen-lang-client-0894185576@appspot.gserviceaccount.com --role=roles/secretmanager.secretAccessor`
- [ ] **9.** Update `cloudbuild.yaml` → Replace hardcoded password with Secret Manager reference

---

## Week 2: Hardening & Monitoring

### Day 8-10: Monitoring Setup
- [ ] **10.** Create Cloud Monitoring alert for DB auth failures
- [ ] **11.** `gcloud run services describe gentlequest-backend --region us-central1 --format='yaml(spec.template.spec.containers[0].env)' > ~/env_backup_$(date +%Y%m%d).yaml` → Backup env vars

### Day 11-12: Cold Start Mitigation
- [ ] **12.** `gcloud run services update gentlequest-backend --region us-central1 --min-instances=1` → Enable min instance

### Day 13-14: Final Validation
- [ ] **13.** `curl -s https://nucleus.gentlequest.app/api/memory/status | jq .` → Confirm `tables_initialized: true`
- [ ] **14.** `curl -s -X POST https://nucleus.gentlequest.app/api/chat -H "Content-Type: application/json" -d '{"message":"hello"}' | jq '.response | length'` → Confirm > 0
- [ ] **15.** `git diff cloudbuild.yaml` → Verify no secrets in pending commits
- [ ] **16.** Commit all changes with message: "chore: Infrastructure hardening complete"

---

## Quick Reference

| Resource | URL |
|:---------|:----|
| Cloud Run Dashboard | https://console.cloud.google.com/run?project=gen-lang-client-0894185576 |
| Cloud SQL Instance | https://console.cloud.google.com/sql/instances/gentlequest-db?project=gen-lang-client-0894185576 |
| Runbook | `docs/infra/DATABASE_DEBUG_HANDOVER.md` |
| Phase History | `docs/infra/PHASE_HISTORY.md` |
| Brain State | `.brain/` |

---

*This thread is the canonical successor to conversation 7c654df4.*
