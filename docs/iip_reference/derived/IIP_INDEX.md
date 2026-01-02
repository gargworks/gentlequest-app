# IIP Module 6 Project - Complete Package Index

**Source Document:** M6W12-D2-IIP-Miro-Export.pdf  
**Generated:** January 1, 2026  
**Project:** Mental Health Support for Students (Stigma Reduction + Early Intervention)  
**Tech Stack:** Flutter (Frontend) + Python/Java (Backend) + PostgreSQL (Database)

---

## 📦 Package Contents

This converted package includes **5 production-ready files** that transform your Miro board into a fully-specified, codeable project:

### 1. **📖 IIP_Project_Specification.md** (MAIN DOCUMENT)
**What it is:** Complete, week-by-week project specification  
**Size:** ~15,000 words  
**Contains:**
- Module 6 overview & context
- **Week 2:** Problem Finding & POV Statement framework (3-category selection filter)
- **Week 3:** Field Research Plan (5 research methods, sampling strategy, data organization)
- **Weeks 4-5:** Research Execution & Persona Development (ANRUM insight extraction template)
- **Weeks 6-7:** Ideation & Prototyping (HMW questions, prototype testing loop)
- **Weeks 8-9:** CVP Definition (JTBD decomposition, trade-offs, competitive positioning)
- **Weeks 10-11:** Experimentation & Final Delivery (hypothesis-driven testing, deliverables checklist)
- Database schema for Python/Java backend (complete ERD)
- Flutter app folder structure
- Interview transcript template (markdown format)
- Submission checklists for each milestone
- Design thinking frameworks & JTBD canvas
- Team roles & responsibilities
- Resources & tools recommendations

**How to use:** 
- ✅ Print or read digitally as your "source of truth" document
- ✅ Reference while planning each week's work
- ✅ Share with team as unified specification
- ✅ Use templates for research capture

---

### 2. **🗄️ database_models.py** (BACKEND - SQLAlchemy ORM)
**What it is:** Complete SQLAlchemy ORM models for PostgreSQL  
**Language:** Python  
**Contains:**
- `Team` — Project team entity
- `TeamMember` — Individual team member
- `POVStatement` — Problem definition (Who/What/Why)
- `ResearchInterview` — Raw interview transcripts & metadata
- `ANRUMInsight` — Structured insight extraction (Attitude, Need, Response, Use case, Mental Model)
- `Persona` — User personas with supporting research
- `CVPCanvas` — Customer Value Proposition with JTBD & competitive analysis
- `Experiment` — Hypothesis testing & results tracking

**How to use:**
- ✅ Copy directly into FastAPI/Flask project
- ✅ Run `alembic` migrations to create tables
- ✅ Use as base for Spring Boot JPA entities (Java)
- ✅ Includes relationships, indexes, and constraints

---

### 3. **🔌 api_schemas.json** (API SPECIFICATION - OpenAPI 2.0 / Swagger)
**What it is:** Complete REST API specification  
**Format:** Swagger/OpenAPI 2.0  
**Contains:**
- **Paths (Endpoints):**
  - `POST /teams` — Create team
  - `GET /teams/{team_id}/pov` — Fetch POV statement
  - `POST /teams/{team_id}/interviews` — Record interview
  - `GET /teams/{team_id}/personas` — List personas
  - `POST /teams/{team_id}/cvp` — Create CVP Canvas
  - `POST /teams/{team_id}/experiments` — Track experiments
- **Definitions (Data Models):** Team, POV, Interview, Persona, CVPCanvas, Experiment, plus request/response DTOs
- **Request/Response Examples** for each endpoint
- **Data Validation** schemas

**How to use:**
- ✅ Import into **Postman** or **Insomnia** for API testing
- ✅ Use **Swagger UI** to generate interactive API docs
- ✅ Auto-generate client SDKs (use **OpenAPI Generator**)
- ✅ Auto-generate server stubs (FastAPI/Spring Boot)
- ✅ Share with team for API contract definition

---

### 4. **📱 flutter_models.dart** (FRONTEND - Flutter Models)
**What it is:** Complete Dart model classes for Flutter app  
**Language:** Dart (Flutter)  
**Contains:**
- **Domain Models:** Team, TeamMember, POVStatement, ResearchInterview, ANRUMInsight, Persona, CVPCanvas, Experiment
- **Request DTOs:** CreateTeamRequest, CreatePOVStatementRequest, CreateInterviewRequest, etc.
- **Features:**
  - JSON serialization with `json_serializable`
  - Equality & comparison with `equatable`
  - Type safety & null safety
  - All fields match backend schema

**How to use:**
- ✅ Copy into `lib/models/` folder
- ✅ Run `flutter pub run build_runner build` to generate serialization code
- ✅ Import in screens & services
- ✅ Maps directly to backend API responses
- ✅ Ready for Provider/Riverpod state management

---

### 5. **📋 README.md** (PROJECT GUIDE & SETUP INSTRUCTIONS)
**What it is:** Complete setup & development guide  
**Contains:**
- **Quick Start (3 sections):**
  - Backend Setup (Python/FastAPI)
  - Backend Setup Alternative (Java/Spring Boot)
  - Flutter Setup
