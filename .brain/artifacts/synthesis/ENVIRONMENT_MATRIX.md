# ENVIRONMENT MATRIX - GentleQuest 2026
## All Environment Variables, Secrets, and Their Purposes

**Purpose:** Single source of truth for configuration  
**Valid Until:** December 2026  
**Last Updated:** January 16, 2026

---

## 1. PRODUCTION (Render)

### Core Application
| Variable | Purpose | Where Set | Example |
|----------|---------|-----------|---------|
| `ENVIRONMENT` | Environment identifier | render.yaml | `production` |
| `RENDER` | Render platform flag | render.yaml | `true` |
| `PORT` | Server port | Dockerfile | `5055` |
| `SECRET_KEY` | Session encryption | Dashboard (generated) | `auto-generated` |
| `VERSION` | App version | render.yaml | `2.1.0` |

### Database
| Variable | Purpose | Where Set | Example |
|----------|---------|-----------|---------|
| `DATABASE_URL` | PostgreSQL connection | Dashboard | `postgresql://user:pass@host:5432/db` |
| `DB_HOST` | Database host (GCP) | cloudbuild.yaml | `/cloudsql/project:region:instance` |
| `DB_USER` | Database user | cloudbuild.yaml | `gentlequest` |
| `DB_NAME` | Database name | cloudbuild.yaml | `gentlequest` |
| `DB_PASSWORD` | Database password | Secret Manager | `secret` |

### Cache/Sessions
| Variable | Purpose | Where Set | Example |
|----------|---------|-----------|---------|
| `REDIS_URL` | Redis connection | Dashboard | `redis://user:pass@host:6379` |
| `SESSION_RETENTION_DAYS` | Session expiry | render.yaml | `14` |

### AI Providers
| Variable | Purpose | Where Set | Example |
|----------|---------|-----------|---------|
| `AI_PROVIDER` | Default provider | render.yaml | `gemini` |
| `GEMINI_API_KEY` | Google Gemini API | Dashboard | `AIza...` |
| `GEMINI_API_KEYS` | Multiple keys (rotation) | Dashboard | `key1,key2,key3` |
| `OPENAI_API_KEY` | OpenAI fallback | Dashboard | `sk-...` |
| `PPLX_API_KEY` | Perplexity fallback | Dashboard | `pplx-...` |

### Data Retention
| Variable | Purpose | Where Set | Default |
|----------|---------|-----------|---------|
| `MESSAGE_RETENTION_DAYS` | Message cleanup | render.yaml | `30` |
| `ERROR_LOG_RETENTION_DAYS` | Error log cleanup | render.yaml | `14` |
| `ANALYTICS_RETENTION_DAYS` | Analytics cleanup | render.yaml | `90` |

### Observability
| Variable | Purpose | Where Set | Example |
|----------|---------|-----------|---------|
| `SENTRY_DSN_BACKEND` | Sentry error tracking | Dashboard | `https://...@sentry.io/...` |
| `SENTRY_TRACES_SAMPLE_RATE` | Trace sampling | render.yaml | `0` (disabled) |
| `SENTRY_PROFILES_SAMPLE_RATE` | Profile sampling | render.yaml | `0` (disabled) |

### Feature Flags
| Variable | Purpose | Where Set | Default |
|----------|---------|-----------|---------|
| `COMMUNITY_ENABLED` | Enable community | render.yaml | `true` |
| `COMMUNITY_POSTING_ENABLED` | Allow user posts | render.yaml | `false` |
| `TEMPLATES_ONLY` | Curated content only | render.yaml | `true` |

### Rate Limits
| Variable | Purpose | Where Set | Default |
|----------|---------|-----------|---------|
| `RATE_LIMITS_COMMUNITY_FEED` | Feed rate limit | render.yaml | `120 per minute` |
| `RATE_LIMITS_REACTION` | Reaction limit | render.yaml | `20/min; 200/day` |
| `RATE_LIMITS_REPORT` | Report limit | render.yaml | `10/min; 100/day` |

