from fastapi import FastAPI
from app.database import init_db
from app.models.persona import Persona # Ensure registration
from app.models.cvp import CVPCanvas # Ensure registration
from app.models.roadmap import MVPRoadmap, MVPFeature # Ensure registration
from app.models.tasks import ProjectTask # Ensure registration
from app.models.chat import InterviewSession, ChatMessage # Ensure registration
from app.models.project_chat import ProjectChatSession, ProjectChatMessage # Ensure registration
from app.api import teams, llm, personas, cvp, roadmap, interviews, tasks, chat, project_chat

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="IIP Module 6 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://iip-frontend-999376128638.us-central1.run.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(teams.router, prefix="/api/v1", tags=["teams"])
app.include_router(interviews.router, prefix="/api/v1", tags=["interviews"])
app.include_router(personas.router, prefix="/api/v1", tags=["personas"])
app.include_router(cvp.router, prefix="/api/v1", tags=["cvp"])
app.include_router(llm.router, prefix="/api/v1", tags=["llm"])
app.include_router(roadmap.router, prefix="/api/v1", tags=["roadmap"])
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(project_chat.router, prefix="/api/v1", tags=["project_chat"])


# Build 16 Force Rebuild (Fix NucleusService Import)
print("APP STARTUP: Backend modules loaded successfully.")