- **Project Structure** (full directory tree)
- **Database Setup** (PostgreSQL with Docker Compose)
- **API Quick Reference** (curl examples)
- **Key Concepts** (Double Diamond, POV, ANRUM, CVP, Experimentation)
- **Week-by-Week Milestones** (timeline & deliverables)
- **Development Tips** (best practices for Python, Dart, testing)
- **Deployment Guide** (Heroku, Railway, Fly.io, Firebase)
- **Resources & Support**

**How to use:**
- ✅ Follow step-by-step setup for first-time project creation
- ✅ Reference during development sprints
- ✅ Share with team as onboarding guide
- ✅ Use deployment section for final submission

---

## 🎯 How These Files Work Together

### **Flow: Spec → Code → App**

```
┌─────────────────────────────────────────────────────────────┐
│  IIP_Project_Specification.md (THE BLUEPRINT)               │
│  - Week-by-week breakdown                                   │
│  - Research methodology                                     │
│  - Personas, CVP, experiments                               │
│  - Interview templates & checklists                         │
└────────────────┬────────────────────────────────────────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
      ▼                     ▼
┌─────────────────┐   ┌──────────────────┐
│ database_       │   │ api_schemas.json │
│ models.py       │   │                  │
│                 │   │ Swagger/OpenAPI  │
│ SQLAlchemy ORM  │   │ - Endpoints      │
│ - Tables        │   │ - Data models    │
│ - Relationships │   │ - Validation     │
│ - Migrations    │   │ - Examples       │
└────────┬────────┘   └────────┬─────────┘
         │                     │
         └──────────┬──────────┘
                    ▼
         ┌──────────────────────┐
         │ Backend (Python/Java)│
         │ - FastAPI/Spring     │
         │ - PostgreSQL         │
         │ - REST API           │
         │ - Business Logic     │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ flutter_models.dart  │
         │                      │
         │ Dart Models          │
         │ - JSON serialization │
         │ - Type safety        │
         │ - API mapping        │
         └──────────┬───────────┘
                    ▼
         ┌──────────────────────┐
         │ Flutter App (iOS/    │
         │ Android/Web)         │
         │                      │
         │ Screens, Services,   │
         │ State Management     │
         └──────────────────────┘
```

---

## 🚀 Getting Started (5 Steps)

### **Step 1: Read the Specification**
```bash
open IIP_Project_Specification.md
# OR
cat IIP_Project_Specification.md | less
```
Take 2-3 hours to understand the full project framework.

### **Step 2: Set Up Backend (Choose One)**

**Option A: Python/FastAPI**
```bash
mkdir iip-backend && cd iip-backend
python -m venv venv && source venv/bin/activate
pip install fastapi sqlalchemy psycopg2-binary
cp ../database_models.py ./app/models.py
# Start with: docker-compose up -d (PostgreSQL)
```

**Option B: Java/Spring Boot**
```bash
mvn archetype:generate -DgroupId=com.iip -DartifactId=iip-backend
cd iip-backend
# Add Spring Data JPA dependencies to pom.xml
# Map database_models.py concepts to JPA entities
```

### **Step 3: Set Up Frontend (Flutter)**
```bash
flutter create iip_app
cd iip_app
flutter pub add http json_annotation equatable provider
cp ../flutter_models.dart ./lib/models/
flutter pub run build_runner build
```

### **Step 4: Generate API Documentation**
```bash
# Use Swagger UI with api_schemas.json
# Option 1: Online Swagger Editor (https://editor.swagger.io/)
#   - Upload api_schemas.json
#   - Get interactive API documentation

# Option 2: Local Swagger UI (Docker)
docker run -p 8080:8080 -v $(pwd)/api_schemas.json:/tmp/swagger.json \
  swaggerapi/swagger-ui -e /tmp/swagger.json

# Option 3: Generate Client SDK
npm install -g @openapitools/openapi-generator-cli
openapi-generator-cli generate -i api_schemas.json -g dart -o ./flutter_app/
```

### **Step 5: Start Developing**
- Follow **README.md** for detailed setup
- Reference **IIP_Project_Specification.md** for weekly requirements
- Use **database_models.py** as ORM
- Use **flutter_models.dart** for frontend
- Use **api_schemas.json** for API contracts

---

## 📊 File Dependencies

```
README.md (Quick Start)
    ↓
IIP_Project_Specification.md (Full Context)
    ↓
    ├─→ database_models.py (Backend ORM)
    │       ↓
    │   [PostgreSQL Database]
    │       ↓
    │   [FastAPI/Spring Boot REST API]
    │
    ├─→ api_schemas.json (API Contract)
    │       ↓
    │   [Swagger/OpenAPI Documentation]
    │       ↓
    │   [OpenAPI Generator → Client SDKs]
    │
    └─→ flutter_models.dart (Frontend Models)
            ↓
        [Flutter App]
            ↓
        [HTTP Calls to Backend]
```

---

## 🎓 Learning Path

