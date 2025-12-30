"""
Tests for Memory System (memory.py, session_memory.py)
Run with: pytest test_memory_system.py -v
"""
import pytest
from unittest.mock import patch, MagicMock


class TestMemoryImports:
    """Test that memory modules import correctly."""
    
    def test_memory_module_imports(self):
        """Memory module should import without errors."""
        from providers.memory import (
            store_memory,
            retrieve_relevant_memories,
            get_memory_context_for_prompt,
            clear_user_memory,
            MEMORY_RETENTION,
        )
        assert callable(store_memory)
        assert callable(retrieve_relevant_memories)
        assert callable(get_memory_context_for_prompt)
        assert callable(clear_user_memory)
        assert isinstance(MEMORY_RETENTION, dict)
    
    def test_session_memory_imports(self):
        """Session memory module should import without errors."""
        from providers.session_memory import (
            get_session_interventions,
            record_intervention_shown,
            get_intervention_variety,
            update_intervention_outcome,
            get_recent_messages,
        )
        assert callable(get_session_interventions)
        assert callable(record_intervention_shown)
        assert callable(get_intervention_variety)
        assert callable(update_intervention_outcome)
        assert callable(get_recent_messages)

    def test_embeddings_imports(self):
        """Embeddings module should import without errors."""
        from providers.embeddings import (
            generate_embedding,
            generate_query_embedding,
            compute_text_hash,
        )
        assert callable(generate_embedding)
        assert callable(generate_query_embedding)
        assert callable(compute_text_hash)


class TestMemoryRetention:
    """Test memory retention configuration."""
    
    def test_retention_policies_defined(self):
        """Retention policies should be defined for all memory types."""
        from providers.memory import MEMORY_RETENTION
        
        assert 'episodic' in MEMORY_RETENTION
        assert 'emotional' in MEMORY_RETENTION
        assert 'preference' in MEMORY_RETENTION
        
    def test_retention_values_reasonable(self):
        """Retention values should be reasonable (in days)."""
        from providers.memory import MEMORY_RETENTION
        
        assert MEMORY_RETENTION['episodic'] >= 7  # At least a week
        assert MEMORY_RETENTION['emotional'] >= 30  # At least a month
        assert MEMORY_RETENTION['preference'] >= 90  # At least 3 months


class TestTextHash:
    """Test text hashing for deduplication."""
    
    def test_hash_consistency(self):
        """Same text should produce same hash."""
        from providers.embeddings import compute_text_hash
        
        text = "I'm feeling anxious today"
        hash1 = compute_text_hash(text)
        hash2 = compute_text_hash(text)
        assert hash1 == hash2
    
    def test_hash_uniqueness(self):
        """Different text should produce different hashes."""
        from providers.embeddings import compute_text_hash
        
        hash1 = compute_text_hash("I'm feeling anxious")
        hash2 = compute_text_hash("I'm feeling happy")
        assert hash1 != hash2


class TestSessionMemoryVariety:
    """Test intervention variety logic."""
    
    def test_variety_returns_dict(self):
        """get_intervention_variety should return a dict."""
        from providers.session_memory import get_intervention_variety
        
        # This will work even without DB as it has fallback
        result = get_intervention_variety("test_session", "anxiety")
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
