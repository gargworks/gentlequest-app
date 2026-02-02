# MASTER CONTEXT INDEX - GentleQuest 2026
## Year-Long Sprint Reference Hub

**Purpose:** Single entry point to all context documents  
**Valid Until:** December 2026  
**Last Updated:** January 16, 2026

---

## 🎯 START HERE

This index connects all context capture documents for the 2026 sprint. Use this as your navigation hub.

---

## 📚 DOCUMENT MAP

### 🔴 START WITH THE PROTOCOL

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [PROTOCOL.md](../../PROTOCOL.md) | **THE SINGLE SOURCE OF TRUTH** | Always start here |
| [protocol.json](../../protocol.json) | Machine-readable protocol | Automated tools |

### Core Reference Documents

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [ARCHITECTURE_MAP.md](./ARCHITECTURE_MAP.md) | System topology, data flows, dependencies | Understanding how components connect |
| [OPERATIONS_PLAYBOOK.md](./OPERATIONS_PLAYBOOK.md) | Deploy, rollback, debug procedures | Operational tasks |
| [API_CONTRACTS.md](./API_CONTRACTS.md) | All endpoints, params, responses | Building/debugging API calls |
| [EXTENSION_GUIDE.md](./EXTENSION_GUIDE.md) | How to add features | Adding new functionality |
| [DECISION_LOG.md](./DECISION_LOG.md) | ADRs - why things are built this way | Understanding past decisions |
| [ENVIRONMENT_MATRIX.md](./ENVIRONMENT_MATRIX.md) | All env vars and secrets | Configuration changes |
| [CRITICAL_PATHS.md](./CRITICAL_PATHS.md) | High-impact code paths | Changes requiring extra care |
| [TECH_DEBT_REGISTRY.md](./TECH_DEBT_REGISTRY.md) | Known issues and workarounds | Understanding limitations |
| [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) | Test coverage map, verification | Running and adding tests |
| [SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md) | Security review and audit | Security verification |
| [AI_PROVIDER_SPECS.md](./AI_PROVIDER_SPECS.md) | AI provider details and limits | AI integration work |
| [GOLD_STANDARD_METHODOLOGY.md](./GOLD_STANDARD_METHODOLOGY.md) | Enterprise-grade doc methodology | Improving documentation |

### Supporting Documents

| Document | Purpose |
|----------|---------|
| [MEGA_CONTEXT_CAPTURE_2026.md](./MEGA_CONTEXT_CAPTURE_2026.md) | Original exploration log |
| [TECHNICAL_APPENDIX_JAN2026.md](./TECHNICAL_APPENDIX_JAN2026.md) | Technical deep-dives |
| [session_synthesis_20260116.md](./session_synthesis_20260116.md) | Session summaries |

---

## 🗂️ QUICK LOOKUP

### "I need to..."

