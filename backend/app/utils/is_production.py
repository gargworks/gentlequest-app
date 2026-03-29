import os


def is_production() -> bool:
    """Return True when running on Render (or ENVIRONMENT is explicitly 'production')."""
    if os.environ.get("RENDER"):
        return True
    return os.getenv("ENVIRONMENT", "").lower() == "production"
