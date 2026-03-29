"""
Tests for providers/memory.py — long-term memory via pgvector semantic search.
Mocks database and embedding calls since pgvector requires PostgreSQL.
"""

import os
import sys
import json
import types
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Stub out heavy dependencies that may not be installed in test env
for mod_name in ("psycopg", "psycopg.rows", "google.generativeai"):
    if mod_name not in sys.modules:
        stub = types.ModuleType(mod_name)
        if mod_name == "psycopg.rows":
            stub.dict_row = MagicMock()
        sys.modules[mod_name] = stub


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def _reset_memory_tables_flag():
    """Reset the cached _memory_tables_ready flag between tests."""
    import providers.memory as mem
    mem._memory_tables_ready = None
    yield
    mem._memory_tables_ready = None


@pytest.fixture
def mock_db():
    """Mock db.engine.raw_connection() to return a fake cursor."""
    cursor = MagicMock()
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("providers.memory.db") as mock:
        mock.engine.raw_connection.return_value = conn
        yield {"conn": conn, "cursor": cursor}


@pytest.fixture
def memory_enabled():
    """Patch module-level flags + table check so memory functions proceed."""
    with patch("providers.memory.MEMORY_ENABLED", True), \
         patch("providers.memory.PGVECTOR_ENABLED", True), \
         patch("providers.memory._check_memory_tables_exist", return_value=True):
        yield


FAKE_EMBEDDING = [0.1] * 768


# ═══════════════════════════════════════════════════════════════
# Embedding lookup  (store_memory → retrieve_relevant_memories)
# ═══════════════════════════════════════════════════════════════

class TestEmbeddingLookup:
    def test_store_memory_calls_embedding_and_inserts(self, mock_db, memory_enabled):
        from providers.memory import store_memory

        cursor = mock_db["cursor"]
        # First fetchone = dedup check returns None (no duplicate)
        cursor.fetchone.return_value = None

        with patch("providers.embeddings.generate_embedding", return_value=FAKE_EMBEDDING), \
             patch("providers.embeddings.compute_text_hash", return_value="abc123"):
            result = store_memory("sess-1", "User likes hiking", "preference")

        assert result is True
        # INSERT was called
        insert_call = cursor.execute.call_args_list[-1]
        assert "INSERT INTO memory_summaries" in insert_call[0][0]
        params = insert_call[0][1]
        assert params[0] == "sess-1"
        assert params[1] == "preference"
        assert params[2] == "User likes hiking"
        mock_db["conn"].commit.assert_called()

    def test_store_memory_deduplicates(self, mock_db, memory_enabled):
        from providers.memory import store_memory

        cursor = mock_db["cursor"]
        # Dedup check returns existing row
        cursor.fetchone.return_value = (42,)

        with patch("providers.embeddings.generate_embedding", return_value=FAKE_EMBEDDING), \
             patch("providers.embeddings.compute_text_hash", return_value="abc123"):
            result = store_memory("sess-1", "User likes hiking", "preference")

        assert result is True
        # Only the SELECT was called, no INSERT
        sql_calls = [c[0][0] for c in cursor.execute.call_args_list]
        assert not any("INSERT" in s for s in sql_calls)

    def test_store_memory_returns_false_when_embedding_fails(self, mock_db, memory_enabled):
        from providers.memory import store_memory

        with patch("providers.embeddings.generate_embedding", return_value=None):
            result = store_memory("sess-1", "some content")

        assert result is False

    def test_retrieve_returns_memories_above_threshold(self, mock_db, memory_enabled):
        from providers.memory import retrieve_relevant_memories

        cursor = mock_db["cursor"]
        # First call: pre-check returns a row (session has memories)
        # We need two raw_connection calls — one for pre-check, one for search
        pre_cursor = MagicMock()
        pre_cursor.fetchone.return_value = (1,)
        pre_conn = MagicMock()
        pre_conn.cursor.return_value.__enter__ = MagicMock(return_value=pre_cursor)
        pre_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        search_cursor = MagicMock()
        search_cursor.fetchall.return_value = [
            {
                "content": "User enjoys morning runs",
                "memory_type": "preference",
                "metadata": json.dumps({"source": "observer"}),
                "created_at": datetime(2026, 3, 1, 10, 0),
                "similarity": 0.85,
            },
            {
                "content": "User felt stressed last week",
                "memory_type": "emotional",
                "metadata": None,
                "created_at": datetime(2026, 3, 5, 14, 0),
                "similarity": 0.2,  # Below 0.3 threshold
            },
        ]
        search_conn = MagicMock()
        search_conn.cursor.return_value.__enter__ = MagicMock(return_value=search_cursor)
        search_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("providers.memory.db") as db_mock:
            db_mock.engine.raw_connection.side_effect = [pre_conn, search_conn]
            with patch("providers.embeddings.generate_query_embedding", return_value=FAKE_EMBEDDING):
                results = retrieve_relevant_memories("sess-1", "tell me about running")

        assert len(results) == 1
        assert results[0]["content"] == "User enjoys morning runs"
        assert results[0]["type"] == "preference"
        assert results[0]["similarity"] == 0.85

    def test_retrieve_skips_embedding_when_session_empty(self, memory_enabled):
        """Fast-path: if session has zero memories, skip the embedding call entirely."""
        from providers.memory import retrieve_relevant_memories

        pre_cursor = MagicMock()
        pre_cursor.fetchone.return_value = None  # No rows
        pre_conn = MagicMock()
        pre_conn.cursor.return_value.__enter__ = MagicMock(return_value=pre_cursor)
        pre_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("providers.memory.db") as db_mock:
            db_mock.engine.raw_connection.return_value = pre_conn
            with patch("providers.embeddings.generate_query_embedding") as mock_embed:
                results = retrieve_relevant_memories("sess-empty", "anything")

        assert results == []
        mock_embed.assert_not_called()


