from __future__ import annotations
import json
import os
import re
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='google.generativeai')
import google.generativeai as genai
from flask import Flask, jsonify, request
from sqlalchemy import text

from models import db


def _send_moderation_alert(post_id: int, body: str, report_count: int) -> None:
    """Send Telegram/Slack alert when a post is auto-hidden."""
    # Try Telegram first
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat = os.getenv("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat:
        try:
            msg = f"🚨 *Community Post Auto-Hidden*\n• Post ID: {post_id}\n• Reports: {report_count} unique IPs\n• Preview: {body[:100]}..."
            requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                json={"chat_id": tg_chat, "text": msg, "parse_mode": "Markdown"},
                timeout=5,
            )
            return
        except Exception:
            pass
    # Fallback to Slack/webhook
    webhook_url = os.getenv("SLACK_WEBHOOK_URL") or os.getenv("MODERATION_WEBHOOK_URL")
    if not webhook_url:
        return
    try:
        payload = {
            "text": f"🚨 *Community Post Auto-Hidden*\n• Post ID: {post_id}\n• Reports: {report_count} unique IPs\n• Preview: {body[:100]}..."
        }
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception:
        pass


SEED_PATH = "data/community_seed.json"

SAFE_REACTION_KINDS = {"relate", "helped", "strength"}

_MODERATION_PROMPT = """You are a content moderator for a mental health support community for teens.
Analyze this post and respond with ONLY one word: ALLOW, CRISIS, or REJECT.

Rules:
- ALLOW: Supportive, relatable, or neutral mental health content (feelings, coping, encouragement)
- CRISIS: Contains self-harm, suicide ideation, or immediate danger signals
- REJECT: Hate speech, harassment, spam, gibberish, or inappropriate content

Post to analyze:
\"\"\"
{body}
\"\"\"

Respond with exactly one word: ALLOW, CRISIS, or REJECT"""


def _moderate_post(body: str) -> Tuple[str, Optional[str]]:
    """AI moderation check. Returns (decision, reason) where decision is 'allow', 'crisis', or 'reject'."""
    api_key = os.getenv("GEMINI_API_KEY", "").split(",")[0].strip()
    if not api_key:
        return ("allow", None)
    try:
        prompt = _MODERATION_PROMPT.format(body=body[:500])
        
        # Try Nucleus DualEngineLLM first, fallback to native google.generativeai
        try:
            from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
            llm = DualEngineLLM("gemini-2.0-flash", api_key=api_key)
            resp = llm.generate_content(prompt)
        except ImportError:
            # Fallback to native google.generativeai when mcp_server_nucleus unavailable
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            resp = model.generate_content(prompt, request_options={"timeout": 30})
        
        raw = (resp.text or "").strip().upper()
        if "CRISIS" in raw:
            return (
                "crisis",
                "This post may indicate a crisis. Please reach out to a trusted adult or crisis line.",
            )
        if "REJECT" in raw:
            return (
                "reject",
                "This post doesn't meet community guidelines. Please share supportive content.",
            )
        return ("allow", None)
    except Exception:
        return ("allow", None)


def _dialect() -> str:
    try:
        eng = db.session.bind
        return eng.dialect.name if eng else "unknown"
    except Exception:
        return "unknown"


