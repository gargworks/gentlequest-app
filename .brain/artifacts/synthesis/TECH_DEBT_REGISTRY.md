# TECH DEBT REGISTRY - GentleQuest 2026
## Known Issues, Workarounds, and Priorities

**Purpose:** Track known issues to prevent rediscovery  
**Valid Until:** December 2026  
**Last Updated:** January 16, 2026

---

## PRIORITY LEGEND

| Priority | Meaning | Action |
|----------|---------|--------|
| 🔴 P0 | Critical - affects users | Fix immediately |
| 🟠 P1 | High - degraded experience | Fix this sprint |
| 🟡 P2 | Medium - inconvenience | Fix when possible |
| 🟢 P3 | Low - minor/cosmetic | Backlog |

---

## ACTIVE TECH DEBT

### TD-001: Render Free Tier Sleep 🟠 P1

**Issue:** Service sleeps after 15 mins of inactivity

**Current Workaround:** 
- GitHub Actions pings /api/ping every 13 mins
- First request after sleep takes 30-60s

**Proper Fix:** Upgrade to Render Starter ($7/month)

**Impact:** Poor first-request experience for new users

---

### TD-002: Missing user_message Column in conversation_logs 🟡 P2

**Issue:** `conversation_logs` table schema missing `user_message` column

**Current Workaround:**
- Using `messages` table as source of truth
- conversation_logs used for metadata only

**Proper Fix:** 
```sql
ALTER TABLE conversation_logs ADD COLUMN user_message TEXT;
ALTER TABLE conversation_logs ADD COLUMN ai_response TEXT;
```

**Impact:** Minor - data is in messages table

---

### TD-003: Flutter Web Bundle Size 🟡 P2

**Issue:** Initial load ~2-3MB, slow on poor connections

**Current Workaround:** None

**Proper Fix:**
- Enable deferred loading
- Tree-shake unused packages
- Consider code splitting

**Impact:** Slower initial load, especially mobile web

---

### TD-004: Service Worker Caching 🟡 P2

**Issue:** Old UI cached, users see stale version

**Current Workaround:** Tell users to hard refresh

**Proper Fix:**
- Implement cache-busting strategy
- Version-based cache invalidation
- Consider disabling SW for now

**Impact:** Users may not see updates

---

### TD-005: SQLite vs PostgreSQL Local Dev 🟢 P3

**Issue:** Local dev can use SQLite, production uses PostgreSQL

**Current Workaround:** Use Docker for local PostgreSQL

**Proper Fix:** Standardize on PostgreSQL everywhere

**Impact:** Potential schema incompatibilities

---

### TD-006: No Automated Database Backups 🟠 P1

**Issue:** Render free tier PostgreSQL has no auto-backup

**Current Workaround:** Manual pg_dump before major changes

**Proper Fix:**
- Script scheduled backups
- Or upgrade to paid PostgreSQL tier

**Impact:** Data loss risk

---

### TD-007: Rate Limiter Redis Dependency 🟡 P2

**Issue:** If Redis down, rate limiting may fail open

**Current Workaround:** Filesystem fallback for sessions, but not rate limits

**Proper Fix:** Add in-memory rate limit fallback

**Impact:** Potential abuse if Redis fails

---

### TD-008: No CI/CD Pipeline 🟡 P2

**Issue:** No automated tests on PR, manual deploy only

**Current Workaround:** Run tests locally before push

**Proper Fix:**
- GitHub Actions for pytest on PR
- Automated deploy on main merge

**Impact:** Potential regressions

---

### TD-009: Hardcoded Crisis Keywords 🟡 P2

**Issue:** Crisis detection uses hardcoded keyword list

**Current Workaround:** Works for common cases

**Proper Fix:**
- ML-based detection
- Configurable keyword list
- Multi-language support

**Impact:** May miss edge cases

---

### TD-010: No Error Boundary in Flutter 🟢 P3

**Issue:** Unhandled exceptions may crash app

