# IIP Module 6 Project Specification & Codebase
**Converted from:** M6W12-D2-IIP-Miro-Export.pdf  
**Generated:** 2026-01-01  
**For:** Boston University Online MBA (OMBA) - Integrated Innovation Project (Module 6)

---

## 📚 What's Inside This Package

This repository contains a **complete, readable conversion** of your Miro board into production-ready specifications and starter code for a Flutter + Python/Java backend IIP project tracking system.

### Files Included:

#### 📖 Documentation
- **`IIP_Project_Specification.md`** — Complete week-by-week breakdown of the module, including:
  - Problem Finding & POV Statement framework (Week 2)
  - Field Research Plan methodology (Week 3)
  - Persona Development with ANRUM insights (Weeks 4–5)
  - Ideation & Prototyping (Weeks 6–7)
  - Customer Value Proposition (CVP) Definition (Weeks 8–9)
  - Experimentation Plan & Final Delivery (Weeks 10–11)
  - Research interview templates
  - Team roles & submission checklists
  - Design thinking frameworks & JTBD decomposition

#### 🏗️ Backend Architecture
- **`database_models.py`** — SQLAlchemy ORM models for:
  - Teams & Team Members
  - POV Statements
  - Research Interviews & ANRUM Insights
  - Personas
  - CVP Canvas
  - Experiments
  - Ready for PostgreSQL integration

- **`api_schemas.json`** — OpenAPI 2.0 (Swagger) specification:
  - All REST endpoints
  - Request/response schemas
  - Data validation definitions
  - Can auto-generate SDKs for Flutter

#### 📱 Frontend
- **`flutter_models.dart`** — Dart model classes:
  - All entities with JSON serialization
  - Request/response DTOs
  - Equatable for easy comparison
  - Ready for integration with API service

---

## 🚀 Quick Start

### 1. **Backend Setup (Python/FastAPI)**

```bash
# Create project directory
mkdir iip-backend && cd iip-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Copy database_models.py to your project
cp /path/to/database_models.py ./app/models.py

# Create requirements.txt
pip install fastapi sqlalchemy psycopg2-binary python-multipart pydantic
pip freeze > requirements.txt

# Initialize PostgreSQL (local or cloud)
# Create database: CREATE DATABASE iip_module6;

# Run migrations (use Alembic for production)
python -m alembic init alembic
python -m alembic revision --autogenerate -m "Initial migration"
python -m alembic upgrade head
```

**FastAPI main.py Example:**
```python
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

DATABASE_URL = "postgresql://user:password@localhost/iip_module6"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IIP Module 6 API",
    description="Design Thinking & Research Platform",
    version="1.0.0"
)

# Import and include routers
from app.api import teams, interviews, personas, cvp_canvas, experiments

app.include_router(teams.router, prefix="/api/v1/teams", tags=["teams"])
app.include_router(interviews.router, prefix="/api/v1/interviews", tags=["interviews"])
app.include_router(personas.router, prefix="/api/v1/personas", tags=["personas"])
app.include_router(cvp_canvas.router, prefix="/api/v1/cvp", tags=["cvp"])
app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["experiments"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Or with Java/Spring Boot:**

```bash
# Create Spring Boot project
mvn archetype:generate -DgroupId=com.iip -DartifactId=iip-backend -DarchetypeArtifactId=maven-archetype-quickstart
cd iip-backend

# Add Spring Data JPA and PostgreSQL
# In pom.xml, add:
# <dependency>
#   <groupId>org.springframework.boot</groupId>
#   <artifactId>spring-boot-starter-data-jpa</artifactId>
# </dependency>
# <dependency>
#   <groupId>org.postgresql</groupId>
#   <artifactId>postgresql</artifactId>
# </dependency>
```

---

### 2. **Flutter Setup**

```bash
# Create Flutter project
flutter create iip_app
cd iip_app

# Add dependencies to pubspec.yaml
flutter pub add http
flutter pub add json_annotation
flutter pub add json_serializable
flutter pub add equatable
flutter pub add provider  # For state management
flutter pub add go_router  # For navigation

# Copy flutter_models.dart
cp /path/to/flutter_models.dart ./lib/models/

# Generate JSON serialization code
flutter pub run build_runner build

# Run app
flutter run
```

**pubspec.yaml Essential Dependencies:**
```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  json_annotation: ^4.8.0
  equatable: ^2.0.5
  provider: ^6.0.0
  go_router: ^10.0.0
  intl: ^0.18.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  json_serializable: ^6.7.0
  build_runner: ^2.4.0
