"""
Memory System for Luna AI
Provides long-term memory using pgvector for semantic search.

Memory Types:
- episodic: Specific events ("User mentioned parents fighting on Dec 24")
- emotional: Patterns ("User responds well to breathing exercises")
- preference: User preferences ("User prefers short responses")
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import threading
import psycopg
from psycopg.rows import dict_row
from sqlalchemy import text

# Import from app context
from models import db


# Memory configuration
MEMORY_ENABLED = os.getenv('ENABLE_MEMORY', 'true').lower() == 'true'
PGVECTOR_ENABLED = os.getenv('ENABLE_PGVECTOR', 'true').lower() == 'true'

# Runtime flag - set to False if tables don't exist or pgvector unavailable
_memory_tables_ready = None

# Retention policies (in days)
MEMORY_RETENTION = {
    'episodic': 30,     # Specific events
    'emotional': 90,    # Emotional patterns
    'preference': 365,  # User preferences
}

# How many memories to retrieve per query
MAX_MEMORIES_RETRIEVED = 5


def _check_memory_tables_exist() -> bool:
    """
    Check if memory tables exist and pgvector is available.
    Caches result to avoid repeated checks.
    """
    global _memory_tables_ready
    
    if _memory_tables_ready is not None:
        return _memory_tables_ready
    
    if not MEMORY_ENABLED or not PGVECTOR_ENABLED:
        _memory_tables_ready = False
        return False
    
    conn = None
    try:
        from flask import current_app
        db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        
        # Robustly sanitize for psycopg (v3) which requires a clean postgresql:// URI
        if '://' in db_url:
            protocol, rest = db_url.split('://', 1)
            if '+' in protocol:
                protocol = protocol.split('+')[0]
            db_url = f"{protocol}://{rest}"
        
        if 'sqlite' in db_url.lower():
            _memory_tables_ready = False
            return False

        # Use raw psycopg connection for check
        conn = psycopg.connect(db_url)
        with conn.cursor() as cur:
            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'memory_summaries'
                )
            """)
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                _memory_tables_ready = False
                return False
            
            # Check if pgvector extension is available
            cur.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
            extension_exists = cur.fetchone()[0]
            
            _memory_tables_ready = bool(extension_exists)
            return _memory_tables_ready
            
    except Exception as e:
        print(f"Memory table check error: {e}")
        _memory_tables_ready = False
        return False
    finally:
        if conn: conn.close()


# ============================================================================
# DATABASE SCHEMA SETUP
# ============================================================================

