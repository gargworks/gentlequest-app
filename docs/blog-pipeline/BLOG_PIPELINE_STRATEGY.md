# Blog Pipeline & Content Strategy

> **Companion Doc**: [blog-post.md](../../.agent/workflows/blog-post.md) — Execution protocol for writing and publishing.

This is the **what to write**. The Blog Post Workflow is the **how to write it**.

> Synthesized from 11+ Antigravity conversations (2026-01-15)

---

## Technical Infrastructure (from prior sessions)

| Component | Stack | Location | Status |
|-----------|-------|----------|--------|
| **GentleQuest Blog** | Astro Blog | `gentlequest-blog/` | ✅ Live on Render |
| **Nucleus Blog** | Astro + Starlight | `mcp-server-nucleus/website/` | ✅ Live on Render |
| **Deployment** | Render Static Sites | `render.yaml` | ✅ Configured |
| **Author Identity** | `gentlequest_dev` / Team | Both blogs | ✅ Privacy-preserved |

### Dual-Blog Cross-Pollination Strategy

| From Nucleus (Brain) | To GentleQuest (Heart) |
|---------------------|------------------------|
| Technical deep-dives | "Why it matters for you" summaries |
| Local-first privacy theory | "Your data stays with you" messaging |
| API/SDK documentation | Feature announcements |

---

## Research Topics (Exhaustive MD Sources)

| Topic | Research Coverage | Blog Potential |
|-------|------------------|----------------|
| **ADHD & Burnout** | Clinical ASRS screening, developer prevalence | "Why Developers Burn Out (And What We're Building)" |
| **Corporate Wellness (B2B)** | Enterprise dashboard, ROI metrics | "The Business Case for Developer Wellness" |
| **Growth Loops** | Reddit JSON hacks, SGE/GEO optimization | "How We Hack Reddit for Organic Growth" |
| **Local-First AI** | Data sovereignty, offline-first architecture | ✅ Published: `why-local-first-ai-matters.md` |
| **Streak Psychology** | Gamification harm, "Total Active Days" concept | ✅ Published: `streaks-are-broken.md` |

> [!NOTE]
> These topics were extensively researched in prior sessions. If writing about them, cross-reference `.brain/artifacts/research/` or ask for the MASTER_SESSION_REPORT.

---

## Key Referenced Documents (from prior chats)

| Document | Path | What It Contains |
|----------|------|------------------|
| **MASTER_SESSION_REPORT** | `.brain/artifacts/synthesis/MASTER_SESSION_REPORT_20260110.md` | Verbatim tables, competitive analysis, technical specs, strategic consensus |
| **Oracle Audit Workflow** | `.agent/workflows/oracle-audit.md` | Anti-hallucination verification protocol |
| **Blog Export Protocol** | `blog-export-20260114/BLOG_EXPORT_PROTOCOL.md` | Source verification, provenance, kill switch rules |
| **Render Config** | `render.yaml` | Dual-blog static site deployment config |
| **Streaks are Broken** | `gentlequest-blog/src/content/blog/streaks-are-broken.md` | Published GentleQuest post on gamification harm |
| **Why Local-First AI** | `mcp-server-nucleus/website/src/content/docs/blog/why-local-first-ai-matters.md` | Published Nucleus post on data sovereignty |
| **GentleQuest Reddit Growth** | `docs/GENTLEQUEST_REDDIT_GROWTH_STRATEGY.md` | Reddit-specific distribution tactics |
| **Nucleus Growth Strategy** | `docs/NUCLEUS_GROWTH_STRATEGY.md` | Channel strategy, posting protocols |
| **Growth Automation** | `docs/product/GROWTH_AUTOMATION_STRATEGY.md` | Marketing → Product feedback loop |
| **2026 Growth Playbook** | `.brain/artifacts/research/2026_growth_playbook.md` | GEO, Social Search, Dark Social, Double-Sided Content Engine |

---

## Research Library (`.brain/artifacts/research/`)

**28 research files available for blog content.** Key docs by category:

### Clinical / Product Research
| File | Blog Potential |
|------|----------------|
| `ADHD_product_strategy.md` | "Why We Built GentleQuest for ADHD Developers" |
| `burnout_recovery_framework.md` | "The Burnout Recovery Framework We Use" |
| `clinical_validation_pathway.md` | "Our Path to Clinical Validation" |
| `crisis_escalation_protocol.md` | "How We Handle Mental Health Crises in an AI App" |
| `simulated_user_research.md` | "What We Learned from 100 Simulated User Sessions" |

