# ARCHITECTURE MAP - GentleQuest 2026
## Component Relationships, Data Flows, Critical Paths

**Purpose:** Enable autonomous development without re-exploration  
**Valid Until:** December 2026  
**Last Updated:** January 16, 2026

---

## 1. SYSTEM TOPOLOGY

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
├─────────────────────────────────────────────────────────────────────┤
│  Flutter Web (ai_buddy_web/)     │  Landing (landing-page/)         │
│  - HomeShell (4 tabs)            │  - Static Astro site             │
│  - Provider state management     │  - gentlequest.app domain        │
│  - Dio HTTP + SSE streaming      │                                  │
└──────────────────┬───────────────┴──────────────────────────────────┘
                   │ HTTPS (Dio/SSE)
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API LAYER (app.py)                            │
├─────────────────────────────────────────────────────────────────────┤
│  Flask 3.0 + Blueprints                                              │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐          │
│  │ /api/chat   │ /api/mood   │ /api/quest  │ /api/community│        │
│  │ (SSE stream)│ (CRUD)      │ (gamification)│ (feed)     │          │
│  └─────────────┴─────────────┴─────────────┴─────────────┘          │
│  Rate Limiting: Flask-Limiter (per-session, not IP)                  │
│  CORS: 6 allowed origins                                             │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐    ┌───────────────┐
│  AI PROVIDERS │    │   DATA LAYER  │
├───────────────┤    ├───────────────┤
│ 1. Gemini     │    │ PostgreSQL    │
│ 2. OpenAI     │    │ - sessions    │
│ 3. Perplexity │    │ - messages    │
│ (failover)    │    │ - moods       │
└───────────────┘    │ - quests      │
                     │ Redis (cache) │
                     └───────────────┘
```

---

## 2. DATA FLOWS

### 2.1 Chat Flow (Critical Path #1)
```
User Input → Flutter ChatProvider → Dio POST /api/chat
    → Flask receives {message, session_id, country}
    → Rate limit check (120/min)
    → Crisis detection (11 country-specific resources)
    → AI Provider chain (Gemini → OpenAI → Perplexity)
    → Response streamed via SSE
    → Flutter StreamController broadcasts to UI
    → Message persisted to PostgreSQL
```

**Key Files:**
- `ai_buddy_web/lib/providers/chat_provider.dart` - State management
- `ai_buddy_web/lib/services/api_service.dart` - HTTP client
- `app.py:chat_route()` - Backend handler
- `providers/gemini_provider.py` - Primary AI

### 2.2 Mood Tracking Flow (Critical Path #2)
```
User selects mood → MoodProvider.addMood()
    → Dio POST /api/mood/entries
    → Flask validates, stores in PostgreSQL
    → Returns updated streak, XP
    → Flutter updates local state
    → Analytics event fired
```

**Key Files:**
- `ai_buddy_web/lib/providers/mood_provider.dart`
- `ai_buddy_web/lib/screens/mood_tracker/mood_tracker.dart`
- `app.py` - Mood routes

### 2.3 Quest/Gamification Flow (Critical Path #3)
```
User starts quest → QuestProvider.startQuest()
    → Dio POST /api/quest/start
    → Flask creates quest_progress record
    → User completes steps → XP awarded
    → ProgressProvider synced
    → Badges/streaks updated
```

**Key Files:**
- `ai_buddy_web/lib/providers/quest_provider.dart`
- `ai_buddy_web/lib/providers/progress_provider.dart`
- `ai_buddy_web/lib/screens/quest_screen/`

---

## 3. COMPONENT DEPENDENCIES

### 3.1 Flutter Provider Graph
```
MaterialApp
└── MultiProvider
    ├── ChatProvider (depends on: ApiService, SessionManager)
    ├── MoodProvider (depends on: ApiService)
    ├── QuestProvider (depends on: ApiService, ProgressProvider)
    ├── ProgressProvider (depends on: ApiService)
    ├── AssessmentProvider (depends on: ApiService)
    ├── TaskProvider (depends on: ApiService)
    └── CommunityProvider (depends on: ApiService)
