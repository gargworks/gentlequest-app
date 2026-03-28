import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.database import init_db
from app.models.persona import Persona # Ensure registration
from app.models.cvp import CVPCanvas # Ensure registration
from app.models.roadmap import MVPRoadmap, MVPFeature # Ensure registration
from app.models.tasks import ProjectTask # Ensure registration
from app.models.chat import InterviewSession, ChatMessage # Ensure registration
from app.models.project_chat import ProjectChatSession, ProjectChatMessage # Ensure registration
from app.api import teams, llm, personas, cvp, roadmap, interviews, tasks, chat, project_chat

from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(title="IIP Module 6 API")


@app.exception_handler(UnicodeDecodeError)
async def unicode_decode_handler(request: Request, exc: UnicodeDecodeError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "Request contains invalid character encoding. Use UTF-8.",
            "code": "ENCODING_ERROR",
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    try:
        logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, traceback.format_exc())
    except (UnicodeDecodeError, UnicodeEncodeError):
        logger.error("Unhandled exception on %s %s (traceback omitted: encoding error)", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
        },
    )


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


