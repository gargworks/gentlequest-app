# THE PROTOCOL
## Single Source of Truth for GentleQuest

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ████████╗██╗  ██╗███████╗    ██████╗ ██████╗  ██████╗ ████████╗ ██████╗    ║
║   ╚══██╔══╝██║  ██║██╔════╝    ██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝██╔═══██╗   ║
║      ██║   ███████║█████╗      ██████╔╝██████╔╝██║   ██║   ██║   ██║   ██║   ║
║      ██║   ██╔══██║██╔══╝      ██╔═══╝ ██╔══██╗██║   ██║   ██║   ██║   ██║   ║
║      ██║   ██║  ██║███████╗    ██║     ██║  ██║╚██████╔╝   ██║   ╚██████╔╝   ║
║      ╚═╝   ╚═╝  ╚═╝╚══════╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝    ║
║                                                                              ║
║                    CANONICAL REFERENCE • VERSION 1.0.0                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**Status:** ACTIVE  
**Integrity Hash:** `sha256:COMPUTE_ON_COMMIT`  
**Last Verified:** 2026-01-16  
**Valid Until:** 2026-12-31

---

## §0 PRIME DIRECTIVE

> **This file is THE truth. When in doubt, consult this file.**
> 
> All humans and machines operating on this codebase MUST treat this file as the
> canonical source. Any conflict between this file and other documentation,
> this file wins. Period.

---

## §1 IDENTITY

```yaml
project:
  name: GentleQuest
  type: Mental Health Companion
  tagline: "Your gentle companion for mental wellness"
  
production:
  url: https://gentlequest.onrender.com
  service_id: srv-d2r3i1fdiees73dqtov0
  provider: Render
  region: Oregon (US West)
  
repository:
  path: .
  vcs: git
  remote: origin
  branch: main
```

---

## §2 ARCHITECTURE (Immutable Facts)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION STACK                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐    │
│   │   FLUTTER    │  HTTP   │    FLASK     │  SQL    │  POSTGRESQL  │    │
│   │   WEB APP    │ ──────▶ │   BACKEND    │ ──────▶ │   DATABASE   │    │
│   │  (Frontend)  │         │   (API)      │         │   (Storage)  │    │
│   └──────────────┘         └──────────────┘         └──────────────┘    │
│                                   │                                      │
│                                   │ Session                              │
│                                   ▼                                      │
│                            ┌──────────────┐                              │
│                            │    REDIS     │                              │
│                            │   (Cache)    │                              │
│                            └──────────────┘                              │
│                                   │                                      │
│                                   │ API Calls                            │
│                                   ▼                                      │
│   ┌──────────────────────────────────────────────────────────────┐      │
│   │              AI PROVIDER CHAIN (Failover)                     │      │
│   │   GEMINI (Primary) → OPENAI (Fallback) → PERPLEXITY (Last)   │      │
│   └──────────────────────────────────────────────────────────────┘      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Stack Versions
| Component | Version | File |
|-----------|---------|------|
| Python | 3.11 | `Dockerfile` |
| Flask | 3.0.x | `requirements.txt` |
| Flutter | 3.x | `ai_buddy_web/pubspec.yaml` |
| PostgreSQL | 15+ | Render managed |
| Redis | 7+ | External |

---

## §3 ENDPOINTS (Canonical)

### Core User-Facing (12 endpoints - in OpenAPI)
| Endpoint | Method | Purpose | Rate Limit |
|----------|--------|---------|------------|
| `/api/health` | GET | Health check | None |
| `/api/ping` | GET | Keep-alive | None |
| `/api/chat` | POST | AI chat | 30/min |
| `/api/chat_stream` | GET | SSE streaming | 120/min |
| `/api/mood` | POST | Log mood | 120/min |
| `/api/mood/history` | GET | Mood history | 120/min |
| `/api/mood/analytics` | GET | Mood analytics | 120/min |
| `/api/quests` | GET | Get quests | 120/min |
| `/api/quests/complete` | POST | Complete quest | 120/min |
| `/api/progress` | GET | Get progress | 120/min |
| `/api/community/feed` | GET | Community feed | 120/min |
| `/api/assessment/<type>` | POST | Self-assessment | 120/min |

