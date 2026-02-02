# TESTING STRATEGY - GentleQuest 2026
## Test Coverage Map and Verification Procedures

**Purpose:** Know what's tested, how to test, and verify changes  
**Valid Until:** December 2026  
**Last Updated:** January 16, 2026

---

## 1. TEST INVENTORY

### Backend Tests (Python)
```
/Users/lokeshgarg/ai-mvp-backend/tests/
├── test_app.py              # Core Flask routes
├── test_providers.py        # AI provider tests
├── test_mood.py             # Mood tracking
├── test_quest.py            # Quest system
├── test_rate_limiter.py     # Rate limiting
└── test_backend_mvp.py      # MVP integration tests
```

### Frontend Tests (Flutter)
```
/Users/lokeshgarg/ai-mvp-backend/ai_buddy_web/test/
├── widget_test.dart         # Widget tests
├── provider_test.dart       # Provider unit tests
└── integration_test/        # Integration tests
```

### Load Tests
```
/Users/lokeshgarg/ai-mvp-backend/tests/
└── locustfile.py            # Locust load tests
```

---

## 2. COVERAGE MAP

### What's Tested

| Component | Unit | Integration | E2E | Load |
|-----------|------|-------------|-----|------|
| /api/health | ✅ | ✅ | ✅ | ✅ |
| /api/chat | ⚠️ | ✅ | ⚠️ | ✅ |
| /api/mood/* | ✅ | ✅ | ❌ | ⚠️ |
| /api/quest/* | ⚠️ | ⚠️ | ❌ | ❌ |
| /api/community/* | ⚠️ | ⚠️ | ❌ | ❌ |
| AI Providers | ✅ | ⚠️ | ❌ | ❌ |
| Crisis Detection | ✅ | ✅ | ❌ | ❌ |
| Rate Limiting | ✅ | ✅ | ❌ | ✅ |

**Legend:** ✅ Good | ⚠️ Partial | ❌ Missing

### What's NOT Tested (Gaps)

1. **E2E Flutter flows** - No Playwright/Selenium
2. **Quest completion full cycle** - Partial coverage
3. **Community reactions** - Minimal tests
4. **Session persistence** - Manual only
5. **AI fallback chain** - Mocked, not live

---

## 3. HOW TO RUN TESTS

### Backend Unit Tests
```bash
cd /Users/lokeshgarg/ai-mvp-backend

# All tests
python3 -m pytest tests/ -v

# Specific test file
python3 -m pytest tests/test_app.py -v

# With coverage
python3 -m pytest tests/ --cov=. --cov-report=html
```

### Backend Integration Tests (Requires running server)
```bash
# Start server first
python3 app.py &

# Run MVP tests
BASE_URL=http://localhost:5055 python3 tests/test_backend_mvp.py
```

### Flutter Tests
```bash
cd /Users/lokeshgarg/ai-mvp-backend/ai_buddy_web

# All tests
flutter test

# Specific test
flutter test test/widget_test.dart

# With coverage
flutter test --coverage
```

### Load Tests
```bash
cd /Users/lokeshgarg/ai-mvp-backend

# Start Locust
locust -f tests/locustfile.py --host=https://gentlequest.onrender.com

# Open http://localhost:8089 to configure and run
```

---

## 4. VERIFICATION PROCEDURES

### Before Any Deploy

```bash
# 1. Run backend tests
python3 -m pytest tests/ -v

# 2. Run Flutter tests
cd ai_buddy_web && flutter test

# 3. Build Flutter web
flutter build web --release

# 4. Verify health endpoint
curl http://localhost:5055/api/health
```

### After Deploy (Smoke Tests)

```bash
# 1. Health check
curl https://gentlequest.onrender.com/api/health

# 2. Ping endpoint
curl https://gentlequest.onrender.com/api/ping

# 3. Quick chat test
curl -X POST https://gentlequest.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "session_id": "smoke-test-123"}'

# 4. Mood endpoint
curl https://gentlequest.onrender.com/api/mood/entries?session_id=test
```

### Critical Path Verification

| Path | Verification Command |
|------|---------------------|
| Chat | `curl -X POST /api/chat -d '{"message":"hi","session_id":"test"}'` |
| Mood | `curl -X POST /api/mood/entries -d '{"mood_value":7,"session_id":"test"}'` |
| Quest | `curl /api/quest/catalog` |
| Crisis | `curl -X POST /api/chat -d '{"message":"I feel hopeless","session_id":"test","country":"US"}'` |

---

## 5. TEST DATA

### Test Session IDs
```
test-session-123        # General testing
smoke-test-123          # Post-deploy smoke
load-test-{n}           # Load testing
crisis-test-123         # Crisis detection testing
```

### Test Countries for Crisis
```
IN, US, UK, CA, AU, NZ, IE, SG, PH, ZA, DE
```

### Test Mood Values
```
1-10 scale (integer)
```

---

## 6. MOCKING STRATEGY

### AI Providers (for unit tests)
```python
# tests/conftest.py
@pytest.fixture
def mock_gemini():
    with patch('providers.gemini_provider.GeminiProvider') as mock:
        mock.return_value.generate_response.return_value = "Mocked response"
        yield mock
```

### Database (for unit tests)
```python
# Use SQLite in-memory for tests
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
```

### Redis (for unit tests)
```python
# Use fakeredis
import fakeredis
app.config['SESSION_REDIS'] = fakeredis.FakeStrictRedis()
```

---

## 7. CI/CD TEST MATRIX (Future)

### Proposed GitHub Actions
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
      - run: cd ai_buddy_web && flutter test
```

---

## 8. REGRESSION TEST CHECKLIST

### After Major Changes

- [ ] Health endpoint returns 200
- [ ] Chat responds within 5s
- [ ] Mood can be logged
- [ ] Quest catalog loads
- [ ] Crisis keywords trigger resources
- [ ] Rate limiting works
- [ ] Sessions persist

### After AI Provider Changes

- [ ] Primary provider works
- [ ] Fallback triggers on error
- [ ] Streaming works (if enabled)
- [ ] Response quality acceptable

### After Database Changes

- [ ] Migrations applied
- [ ] Existing data preserved
- [ ] New columns have defaults
- [ ] Indexes on query columns

---

## 9. PERFORMANCE BASELINES

| Endpoint | Target | Current | Alert |
|----------|--------|---------|-------|
| /api/health | < 100ms | ~50ms | > 500ms |
| /api/chat | < 2s | ~1.5s | > 5s |
| /api/mood/entries POST | < 500ms | ~200ms | > 1s |
| /api/quest/catalog | < 500ms | ~300ms | > 1s |

---

## 10. TEST IMPROVEMENT PRIORITIES

### P1 - Add This Sprint
1. E2E tests for critical paths (Playwright)
2. AI fallback chain integration test
3. Session persistence test

### P2 - Add Next Quarter
1. Full quest cycle tests
2. Community feature tests
3. Automated visual regression

### P3 - Backlog
1. Performance benchmarks in CI
2. Security scanning
3. Accessibility tests
