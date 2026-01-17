# Resource System API Documentation

## Overview
The Resource System provides a library of mental health resources (articles, crisis lines, university contacts) that users can browse and search.

## Authentication
All endpoints require the `X-Session-ID` header.

## Endpoints

### 1. Get Resources
Fetch a paginated list of resources with filtering options.

- **URL:** `/api/resources`
- **Method:** `GET`
- **Headers:** `X-Session-ID: <session_id>`
- **Query Parameters:**
  - `category`: structured filter (e.g., `crisis`, `self_help`, `university`, `external`)
  - `country`: 2-letter country code (e.g., `US`, `IN`)
  - `search`: text search across title, description, and tags
- **Response (200 OK):**
  ```json
  {
    "resources": [
      {
        "id": 101,
        "title": "Grounding Techniques 101",
        "description": "5-4-3-2-1 technique explained.",
        "url": "https://...",
        "category": "self_help",
        "country": null,
        "tags": ["anxiety", "panic", "grounding"]
      },
      ...
    ],
    "count": 15
  }
  ```
- **Response (401 Unauthorized):** Missing Session ID.

### 2. Track Resource View
Log when a user views a specific resource (for analytics and personalisation).

- **URL:** `/api/resources/<resource_id>/view`
- **Method:** `POST`
- **Headers:** `X-Session-ID: <session_id>`
- **Response (200 OK):**
  ```json
  {
    "success": true
  }
  ```
- **Response (404 Not Found):** Invalid Resource ID.

### 3. Admin Management (Admin Only)
CRUD operations for the content library.

- **URL:** `/api/admin/resources`
- **Methods:** `GET`, `POST`, `PUT`, `DELETE`
- **Note:** Currently unsecured/internal use only. Implementation details in `app_resource_routes.py`.

## Data Model (Postgres)
- **Table:** `resources`
- **Columns:**
  - `id`: Integer (PK)
  - `title`: String
  - `description`: String
  - `url`: String (Optional)
  - `category`: Enum (crisis, self_help, university, external)
  - `country`: String (Optional)
  - `tags`: String (CSV)
  - `is_active`: Boolean
