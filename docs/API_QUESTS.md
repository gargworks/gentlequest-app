# Quest System API Documentation

## Overview
The Quest System API allows users to fetch weekly quests, track progress, and earn XP/badges. It is designed to work with the Flutter frontend.

## Authentication
All endpoints require the `X-Session-ID` header or `session_id` query/body parameter.

## Endpoints

### 1. Get Weekly Quests
Fetches the current week's quests and the user's profile summary.

- **URL:** `/api/quests`
- **Method:** `GET`
- **Headers:** `X-Session-ID: <session_id>`
- **Response (200 OK):**
  ```json
  {
    "quests": [
      {
        "id": 1,
        "title": "Mindful Morning",
        "description": "Complete a 5-minute breathing exercise.",
        "xp_reward": 50,
        "status": "available",  // "available" or "completed"
        "type": "task",
        "difficulty": 1
      },
      ...
    ],
    "week": 3,
    "year": 2026,
    "profile": {
      "level": 1,
      "xp": 100,
      "streak_days": 2
    }
  }
  ```
- **Response (400 Bad Request):** Missing Session ID.

### 2. Complete a Quest
Marks a quest as completed and awards XP. Handles leveling up and badge unlocking.

- **URL:** `/api/quests/<quest_id>/complete`
- **Method:** `POST`
- **Headers:** `X-Session-ID: <session_id>`
- **Body:** `{ "session_id": "..." }` (Optional if header is present)
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "xp_earned": 50,
    "new_total_xp": 150,
    "leveled_up": false,
    "new_level": 1,
    "new_badges": [
      { "id": "streak_7" } 
    ]
  }
  ```
- **Response (400 Bad Request):** Quest already completed or invalid request.
- **Response (404 Not Found):** Quest ID does not exist.

### 3. Get User Profile
Retrieves detailed gamification profile.

- **URL:** `/api/user/profile`
- **Method:** `GET`
- **Headers:** `X-Session-ID: <session_id>`
- **Response (200 OK):**
  ```json
  {
    "level": 2,
    "xp": 250,
    "streak_days": 5,
    "badges": "streak_7,early_adopter",
    "last_activity_date": "2026-01-17T12:00:00"
  }
  ```

## Integration Notes
- **Polling:** The frontend should fetch `/api/quests` on startup to determine valid quests for the week.
- **Optimistic Updates:** Upon completion, the frontend can optimistically update the UI, but must handle errors (e.g. "Already completed").
- **Badges:** The `new_badges` array in the completion response triggers the "Badge Unlocked" modal.