def init_memory_tables(app) -> bool:
    """
    Initialize memory tables including pgvector extension.
    Call this during app startup.
    
    Returns True if successful, False if pgvector not available.
    """
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    
    # Robustly sanitize for psycopg (v3) which requires a clean postgresql:// URI
    if '://' in db_url:
        protocol, rest = db_url.split('://', 1)
        if '+' in protocol:
            protocol = protocol.split('+')[0]
        db_url = f"{protocol}://{rest}"

    if 'sqlite' in db_url.lower():
        app.logger.warning("Memory system: SQLite detected, skipping pgvector initialization")
        return False

    conn = None
    try:
        app.logger.info("🔄 Initializing PostgreSQL memory tables...")
        conn = psycopg.connect(db_url)
        with conn.cursor() as cur:
            # 1. Enable pgvector
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                conn.commit()
                app.logger.info("Memory system: pgvector extension enabled")
            except Exception as e:
                app.logger.warning(f"Memory system: pgvector creation skipped: {e}")
                conn.rollback()
            
            # 2. Create tables
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memory_summaries (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(36) NOT NULL,
                    memory_type VARCHAR(20) NOT NULL DEFAULT 'episodic',
                    content TEXT NOT NULL,
                    content_hash VARCHAR(16),
                    embedding vector(768),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            
            # 3. Create indices
            cur.execute("""
                CREATE INDEX IF NOT EXISTS memory_embedding_idx 
                ON memory_summaries 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS memory_session_idx 
                ON memory_summaries (session_id, memory_type)
            """)
            
            conn.commit()
            app.logger.info("✅ Memory system tables initialized successfully")
            return True
            
    except Exception as e:
        app.logger.error(f"❌ Memory system initialization error: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()


# ============================================================================
# MEMORY STORAGE
# ============================================================================

def store_memory(
    session_id: str,
    content: str,
    memory_type: str = 'episodic',
    metadata: Optional[Dict] = None
) -> bool:
    """
    Store a memory with embedding for later retrieval.
    
    Args:
        session_id: User session ID
        content: Memory content to store
        memory_type: Type of memory (episodic, emotional, preference)
        metadata: Optional metadata dict
        
    Returns:
        True if stored successfully
    """
    if not MEMORY_ENABLED or not _check_memory_tables_exist():
        return False
    
    raw_conn = None
    try:
        from providers.embeddings import generate_embedding, compute_text_hash
        
        # Generate embedding
        embedding = generate_embedding(content)
        if not embedding:
            return False
        
        # Compute hash for deduplication
        content_hash = compute_text_hash(content)
        
        # Calculate expiration
        retention_days = MEMORY_RETENTION.get(memory_type, 30)
        expires_at = datetime.utcnow() + timedelta(days=retention_days)
        
        # Store memory
        embedding_str = f"[{','.join(str(x) for x in embedding)}]"
        metadata_json = json.dumps(metadata) if metadata else None
        
        raw_conn = db.engine.raw_connection()
        with raw_conn.cursor() as cur:
            # Check for duplicate
            cur.execute("""
                SELECT id FROM memory_summaries 
                WHERE session_id = %s AND content_hash = %s
                LIMIT 1
            """, (session_id, content_hash))
            
            if cur.fetchone():
                return True  # Already stored
            
            cur.execute("""
                INSERT INTO memory_summaries 
                (session_id, memory_type, content, content_hash, embedding, metadata, expires_at)
                VALUES (%s, %s, %s, %s, %s::vector, %s::jsonb, %s)
            """, (session_id, memory_type, content, content_hash, embedding_str, metadata_json, expires_at))
            
            raw_conn.commit()
        return True
        
    except Exception as e:
        print(f"Memory storage error: {e}")
        if raw_conn: raw_conn.rollback()
        return False
    finally:
        if raw_conn: raw_conn.close()


# ============================================================================
# MEMORY RETRIEVAL
# ============================================================================

def retrieve_relevant_memories(
    session_id: str,
    query: str,
    limit: int = MAX_MEMORIES_RETRIEVED
) -> List[Dict[str, Any]]:
    """
    Retrieve memories relevant to the query using semantic search.
    
    Args:
        session_id: User session ID
        query: Current message to find relevant context for
        limit: Maximum number of memories to retrieve
        
    Returns:
        List of memory dicts with content and similarity score
    """
    if not MEMORY_ENABLED or not PGVECTOR_ENABLED or not _check_memory_tables_exist():
        return []
    
    raw_conn = None
    try:
        from providers.embeddings import generate_query_embedding
        
        # Generate query embedding
        query_embedding = generate_query_embedding(query)
        if not query_embedding:
            return []
        
        embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"
        
        raw_conn = db.engine.raw_connection()
        memories = []
        
        # Use dict_row for easy access
        with raw_conn.cursor(row_factory=dict_row) as cur:
            # Semantic search using cosine similarity
            cur.execute("""
                SELECT 
                    content,
                    memory_type,
                    metadata,
                    created_at,
                    1 - (embedding <=> %s::vector) as similarity
                FROM memory_summaries
                WHERE session_id = %s
                  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (embedding_str, session_id, embedding_str, limit))
            
            results = cur.fetchall()
            
            for row in results:
                # Only include if similarity is above threshold
                sim = row.get('similarity') or 0
                if sim > 0.3:
                    memories.append({
                        "content": row['content'],
                        "type": row['memory_type'],
                        "metadata": row['metadata'] if isinstance(row['metadata'], dict) else json.loads(row['metadata'] or '{}'),
                        "created_at": row['created_at'].isoformat() if hasattr(row['created_at'], 'isoformat') else str(row['created_at']),
                        "similarity": round(float(sim), 3),
                    })
        
        return memories
        
    except Exception as e:
        print(f"Memory retrieval error: {e}")
        return []
    finally:
        if raw_conn: raw_conn.close()


def get_memory_context_for_prompt(session_id: str, message: str) -> str:
    """
    Get formatted memory context to inject into Luna's prompt.
    
    Returns a string like:
    "Previous context about this user:
    - User mentioned sleep issues on Dec 20
    - User responds well to breathing exercises"
    """
    memories = retrieve_relevant_memories(session_id, message)
    
    if not memories:
        return ""
    
    context_lines = ["Previous context about this user:"]
    for mem in memories:
        context_lines.append(f"- {mem['content']}")
    
    return "\n".join(context_lines)


# ============================================================================
# MEMORY MANAGEMENT
# ============================================================================

def clear_user_memory(session_id: str) -> bool:
    """Clear all memories for a user (user-initiated)."""
    raw_conn = None
    try:
        raw_conn = db.engine.raw_connection()
        with raw_conn.cursor() as cur:
            cur.execute("DELETE FROM memory_summaries WHERE session_id = %s", (session_id,))
            raw_conn.commit()
        return True
    except Exception as e:
        print(f"Memory clear error: {e}")
        if raw_conn: raw_conn.rollback()
        return False
    finally:
        if raw_conn: raw_conn.close()


def cleanup_expired_memories() -> int:
    """Remove expired memories. Call periodically."""
    raw_conn = None
    try:
        raw_conn = db.engine.raw_connection()
        with raw_conn.cursor() as cur:
            cur.execute("DELETE FROM memory_summaries WHERE expires_at < CURRENT_TIMESTAMP")
            count = cur.rowcount
            raw_conn.commit()
            return count
    except Exception as e:
        print(f"Memory cleanup error: {e}")
        if raw_conn: raw_conn.rollback()
        return 0
    finally:
        if raw_conn: raw_conn.close()


# ============================================================================
# CONVERSATION SUMMARIZATION
# ============================================================================

def _get_api_key() -> Optional[str]:
    """Get Gemini API key from environment."""
    return os.getenv('GEMINI_API_KEY', '').split(',')[0].strip() or None


def summarize_interaction_llm(
    session_id: str,
    user_message: str,
    ai_response: str
) -> bool:
    """
    Extract memories using Gemini Flash (Observer Pattern).
    Intended to be run asynchronously.
    """
    if not MEMORY_ENABLED or not _check_memory_tables_exist():
        return False
        
    api_key = _get_api_key()
    if not api_key:
        return False
        
    try:
        prompt = f"""
        Analyze this interaction between a user and an AI companion.
        Extract 1-3 atomic facts, emotional states, or preferences worth remembering long-term.
        Ignore trivial chitchat.
        
        User: {user_message}
        AI: {ai_response}
        
        Return ONLY a JSON array of objects with this schema:
        [
            {{
                "type": "episodic" | "emotional" | "preference",
                "content": "concise memory statement"
            }}
        ]
        """
        
        # Try Nucleus DualEngineLLM first, fallback to native google.generativeai
        try:
            from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
            llm = DualEngineLLM('gemini-2.5-flash', api_key=api_key)
            response = llm.generate_content(prompt)
        except ImportError:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
        
        if not response or not getattr(response, "text", None):
            return False
            
        # Clean markdown code blocks if present
        text = response.text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()
            
        memories = json.loads(text)
        
        for mem in memories:
            store_memory(
                session_id=session_id,
                content=mem['content'],
                memory_type=mem.get('type', 'episodic'),
                metadata={"source": "observer", "date": datetime.utcnow().isoformat()}
            )
            
        return True
        
    except Exception as e:
        print(f"Observer LLM error: {e}")
        return False


# Deprecated: _extract_emotions and _extract_topics are replaced by summarize_interaction_llm
# Keeping empty/pass functions if imported elsewhere, or we can just remove them 
# since they were internal helpers (starts with _)

def _extract_emotions(text: str) -> List[str]:
    return []

def _extract_topics(text: str) -> List[str]:
    return []