### Community Endpoints (8 endpoints)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/community/flags` | GET | Feature flags |
| `/api/community/reaction` | POST | Add reaction |
| `/api/community/react/<id>` | POST | Legacy reaction |
| `/api/community/report` | POST | Report content |
| `/api/community/reports` | GET | List reports (admin) |
| `/api/community/moderate` | POST | Moderate (admin) |
| `/api/community/post` | POST | Create post |
| `/api/community/post/<id>` | DELETE | Delete post |

### Brain/Admin Endpoints (8 endpoints)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/brain/status` | GET | Brain status |
| `/api/brain/alert` | POST | Send alert |
| `/api/brain/sprint` | POST | Start sprint |
| `/api/brain/sync` | POST | Sync state |
| `/api/brain/telegram/webhook` | POST | Telegram hook |
| `/api/swarms` | GET | Active swarms |
| `/api/enterprise/status` | GET | Enterprise status |
| `/api/enterprise/metrics` | GET | Enterprise metrics |

### Other Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Landing page |
| `/app` | GET | Flutter app |
| `/privacy` | GET | Privacy policy |
| `/.well-known/assetlinks.json` | GET | Android app links |
| `/api/deploy-test` | GET | Deploy verification |
| `/api/get_or_create_session` | GET | Session management |
| `/api/chat_history` | GET | Chat history |
| `/api/assessment/history` | GET | Assessment history |
| `/api/assessment/<type>/questions` | GET | Assessment questions |

**Full API Spec:** `docs/openapi.yaml` (core endpoints)  
**Total Routes:** ~49 in app.py + 10 in community.py

---

## §4 SECRETS (Names Only - Values NEVER Here)

| Secret | Location | Required |
|--------|----------|----------|
| `SECRET_KEY` | Render Dashboard | ✅ YES |
| `DATABASE_URL` | Render Dashboard | ✅ YES |
| `REDIS_URL` | Render Dashboard | ⚠️ Recommended |
| `GEMINI_API_KEY` | Render Dashboard | ✅ YES (or fallbacks) |
| `OPENAI_API_KEY` | Render Dashboard | ⚠️ Fallback |
| `PPLX_API_KEY` | Render Dashboard | ⚠️ Fallback |
| `SENTRY_DSN_BACKEND` | Render Dashboard | Optional |
| `ADMIN_API_TOKEN` | Render Dashboard | Optional |

**⛔ NEVER commit secrets. NEVER log secrets. NEVER expose in errors.**

**Full Schema:** `docs/schemas/environment.schema.json`

---

## §5 COMMANDS (Copy-Paste Ready)

### Health Check
```bash
curl https://gentlequest.onrender.com/api/health
```

### Local Development
```bash
# Backend
source venv/bin/activate
flask run --port 5055

# Frontend (separate terminal)
cd ai_buddy_web
flutter run -d chrome
```

### Deploy Production
```bash
git push origin main  # Render auto-deploys
# OR
python runbooks/deploy_production.py --execute
```

### Run Tests
```bash
pytest tests/ -v
```

### Check Doc Freshness
```bash
python scripts/check_doc_freshness.py --dir .brain/artifacts/synthesis/ -v
```

### Validate OpenAPI
```bash
python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"
```

---

## §6 FILE MAP (Critical Paths)

```
./
│
├── PROTOCOL.md                    ★ YOU ARE HERE - THE TRUTH
├── protocol.json                  ★ Machine-readable version
│
├── app.py                         ★ Backend entry point
├── requirements.txt               Backend dependencies
├── Dockerfile                     Container definition
├── render.yaml                    Render deployment config
│
├── ai_buddy_web/                  Flutter frontend
│   ├── lib/
│   │   ├── main.dart             ★ Frontend entry point
│   │   ├── screens/              UI screens
│   │   ├── services/             API/streaming services
│   │   ├── providers/            State management
│   │   └── config/               Configuration
│   └── pubspec.yaml              Frontend dependencies
│
├── docs/                          Machine-readable specs
│   ├── openapi.yaml              ★ API specification
│   └── schemas/
│       └── environment.schema.json  Env var schema
│
├── tests/                         Test suites
│   └── test_docs.py              Documentation tests
│
├── scripts/                       Automation
│   └── check_doc_freshness.py    Staleness checker
│
├── runbooks/                      Executable procedures
│   └── deploy_production.py      ★ Deployment runbook
│
└── .brain/artifacts/synthesis/    Human documentation
    ├── MASTER_CONTEXT_INDEX.md   Documentation hub
    ├── ARCHITECTURE_MAP.md       System design
    ├── OPERATIONS_PLAYBOOK.md    How to operate
    ├── API_CONTRACTS.md          API details
    ├── CRITICAL_PATHS.md         High-impact code
    └── ...                       Other docs
```