def _ensure_tables() -> None:
    """Create minimal community tables in a dialect-aware way (sqlite/pg)."""
    d = _dialect()
    try:
        if d == "sqlite":
            db.session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS community_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    body_redacted TEXT NOT NULL,
                    is_curated INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reactions_relate INTEGER DEFAULT 0,
                    reactions_helped INTEGER DEFAULT 0,
                    reactions_strength INTEGER DEFAULT 0
                )
                """
                )
            )
            db.session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS community_reactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    user_hash TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
                )
            )
            db.session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS community_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_type TEXT NOT NULL,
                    target_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
                )
            )
        else:  # assume postgres-compatible
            db.session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS community_posts (
                    id SERIAL PRIMARY KEY,
                    topic VARCHAR(64),
                    body_redacted TEXT NOT NULL,
                    is_curated BOOLEAN DEFAULT TRUE,
                    is_hidden BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reactions_relate INTEGER DEFAULT 0,
                    reactions_helped INTEGER DEFAULT 0,
                    reactions_strength INTEGER DEFAULT 0
                )
                """
                )
            )
            db.session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS community_reactions (
                    id SERIAL PRIMARY KEY,
                    post_id INTEGER NOT NULL,
                    kind VARCHAR(24) NOT NULL,
                    user_hash VARCHAR(64),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                )
            )
            db.session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS community_reports (
                    id SERIAL PRIMARY KEY,
                    target_type VARCHAR(24) NOT NULL,
                    target_id INTEGER NOT NULL,
                    reason VARCHAR(64) NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                )
            )
        # Attempt to add is_hidden and author_hash columns if missing
        try:
            d = _dialect()
            if d == "sqlite":
                try:
                    db.session.execute(
                        text(
                            "ALTER TABLE community_posts ADD COLUMN is_hidden INTEGER DEFAULT 0"
                        )
                    )
                except Exception:
                    pass
                try:
                    db.session.execute(
                        text("ALTER TABLE community_posts ADD COLUMN author_hash TEXT")
                    )
                except Exception:
                    pass
            elif d not in {"unknown"}:
                try:
                    db.session.execute(
                        text(
                            "ALTER TABLE community_posts ADD COLUMN IF NOT EXISTS is_hidden BOOLEAN DEFAULT FALSE"
                        )
                    )
                except Exception:
                    pass
                try:
                    db.session.execute(
                        text(
                            "ALTER TABLE community_posts ADD COLUMN IF NOT EXISTS author_hash VARCHAR(64)"
                        )
                    )
                except Exception:
                    pass
                # Add reporter_ip to community_reports for deduplication
                try:
                    db.session.execute(
                        text(
                            "ALTER TABLE community_reports ADD COLUMN IF NOT EXISTS reporter_ip VARCHAR(45)"
                        )
                    )
                except Exception:
                    pass
        finally:
            db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass
        raise


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(
    r"\b(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{4}\b"
)
URL_RE = re.compile(r"\bhttps?://\S+\b", re.IGNORECASE)
ADDRESS_HINT_RE = re.compile(
    r"\b(?:Street|St\.|Avenue|Ave\.|Road|Rd\.|Lane|Ln\.|Block|Apartment|Apt\.)\b",
    re.IGNORECASE,
)


def _pii_redact(text_in: str) -> str:
    t = EMAIL_RE.sub("[email]", text_in)
    t = PHONE_RE.sub("[phone]", t)
    t = URL_RE.sub("[link]", t)
    # Light hint-based masking (keeps tone while removing specifics)
    t = ADDRESS_HINT_RE.sub("[address]", t)
    return t


def _load_seed_if_empty(app: Flask) -> None:
    count = (
        db.session.execute(text("SELECT COUNT(*) FROM community_posts")).scalar() or 0
    )
    if count > 0:
        return
    try:
        with app.open_resource(SEED_PATH) as f:
            items = json.load(f)
        for it in items:
            topic = (it.get("topic") or "general").strip()[:64]
            body = _pii_redact(it.get("body", "").strip())
            if not body:
                continue
            db.session.execute(
                text(
                    """
                INSERT INTO community_posts (topic, body_redacted, is_curated)
                VALUES (:topic, :body, :is_curated)
                """
                ),
                {"topic": topic, "body": body, "is_curated": True},
            )
        db.session.commit()
    except FileNotFoundError:
        # No seed file; skip silently
        pass
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass


