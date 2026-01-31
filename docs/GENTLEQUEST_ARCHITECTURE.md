# GentleQuest Technical Architecture

## 1. API Endpoints
Based on `app.py` and registered blueprints.

### Core App Routes
| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Landing page or App entry point |
| GET | `/app` | Serves Flutter app |
| GET | `/health` | Health check |
| GET | `/clinical` | Serves Clinical Dashboard |
| GET | `/clinical-dashboard` | Serves Clinical Dashboard |

### Brain / Nucleus Integration
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/brain/telegram/webhook` | Telegram update webhook |
| GET | `/api/brain/status` | Get Brain state |
| POST | `/api/brain/alert` | Send alert to founder via Telegram |
| POST | `/api/brain/sprint` | Start sprint via Telegram command |
| POST | `/api/brain/sync` | Sync local brain state to production |
| GET | `/api/brain/debug_import` | Debug import issues |
| GET | `/api/swarms` | Get active swarms state |

### Assessments & Clinical
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/assessment/<type>/questions` | Get questions for assessment (phq9, gad7) |
| POST | `/api/assessment/<type>` | Submit assessment |
| GET | `/api/assessment/history` | Get user assessment history |

### Quests (`app_quest_routes.py`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/quests` | Get weekly quests |
| POST | `/api/quests/<id>/complete` | Complete a quest |
| GET | `/api/user/profile` | Get user gamification profile |

### Resources (`app_resource_routes.py`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/resources` | Get educational resources |
| POST | `/api/resources/<id>/view` | Track resource view |
| GET/POST/PUT/DELETE | `/api/admin/resources` | Manage resources (Admin) |

### Alerts (`app_alert_routes.py`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/alerts/history` | Get alert history (Counselor Dashboard) |
| GET | `/api/alerts/<id>` | Get alert details |
| POST | `/api/alerts/<id>/acknowledge` | Acknowledge alert |

### Clinical Dashboard (`api_clinical_dashboard.py`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/clinical/summary` | Dashboard summary stats |
| GET | `/api/clinical/triage` | Triage high-priority cases |
| GET | `/api/clinical/engagement` | Engagement metrics |

### Community (`community.py`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/community/feed` | Get community posts |
| POST | `/api/community/reaction` | React to a post |
| POST | `/api/community/posts` | Create a post |
| DELETE | `/api/community/posts/<id>` | Delete a post |
| POST | `/api/community/report` | Report a post |
| GET | `/api/community/flags` | Get moderation flags (Config) |
| POST | `/api/community/moderate` | Moderate content (Admin) |
| GET | `/api/community/reports` | Get reports (Admin) |