---

## §7 DECISION AUTHORITY

| Decision Type | Authority | Approval Required |
|--------------|-----------|-------------------|
| Code changes | Any developer | PR review |
| API changes | Backend lead | Protocol update |
| Schema changes | Architect | Protocol update |
| Secret changes | Founder | Render dashboard |
| Deploy to prod | Any with access | None (auto) |
| Rollback | Any with access | None (emergency) |
| Protocol changes | Founder only | Git commit |

---

## §8 CRISIS DETECTION (Safety Critical)

**This is a mental health app. Crisis detection is P0.**

### Supported Countries
| Country | Hotline | Number |
|---------|---------|--------|
| IN | iCall | 9152987821 |
| US | 988 Lifeline | 988 |
| UK | Samaritans | 116 123 |
| CA | Crisis Line | 1-833-456-4566 |
| AU | Lifeline | 13 11 14 |
| NZ | Lifeline | 0800 543 354 |
| SG | SOS | 1800-221-4444 |
| PH | NCMH | 0917-899-8727 |
| ZA | SADAG | 0800 567 567 |
| IE | Samaritans | 116 123 |
| DE | Telefonseelsorge | 0800 111 0 111 |

**Fallback:** Always show resources if country unknown.

---

## §9 OPERATIONAL CONSTANTS

```yaml
rate_limits:
  global_per_day: 5000
  global_per_hour: 1000
  chat_per_minute: 120
  mood_per_minute: 120

retention:
  messages_days: 30
  sessions_days: 14
  analytics_days: 90
  error_logs_days: 14

timeouts:
  ai_response_seconds: 30
  database_query_seconds: 5
  health_check_seconds: 10

performance:
  target_response_time_ms: 500
  max_message_length: 10000
  max_context_messages: 20
```

---

## §10 VERIFICATION PROTOCOL

### Daily (Automated)
- [ ] Health check returns 200
- [ ] CI pipeline green

### Weekly (Human)
- [ ] Review error logs
- [ ] Check rate limit stats
- [ ] Verify keep-alive working

### Monthly
- [ ] Update TECH_DEBT_REGISTRY
- [ ] Review doc freshness
- [ ] Check dependency updates

### Quarterly
- [ ] Full security review
- [ ] Rotate secrets
- [ ] Verify crisis hotlines
- [ ] Full doc review

---

## §11 RECOVERY PROCEDURES

### Service Down
```bash
# 1. Check Render status
open https://status.render.com

# 2. Check health
curl https://gentlequest.onrender.com/api/health

# 3. Check logs
open https://dashboard.render.com  # → Logs

# 4. Manual restart if needed
# Render Dashboard → Manual Deploy → Latest
```

### Rollback
```bash
# Option 1: Render Dashboard (fastest)
# Select previous deploy → Rollback

# Option 2: Git revert
git revert HEAD
git push origin main
```

### Database Emergency
```bash
# Connection test
psql $DATABASE_URL -c "SELECT 1"

# If Render DB, check dashboard
open https://dashboard.render.com
```

---

## §12 AGENTS PROTOCOL

Per `AGENTS.md`, all AI agents must:

1. **Identify** with codename (CORE_SYN, VISION_ONE, etc.)
2. **Consult** this PROTOCOL before major changes
3. **Log** significant actions to `.brain/ledger/events.jsonl`
4. **Respect** decision authority in §7
5. **Never** modify secrets or bypass safety checks

---

## §13 AMENDMENT PROCESS

To modify this PROTOCOL:

1. **Propose** change in a PR
2. **Review** by Founder or designated authority
3. **Update** version number
4. **Commit** with message: `[PROTOCOL] Description of change`
5. **Regenerate** `protocol.json` from this file
6. **Verify** all references still valid

---

## §14 INTEGRITY CHECK

