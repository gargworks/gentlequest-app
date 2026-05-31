# Security Hardening Documentation

> **Date**: 2026-02-24
> **Phase**: 67 - Infrastructure Hardening
> **Status**: ✅ Complete

## Overview

This document describes the security hardening measures implemented for the Nucleus production infrastructure.

## 1. Secret Management

### Secrets in GCP Secret Manager
| Secret Name | Purpose | Services Using |
|-------------|---------|----------------|
| `gemini-api-key` | Gemini API authentication | gentlequest-backend |
| `gentlequest-db-pass` | PostgreSQL password | gentlequest-backend |

### Usage in Cloud Build
```yaml
--set-secrets=DB_PASSWORD=gentlequest-db-pass:latest,GEMINI_API_KEY=gemini-api-key:latest
```

### Local Development
- Use `.env` files (gitignored)
- Never commit secrets to repository

## 2. SSL/TLS Configuration

### Domains Monitored
| Domain | Certificate Provider | Expiry |
|--------|---------------------|--------|
| app.gentlequest.app | Google Managed | Apr 14, 2026 |
| hud.gentlequest.app | Google Managed | Auto-renewed |
| app.gentlequest.app | Google Managed | Auto-renewed |

### Security Headers (Implemented)
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: upgrade-insecure-requests
```

## 3. Monitoring Scripts

### DB Health Monitor
```bash
scripts/monitor_db_health.py
```
- Checks `/api/health` endpoint
- Alerts via Telegram on failure
- Exit code 1 on unhealthy

### SSL Certificate Monitor
```bash
scripts/monitor_ssl_cert.py
```
- Checks certificate expiry for all domains
- Warns 30 days before expiry
- Alerts via Telegram

### Safe Env Var Update
```bash
scripts/safe_update_env.sh SERVICE_NAME VAR_NAME VAR_VALUE
```
- Backs up current env vars before update
- Preserves all existing vars
- Provides rollback command

## 4. Authentication Architecture

### OAuth-Ready Architecture (v0.6.1)
- **STDIO Transport**: IPC tokens (30s TTL, single-use, HMAC-signed)
- **HTTP/SSE Transport**: OAuth 2.1 stub (Phase 3 - Nucleus Cloud)

See `docs/AUTH_ARCHITECTURE.md` for full details.

## 5. Access Control

### Cloud Run Services
| Service | Auth Required | IAM Policy |
|---------|---------------|------------|
| gentlequest-backend | No (public API) | allUsers |
| nucleus-hud | No (public dashboard) | allUsers |
| nucleus-sovereign | Yes (internal) | Restricted |

## 6. Recommended Cron Jobs

```bash
# DB Health Check (every 6 hours)
0 */6 * * * /path/to/scripts/monitor_db_health.py

# SSL Certificate Check (daily)
0 9 * * * /path/to/scripts/monitor_ssl_cert.py
```

## 7. Incident Response

### DB Connection Failure
1. Check Cloud SQL instance status
2. Verify IAM permissions
3. Check connection string in env vars
4. Review Cloud Run logs

### SSL Certificate Expiry
1. Google Managed certificates auto-renew
2. If failed, check domain mapping
3. Re-provision certificate via Cloud Console

## 8. Audit Trail

All security-related decisions are logged in:
- `.brain/engrams/ledger.jsonl` - Architecture decisions
- `.brain/ledger/auth/` - IPC token events
- Cloud Run logs - Request/response audit

---

**Maintained by**: Nucleus Team
**Last Updated**: 2026-02-24