### Security
| Variable | Purpose | Where Set | Example |
|----------|---------|-----------|---------|
| `ADMIN_API_TOKEN` | Admin endpoint auth | Dashboard | `random-token` |
| `CORS_ORIGINS` | Allowed origins | render.yaml | `https://gentlequest.onrender.com,...` |

---

## 2. LOCAL DEVELOPMENT

### .env file (NOT committed)
```bash
# Copy from .env.example and fill in values

# Database (Docker)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gentlequest

# Redis (Docker)
REDIS_URL=redis://localhost:6379

# AI (use your own keys)
GEMINI_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here

# App
ENVIRONMENT=development
SECRET_KEY=dev-secret-key
PORT=5055
```

### Docker Compose (local services)
```bash
# Start local Postgres + Redis
docker-compose up -d

# Verify
docker ps
```

---

## 3. FLUTTER CONFIGURATION

### Build-time variables
```bash
# Debug (local backend)
flutter run -d chrome

# Release (production)
flutter build web --release \
  --dart-define=API_URL=https://gentlequest.onrender.com
```

### Runtime configuration (api_config.dart)
```dart
class ApiConfig {
  static String get baseUrl {
    if (kIsWeb) {
      if (kDebugMode) {
        return 'http://localhost:5055';  // Local dev
      }
      return '';  // Same-origin in production
    }
    return 'https://gentlequest.onrender.com';  // Mobile
  }
}
```

### Firebase (google-services.json / GoogleService-Info.plist)
- Located in platform-specific folders
- Contains Firebase project config
- NOT committed (in .gitignore)

---

## 4. GCP CONFIGURATION (cloudbuild.yaml)

| Variable | Purpose | Where Set |
|----------|---------|-----------|
| `$PROJECT_ID` | GCP project | Cloud Build |
| `$_NEXT_PUBLIC_API_URL` | Nucleus HUD API | Substitution |
| `$_NEXT_PUBLIC_APP_API_URL` | App API | Substitution |

---

## 5. MOBILE SIGNING

### Android (key.properties) - NOT committed
```properties
storePassword=your-store-password
keyPassword=your-key-password
keyAlias=your-key-alias
storeFile=/path/to/keystore.jks
```

### iOS (via Xcode)
- Team ID in project settings
- Provisioning profiles in Apple Developer

---

## 6. SECRETS ROTATION GUIDE

### When to rotate:
- Suspected compromise
- Team member departure
- Quarterly (best practice)

### How to rotate:

**API Keys:**
1. Generate new key in provider dashboard
2. Add new key to Render environment
3. Deploy to verify
4. Revoke old key

**Database password:**
1. Change in Render PostgreSQL dashboard
2. Update DATABASE_URL in environment
3. Restart service

**SECRET_KEY:**
⚠️ WARNING: Invalidates all sessions
1. Generate new: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Update in Render dashboard
3. Deploy (users will need to re-authenticate)

---

## 7. ENVIRONMENT CHECKLIST

### New deployment setup:
- [ ] DATABASE_URL configured
- [ ] REDIS_URL configured
- [ ] GEMINI_API_KEY set
- [ ] OPENAI_API_KEY set (fallback)
- [ ] SECRET_KEY generated
- [ ] CORS_ORIGINS updated
- [ ] Health check passing

### Feature deployment:
- [ ] Required env vars documented
- [ ] Defaults set in render.yaml
- [ ] Secrets added to dashboard
- [ ] Local .env.example updated

---

## QUICK REFERENCE

| Need | Variable | Where |
|------|----------|-------|
| Change AI provider | `AI_PROVIDER` | render.yaml |
| Add new API key | Dashboard | Render secrets |
| Change rate limits | `RATE_LIMITS_*` | render.yaml |
| Enable feature | `FEATURE_ENABLED` | render.yaml |
| Debug locally | `.env` | Local file |