```

---

## 🗂️ Project Structure

```
iip-project/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── team.py
│   │   │   ├── interview.py
│   │   │   ├── persona.py
│   │   │   ├── cvp_canvas.py
│   │   │   └── experiment.py
│   │   ├── schemas/  (Pydantic request/response models)
│   │   ├── api/
│   │   │   ├── teams.py
│   │   │   ├── interviews.py
│   │   │   ├── personas.py
│   │   │   ├── cvp_canvas.py
│   │   │   └── experiments.py
│   │   ├── services/  (Business logic)
│   │   │   ├── ai_insights_service.py  (NLP for ANRUM)
│   │   │   ├── file_upload_service.py
│   │   │   └── export_service.py  (PDF generation)
│   │   ├── database.py
│   │   └── __init__.py
│   ├── main.py
│   ├── requirements.txt
│   ├── .env  (Database credentials)
│   ├── docker-compose.yml  (PostgreSQL + pgAdmin)
│   └── tests/
│
├── flutter_app/
│   ├── lib/
│   │   ├── main.dart
│   │   ├── models/
│   │   │   ├── team.dart
│   │   │   ├── interview.dart
│   │   │   ├── persona.dart
│   │   │   ├── cvp_canvas.dart
│   │   │   ├── experiment.dart
│   │   │   └── pov_statement.dart
│   │   ├── screens/
│   │   │   ├── home_screen.dart
│   │   │   ├── project_dashboard_screen.dart
│   │   │   ├── research_viewer_screen.dart
│   │   │   ├── persona_builder_screen.dart
│   │   │   ├── cvp_canvas_screen.dart
│   │   │   ├── experiment_tracker_screen.dart
│   │   │   └── milestone_submission_screen.dart
│   │   ├── widgets/
│   │   │   ├── persona_card.dart
│   │   │   ├── insight_chip.dart
│   │   │   ├── cvp_canvas_widget.dart
│   │   │   ├── experiment_card.dart
│   │   │   └── research_timeline_widget.dart
│   │   ├── services/
│   │   │   ├── api_service.dart
│   │   │   ├── local_storage_service.dart
│   │   │   └── auth_service.dart
│   │   ├── theme/
│   │   │   ├── app_theme.dart
│   │   │   └── colors.dart
│   ├── pubspec.yaml
│   └── test/
│
├── docs/
│   ├── IIP_Project_Specification.md
│   ├── API_DOCUMENTATION.md
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
│
├── README.md (this file)
├── .gitignore
└── docker-compose.yml
```

---

## 📋 Database Setup (PostgreSQL)

### Option 1: Local PostgreSQL + Docker

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: iip_module6
      POSTGRES_USER: iip_user
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_/var/lib/postgresql/data

  pgadmin:
    image: dpage/pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"

volumes:
  postgres_
```

```bash
# Start services
docker-compose up -d

# Access pgAdmin: http://localhost:5050
# Add connection:
#   Host: postgres
#   User: iip_user
#   Password: secure_password
#   Database: iip_module6
```

### Option 2: Cloud PostgreSQL (Neon, Railway, Heroku)

```bash
# Update .env
DATABASE_URL=postgresql://user:password@host:5432/iip_module6

# Run migrations
python -m alembic upgrade head
```

---

## 🔌 API Quick Reference

### Create Team
```bash
curl -X POST http://localhost:8000/api/v1/teams \
  -H "Content-Type: application/json" \
  -d '{"team_name": "Team Alpha", "project_focus": "Mental Health Support"}'
```

### Create POV Statement
```bash
curl -X POST http://localhost:8000/api/v1/teams/1/pov \
  -H "Content-Type: application/json" \
  -d '{
    "users_description": "University students",
    "need_description": "Accessible mental health resources",
    "why_matters_description": "Prevent crisis, improve academics"
  }'
```

### Create Interview
```bash
curl -X POST http://localhost:8000/api/v1/teams/1/interviews \
  -H "Content-Type: application/json" \
  -d '{
    "interview_date": "2026-01-15T14:00:00",
    "participant_role": "Student",
    "participant_anonymized_id": "P001",
    "interview_notes": "Raw transcript here...",
    "key_quotes": ["Quote 1", "Quote 2"],
    "researcher_bias_notes": "Reflection here"
  }'
```