def register_community_routes(app: Flask) -> None:
    """Registers Phase 0 Community routes on the given app."""
    # Ensure tables exist and seed under an application context
    try:
        with app.app_context():
            _ensure_tables()
            try:
                _load_seed_if_empty(app)
            except Exception as e:
                try:
                    app.logger.warning(f"Community seed load failed: {e}")
                except Exception:
                    pass
    except Exception as e:
        try:
            app.logger.warning(f"Community init skipped: {e}")
        except Exception:
            pass

    if "community_flags" in app.view_functions:
        return

    def _enabled() -> bool:
        try:
            return str(app.config.get("COMMUNITY_ENABLED", "true")).lower() == "true"
        except Exception:
            return True

    def _posting_enabled() -> bool:
        """Posting is enabled only when COMMUNITY_POSTING_ENABLED=true and TEMPLATES_ONLY!=true"""
        try:
            posting_flag = (
                str(app.config.get("COMMUNITY_POSTING_ENABLED", "false")).lower()
                == "true"
            )
            templates_only = (
                str(app.config.get("TEMPLATES_ONLY", "false")).lower() == "true"
            )
            return posting_flag and not templates_only
        except Exception:
            return False

    # Rate limits (can be overridden via env -> app.config)
    limits_feed = str(app.config.get("RATE_LIMITS_COMMUNITY_FEED", "120 per minute"))
    limits_reaction = str(
        app.config.get("RATE_LIMITS_REACTION", "20 per minute; 200 per day")
    )
    limits_report = str(
        app.config.get("RATE_LIMITS_REPORT", "10 per minute; 100 per day")
    )
    limits_post = str(
        app.config.get("RATE_LIMITS_COMMUNITY_POST", "6 per minute; 60 per day")
    )

    @app.route("/api/community/flags", methods=["GET"])
    @app.limiter.limit(limits_feed)
    def community_flags():
        try:
            return (
                jsonify(
                    {
                        "enabled": _enabled(),
                        "posting_enabled": _posting_enabled(),
                        "templates_only": str(
                            app.config.get("TEMPLATES_ONLY", "false")
                        ).lower()
                        == "true",
                    }
                ),
                200,
            )
        except Exception:
            return jsonify({"error": "Failed to fetch flags"}), 500

    @app.route("/api/community/feed", methods=["GET"])
    @app.limiter.limit(limits_feed)
    def community_feed():
        if not _enabled():
            return jsonify({"error": "Community disabled"}), 403
        try:
            topic = (request.args.get("topic") or "").strip()
            try:
                limit = int(request.args.get("limit", "20"))
            except Exception:
                limit = 20
            limit = max(1, min(limit, 50))

            # Keyset cursor for infinite scroll
            before_created_at_raw = (
                request.args.get("before_created_at") or ""
            ).strip()
            before_id_raw = (request.args.get("before_id") or "").strip()
            before_created_at: Optional[datetime] = None
            before_id: Optional[int] = None
            if before_created_at_raw:
                try:
                    # Accept isoformat; if parse fails, ignore cursor
                    before_created_at = datetime.fromisoformat(before_created_at_raw)
                except Exception:
                    before_created_at = None
            if before_id_raw:
                try:
                    before_id = int(before_id_raw)
                except Exception:
                    before_id = None

            q = (
                "SELECT p.id, p.topic, p.body_redacted, p.created_at, "
                "(SELECT COUNT(DISTINCT COALESCE(NULLIF(r.user_hash, ''), CAST(r.id AS TEXT))) FROM community_reactions r "
                " WHERE r.post_id = p.id AND r.kind = 'relate') AS reactions_relate, "
                "(SELECT COUNT(DISTINCT COALESCE(NULLIF(r.user_hash, ''), CAST(r.id AS TEXT))) FROM community_reactions r "
                " WHERE r.post_id = p.id AND r.kind = 'helped') AS reactions_helped, "
                "(SELECT COUNT(DISTINCT COALESCE(NULLIF(r.user_hash, ''), CAST(r.id AS TEXT))) FROM community_reactions r "
                " WHERE r.post_id = p.id AND r.kind = 'strength') AS reactions_strength "
                "FROM community_posts p"
            )
            params: Dict[str, Any] = {}
            where_clauses: List[str] = []
            # Always exclude hidden posts
            where_clauses.append("COALESCE(p.is_hidden, FALSE) = FALSE")
            if topic:
                where_clauses.append("p.topic = :topic")
                params["topic"] = topic

            # Apply keyset cursor: fetch items strictly older than (created_at, id)
            if before_created_at is not None and before_id is not None:
                where_clauses.append(
                    "(p.created_at < :bts OR (p.created_at = :bts AND p.id < :bid))"
                )
                params["bts"] = before_created_at
                params["bid"] = before_id

            if where_clauses:
                q += " WHERE " + " AND ".join(where_clauses)

            q += " ORDER BY p.created_at DESC, p.id DESC LIMIT :limit"
            params["limit"] = limit

            rows = db.session.execute(text(q), params).fetchall()
            items: List[Dict[str, Any]] = []
            for r in rows:
                created = (
                    r.created_at.isoformat() if getattr(r, "created_at", None) else None
                )
                items.append(
                    {
                        "id": r.id,
                        "topic": r.topic,
                        "body": r.body_redacted,
                        "created_at": created,
                        "reactions": {
                            "relate": r.reactions_relate or 0,
                            "helped": r.reactions_helped or 0,
                            "strength": r.reactions_strength or 0,
                        },
                    }
                )
            # Prepare next cursor from the last item (if any)
            next_cursor: Optional[Dict[str, Any]] = None
            if len(items) == limit:
                last = items[-1]
                if last.get("created_at") is not None and last.get("id") is not None:
                    next_cursor = {
                        "before_created_at": last["created_at"],
                        "before_id": last["id"],
                    }
            return (
                jsonify(
                    {"items": items, "count": len(items), "next_cursor": next_cursor}
                ),
                200,
            )
        except Exception as e:
            try:
                app.logger.error(f"Community feed error: {e}")
            except Exception:
                pass
            return jsonify({"error": "Failed to fetch feed"}), 500

    def _check_admin() -> bool:
        try:
            import secrets
            token = (request.headers.get("X-Admin-Token") or "").strip()
            expected = str(app.config.get("ADMIN_TOKEN") or "").strip()
            return bool(token) and bool(expected) and secrets.compare_digest(token, expected)
        except Exception:
            return False

    def _reaction_counts(post_id: int) -> Dict[str, int]:
        try:
            out: Dict[str, int] = {}
            for k in ("relate", "helped", "strength"):
                n = db.session.execute(
                    text(
                        "SELECT COUNT(DISTINCT COALESCE(NULLIF(user_hash, ''), CAST(id AS TEXT))) "
                        "FROM community_reactions "
                        "WHERE post_id = :pid AND kind = :kind"
                    ),
                    {"pid": post_id, "kind": k},
                ).scalar()
                out[k] = int(n or 0)
            return out
        except Exception:
            return {"relate": 0, "helped": 0, "strength": 0}

    def _sync_post_counters(post_id: int, reactions: Dict[str, int]) -> None:
        try:
            db.session.execute(
                text(
                    "UPDATE community_posts "
                    "SET reactions_relate = :r, reactions_helped = :h, reactions_strength = :s "
                    "WHERE id = :pid"
                ),
                {
                    "pid": post_id,
                    "r": int(reactions.get("relate", 0)),
                    "h": int(reactions.get("helped", 0)),
                    "s": int(reactions.get("strength", 0)),
                },
            )
        except Exception:
            pass

    @app.route("/api/community/reports", methods=["GET"])
    def community_reports_list():
        if not _enabled():
            return jsonify({"error": "Community disabled"}), 403
        if not _check_admin():
            return jsonify({"error": "Unauthorized"}), 401
        try:
            try:
                limit = int(request.args.get("limit", "100"))
            except Exception:
                limit = 100
            limit = max(1, min(limit, 500))
            rows = db.session.execute(
                text(
                    """
                SELECT id, target_type, target_id, reason, notes, created_at
                FROM community_reports
                ORDER BY created_at DESC, id DESC
                LIMIT :limit
                """
                ),
                {"limit": limit},
            ).fetchall()
            items = []
            for r in rows:
                items.append(
                    {
                        "id": r.id,
                        "target_type": r.target_type,
                        "target_id": r.target_id,
                        "reason": r.reason,
                        "notes": r.notes,
                        "created_at": (
                            r.created_at.isoformat()
                            if getattr(r, "created_at", None)
                            else None
                        ),
                    }
                )
            return jsonify({"items": items, "count": len(items)}), 200
        except Exception as e:
            try:
                app.logger.error(f"Community reports list error: {e}")
            except Exception:
                pass
            return jsonify({"error": "Failed to fetch reports"}), 500

    @app.route("/api/community/moderate", methods=["POST"])
    @app.limiter.limit("10 per minute")
    def community_moderate():
        if not _enabled():
            return jsonify({"error": "Community disabled"}), 403
        if not _check_admin():
            return jsonify({"error": "Unauthorized"}), 401
        try:
            data = request.get_json(silent=True) or {}
            action = (data.get("action") or "").strip().lower()
            post_id = data.get("post_id")
            if not post_id or action not in {"hide", "unhide", "curate"}:
                return jsonify({"error": "Invalid moderation action or post_id"}), 400

            if action == "hide":
                db.session.execute(
                    text("UPDATE community_posts SET is_hidden = TRUE WHERE id = :pid"),
                    {"pid": post_id},
                )
            elif action == "unhide":
                db.session.execute(
                    text(
                        "UPDATE community_posts SET is_hidden = FALSE WHERE id = :pid"
                    ),
                    {"pid": post_id},
                )
            elif action == "curate":
                db.session.execute(
                    text(
                        "UPDATE community_posts SET is_curated = TRUE WHERE id = :pid"
                    ),
                    {"pid": post_id},
                )

            db.session.commit()
            return jsonify({"ok": True}), 200
        except Exception as e:
            try:
                db.session.rollback()
            except Exception:
                pass
            try:
                app.logger.error(f"Community moderation error: {e}")
            except Exception:
                pass
            return jsonify({"error": "Failed to apply moderation action"}), 500

    @app.route("/api/community/reaction", methods=["POST"])
    @app.limiter.limit(limits_reaction)
    def community_reaction():
        if not _enabled():
            return jsonify({"error": "Community disabled"}), 403
        try:
            data = request.get_json(silent=True) or {}
            post_id = data.get("post_id")
            kind = (data.get("kind") or "").strip().lower()
            if not post_id or kind not in SAFE_REACTION_KINDS:
                return jsonify({"error": "Invalid post_id or kind"}), 400

            # Optional user hash from session header (no PII)
            sid = (request.headers.get("X-Session-ID") or "").strip()
            if not sid:
                return jsonify({"error": "Missing session"}), 400
            user_hash = sid[:12]

            exists = db.session.execute(
                text(
                    "SELECT 1 FROM community_reactions "
                    "WHERE post_id = :pid AND kind = :kind AND user_hash = :uh "
                    "LIMIT 1"
                ),
                {"pid": post_id, "kind": kind, "uh": user_hash},
            ).first()
            if exists is not None:
                reactions = _reaction_counts(int(post_id))
                _sync_post_counters(int(post_id), reactions)
                db.session.commit()
                return (
                    jsonify(
                        {"ok": True, "already_reacted": True, "reactions": reactions}
                    ),
                    409,
                )

            # Insert reaction
            db.session.execute(
                text(
                    """
                INSERT INTO community_reactions (post_id, kind, user_hash)
                VALUES (:post_id, :kind, :user_hash)
                """
                ),
                {"post_id": post_id, "kind": kind, "user_hash": user_hash},
            )

            reactions = _reaction_counts(int(post_id))
            _sync_post_counters(int(post_id), reactions)
            db.session.commit()
            return (
                jsonify({"ok": True, "already_reacted": False, "reactions": reactions}),
                201,
            )
        except Exception as e:
            try:
                db.session.rollback()
            except Exception:
                pass
            try:
                app.logger.error(f"Community reaction error: {e}")
            except Exception:
                pass
            return jsonify({"error": "Failed to add reaction"}), 500

    @app.route("/api/community/react/<int:post_id>", methods=["POST"])
    @app.limiter.limit(limits_reaction)
    def community_react_legacy(post_id: int):
        """Legacy reaction endpoint for backward compatibility.

        Mirrors /api/community/reaction but takes the post_id in the path.
        """
        if not _enabled():
            return jsonify({"error": "Community disabled"}), 403
        try:
            data = request.get_json(silent=True) or {}
            kind = (data.get("kind") or "").strip().lower()
            if kind not in SAFE_REACTION_KINDS:
                return jsonify({"error": "Invalid reaction kind"}), 400

            # Optional user hash from session header (no PII)
            sid = (request.headers.get("X-Session-ID") or "").strip()
            if not sid:
                return jsonify({"error": "Missing session"}), 400
            user_hash = sid[:12]

            exists = db.session.execute(
                text(
                    "SELECT 1 FROM community_reactions "
                    "WHERE post_id = :pid AND kind = :kind AND user_hash = :uh "
                    "LIMIT 1"
                ),
                {"pid": post_id, "kind": kind, "uh": user_hash},
            ).first()
            if exists is not None:
                reactions = _reaction_counts(int(post_id))
                _sync_post_counters(int(post_id), reactions)
                db.session.commit()
                return (
                    jsonify(
                        {"ok": True, "already_reacted": True, "reactions": reactions}
                    ),
                    409,
                )

            # Insert reaction
            db.session.execute(
                text(
                    """
                INSERT INTO community_reactions (post_id, kind, user_hash)
                VALUES (:post_id, :kind, :user_hash)
                """
                ),
                {"post_id": post_id, "kind": kind, "user_hash": user_hash},
            )

            reactions = _reaction_counts(int(post_id))
            _sync_post_counters(int(post_id), reactions)
            db.session.commit()
            return (
                jsonify({"ok": True, "already_reacted": False, "reactions": reactions}),
                201,
            )
        except Exception as e:
            try:
                db.session.rollback()
            except Exception:
                pass
            try:
                app.logger.error(f"Community legacy reaction error: {e}")
            except Exception:
                pass
            return jsonify({"error": "Failed to add reaction"}), 500

    @app.route("/api/community/report", methods=["POST"])
    @app.limiter.limit(limits_report)
    def community_report():
        if not _enabled():
            return jsonify({"error": "Community disabled"}), 403
        try:
            data = request.get_json(silent=True) or {}
            target_type = (data.get("target_type") or "post").strip().lower()
            target_id = data.get("target_id")
            reason = (data.get("reason") or "").strip().lower()
            notes_raw = (data.get("notes") or "").strip() or None
            notes = _pii_redact(notes_raw) if notes_raw else None

            if target_type not in {"post"} or not target_id or not reason:
                return jsonify({"error": "Invalid report"}), 400

            # Get reporter IP for deduplication
            reporter_ip = request.headers.get(
                "X-Forwarded-For", request.remote_addr or ""
            )
            if reporter_ip:
                reporter_ip = reporter_ip.split(",")[0].strip()[:45]

            db.session.execute(
                text(
                    """
                INSERT INTO community_reports (target_type, target_id, reason, notes, reporter_ip)
                VALUES (:tt, :tid, :reason, :notes, :ip)
                """
                ),
                {
                    "tt": target_type,
                    "tid": target_id,
                    "reason": reason,
                    "notes": notes,
                    "ip": reporter_ip,
                },
            )

            # Auto-hide post if 3+ unique IPs reported it
            if target_type == "post":
                unique_ips = (
                    db.session.execute(
                        text(
                            """
                    SELECT COUNT(DISTINCT reporter_ip) as cnt
                    FROM community_reports
                    WHERE target_type = 'post' AND target_id = :tid AND reporter_ip IS NOT NULL
                    """
                        ),
                        {"tid": target_id},
                    ).scalar()
                    or 0
                )
                if unique_ips >= 3:
                    # Get post body for alert before hiding
                    post_body = db.session.execute(
                        text(
                            "SELECT body_redacted FROM community_posts WHERE id = :pid AND is_curated = FALSE"
                        ),
                        {"pid": target_id},
                    ).scalar()
                    if post_body:
                        db.session.execute(
                            text(
                                "UPDATE community_posts SET is_hidden = TRUE WHERE id = :pid AND is_curated = FALSE"
                            ),
                            {"pid": target_id},
                        )
                        # Send alert after hiding
                        _send_moderation_alert(target_id, post_body, unique_ips)

            db.session.commit()
            return jsonify({"ok": True}), 201
        except Exception as e:
            try:
                db.session.rollback()
            except Exception:
                pass
            try:
                app.logger.error(f"Community report error: {e}")
            except Exception:
                pass
            return jsonify({"error": "Failed to submit report"}), 500



    @app.route("/api/community/post", methods=["POST"])
    @app.limiter.limit(limits_post)
    def community_post():
        if not _enabled():
            return jsonify({"error": "Community disabled"}), 403
        if not _posting_enabled():
            return jsonify({"error": "Community posting disabled"}), 403
        try:
            data = request.get_json(silent=True) or {}
            topic = (data.get("topic") or "").strip()[:64]
            body_raw = (data.get("body") or "").strip()
            if not body_raw:
                return jsonify({"error": "Body is required"}), 400
            if len(body_raw) > 2000:
                # Hard stop on extremely long bodies (frontend uses 280 char soft limit)
                return jsonify({"error": "Body too long"}), 400

            body = _pii_redact(body_raw)

            decision, reason = _moderate_post(body)
            if decision == "crisis":
                return (
                    jsonify(
                        {
                            "error": reason
                            or "Please reach out to a trusted adult or crisis resource.",
                            "moderation": "crisis",
                        }
                    ),
                    422,
                )
            if decision == "reject":
                return (
                    jsonify(
                        {
                            "error": reason
                            or "This post doesn't meet community guidelines.",
                            "moderation": "rejected",
                        }
                    ),
                    422,
                )

            sid = (request.headers.get("X-Session-ID") or "").strip()
            author_hash = sid[:12] if sid else None

            d = _dialect()
            created_at: Optional[datetime] = None
            new_id: Optional[int] = None

            if d == "sqlite":
                db.session.execute(
                    text(
                        """
                    INSERT INTO community_posts (topic, body_redacted, is_curated, author_hash)
                    VALUES (:topic, :body, :is_curated, :author_hash)
                    """
                    ),
                    {
                        "topic": topic or "general",
                        "body": body,
                        "is_curated": False,
                        "author_hash": author_hash,
                    },
                )
                new_id = db.session.execute(text("SELECT last_insert_rowid()")).scalar()
                created_at = db.session.execute(
                    text("SELECT created_at FROM community_posts WHERE id = :id"),
                    {"id": new_id},
                ).scalar()
            else:
                res = db.session.execute(
                    text(
                        """
                    INSERT INTO community_posts (topic, body_redacted, is_curated, author_hash)
                    VALUES (:topic, :body, :is_curated, :author_hash)
                    RETURNING id, created_at
                    """
                    ),
                    {
                        "topic": topic or "general",
                        "body": body,
                        "is_curated": False,
                        "author_hash": author_hash,
                    },
                )
                row = res.first()
                if row is not None:
                    new_id = row.id
                    created_at = row.created_at

            db.session.commit()

            created_iso: Optional[str] = None
            try:
                created_iso = (
                    created_at.isoformat()
                    if isinstance(created_at, datetime)
                    else (created_at or None)
                )
            except Exception:
                created_iso = None

            return (
                jsonify(
                    {
                        "id": new_id,
                        "topic": topic or "general",
                        "body": body,
                        "created_at": created_iso,
                        "reactions": {"relate": 0, "helped": 0, "strength": 0},
                    }
                ),
                201,
            )
        except Exception as e:
            try:
                db.session.rollback()
            except Exception:
                pass
            try:
                app.logger.error(f"Community post error: {e}")
            except Exception:
                pass
            return jsonify({"error": "Failed to create post"}), 500

    @app.route("/api/community/post/<int:post_id>", methods=["DELETE"])
    @app.limiter.limit(limits_post)
    def community_delete_post(post_id: int):
        """Delete own post (soft delete via is_hidden)."""
        if not _enabled():
            return jsonify({"error": "Community disabled"}), 403
        try:
            sid = (request.headers.get("X-Session-ID") or "").strip()
            if not sid:
                return jsonify({"error": "Missing session"}), 400
            user_hash = sid[:12]

            row = db.session.execute(
                text(
                    "SELECT author_hash, is_curated FROM community_posts WHERE id = :pid"
                ),
                {"pid": post_id},
            ).first()

            if row is None:
                return jsonify({"error": "Post not found"}), 404

            author_hash = row.author_hash if hasattr(row, "author_hash") else None
            is_curated = row.is_curated if hasattr(row, "is_curated") else True

            if is_curated:
                return jsonify({"error": "Cannot delete curated posts"}), 403
            if not author_hash or author_hash != user_hash:
                return jsonify({"error": "You can only delete your own posts"}), 403

            db.session.execute(
                text("UPDATE community_posts SET is_hidden = TRUE WHERE id = :pid"),
                {"pid": post_id},
            )
            db.session.commit()
            return jsonify({"ok": True, "deleted": True}), 200
        except Exception as e:
            try:
                db.session.rollback()
            except Exception:
                pass
            try:
                app.logger.error(f"Community delete error: {e}")
            except Exception:
                pass
            return jsonify({"error": "Failed to delete post"}), 500
