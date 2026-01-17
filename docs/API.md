# GentleQuest API Reference v1.0

Mental health companion API for the GentleQuest application.

## Authentication
Authentication is session-based. All endpoints requiring authentication expect a `session_id` (UUID).
- **Header:** `X-Session-ID: <uuid>` (Preferred)
- **Query/Body:** `session_id=<uuid>` (Fallback)

## Base URL
- **Production:** `https://gentlequest-backend-999376128638.us-central1.run.app`
- **Local:** `http://localhost:5055`

---

## 1. Health & Status

### GET /api/health
Returns system health status including database and Redis connectivity.
- **Response:** `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected",
  "ai_provider": "gemini"
}
```

### GET /api/ping
Lightweight keep-alive check.
- **Response:** `200 OK`

---

## 2. AI Chat

### POST /api/chat
Send a message to the AI companion. Used for short text interactions.
- **Body:** `{ "message": "I feel anxious", "session_id": "...", "country": "US" }`
- **Response:** `200 OK`
```json
{
  "response": "I hear you. Let's take a deep breath...",
  "crisis_detected": false,
  "resources": []
}
```

### POST /api/chat/stream
Server-Sent Events (SSE) stream for real-time AI responses.
- **Body:** `{ "message": "...", "session_id": "..." }`
- **Response:** `text/event-stream`

---

## 3. Mood Tracking

### POST /api/mood
Log a mood entry (1-10).
- **Body:** `{ "session_id": "...", "mood_value": 7, "note": "Feeling better" }`
- **Response:** `200 OK`

### GET /api/mood/history
Get mood history for charting.
- **Query:** `session_id=...&days=30`
- **Response:** `200 OK` (Array of entries)

### GET /api/mood/analytics
Get mood statistics (streak, average, trend).
- **Query:** `session_id=...`
- **Response:** `200 OK`

---

## 4. Quests & Gamification

### GET /api/quests
Get weekly available quests and user profile summary.
- **Header:** `X-Session-ID: ...`
- **Response:** `200 OK`
```json
{
  "quests": [
    {
      "id": 1,
      "title": "Mindful Morning",
      "description": "Complete a 5-minute breathing exercise.",
      "xp_reward": 50,
      "status": "available"
    }
  ],
  "profile": { "level": 1, "xp": 100 }
}
```

### POST /api/quests/<quest_id>/complete
Complete a quest and earn XP. Idempotent (safe to retry).
- **Header:** `X-Session-ID: ...`
- **Response:** `200 OK`
```json
{
  "success": true,
  "xp_earned": 50,
  "new_total_xp": 150,
  "leveled_up": false,
  "new_badges": []
}
```

### GET /api/user/profile
Get full user profile including badges and stats.
- **Header:** `X-Session-ID: ...`
- **Response:** `200 OK`

---

## 5. Resources (Content Library)

### GET /api/resources
Search and filter educational resources.
- **Query:** `category=anxiety&search=breathing`
- **Response:** `200 OK`
```json
{
  "resources": [
    {
      "id": 1,
      "title": "5-4-3-2-1 Grounding",
      "category": "Anxiety",
      "url": "..."
    }
  ]
}
```

### POST /api/resources/<id>/view
Track a resource view (analytics).
- **Body:** `{ "session_id": "..." }`
- **Response:** `200 OK`

---

## 6. Assessments

### POST /api/assessment/check-in
Submit a daily self-check-in (PHQ-9/GAD-7 subset). Awards XP once daily.
- **Body:** `{ "session_id": "...", "responses": [...] }`
- **Response:** `200 OK`
