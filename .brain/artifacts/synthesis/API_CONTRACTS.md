# API CONTRACTS - GentleQuest 2026
## All Endpoints, Parameters, Responses, Error Codes

**Purpose:** Complete API reference for autonomous development  
**Base URL:** https://gentlequest.onrender.com  
**Last Updated:** January 16, 2026  
**Valid Until:** December 2026

---

## 1. HEALTH & SYSTEM

### GET /api/health
**Purpose:** Full system health check

**Response 200:**
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "database": "connected",
  "redis": "connected",
  "ai_provider": "gemini",
  "uptime_seconds": 3600
}
```

### GET /api/ping
**Purpose:** Lightweight keep-alive (no DB/Redis check)

**Response 200:**
```json
{"status": "ok", "timestamp": "2026-01-16T12:00:00Z"}
```

### GET /api/metrics
**Purpose:** Prometheus metrics

**Response 200:** Plain text Prometheus format

---

## 2. CHAT (AI Conversation)

### POST /api/chat
**Purpose:** Send message, receive AI response (SSE stream)

**Request:**
```json
{
  "message": "How are you?",
  "session_id": "uuid-string",
  "country": "IN",
  "stream": true
}
```

**Headers:**
```
Content-Type: application/json
Accept: text/event-stream (if streaming)
```

**Response 200 (Streaming):**
```
data: {"type": "token", "content": "I'm"}
data: {"type": "token", "content": " doing"}
data: {"type": "token", "content": " well"}
data: {"type": "done", "full_response": "I'm doing well..."}
```

**Response 200 (Non-streaming):**
```json
{
  "response": "I'm doing well, thank you for asking!",
  "session_id": "uuid-string",
  "crisis_detected": false
}
```

**Response 429:**
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

**Rate Limits:** 120/minute per session

### GET /api/chat/history
**Purpose:** Get conversation history

**Query Params:**
- `session_id` (required)
- `limit` (optional, default 50)

**Response 200:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello", "timestamp": "..."},
    {"role": "assistant", "content": "Hi!", "timestamp": "..."}
  ]
}
```

---

## 3. MOOD TRACKING

### POST /api/mood/entries
**Purpose:** Log a mood entry

**Request:**
```json
{
  "session_id": "uuid-string",
  "mood_value": 7,
  "notes": "Feeling good today",
  "tags": ["grateful", "energetic"]
}
```

**Response 201:**
```json
{
  "id": "entry-uuid",
  "mood_value": 7,
  "streak": 5,
  "xp_earned": 10,
  "created_at": "2026-01-16T12:00:00Z"
}
```

### GET /api/mood/entries
**Purpose:** Get mood history

**Query Params:**
- `session_id` (required)
- `start_date` (optional, ISO format)
- `end_date` (optional, ISO format)
- `limit` (optional, default 30)

**Response 200:**
```json
{
  "entries": [
    {"id": "...", "mood_value": 7, "notes": "...", "created_at": "..."}
  ],
  "stats": {
    "average": 6.5,
    "streak": 5,
    "total_entries": 45
  }
}
```

### GET /api/mood/analytics
**Purpose:** Mood analytics and trends

**Query Params:**
- `session_id` (required)
- `period` (optional: "week", "month", "year")

**Response 200:**
```json
{
  "period": "week",
  "average_mood": 6.8,
  "trend": "improving",
  "trend_percentage": 12,
  "daily_breakdown": [
    {"date": "2026-01-15", "average": 7.0},
    {"date": "2026-01-14", "average": 6.5}
  ]
}
```

---

## 4. QUESTS (Gamification)

### GET /api/quest/catalog
**Purpose:** Get available quests

**Query Params:**
- `category` (optional: "mindfulness", "activity", "social", "learning", "challenge")

**Response 200:**
```json
{
  "quests": [
    {
      "id": "morning-mindfulness",
      "title": "Morning Mindfulness",
      "description": "Start your day with intention",
      "category": "mindfulness",
      "xp_reward": 50,
      "steps": 5,
      "duration_minutes": 15
    }
  ]
}
```

### POST /api/quest/start
**Purpose:** Start a quest

**Request:**
```json
{
  "session_id": "uuid-string",
  "quest_id": "morning-mindfulness"
}
```

**Response 201:**
```json
{
  "progress_id": "progress-uuid",
  "quest_id": "morning-mindfulness",
  "status": "in_progress",
  "current_step": 0,
  "started_at": "2026-01-16T12:00:00Z"
}
```

### POST /api/quest/complete-step
**Purpose:** Complete a quest step

**Request:**
```json
{
  "session_id": "uuid-string",
  "progress_id": "progress-uuid",
  "step_index": 1
}
```

**Response 200:**
```json
{
  "progress_id": "progress-uuid",
  "current_step": 2,
  "completed": false,
  "xp_earned": 10
}
```