# ═══════════════════════════════════════════════════════════════
# Empty session
# ═══════════════════════════════════════════════════════════════

class TestEmptySession:
    def test_retrieve_returns_empty_when_disabled(self):
        from providers.memory import retrieve_relevant_memories

        with patch("providers.memory.MEMORY_ENABLED", False):
            result = retrieve_relevant_memories("sess-1", "hello")
        assert result == []

    def test_retrieve_returns_empty_when_pgvector_disabled(self):
        from providers.memory import retrieve_relevant_memories

        with patch("providers.memory.MEMORY_ENABLED", True), \
             patch("providers.memory.PGVECTOR_ENABLED", False):
            result = retrieve_relevant_memories("sess-1", "hello")
        assert result == []

    def test_store_returns_false_when_disabled(self):
        from providers.memory import store_memory

        with patch("providers.memory.MEMORY_ENABLED", False):
            result = store_memory("sess-1", "content")
        assert result is False

    def test_memory_context_empty_when_no_memories(self, memory_enabled):
        from providers.memory import get_memory_context_for_prompt

        with patch("providers.memory.retrieve_relevant_memories", return_value=[]):
            result = get_memory_context_for_prompt("sess-1", "hi")
        assert result == ""

    def test_memory_context_formats_when_memories_exist(self, memory_enabled):
        from providers.memory import get_memory_context_for_prompt

        memories = [
            {"content": "User mentioned sleep issues", "type": "episodic",
             "similarity": 0.8, "created_at": "2026-03-01T10:00:00"},
        ]
        with patch("providers.memory.retrieve_relevant_memories", return_value=memories):
            result = get_memory_context_for_prompt("sess-1", "I can't sleep")

        assert "You remember this about the person" in result
        assert "User mentioned sleep issues" in result


# ═══════════════════════════════════════════════════════════════
# Memory cleanup on purge
# ═══════════════════════════════════════════════════════════════

class TestMemoryCleanup:
    def test_clear_user_memory_deletes_session(self, mock_db):
        from providers.memory import clear_user_memory

        result = clear_user_memory("sess-1")

        assert result is True
        cursor = mock_db["cursor"]
        delete_call = cursor.execute.call_args_list[-1]
        assert "DELETE FROM memory_summaries" in delete_call[0][0]
        assert delete_call[0][1] == ("sess-1",)
        mock_db["conn"].commit.assert_called()

    def test_clear_user_memory_handles_db_error(self):
        from providers.memory import clear_user_memory

        conn = MagicMock()
        cursor = MagicMock()
        cursor.execute.side_effect = Exception("connection lost")
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("providers.memory.db") as db_mock:
            db_mock.engine.raw_connection.return_value = conn
            result = clear_user_memory("sess-1")

        assert result is False
        conn.rollback.assert_called()

    def test_cleanup_expired_returns_count(self, mock_db):
        from providers.memory import cleanup_expired_memories

        mock_db["cursor"].rowcount = 7

        count = cleanup_expired_memories()

        assert count == 7
        cursor = mock_db["cursor"]
        delete_call = cursor.execute.call_args_list[-1]
        assert "expires_at < CURRENT_TIMESTAMP" in delete_call[0][0]
        mock_db["conn"].commit.assert_called()

    def test_cleanup_expired_returns_zero_on_error(self):
        from providers.memory import cleanup_expired_memories

        conn = MagicMock()
        cursor = MagicMock()
        cursor.execute.side_effect = Exception("timeout")
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("providers.memory.db") as db_mock:
            db_mock.engine.raw_connection.return_value = conn
            count = cleanup_expired_memories()

        assert count == 0
        conn.rollback.assert_called()

    def test_retention_days_applied_on_store(self, mock_db, memory_enabled):
        """Verify that store_memory sets expires_at based on MEMORY_RETENTION config."""
        from providers.memory import store_memory, MEMORY_RETENTION

        cursor = mock_db["cursor"]
        cursor.fetchone.return_value = None

        with patch("providers.embeddings.generate_embedding", return_value=FAKE_EMBEDDING), \
             patch("providers.embeddings.compute_text_hash", return_value="hash1"):
            store_memory("sess-1", "prefers short msgs", "preference")

        insert_call = cursor.execute.call_args_list[-1]
        expires_at = insert_call[0][1][-1]  # Last param is expires_at
        expected_days = MEMORY_RETENTION["preference"]  # 365
        # expires_at should be ~365 days from now
        delta = expires_at - datetime.utcnow()
        assert delta.days >= expected_days - 1
        assert delta.days <= expected_days + 1