### Enterprise
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/enterprise/status` | Enterprise feature status |
| GET | `/api/enterprise/metrics` | Enterprise metrics |

---

## 2. Flutter Screens & Routes
Mapping from `ai_buddy_web/lib/main.dart` and `ai_buddy_web/lib/routes/app_routes.dart`.

### Route Mapping
| Route Name | Screen Widget | File Path |
|---|---|---|
| `/home` | `HomeShell` | `lib/navigation/home_shell.dart` |
| `/home/quest` | `HomeShell` (Quest Tab) | `lib/navigation/home_shell.dart` |
| `/main` | `HomeShell` (Talk Tab) | `lib/navigation/home_shell.dart` |
| `/dhiwise-chat` | `MentalHealthChatScreen` | `lib/screens/dhiwise_chat_screen.dart` |
| `/preview-quest` | `QuestPreviewScreen` | `lib/screens/quest_preview_screen.dart` |
| `/interactive-chat` | `InteractiveChatScreen` | `lib/screens/interactive_chat_screen.dart` |
| `/privacy` | `LegalScreen` | `lib/screens/legal/legal_screen.dart` |
| `/wellness-dashboard` | `WellnessDashboardScreen` | `lib/dhiwise/presentation/wellness_dashboard_screen/wellness_dashboard_screen.dart` |
| `/quests-list` | `QuestScreen` | `lib/dhiwise/presentation/quest_screen/quest_screen.dart` |
| `/clinical-assessment` | `ClinicalAssessmentScreen` | `lib/screens/clinical_assessment_screen.dart` |

### Key Screen Components
*   **HomeShell**: Main container with bottom navigation (Talk, Quest, Mood, Community).
*   **InteractiveChatScreen**: Core chat interface with AI buddy.
*   **ClinicalAssessmentScreen**: Interface for PHQ-9/GAD-7 assessments.
*   **QuestScreen**: Gamification dashboard showing daily quests.
*   **WellnessDashboardScreen**: Visual analytics for user wellness.

---

## 3. Data Flow

### Frontend <-> Backend
1.  **Session Management**:
    *   Frontend generates/manages `X-Session-ID`.
    *   Backend (`app.py`) validates `X-Session-ID` header for all protected routes.
    *   `UserSession` table tracks conversation counts and risk levels.

2.  **Chat Interaction**:
    *   User sends message -> `/api/chat/stream` (implied, handled by `ChatProvider`).
    *   Backend stores message in `Message` table.
    *   AI processes via `providers/ai_provider.py`.
    *   Backend responses stream back to Frontend.

3.  **Clinical Assessment**:
    *   Frontend fetches questions -> `/api/assessment/<type>/questions`.
    *   User submits responses -> `/api/assessment/<type>` (POST).
    *   Backend:
        1.  Validates and scores (PHQ-9/GAD-7).
        2.  Saves to `ClinicalAssessment` table.
        3.  Checks for Crisis/High Severity.
        4.  If Crisis: Triggers `AlertManager` -> Creates `CounselorAlert`.

4.  **Gamification**:
    *   Actions (Chat, Assessment) trigger `QuestEngine`.
    *   `QuestEngine` updates `QuestProgress` and `UserProfile` (XP, Streak).
    *   Frontend polls `/api/user/profile` or `/api/quests` to update UI.

### Backend Internal Flow
*   **Crisis Detection**:
    *   Every message and assessment is analyzed.
    *   `crisis_detection.py` scans for keywords.
    *   `AlertManager` handles escalations to `CounselorAlert`.
*   **Brain Sync**:
    *   `app.py` exposes endpoints for the "Nucleus Brain" to sync state and send Telegram alerts.

---

## 4. Database Schema
Using SQLAlchemy (PostgreSQL/SQLite). Defined in `models.py`.

### Core User Data
*   **UserSession**: Tracks anonymous/registered sessions.
*   **UserProfile**: Gamification stats (XP, Level, Streak).
*   **User**: Optional registered user account.

### Clinical & Wellness
*   **Message**: Chat history.
*   **ConversationLog**: Pairs of User/AI interaction for analysis.
*   **MoodEntry**: Daily mood tracking.
*   **ClinicalAssessment**: PHQ-9/GAD-7 results.
*   **SelfAssessmentEntry**: Generic self-assessment data (JSON).
*   **CrisisEvent**: Log of detected crisis keywords.

### Gamification
*   **Quest**: Definitions of daily/weekly quests.
*   **QuestProgress**: User status on specific quests.

### Resources & Content
*   **Resource**: Educational content urls/metadata.
*   **UserResourceInteraction**: Analytics on resource views.
*   **CommunityPost**: Shared community content.

### System & Admin
*   **University**: Tenant configuration.
*   **UniversityCounselor**: Staff contacts for alerts.
*   **CounselorAlert**: Crisis alerts pending acknowledgment.
*   **AlertAcknowledgment**: Audit trail of counselor actions.
*   **BrainState**: Persistence for the Nucleus AI Brain.
*   **BrainEvent**: Event log for autonomous brain actions.
*   **AnalyticsEvent**: General system usage events.

---

## 5. External Integrations

### AI Providers
*   **Google Gemini**: Primary LLM (via `google.generativeai`).
*   **OpenAI**: Fallback LLM.
*   **Perplexity**: Fallback/Research LLM.

### Services
*   **Telegram**:
    *   Used by `BrainTelegram` (`brain_telegram.py`).
    *   Updates founder on System Health/Sprints.
    *   Webhook: `/api/brain/telegram/webhook`.
*   **Sentry**:
    *   Frontend and Backend error tracking.
    *   Initialized in `main.dart` and `app.py`.
*   **Firebase**:
    *   Used in Flutter App (`firebase_service.dart`).
    *   Analytics and Crashlytics.
*   **IPInfo.io**:
    *   Used in `app.py` (`get_country_code_from_ip`) for localization.
*   **Redis** (Optional):
    *   Session storage fallback.
