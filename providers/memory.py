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
    
    try:
        # Check if table exists
        result = db.session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'memory_summaries'
            )
        """)).scalar()
        
        if not result:
            _memory_tables_ready = False
            return False
        
        # Check if pgvector extension is available
        result = db.session.execute(text("""
            SELECT EXISTS (
                SELECT FROM pg_extension WHERE extname = 'vector'
            )
        """)).scalar()
        
        _memory_tables_ready = bool(result)
        return _memory_tables_ready
        
    except Exception as e:
        print(f"Memory table check error: {e}")
        db.session.rollback()  # Important: don't let failed check abort transaction
        _memory_tables_ready = False
        return False


# ============================================================================
# DATABASE SCHEMA SETUP
# ============================================================================

def init_memory_tables(app) -> bool:
    """
    Initialize memory tables including pgvector extension.
    Call this during app startup.
    
    Returns True if successful, False if pgvector not available.
    """
    with app.app_context():
        try:
            engine = db.session.bind
            dialect = engine.dialect.name if engine else 'unknown'
            
            # Try to enable pgvector extension
            # Try to enable pgvector extension
            try:
                db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                db.session.commit()
                app.logger.info("Memory system: pgvector extension enabled")
            except Exception as e:
                app.logger.warning(f"Memory system: pgvector creation skipped (might exist or permission denied): {e}")
                db.session.rollback()
                
                # Check if it actually exists before giving up
                exists = db.session.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")).scalar()
                if not exists:
                    app.logger.error("Memory system: pgvector extension missing and creation failed")
                    return False
                app.logger.info("Memory system: pgvector verified existing")
            
            # Create memory_summaries table
            db.session.execute(text("""
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
            """))
            
            # Create index for vector similarity search
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS memory_embedding_idx 
                ON memory_summaries 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))
            
            # Create index for session lookups
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS memory_session_idx 
                ON memory_summaries (session_id, memory_type)
            """))
            
            db.session.commit()
            app.logger.info("Memory system: tables initialized successfully")
            return True
            
        except Exception as e:
            app.logger.error(f"Memory system initialization error: {e}")
            db.session.rollback()
            return False


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
    
    try:
        from providers.embeddings import generate_embedding, compute_text_hash
        
        # Generate embedding
        embedding = generate_embedding(content)
        if not embedding:
            return False
        
        # Compute hash for deduplication
        content_hash = compute_text_hash(content)
        
        # Check for duplicate (same session, same content hash)
        existing = db.session.execute(
            text("""
                SELECT id FROM memory_summaries 
                WHERE session_id = :session_id AND content_hash = :hash
                LIMIT 1
            """),
            {"session_id": session_id, "hash": content_hash}
        ).fetchone()
        
        if existing:
            return True  # Already stored
        
        # Calculate expiration
        retention_days = MEMORY_RETENTION.get(memory_type, 30)
        expires_at = datetime.utcnow() + timedelta(days=retention_days)
        
        # Store memory
        embedding_str = f"[{','.join(str(x) for x in embedding)}]"
        
        db.session.execute(
            text("""
                INSERT INTO memory_summaries 
                (session_id, memory_type, content, content_hash, embedding, metadata, expires_at)
                VALUES (:session_id, :memory_type, :content, :hash, :embedding::vector, :metadata, :expires_at)
            """),
            {
                "session_id": session_id,
                "memory_type": memory_type,
                "content": content,
                "hash": content_hash,
                "embedding": embedding_str,
                "metadata": json.dumps(metadata) if metadata else None,
                "expires_at": expires_at,
            }
        )
        db.session.commit()
        return True
        
    except Exception as e:
        print(f"Memory storage error: {e}")
        db.session.rollback()
        return False


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
    
    try:
        from providers.embeddings import generate_query_embedding
        
        # Generate query embedding
        query_embedding = generate_query_embedding(query)
        if not query_embedding:
            return []
        
        embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"
        
        # Semantic search using cosine similarity
        results = db.session.execute(
            text("""
                SELECT 
                    content,
                    memory_type,
                    metadata,
                    created_at,
                    1 - (embedding <=> CAST(:query_embedding AS vector)) as similarity
                FROM memory_summaries
                WHERE session_id = :session_id
                  AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY embedding <=> CAST(:query_embedding AS vector)
                LIMIT :limit
            """),
            {
                "session_id": session_id,
                "query_embedding": embedding_str,
                "limit": limit,
            }
        ).fetchall()
        
        memories = []
        for row in results:
            # Only include if similarity is above threshold
            if row.similarity and row.similarity > 0.3:
                memories.append({
                    "content": row.content,
                    "type": row.memory_type,
                    "metadata": json.loads(row.metadata) if row.metadata else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "similarity": round(row.similarity, 3),
                })
        
        return memories
        
    except Exception as e:
        print(f"Memory retrieval error: {e}")
        db.session.rollback()  # Prevent transaction cascade
        return []


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
    try:
        db.session.execute(
            text("DELETE FROM memory_summaries WHERE session_id = :session_id"),
            {"session_id": session_id}
        )
        db.session.commit()
        return True
    except Exception as e:
        print(f"Memory clear error: {e}")
        db.session.rollback()
        return False


def cleanup_expired_memories() -> int:
    """Remove expired memories. Call periodically."""
    try:
        result = db.session.execute(
            text("DELETE FROM memory_summaries WHERE expires_at < NOW()")
        )
        db.session.commit()
        return result.rowcount
    except Exception as e:
        print(f"Memory cleanup error: {e}")
        db.session.rollback()
        return 0


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
