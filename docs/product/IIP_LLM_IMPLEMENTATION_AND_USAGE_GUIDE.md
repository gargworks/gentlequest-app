# IIP LLM Implementation & Usage Guide (Parent/Creator View)

This guide explains **exactly how to use the existing repo files + folders** to build and run your IIP app, and what the system can do for you as the **creator/parent of the idea** (i.e., the person overseeing the project and using the LLM to accelerate work). [file:8][file:11][file:7]

---

## What you already have

The repository already contains:
- A **course-to-product specification** that describes the IIP workflow (Weeks 2–11) and the data model you need to store it. [file:11]
- A **backend contract** (Swagger/OpenAPI) that defines the REST endpoints and JSON shapes. [file:7]
- A **Quick Start** that describes how to set up FastAPI + Postgres + Flutter. [file:8]

**Prudent assumption:** treat these as the “contracts” and build a thin, working vertical slice before adding extras. [file:8][file:11]

---

## Folder map (what each folder/file is for)

> If a file is duplicated in your workspace, pick one canonical copy and keep the rest as backups.

### `/docs/`
Use `/docs/` as the **single source of truth** for how the app should behave.

Recommended structure:
```
/docs/
  /iip_reference/
    /raw/
      M6W12-D2-IIP-Miro-Export.pdf
    /derived/
      IIP_MIRO_FULL_CONTEXT_EXPANDED.md
      IIP_MIRO_WEEKS_4_5_SOLO.md
      WEEK_9_10_INDIVIDUAL_COMPLETE.md
      WEEK_14_FINAL_DELIVERABLE.md
      ...
  /product/
    IIP_LLM_IMPLEMENTATION_AND_USAGE_GUIDE.md   (this file)
```

Key inputs inside your current package:
- `IIP_Project_Specification.md` — the week-by-week blueprint and recommended backend structure (models/schemas/api/services). [file:11]
- `api_schemas.json` — the API contract you must implement. [file:7]
- `README.md` — setup commands and the suggested folder layout for backend + Flutter. [file:8]

### `/backend/` (to be created if not present)
Contains the working FastAPI app and database.

Target structure (recommended by README/spec):
```
/backend/
  main.py
  requirements.txt
  app/
    api/
      teams.py
      interviews.py
      personas.py
      cvp_canvas.py
      experiments.py
      llm_coach.py            # (you will add)
    models/
      models.py               # (or split files)
    schemas/
      team_schema.py
      interview_schema.py
      persona_schema.py
      cvp_schema.py
      experiment_schema.py
      llm_schema.py           # (you will add)
    services/
      ai_insights_service.py  # ANRUM extraction
      export_service.py       # PDF/MD export
      llm_service.py          # provider wrapper (OpenAI/local)
      retrieval_service.py    # chunking + search over docs
    database.py
    config.py
  alembic/
  .env
  docker-compose.yml
```
The split matches the recommended architecture in the provided docs. [file:8][file:11]

### `/flutter_app/` (to be created if not present)
Contains the UI and uses the models defined in the repo.

Target structure from README:
```
/flutter_app/
  lib/
    models/
      flutter_models.dart
    services/
      api_service.dart
    screens/
      project_dashboard_screen.dart
      research_viewer_screen.dart
      persona_builder_screen.dart
      cvp_canvas_screen.dart
      experiment_tracker_screen.dart
```
The Flutter models file is intended to match the backend schemas. [file:8]

---

## How to use the text files (exactly)

### 1) `IIP_Project_Specification.md` (your “product requirements document”)
Use this file to:
- Define what the app should support **feature-wise** (POV, interviews, ANRUM, personas, CVP, experiments). [file:11]
- Define the **workflow states** you’ll expose in UI: Discover/Define/Develop/Deliver (Double Diamond). [file:11]
- Decide what LLM outputs must look like (especially ANRUM extraction and experiment hypotheses). [file:11]

**Operational rule:** any feature not described here is a “nice-to-have” and should be gated behind a later milestone. [file:11]

### 2) `api_schemas.json` (your API “contract”) 
Use this file to:
- Generate your endpoint skeletons.
- Validate request/response shapes.
- Create test cases.

Minimum endpoints you must implement (v1):
- `POST /api/v1/teams`, `GET /api/v1/teams` [file:7]
- `POST /api/v1/teams/{team_id}/pov`, `GET /api/v1/teams/{team_id}/pov` [file:7]
- `POST /api/v1/teams/{team_id}/interviews`, `GET /api/v1/teams/{team_id}/interviews` [file:7]
- `POST /api/v1/teams/{team_id}/personas`, `GET /api/v1/teams/{team_id}/personas` [file:7]
- `POST /api/v1/teams/{team_id}/cvp`, `GET /api/v1/teams/{team_id}/cvp` [file:7]
- `POST /api/v1/teams/{team_id}/experiments`, `GET /api/v1/teams/{team_id}/experiments` [file:7]

### 3) `README.md` (your “runbook”)
Use this file for:
- One-time setup commands for backend + Flutter.
- Local Postgres via Docker.
- Curl examples for the key endpoints.

It includes FastAPI wiring guidance and folder layout you should follow. [file:8]

### 4) Derived IIP context MD files (your “knowledge base”)
These docs are for the LLM retrieval layer. The LLM should be able to:
- Summarize the project history.
- Answer questions like “what did we decide and why?”
- Generate new hypotheses/experiments consistent with the existing work.

