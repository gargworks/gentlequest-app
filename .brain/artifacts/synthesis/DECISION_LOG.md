# DECISION LOG (ADRs) - GentleQuest 2026
## Architecture Decision Records - Why Things Are Built This Way

**Purpose:** Capture decision rationale to prevent re-debating settled issues  
**Valid Until:** December 2026  
**Last Updated:** January 16, 2026

---

## ADR-014: Native google.generativeai Fallback

**Date:** January 16, 2026  
**Status:** Accepted  
**Context:** `providers/gemini.py` used `mcp_server_nucleus.runtime.llm_client.DualEngineLLM` exclusively, but mcp_server_nucleus is not deployed to Render production, causing chat endpoint failure.

**Decision:** Add native `google.generativeai` fallback when `mcp_server_nucleus` import fails.

**Rationale:**
- Production environment doesn't have mcp_server_nucleus installed
- google-generativeai is already in requirements.txt
- Maintains backward compatibility with local development

**Implementation:**
```python
try:
    from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
    # ... use DualEngineLLM
except ImportError:
    import google.generativeai as genai
    # ... use native genai
```

**Consequences:**
- ✅ Chat endpoint works in production without mcp_server_nucleus
- ✅ Local development can use DualEngineLLM when available
- ⚠️ Function calling tools format may differ slightly

---

## ADR-001: Flask over FastAPI for Backend

**Date:** 2024 (Initial)  
**Status:** Accepted  
**Context:** Needed Python backend for AI integration

**Decision:** Use Flask 3.0

**Rationale:**
- Simpler learning curve
- Sufficient for current scale
- Good ecosystem (Flask-SQLAlchemy, Flask-CORS, etc.)
- SSE streaming works well with Flask

**Alternatives Considered:**
- FastAPI: More modern but added complexity
- Django: Overkill for API-focused app

**Consequences:**
- Synchronous by default (async possible but not native)
- Manual OpenAPI docs (vs FastAPI auto-gen)

---

## ADR-002: Provider Pattern for AI Failover

**Date:** 2024  
**Status:** Accepted  
**Context:** Need reliability when AI providers have outages

**Decision:** Chain of providers: Gemini → OpenAI → Perplexity

**Rationale:**
- Gemini is cheapest and fastest
- OpenAI is most reliable fallback
- Perplexity as last resort
- Automatic failover on any exception

**Implementation:**
```python
for provider in [GeminiProvider, OpenAIProvider, PerplexityProvider]:
    try:
        return provider().generate(message)
    except:
        continue
```

**Consequences:**
- Need API keys for all providers
- Slight latency on failover
- Cost varies by provider used

---

## ADR-003: Flutter Web over React/Next.js

**Date:** 2024  
**Status:** Accepted  
**Context:** Need web + mobile from single codebase

**Decision:** Flutter for all platforms

**Rationale:**
- Single codebase for web, iOS, Android
- DhiWise Figma-to-Flutter tooling
- Provider state management is simple
- Hot reload speeds development

**Alternatives Considered:**
- React + React Native: Two codebases
- Next.js: Web only, would need separate mobile

**Consequences:**
- Larger initial bundle size
- SEO requires extra work
- Web performance slightly behind native React

---

## ADR-004: Per-Session Rate Limiting (Not IP)

**Date:** November 2025  
**Status:** Accepted  
**Context:** IP-based limits blocked legitimate users behind NAT

**Decision:** Rate limit by session_id, not IP

**Rationale:**
- Many users share IPs (offices, universities, mobile carriers)
- Session ID is unique per user
- Prevents blocking legitimate traffic

**Implementation:**
```python
@limiter.limit("120 per minute", key_func=lambda: request.json.get('session_id', 'anonymous'))
```

**Consequences:**
- Malicious users can create new sessions
- Mitigated by combining with global limits

---

## ADR-005: SSE over WebSockets for Streaming

**Date:** 2024  
**Status:** Accepted  
**Context:** Need real-time AI response streaming

**Decision:** Server-Sent Events (SSE)

**Rationale:**
- Simpler than WebSockets
- Works through most proxies/firewalls
- One-way is sufficient (server → client)
- Native browser support

**Alternatives Considered:**
- WebSockets: Bidirectional overkill
- Long polling: Less efficient

**Consequences:**
- Can't send client messages mid-stream
- Must use POST for new messages

---

## ADR-006: PostgreSQL over SQLite for Production