### Market / Competitive Research
| File | Blog Potential |
|------|----------------|
| `competitive_mental_health_2024.md` | "Mental Health App Landscape 2024" |
| `b2b_market_sizing_2024.md` | "The $X Billion B2B Wellness Market" |
| `corporate_wellness_landscape.md` | "Why Corporate Wellness Programs Fail" |
| `funding_landscape_2024.md` | "Mental Health Startup Funding Trends" |
| `benchmark_sota_2025.md` | "State of the Art in AI Mental Health (2025)" |

### Technical / Infrastructure Research
| File | Blog Potential |
|------|----------------|
| `mcp_usage_synthesis.md` | "How We Use MCP in Production" |
| `mcp_dev_best_practices.md` | "MCP Development Best Practices" |
| `hardening_patterns_research.md` | "Hardening Patterns for Production AI" |
| `agentic_communities_map.md` | "The Agentic AI Community Landscape" |
| `growth_loop_technical_analysis.md` | "Building Growth Loops into Your Product" |

### B2B Strategy
| File | Blog Potential |
|------|----------------|
| `B2B_dashboard_spec.md` | "What Enterprise Wellness Buyers Actually Want" |
| `b2b_pricing_strategy.md` | "How We Price for Enterprise" |
| `university_pilot_playbook.md` | "Running a University Pilot: A Playbook" |
| `clinical_advisor_playbook.md` | "Working with Clinical Advisors" |

> [!TIP]
> Before writing a blog, search this library for existing research to prevent re-work and ensure claims are grounded.

### Core Frameworks (from 2026 Growth Playbook)

**The Three Buckets of Organic Reach:**
1. **GEO (Generative Engine Optimization)**: Optimize for AI citations, not clicks. Use JSON-LD, "TL;DR for AI" at top.
2. **Social Search**: TikTok/Reddit are the new Google. 15-second "Paralysis Hacks", lo-fi authentic video.
3. **Dark Social**: Build trust in unsearchable spaces (Discord, Slack). Open source + building in public.

**The Dopamine-Trust Loop:**
```
Dopamine (Social hack) → Education (Blog deep-dive) → Trust (Privacy guarantee) → Conversion
```

### Verbatim Excerpts Worth Preserving

> **"Vibe Coding" Strategy**: Use Astro + Starlight for docs and blogs in the same repo. Write alongside code.

> **SGE/GEO Principle**: "TL;DR for AI Engines" — First 2 sentences should answer the question directly so AI search engines cite you.

> **Dual-Blog Synergy**: "Both articles include 'The Engine of Trust' sections that link to each other, creating a high-trust loop for readers."

> **Author Privacy**: "Confirmed `author: 'gentlequest_dev'` for both to protect your professional identity while building brand reputation."

---

## Cross-Conversation Themes → Blog Ideas

| Conversation | Theme | Blog Potential | Anti-Hallucination Check |
|--------------|-------|----------------|--------------------------|
| **Strategic Alignment & UI Verification** (Current) | IIP as Meta-Engine | ✅ Published: `BLOG_IIP_VS_CHATGPT_STRESS_TEST.md` | Browser recordings, API logs |
| **Fixing Lint Errors** | Astro build gotchas | 📝 "Common Astro Blog Build Errors (And How to Fix Them)" | Terminal output from actual builds |
| **Render Billing Rescue** | Cost control for startups | 📝 "How We Cut Our Render Bill by 70% Without Downtime" | Billing screenshots, service configs |
| **Recall DB Recovery Protocol** | Postgres disaster recovery | 📝 "The Day Our Database Died: A Recovery Playbook" | Cloud SQL logs, migration scripts |
| **Fixing Chat UI** | Flutter real-time chat | 📝 "Building a Real-Time Chat UI in Flutter with Riverpod" | Code diffs, screenshot comparisons |
| **Fix App Routing Protocol** | Domain-based routing | 📝 "Subdomain Routing in FastAPI: app.* vs www.*" | curl commands, Host header tests |
| **Reviewing Default App Route Fix** | Code review process | 📝 "How We Use AI Critic Agents for PR Reviews" | Review checklists, actual findings |
| **Archival Protocol Refinement** | Agentic memory | ✅ Partial: `why-local-first-ai-matters.md` | Protocol docs, Nucleus MCP code |
| **Windsurf Context Migration** | IDE context portability | 📝 "Migrating AI Context Between Cursor, Windsurf, and Claude" | Export scripts, file diffs |
| **Next Task Prioritization** | Agentic task management | 📝 "How We Let AI Prioritize Our Sprint Backlog" | Nucleus task outputs, decision logs |
| **Implementing Agentic Wellness** | AI-driven interventions | 📝 "Agentic Wellness: When AI Decides You Need a Break" | Function call logs, intervention traces |