**Current Workaround:** Try-catch in critical paths

**Proper Fix:** Global error boundary widget

**Impact:** Poor UX on unexpected errors

---

### TD-011: Mixed Async Patterns 🟢 P3

**Issue:** Some Flutter code uses async/await, some uses .then()

**Current Workaround:** None

**Proper Fix:** Standardize on async/await

**Impact:** Code readability only

---

### TD-012: Deprecated withOpacity() Usage 🟢 P3

**Issue:** Analyzer warns about deprecated Color.withOpacity()

**Current Workaround:** Ignore warning

**Proper Fix:** Update to Color.withValues()

**Impact:** None currently, future deprecation

---

## RESOLVED TECH DEBT

### TD-R004: mcp_server_nucleus Import in Production ✅ Fixed Jan 16, 2026

**Was:** Multiple production files imported from mcp_server_nucleus which isn't deployed to Render, breaking endpoints.

**Files Fixed:**
- `providers/gemini.py` - Chat endpoint (2 locations)
- `community.py` - Content moderation
- `providers/embeddings.py` - Memory embeddings (2 locations)
- `providers/memory.py` - Memory observer LLM
- `providers/safety.py` - Safety verification LLM

**Fix:** Added native `google.generativeai` fallback with try/except ImportError in all locations.

```python
try:
    from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
    # ... use DualEngineLLM
except ImportError:
    import google.generativeai as genai
    # ... use native genai
```

**Impact:** All AI-powered endpoints now work in production without mcp_server_nucleus

---

### TD-R001: IP-Based Rate Limiting ✅ Fixed Nov 2025

**Was:** Rate limiting by IP blocked users behind NAT

**Fix:** Changed to session-based rate limiting

---

### TD-R002: Keep-Alive Endpoint ✅ Fixed Nov 2025

**Was:** No lightweight health endpoint

**Fix:** Added /api/ping (no DB/Redis check)

---

### TD-R003: RenderFlex Overflow ✅ Fixed Nov 2025

**Was:** Wellness Dashboard overflow on narrow screens

**Fix:** Wrapped chips with Flexible widget

---

## WORKAROUNDS IN PRODUCTION

### W-001: Session ID Injection

**Where:** `api_service.dart` interceptor

**Why:** Ensure every request has session_id

```dart
dio.interceptors.add(InterceptorsWrapper(
  onRequest: (options, handler) {
    options.headers['X-Session-ID'] = SessionManager.sessionId;
    // Also inject in body for POST
    if (options.data is Map) {
      options.data['session_id'] = SessionManager.sessionId;
    }
    return handler.next(options);
  },
));
```

---

### W-002: Country Inference

**Where:** `api_service.dart`

**Why:** Provide crisis resources without explicit location

```dart
String get _inferredCountry {
  final locale = Platform.localeName;
  // Map locale to country code
  return countryFromLocale(locale) ?? 'US';
}
```

---

### W-003: AI Provider Failover

**Where:** `app.py` chat_route

**Why:** Handle provider outages gracefully

```python
for provider in [gemini, openai, perplexity]:
    try:
        return provider.generate(message)
    except Exception as e:
        log_warning(f"[AI_FALLBACK] {provider} failed")
        continue
```

---

## TECH DEBT BUDGET

**Current debt score:** 23 points (moderate)

| Priority | Count | Points Each | Total |
|----------|-------|-------------|-------|
| P0 | 0 | 10 | 0 |
| P1 | 2 | 5 | 10 |
| P2 | 6 | 2 | 12 |
| P3 | 4 | 0.25 | 1 |

**Target:** Keep below 30 points

**Action:** Address P1 items before adding new features

---

## QUARTERLY REVIEW CHECKLIST

- [ ] Review all P0/P1 items
- [ ] Update status of resolved items
- [ ] Add newly discovered debt
- [ ] Recalculate debt score
- [ ] Plan debt paydown for next quarter