Primary knowledge files:
- `IIP_MIRO_FULL_CONTEXT_EXPANDED.md` (main timeline Weeks 2–12) 
- `IIP_MIRO_WEEKS_4_5_SOLO.md` (raw research/personas)
- `WEEK_9_10_INDIVIDUAL_COMPLETE.md` (divergent CVPs/BMCs)
- `WEEK_14_FINAL_DELIVERABLE.md` (final reflection narrative)

These are meant to be indexed + chunked into embeddings or full-text search. [file:11]

---

## What the app can do (as the Parent/Creator)

Think of yourself as the **program manager + product owner** for the innovation journey.

### Create and manage teams
- Create teams and set `project_focus` (e.g., “Mental Health Support”). [file:7]
- List teams to switch context quickly. [file:7]

### Capture the POV (Week 2)
- Create/update POV with Who/What/Why.
- Auto-generate the combined `full_statement` string.
- Track `iteration_count` over time (important for learning). [file:7][file:11]

### Capture research (Weeks 4–5)
- Add interviews with:
  - `interview_notes`
  - `key_quotes`
  - `researcher_bias_notes` [file:7][file:11]

### Generate structured insights (ANRUM) via LLM
The system should provide a “Generate ANRUM” action that:
1. Takes interview text as input.
2. Outputs structured ANRUM entries (Attitude/Need/Response/Use case/Mental model).
3. Saves them either:
   - inside `insights_extracted` in the Interview record, OR
   - as a dedicated table if you extend the DB later. [file:11][file:7]

### Build and refine personas
- Create personas with goals/frustrations/behaviors/motivations/barriers + supporting quotes. [file:7][file:11]
- Link personas to interviews via `supporting_interview_ids` (traceability). [file:7]

### Define the CVP (Weeks 8–9)
- Create/update CVP: customer segment, JTBD, pains/gains, differentiation, competitive positioning. [file:7][file:11]

### Track experiments (Weeks 10–11)
- Create experiments with:
  - hypothesis, assumption, test_method, success_metric, learning_goal [file:7][file:11]
- Update status: `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`. [file:7]
- Save results and learnings when complete (result_summary, metric_value, learnings). [file:7]

### Use the LLM as a “coach”
As parent/creator, the most valuable LLM actions are:
- “What’s the next best experiment to run?” (based on POV + interviews + CVP). [file:11]
- “Extract top 10 insights from these interviews in ANRUM format.” [file:11]
- “Write a 1-page executive summary / pitch memo from our stored data.” [file:11]

---

## LLM system design (how your LLM should operate)

### Modes of operation
1. **Data-entry assistant (write mode)**
   - Helps generate structured objects to store via the API.
   - Example outputs: POVStatementCreate, InterviewCreate, PersonaCreate, ExperimentCreate. [file:7]

2. **Coach assistant (read + recommend mode)**
   - Reads existing stored data for a team and provides:
     - prioritization
     - tradeoff analysis
     - next-step recommendations (aligned with Double Diamond).

3. **Retrieval assistant (docs grounding)**
   - Searches the derived Miro exports to answer project-history questions.

### Recommended retrieval approach
- Build a small ingestion job that:
  - Reads all `.md` in `docs/iip_reference/derived/`
  - Splits into chunks (e.g., 800–1200 tokens)
  - Stores into a vector DB OR Postgres full-text search
  - Returns top-k chunks as context to the LLM.

This is how you “use these text files and folders” for real functionality. [file:11]

### Parent-safe constraints (recommended)
Because the domain is student mental health:
- The LLM must never claim to provide clinical diagnosis.
- The LLM should present content as “research insights / product hypotheses” and encourage professional review.

(Implement as system prompts + refusal rules.)

---

## Concrete build milestones (what your LLM should implement)

### Milestone A (1–2 days): API + DB running
- Stand up Postgres + migrations.
- Implement `/teams` and `/teams/{team_id}/pov` endpoints. [file:7][file:8]

### Milestone B (2–4 days): Research capture
- Implement interviews CRUD (create + list).
- Implement persona CRUD (create + list).

### Milestone C (2–3 days): CVP + experiments
- Implement CVP create/update + get.
- Implement experiment create + list.

### Milestone D (3–6 days): LLM coach v1
- Implement backend endpoint: `POST /teams/{team_id}/llm/anrum` (you add this)
  - Reads a specific interview or raw text
  - Returns ANRUM JSON
  - Saves into interview.insights_extracted
- Implement backend endpoint: `POST /teams/{team_id}/llm/experiments` (you add this)
  - Reads team context
  - Returns 3–5 ExperimentCreate objects
  - Optionally auto-saves them

### Milestone E (optional): Export to “submission PDFs”
- Use `export_service.py` to output Week milestones as a report.

---

## Example end-to-end usage (Parent workflow)

1. Create a team: `POST /api/v1/teams` with name + focus. [file:7][file:8]
2. Capture POV: `POST /api/v1/teams/{id}/pov`. [file:7]
3. Add interviews weekly: `POST /api/v1/teams/{id}/interviews`. [file:7]
4. Press “Generate ANRUM” for each interview (LLM) and store it.
5. Create personas from clustered ANRUM insights. [file:11]
6. Build/update CVP as you learn. [file:7]
7. Ask LLM: “Propose 3 experiments to validate our biggest risks.”
8. Track experiment status and results. [file:7]

---

## Next question (to finalize exact instructions)

Which LLM runtime will you use for `llm_service.py`?
- OpenAI API
- Azure OpenAI
- Local (Ollama / llama.cpp)
- Other
