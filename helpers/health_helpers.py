"""
Health check helpers for database, Redis, Ollama, and platform detection.
Extracted from app.py monolith.
"""

import os

import requests
from flask import current_app
from sqlalchemy import text as sql_text

from models import db


def _check_database_health() -> str:
    """Check database connection health"""
    try:
        engine = db.session.bind
        dialect = engine.dialect.name if engine else None
        if dialect == "postgresql":
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(sql_text("SET LOCAL statement_timeout = 2000"))
                    conn.execute(sql_text("SELECT 1"))
        else:
            db.session.execute(sql_text("SELECT 1"))
        return "healthy"
    except Exception as e:
        try:
            current_app.logger.error(f"Database health check failed: {e}")
        except Exception:
            pass
        return "unhealthy"


def _check_redis_health() -> str:
    """Check Redis connection health"""
    try:
        if current_app.config.get("SESSION_TYPE") == "redis":
            redis_client = current_app.config.get("SESSION_REDIS")
            if redis_client:
                redis_client.ping()
                return "healthy"
            else:
                return "not configured"
        else:
            return "using filesystem"
    except Exception as e:
        try:
            current_app.logger.error(f"Redis health check failed: {e}")
        except Exception:
            pass
        return "unhealthy"


def _check_ollama_health() -> dict:
    """Check Ollama reachability and whether the third-brother model is loaded."""
    base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    result = {"status": "unknown", "model_loaded": False}
    try:
        resp = requests.get(f"{base}/api/tags", timeout=2)
        resp.raise_for_status()
        models = [m.get("name", "") for m in resp.json().get("models", [])]
        result["status"] = "healthy"
        result["models"] = models
        result["model_loaded"] = any("third-brother" in m for m in models)
    except requests.ConnectionError:
        result["status"] = "unreachable"
    except requests.Timeout:
        result["status"] = "timeout"
    except Exception as e:
        result["status"] = f"unhealthy: {str(e)}"
    return result


def _detect_platform() -> str:
    """Detect deployment platform for single codebase usage"""
    if os.environ.get("RENDER"):
        return "render"
    elif os.environ.get("DOCKER_ENV") or os.environ.get("DOCKER"):
        return "docker"
    else:
        return "local"