### **For Project Managers:**
1. Read: `IIP_Project_Specification.md` (Weeks 2-11 overview)
2. Reference: `README.md` (Milestones table)
3. Track: Database schema for understanding what data you're collecting

### **For Backend Developers (Python):**
1. Read: `README.md` (Backend Setup section)
2. Study: `database_models.py` (ORM models)
3. Implement: `api_schemas.json` endpoints
4. Integrate: PostgreSQL with Alembic migrations

### **For Backend Developers (Java):**
1. Read: `README.md` (Backend Setup - Java section)
2. Map: `database_models.py` to JPA entities
3. Implement: `api_schemas.json` REST controllers
4. Integrate: PostgreSQL with Spring Data JPA

### **For Mobile/Frontend Developers (Flutter):**
1. Read: `README.md` (Flutter Setup section)
2. Study: `flutter_models.dart` (Dart models)
3. Create: API service using models
4. Build: Screens referencing specification

### **For Full-Stack Developers:**
1. Read: `IIP_Project_Specification.md` (entire)
2. Setup: Backend + Database (steps 1-2)
3. Setup: Frontend (step 3)
4. Connect: Models + API service
5. Deploy: Using README.md deployment section

---

## 🔍 Key Data Models at a Glance

### **Team**
- `team_id`, `team_name`, `project_focus`
- Relations: members, pov_statements, interviews, personas, cvp_canvas, experiments

### **POVStatement**
- **Who:** `users_description` (e.g., "University students")
- **What:** `need_description` (e.g., "Accessible mental health resources")
- **Why:** `why_matters_description` (e.g., "Prevent crisis, improve academics")
- **Full:** Complete statement synthesizing all three

### **ResearchInterview**
- `interview_date`, `participant_role`, `interview_notes`
- `key_quotes` (array), `insights_extracted` (ANRUM objects)
- `researcher_bias_notes` (reflection)

### **Persona**
- `name`, `age`, `context`, `goals`, `frustrations`, `behaviors`, `motivations`, `barriers`
- Supported by: `supporting_interview_ids`, `supporting_quotes`

### **CVPCanvas**
- **Customer:** `customer_segment`
- **Jobs:** `jobs_to_be_done` (functional, emotional, social)
- **Value:** `value_proposition`, `pains`, `pain_relievers`, `gains`, `gain_creators`
- **Competition:** `competitive_positioning`, `differentiation`

### **Experiment**
- `hypothesis`, `assumption`, `test_method`, `success_metric`
- `status` (PENDING, IN_PROGRESS, COMPLETED, FAILED)
- `metric_value`, `learnings` (results)

---

## ✅ Pre-Development Checklist

- [ ] **Read** IIP_Project_Specification.md completely
- [ ] **Understand** Double Diamond framework & your team's role
- [ ] **Choose** tech stack (Python/Java for backend, Flutter for frontend)
- [ ] **Install** required tools (Python/Java, Flutter SDK, PostgreSQL client)
- [ ] **Fork/Clone** starter code from GitHub (if available)
- [ ] **Set up** local development environment (database, backend, frontend)
- [ ] **Generate** API docs from api_schemas.json
- [ ] **Test** API endpoints (use Postman/Insomnia with api_schemas.json)
- [ ] **Build** first Flutter screen (home_screen.dart)
- [ ] **Connect** Flutter app to backend API
- [ ] **Plan** Week 2 milestone (POV Statement)

---

## 📞 Support & Next Steps

### **Questions About Specification?**
→ Refer to `IIP_Project_Specification.md` (detailed explanations + templates)

### **Setup Issues?**
→ Follow `README.md` step-by-step

### **API Integration?**
→ Use `api_schemas.json` in Swagger Editor or Postman

### **Coding Questions?**
→ Check relevant section:
- Backend: `database_models.py`
- Frontend: `flutter_models.dart`
- Both: `README.md` (Development Tips)

### **Creating Additional Files?**
→ Ask your AI editor to extend any of these files with:
- Authentication layer (JWT, OAuth)
- PDF export for milestones
- NLP service for ANRUM extraction
- Analytics dashboard
- Testing suites
- CI/CD pipeline

---

## 📈 Success Metrics

Your project is on track when:

✅ **Week 2:** POV Statement submitted (clear Who/What/Why)  
✅ **Week 3:** Field Research Plan approved  
✅ **Weeks 4-5:** 12+ interviews conducted, 3-5 personas developed  
✅ **Weeks 6-7:** 2-3 prototypes tested with users  
✅ **Weeks 8-9:** CVP Canvas completed with clear positioning  
✅ **Weeks 10-11:** Pitch ready, experiments validated, app prototype functional  

---

## 🎉 You're Ready!

You now have:
- ✅ Complete project specification (15,000+ words)
- ✅ Production-ready database schema
- ✅ Full REST API specification
- ✅ Flutter model classes
- ✅ Setup & deployment guides

**Next action:** Open `README.md` and follow "Quick Start" section.

**Questions?** Ask your AI editor to expand any section or create additional components.

---

**Generated:** January 1, 2026  
**Version:** 1.0  
**Status:** Ready for Development 🚀
