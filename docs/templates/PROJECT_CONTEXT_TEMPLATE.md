# PROJECT_CONTEXT_TEMPLATE.md
> **Purpose:** Drop this into the first message of any new LLM conversation to preserve critical context.  
> **Last Updated:** [DATE]  
> **Project:** [PROJECT_NAME]

---

## 1. Project Goal & Success Metrics

### Goal
[One sentence: What are we building and why?]

### Success Metrics
| Metric | Target | Current |
|:-------|:-------|:--------|
| [Metric 1] | [Target] | [Status] |
| [Metric 2] | [Target] | [Status] |

### Non-Goals
- [What we are explicitly NOT doing]

---

## 2. System Architecture

### Stack
| Layer | Technology |
|:------|:-----------|
| Frontend | [e.g., Flutter Web / Next.js] |
| Backend | [e.g., Flask / FastAPI] |
| Database | [e.g., PostgreSQL + pgvector] |
| LLM | [e.g., Gemini 2.5 Flash] |
| Infra | [e.g., Cloud Run / Render] |

### Architecture Diagram
```
[Simple ASCII or Mermaid diagram]
User → Frontend → Backend → Database
                ↘ LLM API
```

### Key Services
| Service | URL | Purpose |
|:--------|:----|:--------|
| [Service 1] | [URL] | [What it does] |

---

## 3. Key Decisions & Constraints

### Architectural Decisions (ADRs)
| Decision | Rationale | Date |
|:---------|:----------|:-----|
| [e.g., Use Cloud SQL over self-managed] | [Why] | [When] |

### Constraints
- **Budget:** [e.g., $0/mo for MVP]
- **Timeline:** [e.g., Ship by Jan 2026]
- **Technical:** [e.g., Must support Python 3.11+]

### Dead Ends (What NOT to try)
- [Approach tried and failed, with reason]

---

## 4. Active Agents & Workflows

### Slash Commands Available
| Command | Purpose |
|:--------|:--------|
| `/deploy` | [e.g., Deploy to Cloud Run] |
| `/archive` | [e.g., Save session state] |

### Active Agents
| Agent | Trigger | Responsibility |
|:------|:--------|:---------------|
| [e.g., Synthesizer] | [When] | [What it does] |

### Key Files
| File | Purpose |
|:-----|:--------|
| `cloudbuild.yaml` | CI/CD pipeline |
| `.brain/state.json` | Brain state |
| `task.md` | Sprint backlog |

---

## 5. Open Tasks & Backlog

### 🔴 Must Do (Blocking)
- [ ] [Task 1] — [File/Command]
- [ ] [Task 2] — [File/Command]

### 🟡 Should Do (Tech Debt)
- [ ] [Task 3] — [File/Command]

### 🟢 Nice to Have
- [ ] [Task 4]

---

## 6. Gotchas & Non-Obvious Behavior

### Pitfall #1: [Name]
- **Symptom:** [What you'll see]
- **Cause:** [Why it happens]
- **Fix:** [How to resolve]

### Pitfall #2: [Name]
- **Symptom:** [What you'll see]
- **Cause:** [Why it happens]  
- **Fix:** [How to resolve]

### Edge Cases
| Scenario | Behavior | Workaround |
|:---------|:---------|:-----------|
| [e.g., Cold start] | [30s delay] | [Pre-warm] |

---

## 7. Credentials & Secrets (Reference Only)

> ⚠️ **Never include actual secrets.** Reference locations only.

| Secret | Location | Notes |
|:-------|:---------|:------|
| [DB Password] | [Secret Manager / Env Var] | [Last rotated] |

---

## 8. Quick Commands

```bash
# Health check
curl [URL]/api/health

# Deploy
gcloud builds submit --config=cloudbuild.yaml

# Rollback
gcloud run services update-traffic [SERVICE] --to-revisions=[REV]=100

# View logs
gcloud run services logs read [SERVICE] --region [REGION]
```

---

## 9. Session Resumption Key

**Last Session:** [DATE]  
**Stopped At:** [What we were doing]  
**Next Step:** [Exact next action]  
**Blockers:** [If any]

---

*Template Version: 1.0 | Created for Antigravity context preservation*