**Date:** 2025  
**Status:** Accepted  
**Context:** Need persistent, scalable database

**Decision:** PostgreSQL on Render

**Rationale:**
- Production-grade reliability
- JSON column support
- Managed service reduces ops burden
- Better concurrent access than SQLite

**Consequences:**
- Requires connection string management
- Free tier has storage limits
- Need migration strategy for schema changes

---

## ADR-007: Redis for Sessions and Rate Limits

**Date:** 2025  
**Status:** Accepted  
**Context:** Need fast session lookups and rate limit counters

**Decision:** External Redis (not Render managed)

**Rationale:**
- Flask-Session supports Redis backend
- Fast atomic operations for rate limiting
- Shared state across potential replicas

**Alternatives Considered:**
- Filesystem sessions: Doesn't scale
- Database sessions: Slower

**Consequences:**
- Extra service dependency
- Fallback to filesystem if Redis unavailable

---

## ADR-008: Render Free Tier with Keep-Alive

**Date:** November 2025  
**Status:** Accepted (temporary)  
**Context:** Service sleeps after 15 mins on free tier

**Decision:** GitHub Actions pings /api/ping every 13 minutes

**Rationale:**
- Keeps service warm without cost
- Lightweight endpoint (no DB/Redis)
- Automated via scheduled workflow

**Consequences:**
- Still cold starts on first request after sleep
- Should upgrade to paid tier for production

---

## ADR-009: Community Phase 0 (Templates Only)

**Date:** November 2025  
**Status:** Accepted  
**Context:** Want community features but need moderation

**Decision:** Start with curated template posts only

**Rationale:**
- No user-generated content initially
- Avoids moderation burden
- Tests engagement before full feature

**Consequences:**
- Limited community interaction
- Need Phase 1 for real community

---

## ADR-010: Crisis Detection Inline (Not Separate Service)

**Date:** 2024  
**Status:** Accepted  
**Context:** Need to detect crisis keywords and provide resources

**Decision:** Inline detection in chat route with country-specific resources

**Rationale:**
- Speed: No extra network hop
- Simplicity: Pattern matching sufficient
- Coverage: 11 countries with local helplines

**Implementation:**
```python
CRISIS_KEYWORDS = ["suicide", "kill myself", "end my life", ...]
if any(kw in message.lower() for kw in CRISIS_KEYWORDS):
    return crisis_response(country)
```

**Consequences:**
- May have false positives/negatives
- Consider ML-based detection for v2

---

## ADR-011: XP/Gamification for Engagement

**Date:** 2024  
**Status:** Accepted  
**Context:** Need to encourage consistent usage

**Decision:** XP system with levels, streaks, badges

**Rationale:**
- Proven engagement pattern
- Mental health benefits from habit formation
- Non-punitive (no penalties for missing days)

**Implementation:**
- Mood log: 10 XP
- Quest step: 10 XP
- Quest complete: 50 XP bonus
- Daily assessment: 25 XP (once/day)

**Consequences:**
- Must balance gamification vs therapy
- Avoid addictive patterns

---

## ADR-012: Multi-Environment Agent Hierarchy

**Date:** December 2025  
**Status:** Accepted  
**Context:** Multiple AI tools, need coordination

**Decision:** AGENTS.md constitution with roles

**Rationale:**
- Windsurf: Strategy (the "WHY")
- Antigravity: Creation (the "HOW")
- Gemini CLI: Execution (the "WHAT")

**Consequences:**
- Context must be portable (.brain/ folder)
- Need session handoff protocols

---

## DECISION TEMPLATE

```markdown
## ADR-XXX: [Title]

**Date:** [When decided]
**Status:** [Proposed | Accepted | Deprecated | Superseded]
**Context:** [Why this decision was needed]

**Decision:** [What was decided]

**Rationale:**
- [Reason 1]
- [Reason 2]

**Alternatives Considered:**
- [Alternative 1]: [Why rejected]

**Consequences:**
- [Positive/negative outcomes]
```

---

## PENDING DECISIONS

| Topic | Status | Notes |
|-------|--------|-------|
| Upgrade to Render paid tier | Pending | Need to evaluate costs vs benefits |
| ML-based crisis detection | Proposed | Current keyword matching may miss cases |
| Community Phase 1 | Pending | User posting with moderation |
| Native mobile apps | Deferred | Flutter web-first, native later |
