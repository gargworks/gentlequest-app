from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
import os

# Default to asyncpg for local if not specified, but prefer psycopg for prod consistency if env var is set
default_db_url = "postgresql+psycopg://iip_user:iip_password@localhost:5433/iip_db"
DATABASE_URL = os.getenv("DATABASE_URL", default_db_url)

# Normalize URL to ensure valid async driver scheme (postgresql+psycopg://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
if "postgresql://" in DATABASE_URL and "psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
# Enforce asyncpg -> psycopg switch if we decided to fully migrate
if "asyncpg" in DATABASE_URL:
     DATABASE_URL = DATABASE_URL.replace("asyncpg", "psycopg")

# Production SSL and Timeout handling (Mirrors main app logic)
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
if ENVIRONMENT == "production" or os.getenv("RENDER"):
    try:
        parsed = urlparse(DATABASE_URL)
        if parsed.scheme.startswith("postgresql"):
            query_items = dict(parse_qsl(parsed.query)) if parsed.query else {}
            lower_keys = {k.lower() for k in query_items.keys()}
            
            # Enforce SSL for Cloud SQL/Production
            if "sslmode" not in lower_keys:
                query_items["sslmode"] = "require"
            
            # Short timeout to fail fast
            if "connect_timeout" not in lower_keys:
                query_items["connect_timeout"] = "2"
                
            new_query = urlencode(query_items)
            parsed = parsed._replace(query=new_query)
            DATABASE_URL = urlunparse(parsed)
            print("DEBUG: Enforced SSL and Timeout on DATABASE_URL")
    except Exception as e:
        print(f"WARNING: Failed to process DB URL params: {e}")

# Debug Log (Masked)
try:
    if "@" in DATABASE_URL:
        safe_url = DATABASE_URL.replace(DATABASE_URL.split("@")[0].split("//")[1].split(":")[1], "***")
        print(f"DEBUG: Connecting to: {safe_url}")
except:
    pass

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
