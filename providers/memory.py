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
from sqlalchemy import text

# Import from app context
from models import db


# Memory configuration
MEMORY_ENABLED = os.getenv('ENABLE_MEMORY', 'true').lower() == 'true'
PGVECTOR_ENABLED = os.getenv('ENABLE_PGVECTOR', 'true').lower() == 'true'

# Retention policies (in days)
MEMORY_RETENTION = {
    'episodic': 30,     # Specific events
    'emotional': 90,    # Emotional patterns
    'preference': 365,  # User preferences
}

# How many memories to retrieve per query
MAX_MEMORIES_RETRIEVED = 5


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
            
            if dialect != 'postgresql':
                app.logger.info("Memory system: pgvector requires PostgreSQL, using fallback")
                return False
            
            # Try to enable pgvector extension
            try:
                db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                db.session.commit()
                app.logger.info("Memory system: pgvector extension enabled")
            except Exception as e:
                app.logger.warning(f"Memory system: pgvector not available: {e}")
                db.session.rollback()
                return False
            
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
    if not MEMORY_ENABLED:
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
    if not MEMORY_ENABLED or not PGVECTOR_ENABLED:
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
                    1 - (embedding <=> :query_embedding::vector) as similarity
                FROM memory_summaries
                WHERE session_id = :session_id
                  AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY embedding <=> :query_embedding::vector
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

def summarize_and_store_conversation(
    session_id: str,
    user_message: str,
    ai_response: str,
    risk_level: str = 'low'
) -> bool:
    """
    Extract key information from a conversation turn and store as memory.
    
    This is called after each conversation to build long-term memory.
    """
    if not MEMORY_ENABLED:
        return False
    
    # Don't store crisis conversations as memories (privacy/safety)
    if risk_level == 'crisis':
        return False
    
    try:
        # Extract emotional state if present
        emotions = _extract_emotions(user_message)
        if emotions:
            emotion_summary = f"User expressed feeling {emotions[0]}"
            if len(user_message) > 20:
                # Add context if message is substantial
                context = user_message[:100].replace('\n', ' ')
                emotion_summary += f" about: {context}"
            
            store_memory(
                session_id=session_id,
                content=emotion_summary,
                memory_type='emotional',
                metadata={"emotions": emotions, "date": datetime.utcnow().isoformat()}
            )
        
        # Extract topics mentioned
        topics = _extract_topics(user_message)
        if topics:
            for topic in topics[:2]:  # Max 2 topics per message
                topic_summary = f"User mentioned {topic}"
                store_memory(
                    session_id=session_id,
                    content=topic_summary,
                    memory_type='episodic',
                    metadata={"topic": topic, "date": datetime.utcnow().isoformat()}
                )
        
        return True
        
    except Exception as e:
        print(f"Conversation summarization error: {e}")
        return False


def _extract_emotions(text: str) -> List[str]:
    """Extract emotional keywords from text."""
    emotion_keywords = {
        'anxious': ['anxious', 'anxiety', 'worried', 'nervous', 'panic'],
        'sad': ['sad', 'depressed', 'down', 'unhappy', 'lonely', 'hopeless'],
        'stressed': ['stressed', 'overwhelmed', 'pressure', 'exhausted'],
        'angry': ['angry', 'frustrated', 'annoyed', 'irritated'],
        'happy': ['happy', 'good', 'great', 'excited', 'grateful'],
        'tired': ['tired', 'exhausted', 'drained', 'fatigued'],
        'scared': ['scared', 'afraid', 'fearful', 'terrified'],
    }
    
    text_lower = text.lower()
    found = []
    
    for emotion, keywords in emotion_keywords.items():
        if any(kw in text_lower for kw in keywords):
            found.append(emotion)
    
    return found


def _extract_topics(text: str) -> List[str]:
    """Extract key topics mentioned in text."""
    topic_patterns = {
        'school': ['school', 'class', 'teacher', 'homework', 'exam', 'test', 'grades'],
        'family': ['parents', 'mom', 'dad', 'family', 'brother', 'sister', 'home'],
        'friends': ['friend', 'friends', 'social', 'popularity'],
        'sleep': ['sleep', 'insomnia', 'tired', 'nightmares', 'rest'],
        'relationships': ['boyfriend', 'girlfriend', 'crush', 'dating', 'breakup'],
        'future': ['future', 'college', 'career', 'job', 'uncertainty'],
        'self-esteem': ['confidence', 'self-esteem', 'worthless', 'ugly', 'failure'],
    }
    
    text_lower = text.lower()
    found = []
    
    for topic, keywords in topic_patterns.items():
        if any(kw in text_lower for kw in keywords):
            found.append(topic)
    
    return found