```

### 3.2 Backend Module Graph
```
app.py (main)
├── providers/
│   ├── gemini_provider.py (PRIMARY)
│   ├── openai_provider.py (FALLBACK 1)
│   └── perplexity_provider.py (FALLBACK 2)
├── brain_*.py (MCP integration)
│   ├── brain_memory.py
│   ├── brain_ledger.py
│   └── brain_tasks.py
└── routes/ (implicit in app.py)
    ├── /api/chat
    ├── /api/mood/*
    ├── /api/quest/*
    ├── /api/community/*
    └── /api/health
```

---

## 4. STATE MANAGEMENT

### 4.1 Client State (Flutter)
| Provider | Persisted | Source of Truth |
|----------|-----------|-----------------|
| ChatProvider | Session only | Backend PostgreSQL |
| MoodProvider | SharedPreferences + Backend | Backend |
| QuestProvider | Backend | Backend |
| ProgressProvider | Backend | Backend |

### 4.2 Server State
| Store | Purpose | Retention |
|-------|---------|-----------|
| PostgreSQL | All persistent data | MESSAGE_RETENTION_DAYS=30 |
| Redis | Session cache, rate limits | SESSION_RETENTION_DAYS=14 |
| Filesystem | Fallback session store | On-demand |

---

## 5. CRITICAL PATHS (80/20)

### The 5 paths that handle 80% of user value:

1. **Chat with AI** - `app.py:chat_route` + `gemini_provider.py`
2. **Log Mood** - `app.py:mood_routes` + `mood_tracker.dart`
3. **Complete Quest Step** - `quest_provider.dart` + backend quest routes
4. **View Progress** - `progress_provider.dart` + `wellness_dashboard_screen.dart`
5. **Crisis Detection** - Inline in chat_route, 11-country resources

### Code Coverage for Critical Paths:
```
ai_buddy_web/lib/providers/chat_provider.dart     ← CRITICAL
ai_buddy_web/lib/providers/mood_provider.dart     ← CRITICAL
ai_buddy_web/lib/providers/quest_provider.dart    ← CRITICAL
ai_buddy_web/lib/providers/progress_provider.dart ← CRITICAL
app.py (lines 1-500)                              ← CRITICAL
providers/gemini_provider.py                      ← CRITICAL
```

---

## 6. INTEGRATION POINTS

### 6.1 External Services
| Service | Purpose | Config Key |
|---------|---------|------------|
| Google Gemini | Primary AI | GEMINI_API_KEY |
| OpenAI | Fallback AI | OPENAI_API_KEY |
| Perplexity | Fallback AI | PPLX_API_KEY |
| Stripe | Payments (future) | STRIPE_* |
| Sentry | Error tracking | SENTRY_DSN_BACKEND |
| Firebase | Analytics, Crashlytics | google-services.json |

### 6.2 MCP Integration (Nucleus)
```
.brain/ ← Local state
mcp-server-nucleus/ ← MCP server for AI agents
    src/mcp_server_nucleus/
        tools/ ← 80+ brain_* tools
        runtime/ ← Agent execution
```

---

## 7. DEPLOYMENT TOPOLOGY

### 7.1 Production (Render)
```
gentlequest.onrender.com
├── Web Service (Docker)
│   ├── Flask backend (port 5055)
│   └── Flutter web (static, served by Flask)
├── PostgreSQL (managed)
└── Redis (external URL)
```

### 7.2 GCP (Alternative)
```
Cloud Run
├── gentlequest-backend
├── nucleus-hud
└── CloudSQL (gentlequest-db)
```

---

## 8. NAVIGATION STRUCTURE

```
HomeShell (home_shell.dart)
├── Tab 0: Talk (ChatScreen)
│   └── Interactive AI conversation
├── Tab 1: Mood (MoodTracker)
│   ├── Mood input
│   ├── Weekly Pulse
│   └── Analytics
├── Tab 2: Quest (WellnessDashboard)
│   ├── Today (active quests)
│   └── Explore (quest catalog)
└── Tab 3: Community (CommunityFeed)
    └── Curated content (Phase 0)
```

---

## QUICK REFERENCE

**To modify chat behavior:** `app.py:chat_route` + `providers/gemini_provider.py`
**To add new quest type:** `ai_buddy_web/lib/providers/quest_provider.dart`
**To change mood tracking:** `ai_buddy_web/lib/providers/mood_provider.dart`
**To update AI prompts:** `providers/gemini_provider.py:SYSTEM_PROMPT`
**To add new API endpoint:** `app.py` + corresponding Flutter service call
**To modify UI layout:** `ai_buddy_web/lib/screens/` + `widgets/`
**To change deployment:** `render.yaml` (Render) or `cloudbuild.yaml` (GCP)