---

## Current Pipeline Status

### ✅ Published
| File | Location | Status |
|------|----------|--------|
| `streaks-are-broken.md` | GentleQuest Blog | Live |
| `why-local-first-ai-matters.md` | Nucleus Blog | Live |

### 📦 Ready to Publish (Export Bundles Exist)
| File | Location | Needs |
|------|----------|-------|
| `BLOG_IIP_VS_CHATGPT_STRESS_TEST.md` | `blog-export-stress-test/` | Final proofread, deploy |
| `BLOG_IIP_PRODUCT_DISCOVERY_ENGINE.md` | `blog-export-iip/` | Update paths, deploy |
| `BLOG_CLOUD_RUN_JOURNEY.md` | `blog-export-20260114/` | Oracle audit, deploy |
| `BLOG_MASTER_NUCLEUS_JOURNEY.md` | `blog-export-20260114/` | Oracle audit, deploy |

### 📝 Drafts / Ideas (Need Creation)
| Topic | Source Conversation | Priority | Effort |
|-------|---------------------|----------|--------|
| "Common Astro Blog Build Errors" | Fixing Lint Errors | Medium | Low |
| "How We Cut Render Bill 70%" | Render Billing Rescue | High | Medium |
| "The Day Our Database Died" | Recall DB Recovery | High | High |
| "Real-Time Chat in Flutter" | Fixing Chat UI | Medium | Medium |
| "Subdomain Routing in FastAPI" | Fix App Routing | Low | Low |
| "AI Critic Agents for PR Reviews" | Reviewing Default App Route | Medium | Medium |
| "Migrating AI Context Between IDEs" | Windsurf Context Migration | Medium | Low |
| "AI Prioritizes Our Sprint Backlog" | Next Task Prioritization | High | Medium |
| "Agentic Wellness Interventions" | Implementing Agentic Wellness | High | High |

---

## Recommended Blog Series

### Series 1: "Building in Production" (DevOps/Infra)
1. "The Day Our Database Died" (Recovery story)
2. "How We Cut Render Bill 70%" (Cost optimization)
3. "Subdomain Routing in FastAPI" (Architecture)
4. "Common Astro Build Errors" (Gotchas)

**Audience**: r/devops, Hacker News, Twitter DevOps community
**Persona**: "The Ops-Fatigued Founder"

### Series 2: "Agentic AI in Practice" (AI/Tooling)
1. "IIP vs ChatGPT: 3 Stress Tests" (Benchmark) ✅ Ready
2. "AI Prioritizes Our Sprint Backlog" (Workflow)
3. "AI Critic Agents for PR Reviews" (Code quality)
4. "Migrating AI Context Between IDEs" (Portability)

**Audience**: r/ClaudeAI, r/LocalLLaMA, AI Twitter
**Persona**: "Context-Fatigued Claude User"

### Series 3: "Mental Health for Builders" (Product)
1. "Streaks are Broken" ✅ Published
2. "Agentic Wellness Interventions" (AI-driven self-care)
3. "Why We Built a Mental Health App for Devs" (Origin story)

**Audience**: LinkedIn, r/ExperiencedDevs, Indie Hackers
**Persona**: "Alex the Anxious Coder"

---

## Anti-Hallucination Checklist (Apply to Each Post)

| Check | How to Verify |
|-------|---------------|
| **Code exists in repo** | `ls` or `cat` the file path |
| **Terminal output is real** | Check command IDs in Antigravity logs |
| **Recordings are authentic** | Timestamp in filename (e.g., `_1768460271524.webp`) |
| **Metrics are sourced** | Cross-reference with Cloud Console, Render Dashboard |
| **Quotes are not fabricated** | Link to source or conversation ID |

---

## Next Actions

1. **Immediate**: Publish `BLOG_IIP_VS_CHATGPT_STRESS_TEST.md` (ready, verified)
2. **This Week**: Write "How We Cut Render Bill 70%" (high impact, medium effort)
3. **Backlog**: Create series structure in `docs/blog-pipeline/` folder

---

## Provenance
- **Session ID**: `6c8d0959-9c69-4eb5-8e9c-303dd8b732ac`
- **Date Generated**: 2026-01-15
- **Source Conversations**: 11+ (listed in table above)
- **Verification**: Cross-referenced with file system, no fabricated claims