This file's integrity can be verified:

```bash
# Generate hash
sha256sum PROTOCOL.md

# Verify against committed hash
cat protocol.json | jq '.integrity.hash'
```

**Last Known Good Hash:** `<computed on commit>`

---

## §15 QUICK REFERENCE CARD

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        QUICK REFERENCE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PRODUCTION:  https://gentlequest.onrender.com                          │
│  HEALTH:      curl <production>/api/health                              │
│  DEPLOY:      git push origin main                                       │
│  ROLLBACK:    Render Dashboard → Previous Deploy → Rollback             │
│                                                                          │
│  DOCS HUB:    .brain/artifacts/synthesis/MASTER_CONTEXT_INDEX.md        │
│  API SPEC:    docs/openapi.yaml                                          │
│  RUNBOOKS:    runbooks/                                                  │
│                                                                          │
│  SECRETS:     Render Dashboard (NEVER in code)                          │
│  LOGS:        Render Dashboard → Logs                                    │
│                                                                          │
│  AI CHAIN:    Gemini → OpenAI → Perplexity                              │
│  RATE LIMIT:  120/min per session                                        │
│                                                                          │
│  EMERGENCY:   Check status.render.com first                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## §16 SESSION HISTORY (Cross-Platform Work)

This protocol consolidates work across **Windsurf** and **Antigravity** sessions:

### Artifacts Created (Total: ~200KB)

| Artifact | Size | Session | Purpose |
|----------|------|---------|---------|
| `MEGA_CONTEXT_CAPTURE_2026.md` | 36KB | Windsurf | Original 292-checkpoint exploration |
| `TECHNICAL_APPENDIX_JAN2026.md` | 24KB | Windsurf | Deep technical dives |
| `GOLD_STANDARD_METHODOLOGY.md` | 21KB | Antigravity | Enterprise doc methodology |
| `ARCHITECTURE_MAP.md` | 10KB | Windsurf | System topology |
| `OPERATIONS_PLAYBOOK.md` | 8KB | Windsurf | Deploy/debug procedures |
| `API_CONTRACTS.md` | 9KB | Windsurf | All API endpoints |
| `EXTENSION_GUIDE.md` | 9KB | Windsurf | How to add features |
| `CRITICAL_PATHS.md` | 8KB | Windsurf | High-impact code |
| `DECISION_LOG.md` | 7KB | Windsurf | ADRs |
| `ENVIRONMENT_MATRIX.md` | 7KB | Windsurf | Env vars |
| `TECH_DEBT_REGISTRY.md` | 6KB | Windsurf | Known issues |
| `TESTING_STRATEGY.md` | 7KB | Antigravity | Test coverage |
| `SECURITY_CHECKLIST.md` | 8KB | Antigravity | Security audit |
| `AI_PROVIDER_SPECS.md` | 10KB | Antigravity | Provider details |
| `MASTER_CONTEXT_INDEX.md` | 9KB | Windsurf | Navigation hub |
| `STRATEGIC_PLANNING_2026.md` | 12KB | Antigravity | The Billion Dollar Plan |
| `SESSION_NOTES_20260116.md` | 8KB | Antigravity | Deep Research Session |

### Daily Digests
```
digest_20251226.md → digest_20260116.md (11 files)
```

### Session Reports
```
session_synthesis_20260110.md
session_synthesis_20260116.md
MASTER_SESSION_REPORT_20260110.md
founders_desk_20251226.md
20251230_consolidation_report.md
```

### Machine-Readable Additions (This Session)
```
docs/openapi.yaml              - 450+ lines API spec
docs/schemas/environment.schema.json - Env validation
protocol.json                  - Machine-readable protocol
scripts/validate_protocol.py   - Truth enforcer
scripts/check_doc_freshness.py - Staleness detector
tests/test_docs.py             - Doc validation tests
runbooks/deploy_production.py  - Executable runbook
.github/workflows/docs-validation.yml - CI pipeline
```

---

## §17 SIGNATURES

```
This PROTOCOL is authoritative and binding.

Established: January 16, 2026
Author: Founder's Desk
Version: 1.0.0

"The truth shall set you free, but first it must be documented."
```

---

**END OF PROTOCOL**

*When lost, return here. When in doubt, consult here. This is the way.*
