"""
Embedding Generation for Luna Memory System
Uses Gemini's embedding API (free) for semantic search.
"""

import os
import hashlib
from typing import List, Optional
from datetime import datetime

# Embedding model configuration
EMBEDDING_MODEL = "gemini-embedding-001"  # Gemini's current embedding model
EMBEDDING_DIMENSION = 768  # Truncated via output_dimensionality to match pgvector column


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
    api_key = _get_api_key()
    if not api_key:
        return None
    
    try:
        # Truncate text if too long (embedding model has limits)
        max_chars = 8000  # Safe limit for embedding
        if len(text) > max_chars:
            text = text[:max_chars]

        # Try Nucleus DualEngineLLM first, fallback to native google.generativeai
        try:
            from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
            llm = DualEngineLLM(EMBEDDING_MODEL, api_key=api_key)
            result = llm.embed_content(text, task_type="retrieval_document")
            if result and 'embedding' in result:
                return result['embedding']
        except ImportError:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                result = client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=text,
                    config={'task_type': 'RETRIEVAL_DOCUMENT', 'output_dimensionality': EMBEDDING_DIMENSION}
                )
                if result and hasattr(result, 'embeddings') and result.embeddings:
                    return result.embeddings[0].values
            except ImportError:
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=api_key)
                result = genai_legacy.embed_content(
                    model=EMBEDDING_MODEL,
                    content=text,
                    task_type="retrieval_document",
                    output_dimensionality=EMBEDDING_DIMENSION
                )
                if result and 'embedding' in result:
                    return result['embedding']
        
        return None
        
    except Exception as e:
        print(f"Embedding generation error: {e}")
        return None


def generate_query_embedding(query: str) -> Optional[List[float]]:
    """
    Generate embedding for a search query.
    Uses task_type="retrieval_query" for better search results.
    """
    api_key = _get_api_key()
    if not api_key:
        return None
    
    try:
        # Try Nucleus DualEngineLLM first, fallback to native google.generativeai
        try:
            from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
            llm = DualEngineLLM(EMBEDDING_MODEL, api_key=api_key)
            result = llm.embed_content(query, task_type="retrieval_query")
            if result and 'embedding' in result:
                return result['embedding']
        except ImportError:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                result = client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=query,
                    config={'task_type': 'RETRIEVAL_QUERY', 'output_dimensionality': EMBEDDING_DIMENSION}
                )
                if result and hasattr(result, 'embeddings') and result.embeddings:
                    return result.embeddings[0].values
            except ImportError:
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=api_key)
                result = genai_legacy.embed_content(
                    model=EMBEDDING_MODEL,
                    content=query,
                    task_type="retrieval_query",
                    output_dimensionality=EMBEDDING_DIMENSION
                )
                if result and 'embedding' in result:
                    return result['embedding']
            
        return None
        
    except Exception as e:
        print(f"Query embedding error: {e}")
        return None


def compute_text_hash(text: str) -> str:
    """Compute hash for deduplication."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