| Task | Go To |
|------|-------|
| Deploy changes | [OPERATIONS_PLAYBOOK.md](./OPERATIONS_PLAYBOOK.md#1-deployment-procedures) |
| Fix a bug | [CRITICAL_PATHS.md](./CRITICAL_PATHS.md) → [OPERATIONS_PLAYBOOK.md](./OPERATIONS_PLAYBOOK.md#3-debugging-procedures) |
| Add new endpoint | [EXTENSION_GUIDE.md](./EXTENSION_GUIDE.md#1-add-a-new-api-endpoint) |
| Add new screen | [EXTENSION_GUIDE.md](./EXTENSION_GUIDE.md#2-add-a-new-screenpage) |
| Understand data flow | [ARCHITECTURE_MAP.md](./ARCHITECTURE_MAP.md#2-data-flows) |
| Check API format | [API_CONTRACTS.md](./API_CONTRACTS.md) |
| Find env var | [ENVIRONMENT_MATRIX.md](./ENVIRONMENT_MATRIX.md) |
| Understand why X | [DECISION_LOG.md](./DECISION_LOG.md) |
| Check known issues | [TECH_DEBT_REGISTRY.md](./TECH_DEBT_REGISTRY.md) |
| Rollback deploy | [OPERATIONS_PLAYBOOK.md](./OPERATIONS_PLAYBOOK.md#2-rollback-procedures) |
| Run tests | [TESTING_STRATEGY.md](./TESTING_STRATEGY.md#3-how-to-run-tests) |
| Security review | [SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md) |
| Change AI provider | [AI_PROVIDER_SPECS.md](./AI_PROVIDER_SPECS.md) |
| Rotate secrets | [SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md#1-secrets-management) |

---

## 🏗️ ARCHITECTURE QUICK VIEW

```
┌─────────────────────────────────────────────────────────┐
│                    GENTLEQUEST                          │
├─────────────────────────────────────────────────────────┤
│  FRONTEND: Flutter Web (ai_buddy_web/)                  │
│  ├── Providers: Chat, Mood, Quest, Progress, Community  │
│  ├── Screens: HomeShell → 4 tabs                        │
│  └── Services: API, Analytics, Session, Streaming       │
├─────────────────────────────────────────────────────────┤
│  BACKEND: Flask (app.py)                                │
│  ├── Routes: /api/chat, /api/mood, /api/quest, etc.     │
│  ├── AI: Gemini → OpenAI → Perplexity (failover)        │
│  └── Data: PostgreSQL + Redis                           │
├─────────────────────────────────────────────────────────┤
│  INFRA: Render (primary) / GCP (alternative)            │
│  └── URL: https://gentlequest.onrender.com              │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 KEY FILE LOCATIONS

### Backend
```
/Users/lokeshgarg/ai-mvp-backend/
├── app.py                    # Main Flask app
├── providers/                # AI providers
│   ├── gemini_provider.py
│   ├── openai_provider.py
│   └── perplexity_provider.py
├── requirements.txt          # Python deps
├── Dockerfile               # Container
└── render.yaml              # Render config
```

### Flutter
```
/Users/lokeshgarg/ai-mvp-backend/ai_buddy_web/lib/
├── main.dart                # Entry point
├── providers/               # State management
├── screens/                 # UI screens
├── widgets/                 # Reusable widgets
├── services/                # API, analytics
├── models/                  # Data models
├── navigation/              # Routing
└── config/                  # App config
```

### Brain/MCP
```
/Users/lokeshgarg/ai-mvp-backend/.brain/
├── artifacts/               # Documents
├── ledger/                  # Events, decisions
├── agents/                  # Agent definitions
└── state.json               # Current state
```

---

## 🔑 CRITICAL KNOWLEDGE

### Production URL
```
https://gentlequest.onrender.com
```

### Health Check
```bash
curl https://gentlequest.onrender.com/api/health
```

### AI Provider Chain
```
Gemini (primary) → OpenAI (fallback) → Perplexity (last resort)
```

### Rate Limits
```
Global: 5000/day, 1000/hour
Chat/Mood: 120/minute (per session)
```

### Data Retention
```
Messages: 30 days
Sessions: 14 days
Analytics: 90 days
```

---

## 🚨 CRISIS DETECTION

**11 countries with local helplines:**
IN, US, UK, CA, AU, NZ, IE, SG, PH, ZA, DE

**Trigger keywords monitored** (see app.py)

**NEVER modify crisis detection without clinical review**

---

## 📊 METRICS TO WATCH

| Metric | Target | Alert If |
|--------|--------|----------|
| Chat response time | < 2s | > 5s |
| Error rate | < 1% | > 5% |
| AI fallback rate | < 5% | > 20% |
| Health check | 200 | non-200 |

---

## 🔄 MAINTENANCE SCHEDULE

### Daily
- Check /api/health
- Review Render logs for errors

### Weekly
- Review AI fallback rate
- Check database size

### Monthly
- Rotate API keys (if policy requires)
- Review tech debt

### Quarterly
- Full tech debt review
- Update context documents
- Review ADRs

---

## 📝 CONTEXT CAPTURE STATS

**Completed January 16, 2026**

| Metric | Value |
|--------|-------|
| Documents Created | 9 structured + 1 index |
| Total Lines | ~3,500+ |
| Checkpoints | 300+ |
| Files Explored | 350+ |
| Code Lines Indexed | ~70,000 |

---

## 🎯 2026 SPRINT PRINCIPLES

1. **Use this index first** - Don't re-explore
2. **Update documents** - Keep them current
3. **Follow ADRs** - Don't re-debate settled decisions
4. **Respect critical paths** - Extra care on high-impact code
5. **Track tech debt** - Add new issues to registry
6. **Document changes** - Update relevant docs after major work

---

## DOCUMENT FRESHNESS

| Document | Last Updated | Review By |
|----------|--------------|-----------|
| ARCHITECTURE_MAP | Jan 16, 2026 | Apr 2026 |
| OPERATIONS_PLAYBOOK | Jan 16, 2026 | Apr 2026 |
| API_CONTRACTS | Jan 16, 2026 | Apr 2026 |
| EXTENSION_GUIDE | Jan 16, 2026 | Apr 2026 |
| DECISION_LOG | Jan 16, 2026 | Ongoing |
| ENVIRONMENT_MATRIX | Jan 16, 2026 | Apr 2026 |
| CRITICAL_PATHS | Jan 16, 2026 | Apr 2026 |
| TECH_DEBT_REGISTRY | Jan 16, 2026 | Monthly |
| TESTING_STRATEGY | Jan 16, 2026 | Apr 2026 |
| SECURITY_CHECKLIST | Jan 16, 2026 | Quarterly |
| AI_PROVIDER_SPECS | Jan 16, 2026 | Apr 2026 |

---

**This is your 2026 sprint reference hub. Bookmark it. Use it. Update it.**
