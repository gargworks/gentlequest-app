# GentleQuest API Reference (v1.3.0)

## Base URL
Production: `https://gentlequest.app/api`
Staging: `https://staging.gentlequest.app/api`
Local: `http://localhost:5000/api`

## API Versioning
The current stable version is `v1.3`. All endpoints are prefixed with `/api` unless otherwise noted. Breaking changes will increment the minor version and be announced via the CAPS administrator dashboard.

## Rate Limiting & Safety
To ensure service availability and prevent abuse, the following limits apply:
- **Default:** 60 requests per minute per IP.
- **Chat:** 20 messages per minute.
- **Safety Overrides:** High-risk messages (detected via crisis keywords) are exempt from rate limits if they trigger emergency redirection.

## Authentication
Most API endpoints require the `X-Session-ID` header. If missing, a new session ID will be generated and returned in the response.
```http
X-Session-ID: <session_uuid>
```

---

## 1. Chat & AI

### **Send Message**
Send a user message to receive an AI response with crisis detection.
- **POST** `/chat`
- **Headers:** `X-Session-ID` (optional, will be generated if missing)
- **Body:**
  ```json
  {
    "message": "I feel anxious about exams."
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "response": "I hear you. Exam stress is real. Let's try deep breathing?",
    "risk_level": "low",
    "session_id": "uuid",
    "crisis_msg": "If you are in immediate danger...",
    "crisis_numbers": ["988", "Text HOME to 741741"]
  }
  ```

### **Stream Chat**
SSE endpoint for streaming AI responses.
- **GET** `/chat_stream`
- **Query Params:** `message`, `session_id` (optional), `country` (optional)
- **Streams:** JSON objects with `type`: `token`, `meta`, `done`, or `error`.

---

## 2. Quests (Gamification)

### **List Weekly Quests**
Retrieve quests for the current week and user profile status.
- **GET** `/quests`
- **Headers:** `X-Session-ID`
- **Response (200 OK):**
  ```json
  {
    "quests": [
      {
        "id": 101,
        "title": "Morning Check-in",
        "description": "Log your mood before 10 AM",
        "xp_reward": 50,
        "status": "available",
        "type": "check_in",
        "difficulty": 1,
        "progress": 0
      }
    ],
    "profile": {
      "level": 1,
      "xp": 0,
      "streak_days": 0
    },
    "week": 3,
    "year": 2026
  }
  ```

### **Complete Quest**
Mark a quest as completed.
- **POST** `/quests/{quest_id}/complete`
- **Headers:** `X-Session-ID`
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "xp_earned": 50,
    "new_total_xp": 150,
    "leveled_up": false,
    "new_level": 1,
    "new_badges": []
  }
  ```
- **Response (400 Bad Request):** If already completed.

---

## 3. Resources & Library

### **List Resources**
Get list of available resources.
- **GET** `/resources`
- **Headers:** `X-Session-ID`
- **Query Params:** `category`, `country`, `search`
- **Response (200 OK):**
  ```json
  {
    "count": 1,
    "resources": [
      {
        "id": 1,
        "title": "Box Breathing Guide",
        "description": "A simple breathing technique...",
        "url": "https://...",
        "category": "self_help",
        "country": "US",
        "tags": ["anxiety", "breath"]
      }
    ]
  }
  ```

### **Track View**
Record that a user viewed a resource.
- **POST** `/resources/{id}/view`
- **Headers:** `X-Session-ID`

---

## 4. Clinical Assessments

### **Get Questions**
- **GET** `/assessment/{phq9|gad7}/questions`
- **Response (200 OK):** List of questions with options.

### **Submit Assessment**
- **POST** `/assessment/{phq9|gad7}`
- **Headers:** `X-Session-ID`
- **Body:**
  ```json
  {
    "responses": [0, 1, 3, 2, ...]
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "total_score": 12,
    "severity": "moderate",
    "recommendations": ["Consider speaking with a counselor."],
    "requires_follow_up": false,
    "assessment_id": 5
  }
  ```

---

## 5. Analytics

### **Log Event**
Record generic UI events or interactions.
- **POST** `/analytics/log`
- **Headers:** `X-Session-ID`
- **Body:**
  ```json
  {
    "event_type": "button_click",
    "metadata": {
      "label": "start_quest",
      "quest_id": 101
    }
  }
  ```

### **Mood Analytics**
- **GET** `/mood_analytics`
- **Headers:** `X-Session-ID`
- **Response (200 OK):**
  ```json
  {
    "entries": [ ... ],
    "analytics": {
      "average_mood": 3.5,
      "trend": "improving"
    }
  }
  ```

### **Intervention Outcome**
Log outcome of a wellness intervention (breathing, grounding, etc.).
- **POST** `/intervention/outcome`
- **Headers:** `X-Session-ID`
- **Body:**
  ```json
  {
    "intervention_id": "box_breathing",
    "outcome": "completed",
    "effectiveness": 5,
    "feedback": "I feel much calmer."
  }
  ```

---

## 6. Counselor Alerts (Admin)

### **List Alerts**
Retrieve alerts requiring attention.
- **GET** `/alerts`
- **Query Params:** `status` (pending|acknowledged), `severity`
- **Response (200 OK):**
  ```json
  {
    "alerts": [
      {
        "id": 1,
        "session_id": "uuid",
        "severity": "high",
        "status": "pending",
        "trigger_message": "I want to hurt myself",
        "timestamp": "2026-01-18T10:00:00Z"
      }
    ]
  }
  ```

### **Acknowledge Alert**
Mark an alert as reviewed by a professional.
- **POST** `/alerts/{alert_id}/acknowledge`
- **Body:**
  ```json
  {
    "acknowledged_by": "Dr. Smith",
    "notes": "Spoke with user, referral provided."
  }
  ```
- **Response (200 OK):** `{"success": true}`

---

## Error Codes
| Code | Meaning | Action |
|------|---------|--------|
| 400 | Bad Request | Check payload/logic |
| 401 | Unauthorized | Session ID required |
| 404 | Not Found | Resource/Quest missing |
| 429 | Rate Limit | Slow down requests |
| 500 | Server Error | Internal issue |
