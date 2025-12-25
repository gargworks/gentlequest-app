"""
Embedding Generation for Luna Memory System
Uses Gemini's embedding API (free) for semantic search.
"""

import os
import hashlib
from typing import List, Optional
from datetime import datetime

# Try to import Gemini for embeddings
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# Embedding model configuration
EMBEDDING_MODEL = "models/text-embedding-004"  # Gemini's embedding model
EMBEDDING_DIMENSION = 768  # Dimension of text-embedding-004


def _get_api_key() -> Optional[str]:
    """Get Gemini API key from environment."""
    return os.getenv('GEMINI_API_KEY', '').split(',')[0].strip() or None


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding vector for text using Gemini's embedding API.
    
    Args:
        text: Text to embed (max ~2000 tokens recommended)
        
    Returns:
        List of floats (768 dimensions) or None if failed
    """
    if not GEMINI_AVAILABLE:
        return None
    
    api_key = _get_api_key()
    if not api_key:
        return None
    
    try:
        genai.configure(api_key=api_key)
        
        # Truncate text if too long (embedding model has limits)
        max_chars = 8000  # Safe limit for embedding
        if len(text) > max_chars:
            text = text[:max_chars]
        
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_document"
        )
        
        return result['embedding']
        
    except Exception as e:
        print(f"Embedding generation error: {e}")
        return None


def generate_query_embedding(query: str) -> Optional[List[float]]:
    """
    Generate embedding for a search query.
    Uses task_type="retrieval_query" for better search results.
    """
    if not GEMINI_AVAILABLE:
        return None
    
    api_key = _get_api_key()
    if not api_key:
        return None
    
    try:
        genai.configure(api_key=api_key)
        
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=query,
            task_type="retrieval_query"
        )
        
        return result['embedding']
        
    except Exception as e:
        print(f"Query embedding error: {e}")
        return None


def compute_text_hash(text: str) -> str:
    """Compute hash for deduplication."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
