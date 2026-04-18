"""
Database URL normalization and DNS diagnostics.
Extracted from app.py monolith.

`configure_database_url(app)` applies:
- Render-style `postgres://` → `postgresql+psycopg://`
- Appends `sslmode=require` + `connect_timeout=2` for production Postgres
- Sets SQLAlchemy engine options (pool size, pre-ping, recycle) with SQLite-safe fallback
- Logs a masked DB URL + DNS resolution info for debugging
"""

import os
import socket
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from flask import Flask

from config.settings import Config


def _normalize_postgres_url(db_url: str, app: Flask) -> str:
    """Apply psycopg driver + sslmode + connect_timeout for Postgres URLs."""
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if "postgresql://" in db_url and "psycopg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    try:
        needs_ssl = (
            getattr(Config, "RENDER", False)
            or str(getattr(Config, "ENVIRONMENT", "")).lower() == "production"
        )
        parsed = urlparse(db_url)
        if parsed.scheme.startswith("postgresql"):
            query_items = dict(parse_qsl(parsed.query)) if parsed.query else {}
            lower_keys = {k.lower() for k in query_items}
            if needs_ssl and "sslmode" not in lower_keys:
                query_items["sslmode"] = "require"
            if "connect_timeout" not in lower_keys:
                query_items["connect_timeout"] = "2"
            new_query = urlencode(query_items)
            parsed = parsed._replace(query=new_query)
            db_url = urlunparse(parsed)
    except Exception as e:
        app.logger.warning(f"Failed to process DB URL SSL params: {e}")

    return db_url


def _mask_db_url(url: str) -> str:
    """Mask password in a DB URL for safe logging."""
    try:
        if isinstance(url, str) and url.strip().lower().startswith("sqlite:"):
            return url
        p = urlparse(url)
        netloc = p.netloc
        if "@" in netloc:
            creds, host = netloc.split("@", 1)
            if ":" in creds:
                user, _pwd = creds.split(":", 1)
                creds_masked = f"{user}:***"
            else:
                creds_masked = f"{creds}:***"
            netloc_masked = f"{creds_masked}@{host}"
        else:
            netloc_masked = netloc
        return urlunparse(
            (p.scheme, netloc_masked, p.path, p.params, p.query, p.fragment)
        )
    except Exception:
        return "<mask_failed>"


def _log_dns_resolution(effective_url: str, app: Flask) -> None:
    """Best-effort DNS resolution to aid debug of host/network issues."""
    try:
        if not effective_url:
            return
        p = urlparse(effective_url)
        if p.scheme and p.scheme.lower().startswith("sqlite"):
            return
        host = p.hostname
        if not host:
            return
        try:
            addr_list = socket.getaddrinfo(host, None)
            ips = sorted(
                {
                    item[4][0]
                    for item in addr_list
                    if item and item[4] and item[4][0]
                }
            )
            app.logger.info(f"DB host '{host}' resolves to: {', '.join(ips)}")
        except Exception as e:
            app.logger.warning(f"DNS resolution failed for DB host '{host}': {e}")
    except Exception as e:
        app.logger.warning(f"Failed to log DB URL or DNS info: {e}")


def configure_database_url(app: Flask) -> None:
    """Normalize DB URL, set engine options, log masked URL + DNS resolution."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        db_url = _normalize_postgres_url(db_url, app)
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    elif not app.config.get("TESTING"):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instance/mental_health.db"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    engine_options = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not db_uri.startswith("sqlite"):
        engine_options.update({
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 2,
        })
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options

    # Log masked URL + DNS
    effective_url = app.config.get("SQLALCHEMY_DATABASE_URI")
    masked = _mask_db_url(effective_url) if effective_url else "None"
    app.logger.info(f"Database URL (masked): {masked}")
    _log_dns_resolution(effective_url or "", app)