### GET /api/quest/progress
**Purpose:** Get quest progress

**Query Params:**
- `session_id` (required)
- `status` (optional: "in_progress", "completed")

**Response 200:**
```json
{
  "active_quests": [...],
  "completed_today": 2,
  "total_xp": 150,
  "streak": 7
}
```

---

## 5. PROGRESS & ACHIEVEMENTS

### GET /api/progress
**Purpose:** Get overall progress

**Query Params:**
- `session_id` (required)

**Response 200:**
```json
{
  "level": 5,
  "total_xp": 1250,
  "xp_to_next_level": 250,
  "streak_days": 14,
  "badges": ["early_bird", "mood_master"],
  "stats": {
    "moods_logged": 45,
    "quests_completed": 23,
    "chat_sessions": 67
  }
}
```

### GET /api/achievements
**Purpose:** Get badge/achievement status

**Query Params:**
- `session_id` (required)

**Response 200:**
```json
{
  "earned": [
    {"id": "early_bird", "name": "Early Bird", "earned_at": "..."}
  ],
  "available": [
    {"id": "mood_master", "name": "Mood Master", "progress": 80, "requirement": "Log 100 moods"}
  ]
}
```

---

## 6. COMMUNITY (Phase 0)

### GET /api/community/feed
**Purpose:** Get community feed (curated content)

**Query Params:**
- `page` (optional, default 1)
- `limit` (optional, default 20)

**Response 200:**
```json
{
  "posts": [
    {
      "id": "post-uuid",
      "type": "template",
      "content": "Remember: Progress, not perfection",
      "author": "GentleQuest",
      "reactions": {"❤️": 45, "🙏": 23},
      "created_at": "..."
    }
  ],
  "pagination": {
    "page": 1,
    "total_pages": 5,
    "has_more": true
  }
}
```

### POST /api/community/react
**Purpose:** React to a post

**Request:**
```json
{
  "session_id": "uuid-string",
  "post_id": "post-uuid",
  "reaction": "❤️"
}
```

**Response 200:**
```json
{
  "success": true,
  "new_count": 46
}
```

**Rate Limits:** 20/minute, 200/day

---

## 7. ASSESSMENT (Self-Check)

### GET /api/assessment/questions
**Purpose:** Get assessment questions

**Response 200:**
```json
{
  "questions": [
    {
      "id": 1,
      "text": "How would you rate your overall mood today?",
      "type": "scale",
      "min": 1,
      "max": 10
    }
  ]
}
```

### POST /api/assessment/submit
**Purpose:** Submit assessment

**Request:**
```json
{
  "session_id": "uuid-string",
  "answers": [
    {"question_id": 1, "value": 7},
    {"question_id": 2, "value": 8}
  ]
}
```

**Response 200:**
```json
{
  "score": 75,
  "interpretation": "You're doing well!",
  "xp_earned": 25,
  "can_retake_at": "2026-01-17T00:00:00Z"
}
```

**Note:** XP only awarded once per day

---

## 8. ERROR CODES

| Code | Meaning | Action |
|------|---------|--------|
| 400 | Bad Request | Check request body/params |
| 401 | Unauthorized | Check session_id |
| 404 | Not Found | Resource doesn't exist |
| 429 | Rate Limited | Wait for Retry-After header |
| 500 | Server Error | Check logs, retry later |
| 503 | Service Unavailable | AI provider down, using fallback |

**Standard Error Response:**
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {},
  "retry_after": 60
}
```

---

## 9. FLUTTER CLIENT USAGE

### ApiService Configuration
```dart
// ai_buddy_web/lib/services/api_service.dart
final dio = Dio(BaseOptions(
  baseUrl: ApiConfig.baseUrl,  // https://gentlequest.onrender.com
  connectTimeout: Duration(seconds: 30),
  receiveTimeout: Duration(seconds: 30),
));

// Session injection
dio.interceptors.add(InterceptorsWrapper(
  onRequest: (options, handler) {
    options.headers['X-Session-ID'] = SessionManager.sessionId;
    return handler.next(options);
  },
));
```

### SSE Streaming (Web)
```dart
// ai_buddy_web/lib/services/streaming/streaming_sse_web.dart
final eventSource = EventSource('$baseUrl/api/chat?stream=true');
eventSource.onMessage.listen((event) {
  final data = jsonDecode(event.data);
  // Handle token or done event
});
```

---

## QUICK REFERENCE

| Action | Method | Endpoint |
|--------|--------|----------|
| Send chat | POST | /api/chat |
| Log mood | POST | /api/mood/entries |
| Get moods | GET | /api/mood/entries |
| Start quest | POST | /api/quest/start |
| Complete step | POST | /api/quest/complete-step |
| Get progress | GET | /api/progress |
| Get feed | GET | /api/community/feed |
| Health check | GET | /api/health |