See **`api_schemas.json`** for full OpenAPI documentation.

---

## 🎯 Key Concepts & Frameworks

### Double Diamond
**Discover** → **Define** → **Develop** → **Deliver**

- **Discover (Weeks 2–3):** Problem Finding, Field Research Plan
- **Define (Weeks 2, 8–9):** POV Statement, CVP Canvas
- **Develop (Weeks 6–7):** Ideation, Prototyping
- **Deliver (Weeks 10–11):** Final Pitch, Experiments

### POV Statement Framework
```
[Users] need a way to [Unmet Need] because [Why It Matters].

Example:
"University students need a way to access stigma-free, affordable mental health 
support because they're struggling with isolation and don't know where to begin."
```

### ANRUM Insight Extraction
- **Attitude:** Emotion/belief detected
- **Need:** Unmet need revealed
- **Response:** Current coping behavior
- **Use case:** Specific scenario
- **Mental model:** Underlying assumption

### CVP Canvas (Customer Value Proposition)
- **Customer Segment:** Who?
- **Jobs to be Done (JTBD):** Functional, Emotional, Social
- **Value Proposition:** Specific benefits
- **Pains:** Current barriers
- **Gains:** Desired outcomes
- **Pain Relievers:** How solution eases pains
- **Gain Creators:** How solution enables gains

### Experimentation (Hypothesis-Driven)
```
Hypothesis: "Students will use AI check-ins if anonymous within university portal"
Assumption: Users trust platform + anonymity reduces stigma
Test Method: A/B test (anonymous vs. named)
Success Metric: >40% completion rate in 2 weeks
Learning Goal: Validate platform + anonymity combination
```

---

## 📝 Week-by-Week Milestones

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| **Week 2** | Problem Finding & POV | POV Statement (PDF) |
| **Week 3** | Field Research Plan | Research Plan (PDF) |
| **Weeks 4–5** | Research & Personas | 12+ Interviews, 3–5 Personas |
| **Weeks 6–7** | Ideation & Prototype | 2–3 Prototypes + Feedback |
| **Weeks 8–9** | CVP Definition | CVP Canvas + Business Model |
| **Weeks 10–11** | Experiments & Pitch | Pitch Video + Prototype + Report |

---

## 🛠️ Development Tips

### Backend
- Use **SQLAlchemy ORM** for database access
- Use **Pydantic** for request validation
- Implement **async endpoints** for performance
- Use **Alembic** for database migrations
- Add **logging** for debugging
- Write **unit tests** for business logic

### Frontend (Flutter)
- Use **Provider** or **Riverpod** for state management
- Use **go_router** for navigation
- Implement **offline support** with SQLite
- Use **json_serializable** for API integration
- Add **error handling** for network requests
- Use **LocalStorage** for caching

### Testing
```bash
# Backend (Python)
pytest app/ -v

# Frontend (Flutter)
flutter test
```

---

## 🚢 Deployment

### Backend Deployment (Heroku/Railway/Fly.io)
```bash
# Create Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port $PORT" > Procfile

# Deploy to Heroku
heroku create iip-backend
heroku config:set DATABASE_URL=postgresql://...
git push heroku main

# API will be available at: https://iip-backend.herokuapp.com/api/v1/
```

### Frontend Deployment (Flutter)
```bash
# Build for iOS
flutter build ios

# Build for Android
flutter build apk

# Build for Web
flutter build web

# Deploy to Firebase Hosting (optional)
flutter pub global activate firebase_cli
firebase deploy
```

---

## 📚 Additional Resources

- **Design Thinking:** https://www.ideo.com/
- **Jobs to be Done (JTBD):** https://jobs-to-be-done.com/
- **Value Proposition Canvas:** https://strategyzer.com/canvas/value-proposition-canvas
- **Double Diamond:** https://www.designcouncil.org.uk/
- **Boston University OMBA:** https://www.bu.edu/

---

## 📞 Support & Questions

- **Module Instructors:** [Add contact info from course materials]
- **Technical Issues:** Check `docs/TROUBLESHOOTING.md`
- **API Documentation:** See `api_schemas.json` (Swagger/OpenAPI)
- **GitHub Issues:** Report bugs and feature requests

---

## 📄 License

This project specification and starter code is provided by Boston University for OMBA Module 6 students. Use for educational purposes only.

---

**Last Updated:** 2026-01-01  
**Version:** 1.0.0  
**Status:** Ready for Development 🚀
