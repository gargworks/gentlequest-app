# CRITICAL PATHS - GentleQuest 2026
## The 20% Code Handling 80% Functionality

**Purpose:** Focus attention on high-impact code paths  
**Valid Until:** December 2026  
**Last Updated:** January 16, 2026

---

## OVERVIEW

These are the code paths that handle the majority of user value. Changes here require extra care and testing.

```
Priority Matrix:
┌─────────────────────────────────────────┐
│  HIGH IMPACT                            │
│  ┌─────────────────────────────────┐    │
│  │ 1. Chat/AI Response             │ ★★★│
│  │ 2. Mood Logging                 │ ★★★│
│  │ 3. Quest Completion             │ ★★ │
│  │ 4. Crisis Detection             │ ★★★│
│  │ 5. Session Management           │ ★★ │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

---

## PATH 1: CHAT/AI RESPONSE (★★★)

**User Journey:** User sends message → AI responds

### Backend Critical Files
```
app.py
├── chat_route()           # Lines ~100-200
│   ├── Rate limit check
│   ├── Crisis detection
│   ├── Provider selection
│   └── Response streaming
│
providers/
├── gemini_provider.py     # PRIMARY - All lines critical
│   ├── __init__()         # API key setup
│   ├── generate_response() # Main generation
│   └── stream_response()   # SSE streaming
├── openai_provider.py     # FALLBACK 1
└── perplexity_provider.py # FALLBACK 2
```

### Flutter Critical Files
```
ai_buddy_web/lib/
├── providers/
│   └── chat_provider.dart     # ALL LINES CRITICAL
│       ├── sendMessage()       # Initiates chat
│       ├── _handleStreaming()  # SSE handling
│       └── messages list       # State
├── services/
│   ├── api_service.dart       # HTTP client
│   └── streaming/
│       └── streaming_sse_web.dart  # SSE implementation
└── screens/
    └── chat_screen/
        └── chat_screen.dart   # UI rendering
```

### Test Command
```bash
curl -X POST https://gentlequest.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test-123"}'
```

### Failure Modes
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| No response | AI provider down | Check fallback chain |
| Timeout | Network/slow AI | Increase timeout |
| 429 error | Rate limited | Wait or check limits |
| Garbled text | SSE parsing | Check streaming_sse_web.dart |

---

## PATH 2: MOOD LOGGING (★★★)

**User Journey:** User selects mood → Saved → Stats updated

### Backend Critical Files
```
app.py
├── mood_routes
│   ├── POST /api/mood/entries  # Create mood
│   ├── GET /api/mood/entries   # Get history
│   └── GET /api/mood/analytics # Get stats
```

### Flutter Critical Files
```
ai_buddy_web/lib/
├── providers/
│   └── mood_provider.dart     # ALL LINES CRITICAL
│       ├── addMood()          # Save mood
│       ├── getMoodHistory()   # Fetch history
│       ├── streak             # Streak calculation
│       └── analytics          # Trend analysis
└── screens/
    └── mood_tracker/
        └── mood_tracker.dart  # UI
```

### Test Command
```bash
curl -X POST https://gentlequest.onrender.com/api/mood/entries \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-123", "mood_value": 7}'
```

### Failure Modes
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Mood not saving | DB connection | Check DATABASE_URL |
| Streak wrong | Timezone issue | Verify UTC handling |
| Analytics empty | No data | Check date range |

---

## PATH 3: QUEST COMPLETION (★★)

**User Journey:** Start quest → Complete steps → Earn XP

### Backend Critical Files
```
app.py
├── quest_routes
│   ├── GET /api/quest/catalog    # Available quests
│   ├── POST /api/quest/start     # Begin quest
│   └── POST /api/quest/complete-step  # Progress
```

### Flutter Critical Files
```
ai_buddy_web/lib/
├── providers/
│   ├── quest_provider.dart    # Quest state
│   └── progress_provider.dart # XP/level state
└── screens/
    └── quest_screen/          # All files
```

### Test Command
```bash
# Get quests
curl https://gentlequest.onrender.com/api/quest/catalog

# Start quest
curl -X POST https://gentlequest.onrender.com/api/quest/start \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-123", "quest_id": "morning-mindfulness"}'
```

---

## PATH 4: CRISIS DETECTION (★★★)

**User Journey:** User mentions crisis → Immediate resources shown

### Backend Critical Code
```python
# app.py - Inline in chat_route

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "want to die",
    "self harm", "hurt myself", ...
]

CRISIS_RESOURCES = {
    "IN": {"name": "iCall", "number": "9152987821"},
    "US": {"name": "988 Suicide & Crisis Lifeline", "number": "988"},
    "UK": {"name": "Samaritans", "number": "116 123"},
    # ... 11 countries total
}

def check_crisis(message, country):
    if any(kw in message.lower() for kw in CRISIS_KEYWORDS):
        return get_crisis_response(country)
    return None
```

### Test Command
```bash
# Should trigger crisis response
curl -X POST https://gentlequest.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to hurt myself", "session_id": "test", "country": "IN"}'
```

### NEVER MODIFY WITHOUT:
- [ ] Testing all 11 country responses
- [ ] Verifying no false negatives
- [ ] Clinical review of keywords

---

## PATH 5: SESSION MANAGEMENT (★★)

**User Journey:** App opens → Session created/restored → Persists

### Backend Critical Files
```
app.py
├── Session configuration
│   ├── Flask-Session setup
│   ├── Redis backend
│   └── Filesystem fallback
```

### Flutter Critical Files
```
ai_buddy_web/lib/
├── services/
│   └── session_manager.dart   # Session ID management
└── main.dart
    └── _initSession()         # Startup session
```

### Session Flow
```
App Start
├── Check SharedPreferences for session_id
├── If none, generate UUID
├── Store in SharedPreferences
└── Inject into all API calls via interceptor
```

---

## CODE COVERAGE PRIORITY

### Must Have 100% Understanding
```
app.py (lines 1-300)
providers/gemini_provider.py (all)
ai_buddy_web/lib/providers/chat_provider.dart (all)
ai_buddy_web/lib/providers/mood_provider.dart (all)
```

### Should Have 80% Understanding
```
ai_buddy_web/lib/providers/quest_provider.dart
ai_buddy_web/lib/providers/progress_provider.dart
ai_buddy_web/lib/services/api_service.dart
```

### Nice to Have Understanding
```
ai_buddy_web/lib/screens/* (UI only)
ai_buddy_web/lib/widgets/* (UI only)
```

---

## CHANGE IMPACT MATRIX

| Change Type | Impact | Required Testing |
|-------------|--------|------------------|
| AI prompt change | HIGH | Full regression |
| New API endpoint | MEDIUM | Endpoint + integration |
| UI layout change | LOW | Visual verification |
| New quest type | LOW | Quest flow only |
| Rate limit change | MEDIUM | Load testing |
| Database schema | HIGH | Migration + backup |

---

## MONITORING PRIORITIES

### Must Monitor
- Chat response time (< 2s target)
- AI fallback rate (< 5% target)
- Error rate (< 1% target)
- Crisis detection accuracy

### Should Monitor
- Mood logging frequency
- Quest completion rates
- Session duration

---

## QUICK DEBUG CHECKLIST

When something breaks:

1. **Check /api/health** - Is service up?
2. **Check Render logs** - Any errors?
3. **Check AI provider status** - Gemini/OpenAI down?
4. **Check DATABASE_URL** - Connection valid?
5. **Check REDIS_URL** - Sessions working?
6. **Check recent deploys** - What changed?
