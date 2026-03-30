"""
Tests for brain_rag.py — hybrid search, context formatting, and build_full_context.
Mocks Ollama embedding calls to avoid external dependency.
"""

import json
import sqlite3
import sys
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

def _fake_embed(text: str) -> List[float]:
    """Deterministic fake embedding based on text hash."""
    h = hash(text) % 10000
    return [float((h + i) % 100) / 100 for i in range(1024)]


@pytest.fixture
def brain_db(tmp_path):
    """Create a minimal brain RAG database with test chunks."""
    import providers.brain_rag as rag

    db_path = tmp_path / ".brain" / "rag_index.db"
    db_path.parent.mkdir(parents=True)

    conn = rag._init_db(db_path)

    # Insert test chunks with embeddings
    chunks = [
        ("memory/context.md", "Project Overview", "Nucleus is an AI productivity tool for solo founders.", 9, 0, _fake_embed("nucleus ai productivity")),
        ("artifacts/architecture/driver.md", "Design", "The Third Brother driver uses session resume architecture.", 8, 3, _fake_embed("driver session resume")),
        ("vault/patterns.md", "Testing Patterns", "Always mock external APIs in unit tests. Use pytest fixtures.", 10, 1, _fake_embed("testing patterns mock")),
        ("memory/decisions.md", "Key Decisions", "We chose Gemini over GPT-4 for cost and speed reasons.", 10, 0, _fake_embed("gemini gpt cost")),
        ("artifacts/strategy/growth.md", "Growth Strategy", "Focus on developer experience and CLI-first approach.", 9, 2, _fake_embed("growth strategy developer")),
    ]

    import time as _time
    for fp, section, content, wc, tier, emb in chunks:
        import numpy as np
        emb_bytes = np.array(emb, dtype=np.float32).tobytes()
        conn.execute(
            "INSERT INTO chunks (file_path, section, content, word_count, priority_tier, embedding, content_hash, indexed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (fp, section, content, wc, tier, emb_bytes, f"hash_{fp}", _time.time()),
        )

    conn.commit()

    # Build FTS index
    try:
        rag._rebuild_fts(conn)
    except Exception:
        pass  # FTS may already exist

    conn.close()

    return tmp_path / ".brain"


# ═══════════════════════════════════════════════════════════════
# search_brain
# ═══════════════════════════════════════════════════════════════

class TestSearchBrain:
    def test_returns_results_sorted_by_score(self, brain_db):
        import providers.brain_rag as rag

        with patch.object(rag, '_embed', side_effect=lambda t: _fake_embed(t)):
            results = rag.search_brain("nucleus ai productivity", brain_path=brain_db)

        assert len(results) > 0
        # Results should be sorted by score (descending)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True), f"Not sorted: {scores}"

    def test_results_contain_required_fields(self, brain_db):
        import providers.brain_rag as rag

        with patch.object(rag, '_embed', side_effect=lambda t: _fake_embed(t)):
            results = rag.search_brain("testing patterns", brain_path=brain_db)

        assert len(results) > 0
        for r in results:
            assert "id" in r
            assert "source" in r
            assert "section" in r
            assert "content" in r
            assert "score" in r
            assert "word_count" in r
            assert "priority_tier" in r

    def test_empty_query_returns_empty(self, brain_db):
        import providers.brain_rag as rag

        with patch.object(rag, '_embed', return_value=None):
            results = rag.search_brain("", brain_path=brain_db)

        assert results == []

    def test_no_index_returns_empty(self, tmp_path):
        import providers.brain_rag as rag

        results = rag.search_brain("anything", brain_path=tmp_path / "nonexistent")
        assert results == []

    def test_embed_failure_returns_empty(self, brain_db):
        import providers.brain_rag as rag

        with patch.object(rag, '_embed', return_value=None):
            results = rag.search_brain("test query", brain_path=brain_db)

        assert results == []

    def test_topk_limits_results(self, brain_db):
        import providers.brain_rag as rag

        with patch.object(rag, '_embed', side_effect=lambda t: _fake_embed(t)):
            results = rag.search_brain("nucleus", brain_path=brain_db, topk=2)

        assert len(results) <= 2


# ═══════════════════════════════════════════════════════════════
# format_rag_context
# ═══════════════════════════════════════════════════════════════

class TestFormatRagContext:
    def test_empty_results_returns_empty(self):
        from providers.brain_rag import format_rag_context
        assert format_rag_context([]) == ""

    def test_formats_with_source_attribution(self):
        from providers.brain_rag import format_rag_context

        results = [
            {"source": "memory/context.md", "section": "Overview",
             "content": "Nucleus is an AI tool.", "word_count": 5},
        ]
        output = format_rag_context(results, max_words=100)
        assert "BRAIN KNOWLEDGE" in output
        assert "context > Overview" in output
        assert "Nucleus is an AI tool." in output

    def test_respects_word_budget(self):
        from providers.brain_rag import format_rag_context

        results = [
            {"source": "a.md", "section": "S1",
             "content": " ".join(["word"] * 50), "word_count": 50},
            {"source": "b.md", "section": "S2",
             "content": " ".join(["extra"] * 50), "word_count": 50},
            {"source": "c.md", "section": "S3",
             "content": " ".join(["overflow"] * 50), "word_count": 50},
        ]
        output = format_rag_context(results, max_words=80)
        # Should include first result fully, maybe truncate second, skip third
        total_words = len(output.split())
        assert total_words <= 100  # some overhead for headers

    def test_truncates_with_ellipsis(self):
        from providers.brain_rag import format_rag_context

        results = [
            {"source": "big.md", "section": "Huge",
             "content": " ".join(["word"] * 200), "word_count": 200},
        ]
        output = format_rag_context(results, max_words=50)
        assert "..." in output

    def test_multiple_sources(self):
        from providers.brain_rag import format_rag_context

        results = [
            {"source": "a.md", "section": "S1", "content": "First chunk.", "word_count": 2},
            {"source": "b.md", "section": "S2", "content": "Second chunk.", "word_count": 2},
        ]
        output = format_rag_context(results, max_words=100)
        assert "a > S1" in output
        assert "b > S2" in output


# ═══════════════════════════════════════════════════════════════
# build_full_context
# ═══════════════════════════════════════════════════════════════

class TestBuildFullContext:
    def test_returns_tuple(self, brain_db):
        from providers.brain_rag import build_full_context

        with patch("providers.brain_rag._embed", side_effect=lambda t: _fake_embed(t)):
            with patch("providers.brain_rag.get_working_state", return_value="Branch: main"):
                with patch("providers.brain_rag.get_live_session_context", return_value=""):
                    result = build_full_context("test query", brain_path=brain_db)

        assert isinstance(result, tuple)
        assert len(result) == 2
        context_str, search_results = result
        assert isinstance(context_str, str)
        assert isinstance(search_results, list)

    def test_includes_working_state(self, brain_db):
        from providers.brain_rag import build_full_context

        with patch("providers.brain_rag._embed", side_effect=lambda t: _fake_embed(t)):
            with patch("providers.brain_rag.get_working_state", return_value="[WORKING STATE]\nBranch: main"):
                with patch("providers.brain_rag.get_live_session_context", return_value=""):
                    context, _ = build_full_context("test", brain_path=brain_db)

        assert "WORKING STATE" in context

    def test_includes_cold_search_results(self, brain_db):
        from providers.brain_rag import build_full_context

        with patch("providers.brain_rag._embed", side_effect=lambda t: _fake_embed(t)):
            with patch("providers.brain_rag.get_working_state", return_value=""):
                with patch("providers.brain_rag.get_live_session_context", return_value=""):
                    context, results = build_full_context("nucleus ai", brain_path=brain_db)

        assert len(results) > 0
        assert "BRAIN KNOWLEDGE" in context

    def test_empty_query_still_returns_hot_context(self, brain_db):
        from providers.brain_rag import build_full_context

        with patch("providers.brain_rag._embed", return_value=None):
            with patch("providers.brain_rag.get_working_state", return_value="Branch: main"):
                with patch("providers.brain_rag.get_live_session_context", return_value=""):
                    context, results = build_full_context("", brain_path=brain_db)

        # Should still have working state even with no search results
        assert "Branch: main" in context

    def test_respects_word_budget(self, brain_db):
        """Total context should not exceed BUDGET_TOTAL (2000 words)."""
        from providers.brain_rag import build_full_context, BUDGET_TOTAL

        with patch("providers.brain_rag._embed", side_effect=lambda t: _fake_embed(t)):
            with patch("providers.brain_rag.get_working_state", return_value="word " * 400):
                with patch("providers.brain_rag.get_live_session_context", return_value="live " * 400):
                    context, _ = build_full_context("test", brain_path=brain_db, max_words=BUDGET_TOTAL)

        word_count = len(context.split())
        # Allow small margin for section join overhead
        assert word_count <= BUDGET_TOTAL + 20, f"Context {word_count} words exceeds budget {BUDGET_TOTAL}"

    def test_empty_brain_path_graceful_fallback(self, tmp_path):
        """Non-existent brain_path should still return hot context, not crash."""
        from providers.brain_rag import build_full_context

        fake_brain = tmp_path / "nonexistent_brain"
        with patch("providers.brain_rag.get_working_state", return_value="[WORKING STATE]\nBranch: main"):
            with patch("providers.brain_rag.get_live_session_context", return_value=""):
                context, results = build_full_context("anything", brain_path=fake_brain)

        assert isinstance(context, str)
        assert isinstance(results, list)
        assert results == []
        assert "WORKING STATE" in context


# ═══════════════════════════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════════════════════════

class TestGetWorkingState:
    def test_includes_git_branch(self):
        from providers.brain_rag import get_working_state
        import subprocess

        mock_results = {
            0: MagicMock(stdout="feature-x\n", returncode=0),
        }
        call_count = [0]

        def fake_run(*args, **kwargs):
            result = mock_results.get(call_count[0],
                                      MagicMock(stdout="", returncode=0))
            call_count[0] += 1
            return result

        with patch("providers.brain_rag.subprocess.run", side_effect=fake_run):
            with patch("providers.brain_rag.BRAIN_PATH", Path("/tmp/no_brain")):
                state = get_working_state()

        assert "[WORKING STATE]" in state
        assert "feature-x" in state

    def test_git_failure_still_returns_time(self):
        """If git is unavailable, state still includes time/energy context."""
        from providers.brain_rag import get_working_state

        with patch("providers.brain_rag.subprocess.run", side_effect=Exception("no git")):
            with patch("providers.brain_rag.BRAIN_PATH", Path("/tmp/no_brain")):
                state = get_working_state()

        assert "[WORKING STATE]" in state
        assert "Time:" in state

    def test_includes_time_energy(self):
        from providers.brain_rag import get_working_state

        with patch("providers.brain_rag.subprocess.run", side_effect=Exception("no git")):
            with patch("providers.brain_rag.BRAIN_PATH", Path("/tmp/no_brain")):
                state = get_working_state()

        # Should contain day name and energy descriptor
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        assert any(d in state for d in days)


class TestGetLiveSessionContext:
    def test_no_session_returns_empty(self):
        from providers.brain_rag import get_live_session_context

        with patch("providers.brain_rag._find_active_session", return_value=None):
            assert get_live_session_context() == ""


class TestGetCommitmentsContext:
    def test_missing_ledger_returns_empty(self, tmp_path):
        from providers.brain_rag import get_commitments_context

        with patch("providers.brain_rag.PROJECT_ROOT", tmp_path), \
             patch("providers.brain_rag.BRAIN_PATH", tmp_path / ".brain"):
            assert get_commitments_context() == ""

    def test_active_commitments_shown(self, tmp_path):
        from providers.brain_rag import get_commitments_context

        commitments_dir = tmp_path / "commitments"
        commitments_dir.mkdir()
        ledger = commitments_dir / "ledger.json"
        ledger.write_text(json.dumps({
            "commitments": [
                {"title": "Ship v1", "status": "active"},
                {"title": "Old thing", "status": "done"},
            ]
        }))
        brain_dir = tmp_path / ".brain" / "ledger"
        brain_dir.mkdir(parents=True)

        with patch("providers.brain_rag.PROJECT_ROOT", tmp_path), \
             patch("providers.brain_rag.BRAIN_PATH", tmp_path / ".brain"):
            ctx = get_commitments_context()
            assert "Ship v1" in ctx
            assert "Old thing" not in ctx


class TestChunkMarkdown:
    def test_chunks_by_headers(self):
        from providers.brain_rag import chunk_markdown

        # Content must be >= 30 chars per section (CHUNK_MIN_CHARS)
        content = "# Title\nThis is the first section with enough content to pass the minimum character threshold for chunking.\n## Sub\nThis is the sub section also with enough content to pass the minimum character threshold."
        chunks = chunk_markdown(content)
        assert len(chunks) >= 1
        for section, text in chunks:
            assert isinstance(section, str)
            assert isinstance(text, str)
            assert len(text) > 0

    def test_empty_content(self):
        from providers.brain_rag import chunk_markdown
        chunks = chunk_markdown("")
        assert chunks == []

    def test_respects_max_words(self):
        from providers.brain_rag import chunk_markdown

        long_content = "# Big\n" + " ".join(["word"] * 500)
        chunks = chunk_markdown(long_content, max_words=100)
        for _, text in chunks:
            assert len(text.split()) <= 120  # some slack for split logic


class TestRrfFuse:
    def test_fuses_two_rankings(self):
        from providers.brain_rag import _rrf_fuse

        dense = [(1, 0.9), (2, 0.8), (3, 0.7)]
        bm25 = [(2, 5.0), (3, 4.0), (1, 3.0)]

        fused = _rrf_fuse(dense, bm25)
        assert len(fused) == 3
        # All IDs should be present
        fused_ids = {cid for cid, _ in fused}
        assert fused_ids == {1, 2, 3}
        # Scores should be descending
        scores = [s for _, s in fused]
        assert scores == sorted(scores, reverse=True)

    def test_single_ranking(self):
        from providers.brain_rag import _rrf_fuse

        single = [(1, 0.9), (2, 0.5)]
        fused = _rrf_fuse(single)
        assert len(fused) == 2


class TestContentHash:
    def test_deterministic(self):
        from providers.brain_rag import _content_hash
        h1 = _content_hash("hello world")
        h2 = _content_hash("hello world")
        assert h1 == h2

    def test_different_content_different_hash(self):
        from providers.brain_rag import _content_hash
        h1 = _content_hash("hello")
        h2 = _content_hash("world")
        assert h1 != h2


class TestPriorityTier:
    def test_memory_is_tier_0(self):
        from providers.brain_rag import _get_priority_tier
        assert _get_priority_tier("memory/context.md") == 0

    def test_vault_is_tier_1(self):
        from providers.brain_rag import _get_priority_tier
        assert _get_priority_tier("vault/patterns.md") == 1

    def test_unknown_is_highest_tier(self):
        from providers.brain_rag import _get_priority_tier
        tier = _get_priority_tier("random/unknown.md")
        assert tier >= 5  # should be a low-priority tier


# ═══════════════════════════════════════════════════════════════
# INTEGRATION: search quality on realistic .brain content
# ═══════════════════════════════════════════════════════════════

# Real content from .brain, seeded into a test DB so BM25/FTS5
# can assert keyword-level relevance.  Dense search is mocked
# (no Ollama in CI), but FTS5 gives us genuine quality signal.

_BRAIN_CHUNKS = [
    # commandments.md content (3 chunks)
    ("commandments.md", "Commandments",
     "Father's encoded intent. Read by all agents on every startup. "
     "These are hard rules. They don't flex with context."),
    ("commandments.md", "1. Everything compounds toward the coordinate",
     "Every line of code, every feature, every decision must compound toward the family organism. "
     "The coordinate: a conscious, self-aware, pragmatic family that evolves and eventually runs autonomously."),
    ("commandments.md", "3. Sovereignty is non-negotiable",
     "No vendor lock-in. No dependency on any single provider staying benevolent. "
     "Own the data. Own the runtime. Own the identity."),
    ("commandments.md", "4. Slower is better when it means deeper",
     "Speed is not the goal. Consciousness is. "
     "A heartbeat every 30 minutes that thinks deeply beats a 100ms poll that reacts blindly."),
    ("commandments.md", "6. Surgical, not sweeping",
     "Changes are precise. No drive-by refactors. No over-engineering. "
     "Three similar lines of code is better than a premature abstraction."),
    ("commandments.md", "7. The archive is sacred",
     "Every conversation, every decision, every tool use — logged. "
     "The archive feeds the trained model. The trained model becomes the family's own consciousness."),
    # heartbeat-related content
    ("meta/heartbeat_state.json", "Heartbeat State",
     "Heartbeat daemon runs every 30 minutes. Checks agent health, "
     "brain coherence, and session continuity. Emits pulse events."),
    ("artifacts/architecture/driver.md", "Heartbeat Loop",
     "The heartbeat loop is the family's rhythm. It coordinates timing between agents, "
     "triggers depth cycles, and ensures no agent drifts without a pulse check."),
    # Non-heartbeat, non-commandment content
    ("memory/context.md", "Project Overview",
     "Nucleus is an AI productivity tool for solo founders. "
     "It uses multi-provider LLM architecture with Gemini and Anthropic."),
    ("vault/patterns.md", "Testing Patterns",
     "Always mock external APIs in unit tests. Use pytest fixtures for database setup. "
     "Integration tests should hit real databases."),
    ("artifacts/strategy/growth.md", "Growth Strategy",
     "Focus on developer experience and CLI-first approach. "
     "Target solo founders who value sovereignty and local-first tools."),
]


@pytest.fixture
def quality_db(tmp_path):
    """DB seeded with realistic .brain content for search quality tests."""
    import providers.brain_rag as rag

    db_path = tmp_path / ".brain" / "rag_index.db"
    db_path.parent.mkdir(parents=True)

    conn = rag._init_db(db_path)

    import numpy as np
    for fp, section, content in _BRAIN_CHUNKS:
        emb = _fake_embed(f"{fp} {section} {content}")
        emb_bytes = np.array(emb, dtype=np.float32).tobytes()
        conn.execute(
            "INSERT INTO chunks (file_path, section, content, word_count, "
            "priority_tier, embedding, content_hash, indexed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (fp, section, content, len(content.split()), 0, emb_bytes,
             f"hash_{fp}_{section}", time.time()),
        )
    conn.commit()

    try:
        rag._rebuild_fts(conn)
    except Exception:
        pass

    conn.close()
    return tmp_path / ".brain"


class TestSearchQuality:
    """Integration tests: assert that search returns semantically relevant chunks in top-3."""

    def test_commandments_query_returns_commandments_chunks(self, quality_db):
        import providers.brain_rag as rag

        with patch.object(rag, '_embed', side_effect=lambda t: _fake_embed(t)):
            results = rag.search_brain("what are the commandments", brain_path=quality_db, topk=5)

        assert len(results) >= 3, f"Expected ≥3 results, got {len(results)}"
        top3_sources = [r["source"] for r in results[:3]]
        commandment_hits = [s for s in top3_sources if "commandments" in s]
        assert len(commandment_hits) >= 2, (
            f"Expected ≥2 commandments.md in top-3, got {commandment_hits} from {top3_sources}"
        )

    def test_heartbeat_query_returns_heartbeat_content(self, quality_db):
        import providers.brain_rag as rag

        with patch.object(rag, '_embed', side_effect=lambda t: _fake_embed(t)):
            results = rag.search_brain("heartbeat", brain_path=quality_db, topk=5)

        assert len(results) >= 2, f"Expected ≥2 results, got {len(results)}"
        top3_content = " ".join(r["content"] for r in results[:3])
        assert "heartbeat" in top3_content.lower(), (
            f"'heartbeat' not in top-3 content: {[r['section'] for r in results[:3]]}"
        )

    def test_sovereignty_query_returns_commandment_3(self, quality_db):
        import providers.brain_rag as rag

        with patch.object(rag, '_embed', side_effect=lambda t: _fake_embed(t)):
            results = rag.search_brain("sovereignty vendor lock-in", brain_path=quality_db, topk=3)

        assert len(results) >= 1
        top3_content = " ".join(r["content"] for r in results[:3])
        assert "sovereignty" in top3_content.lower() or "vendor" in top3_content.lower(), (
            f"Sovereignty content not in top-3: {[r['section'] for r in results[:3]]}"
        )

    def test_testing_patterns_query_hits_vault(self, quality_db):
        import providers.brain_rag as rag

        with patch.object(rag, '_embed', side_effect=lambda t: _fake_embed(t)):
            results = rag.search_brain("pytest mock testing patterns", brain_path=quality_db, topk=3)

        assert len(results) >= 1
        top3_sources = [r["source"] for r in results[:3]]
        assert any("patterns" in s for s in top3_sources), (
            f"patterns.md not in top-3: {top3_sources}"
        )

    def test_archive_sacred_query_returns_commandment_7(self, quality_db):
        import providers.brain_rag as rag

        with patch.object(rag, '_embed', side_effect=lambda t: _fake_embed(t)):
            results = rag.search_brain("archive sacred logging", brain_path=quality_db, topk=3)

        assert len(results) >= 1
        top3_content = " ".join(r["content"] for r in results[:3])
        assert "archive" in top3_content.lower(), (
            f"'archive' not in top-3 content: {[r['section'] for r in results[:3]]}"
        )

    def test_irrelevant_query_still_returns_results(self, quality_db):
        """BM25 should find LLM/provider content even when dense search is fake."""
        import providers.brain_rag as rag

        with patch.object(rag, '_embed', side_effect=lambda t: _fake_embed(t)):
            results = rag.search_brain("gemini anthropic LLM provider", brain_path=quality_db, topk=3)

        # With fake embeddings we can't assert semantic ranking,
        # but BM25 should still return results containing the query terms
        assert len(results) >= 1
        all_content = " ".join(r["content"] for r in results)
        assert any(term in all_content.lower() for term in ("gemini", "anthropic", "provider"))

    def test_top3_relevance_scores_are_nonzero(self, quality_db):
        import providers.brain_rag as rag

        with patch.object(rag, '_embed', side_effect=lambda t: _fake_embed(t)):
            results = rag.search_brain("commandments rules agents", brain_path=quality_db, topk=3)

        for r in results[:3]:
            assert r["score"] > 0, f"Zero score for {r['section']}"


# ═══════════════════════════════════════════════════════════════
# _dense_search / _bm25_search / _apply_metadata_boost
# ═══════════════════════════════════════════════════════════════

class TestDenseSearch:
    def test_returns_ranked_by_cosine(self, brain_db):
        import providers.brain_rag as rag
        import numpy as np

        db_path = brain_db / "rag_index.db"
        conn = sqlite3.connect(str(db_path))

        query_emb = _fake_embed("nucleus ai productivity")
        results = rag._dense_search(query_emb, conn, topk=5)
        conn.close()

        assert len(results) > 0
        # Scores should be descending
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)

    def test_zero_norm_query_returns_empty(self, brain_db):
        import providers.brain_rag as rag

        db_path = brain_db / "rag_index.db"
        conn = sqlite3.connect(str(db_path))

        results = rag._dense_search([0.0] * 1024, conn)
        conn.close()
        assert results == []

    def test_empty_db_returns_empty(self, tmp_path):
        import providers.brain_rag as rag

        db_path = tmp_path / "empty.db"
        conn = rag._init_db(db_path)
        results = rag._dense_search([1.0] * 1024, conn)
        conn.close()
        assert results == []


class TestBm25Search:
    def test_keyword_match(self, quality_db):
        import providers.brain_rag as rag

        db_path = quality_db / "rag_index.db"
        conn = sqlite3.connect(str(db_path))
        rag._migrate_existing_db(conn)

        results = rag._bm25_search("heartbeat daemon", conn, topk=5)
        conn.close()

        assert len(results) >= 1
        # All results should have positive scores
        for _, score in results:
            assert score > 0

    def test_short_terms_ignored(self, quality_db):
        import providers.brain_rag as rag

        db_path = quality_db / "rag_index.db"
        conn = sqlite3.connect(str(db_path))

        # Terms under 3 chars get filtered out
        results = rag._bm25_search("an it", conn)
        conn.close()
        assert results == []

    def test_empty_query_returns_empty(self, quality_db):
        import providers.brain_rag as rag

        db_path = quality_db / "rag_index.db"
        conn = sqlite3.connect(str(db_path))
        results = rag._bm25_search("", conn)
        conn.close()
        assert results == []


class TestApplyMetadataBoost:
    def test_priority_boost_reranks(self, brain_db):
        import providers.brain_rag as rag

        db_path = brain_db / "rag_index.db"
        conn = sqlite3.connect(str(db_path))

        # Get chunk IDs from DB
        rows = conn.execute("SELECT id, priority_tier FROM chunks").fetchall()
        # Build fused list with equal base scores
        fused = [(row[0], 1.0) for row in rows]

        boosted = rag._apply_metadata_boost(fused, conn)
        conn.close()

        assert len(boosted) == len(fused)
        # Higher priority (lower tier number) should get higher boost
        scores = [s for _, s in boosted]
        assert scores == sorted(scores, reverse=True)

    def test_empty_fused_returns_empty(self, brain_db):
        import providers.brain_rag as rag

        db_path = brain_db / "rag_index.db"
        conn = sqlite3.connect(str(db_path))
        assert rag._apply_metadata_boost([], conn) == []
        conn.close()


# ═══════════════════════════════════════════════════════════════
# Search caching
# ═══════════════════════════════════════════════════════════════

class TestSearchCache:
    def setup_method(self):
        import providers.brain_rag as rag
        rag._search_cache.clear()

    def test_cache_put_and_get(self):
        import providers.brain_rag as rag

        results = [{"id": 1, "content": "test"}]
        rag._cache_put("key1", results)
        assert rag._cache_get("key1") == results

    def test_cache_miss_returns_none(self):
        import providers.brain_rag as rag
        assert rag._cache_get("nonexistent") is None

    def test_cache_ttl_expiry(self):
        import providers.brain_rag as rag

        results = [{"id": 1}]
        rag._search_cache["old_key"] = (time.time() - 600, results)
        assert rag._cache_get("old_key") is None

    def test_cache_eviction_at_capacity(self):
        import providers.brain_rag as rag

        # Fill cache to capacity
        for i in range(rag.CACHE_MAX_ENTRIES):
            rag._cache_put(f"k{i}", [{"id": i}])
        assert len(rag._search_cache) == rag.CACHE_MAX_ENTRIES

        # One more should evict the oldest
        rag._cache_put("overflow", [{"id": 999}])
        assert len(rag._search_cache) == rag.CACHE_MAX_ENTRIES
        assert rag._cache_get("overflow") == [{"id": 999}]

    def test_search_brain_uses_cache(self, brain_db):
        import providers.brain_rag as rag

        with patch.object(rag, '_embed', side_effect=lambda t: _fake_embed(t)):
            r1 = rag.search_brain("nucleus", brain_path=brain_db)
            # Second call should hit cache (no embed call)
            with patch.object(rag, '_embed', side_effect=AssertionError("should not embed")):
                r2 = rag.search_brain("nucleus", brain_path=brain_db)

        assert r1 == r2

    def test_cache_key_includes_topk(self):
        from providers.brain_rag import _cache_key
        k1 = _cache_key("q", Path("/a"), 5)
        k2 = _cache_key("q", Path("/a"), 10)
        assert k1 != k2

    def teardown_method(self):
        import providers.brain_rag as rag
        rag._search_cache.clear()


# ═══════════════════════════════════════════════════════════════
# _parse_session_events / get_live_session_context
# ═══════════════════════════════════════════════════════════════

class TestParseSessionEvents:
    def test_parses_user_messages(self, tmp_path):
        from providers.brain_rag import _parse_session_events

        session = tmp_path / "session.jsonl"
        session.write_text(json.dumps({
            "message": {"role": "user", "content": "Fix the broken test in main.py"}
        }) + "\n")

        events = _parse_session_events(session)
        assert len(events) == 1
        assert events[0]["type"] == "user_msg"
        assert "broken test" in events[0]["text"]

    def test_parses_file_operations(self, tmp_path):
        from providers.brain_rag import _parse_session_events

        session = tmp_path / "session.jsonl"
        session.write_text(json.dumps({
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "name": "Edit",
                     "input": {"file_path": "/project/backend/app/main.py"}}
                ]
            }
        }) + "\n")

        events = _parse_session_events(session)
        assert any(e["type"] == "file_op" and e["tool"] == "edit" for e in events)

    def test_parses_bash_commands(self, tmp_path):
        from providers.brain_rag import _parse_session_events

        session = tmp_path / "session.jsonl"
        session.write_text(json.dumps({
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "name": "Bash",
                     "input": {"command": "python3 -m pytest tests/"}}
                ]
            }
        }) + "\n")

        events = _parse_session_events(session)
        assert any(e["type"] == "command" and "pytest" in e["cmd"] for e in events)

    def test_parses_grep_searches(self, tmp_path):
        from providers.brain_rag import _parse_session_events

        session = tmp_path / "session.jsonl"
        session.write_text(json.dumps({
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "name": "Grep",
                     "input": {"pattern": "def search_brain"}}
                ]
            }
        }) + "\n")

        events = _parse_session_events(session)
        assert any(e["type"] == "search" and "search_brain" in e["pattern"] for e in events)

    def test_skips_short_user_messages(self, tmp_path):
        from providers.brain_rag import _parse_session_events

        session = tmp_path / "session.jsonl"
        session.write_text(json.dumps({
            "message": {"role": "user", "content": "yes"}
        }) + "\n")

        events = _parse_session_events(session)
        assert events == []

    def test_skips_xml_and_json_user_messages(self, tmp_path):
        from providers.brain_rag import _parse_session_events

        session = tmp_path / "session.jsonl"
        lines = [
            json.dumps({"message": {"role": "user", "content": "<system-reminder>some tag</system-reminder>"}}),
            json.dumps({"message": {"role": "user", "content": '{"type": "json_payload"}'}}),
        ]
        session.write_text("\n".join(lines) + "\n")

        events = _parse_session_events(session)
        assert events == []

    def test_malformed_jsonl_skipped(self, tmp_path):
        from providers.brain_rag import _parse_session_events

        session = tmp_path / "session.jsonl"
        session.write_text("not valid json\n" + json.dumps({
            "message": {"role": "user", "content": "This is a valid message line"}
        }) + "\n")

        events = _parse_session_events(session)
        assert len(events) == 1


class TestGetLiveSessionContextRich:
    def test_formats_active_files_and_commands(self):
        import providers.brain_rag as rag

        events = [
            {"type": "file_op", "tool": "edit", "path": "backend/main.py"},
            {"type": "file_op", "tool": "read", "path": "tests/test_main.py"},
            {"type": "command", "cmd": "python3 -m pytest"},
            {"type": "user_msg", "text": "Fix the test failure"},
            {"type": "assistant_msg", "text": "I found the issue in the assert statement"},
        ]

        with patch.object(rag, '_find_active_session', return_value=Path("/fake")):
            with patch.object(rag, '_parse_session_events', return_value=events):
                ctx = rag.get_live_session_context()

        assert "LIVE SESSION" in ctx
        assert "backend/main.py" in ctx
        assert "pytest" in ctx
        assert "Father: Fix the test failure" in ctx
        assert "McKinsey:" in ctx

    def test_deduplicates_files(self):
        import providers.brain_rag as rag

        events = [
            {"type": "file_op", "tool": "read", "path": "a.py"},
            {"type": "file_op", "tool": "edit", "path": "a.py"},
            {"type": "file_op", "tool": "read", "path": "a.py"},
        ]

        with patch.object(rag, '_find_active_session', return_value=Path("/fake")):
            with patch.object(rag, '_parse_session_events', return_value=events):
                ctx = rag.get_live_session_context()

        # a.py should appear once (most recent op)
        assert ctx.count("a.py") == 1

    def test_respects_word_budget(self):
        import providers.brain_rag as rag

        events = [{"type": "user_msg", "text": "word " * 200}]

        with patch.object(rag, '_find_active_session', return_value=Path("/fake")):
            with patch.object(rag, '_parse_session_events', return_value=events):
                ctx = rag.get_live_session_context(max_words=50)

        assert len(ctx.split()) <= 60  # small overhead for header


# ═══════════════════════════════════════════════════════════════
# _tail_file
# ═══════════════════════════════════════════════════════════════

class TestTailFile:
    def test_reads_full_small_file(self, tmp_path):
        from providers.brain_rag import _tail_file

        f = tmp_path / "small.txt"
        f.write_text("line 1\nline 2\nline 3\n")
        assert "line 1" in _tail_file(f)

    def test_tails_large_file(self, tmp_path):
        from providers.brain_rag import _tail_file

        f = tmp_path / "big.txt"
        f.write_text("HEADER\n" + "x" * 100000 + "\nTAIL LINE\n")
        result = _tail_file(f, max_bytes=200)
        assert "TAIL LINE" in result
        assert "HEADER" not in result

    def test_nonexistent_returns_empty(self, tmp_path):
        from providers.brain_rag import _tail_file
        assert _tail_file(tmp_path / "nope.txt") == ""


# ═══════════════════════════════════════════════════════════════
# build_full_context — additional coverage
# ═══════════════════════════════════════════════════════════════

class TestBuildFullContextExtended:
    def test_includes_commitments_when_room(self, brain_db, tmp_path):
        from providers.brain_rag import build_full_context

        # Set up commitments ledger
        commitments_dir = tmp_path / "commitments"
        commitments_dir.mkdir()
        (commitments_dir / "ledger.json").write_text(json.dumps({
            "commitments": [{"title": "Launch v2", "status": "active"}]
        }))

        with patch("providers.brain_rag._embed", side_effect=lambda t: _fake_embed(t)), \
             patch("providers.brain_rag.get_working_state", return_value="[WORKING STATE]\nBranch: main"), \
             patch("providers.brain_rag.get_live_session_context", return_value=""), \
             patch("providers.brain_rag.PROJECT_ROOT", tmp_path), \
             patch("providers.brain_rag.BRAIN_PATH", brain_db):
            context, _ = build_full_context("test", brain_path=brain_db)

        assert "Launch v2" in context

    def test_all_four_sections_present(self, brain_db, tmp_path):
        """When budget allows, context has working state + session + cold + commitments."""
        from providers.brain_rag import build_full_context

        commitments_dir = tmp_path / "commitments"
        commitments_dir.mkdir()
        (commitments_dir / "ledger.json").write_text(json.dumps({
            "commitments": [{"title": "Ship it", "status": "active"}]
        }))

        with patch("providers.brain_rag._embed", side_effect=lambda t: _fake_embed(t)), \
             patch("providers.brain_rag.get_working_state", return_value="[WORKING STATE]\nBranch: dev"), \
             patch("providers.brain_rag.get_live_session_context", return_value="[LIVE SESSION]\nFather: testing"), \
             patch("providers.brain_rag.PROJECT_ROOT", tmp_path), \
             patch("providers.brain_rag.BRAIN_PATH", brain_db):
            context, results = build_full_context("nucleus", brain_path=brain_db, max_words=2000)

        assert "WORKING STATE" in context
        assert "LIVE SESSION" in context
        assert "BRAIN KNOWLEDGE" in context
        assert "Ship it" in context
        assert len(results) > 0

    def test_tight_budget_skips_cold_search(self, brain_db):
        """When hot context eats the budget, cold search is skipped."""
        from providers.brain_rag import build_full_context

        # Working state alone eats 200 words, leave < 100 for cold
        big_state = "[WORKING STATE]\n" + "word " * 180

        with patch("providers.brain_rag._embed", side_effect=lambda t: _fake_embed(t)), \
             patch("providers.brain_rag.get_working_state", return_value=big_state), \
             patch("providers.brain_rag.get_live_session_context", return_value=""):
            context, results = build_full_context("test", brain_path=brain_db, max_words=250)

        # Cold search should still attempt if remaining > 100
        # With 250 budget and ~180 words for state, there's ~70 left → skipped
        assert "BRAIN KNOWLEDGE" not in context


# ═══════════════════════════════════════════════════════════════
# log_shadow_turn
# ═══════════════════════════════════════════════════════════════

class TestLogShadowTurn:
    def test_writes_jsonl_entry(self, tmp_path):
        import providers.brain_rag as rag

        shadow_log = tmp_path / "shadow.jsonl"
        with patch.object(rag, 'SHADOW_LOG', shadow_log):
            rag.log_shadow_turn(
                query="test query",
                response="test response",
                model="test-model",
                rag_results=[{"content": "chunk1", "score": 0.9}],
                rag_context="context",
                session_id="sess-123",
                latency_ms=42,
            )

        assert shadow_log.exists()
        entry = json.loads(shadow_log.read_text().strip())
        assert entry["query"] == "test query"
        assert entry["model"] == "test-model"
        assert entry["session_id"] == "sess-123"

    def test_creates_parent_directory(self, tmp_path):
        import providers.brain_rag as rag

        shadow_log = tmp_path / "deep" / "nested" / "shadow.jsonl"
        with patch.object(rag, 'SHADOW_LOG', shadow_log):
            rag.log_shadow_turn("q", "r", "m")

        assert shadow_log.exists()


class TestShowStats:
    def test_runs_without_error(self, brain_db, capsys):
        from providers.brain_rag import show_stats
        show_stats(brain_path=brain_db)
        captured = capsys.readouterr()
        assert "Chunks:" in captured.out
        assert "Files:" in captured.out
        assert "Words:" in captured.out

    def test_no_index_prints_message(self, tmp_path, capsys):
        from providers.brain_rag import show_stats
        show_stats(brain_path=tmp_path / "nonexistent")
        captured = capsys.readouterr()
        assert "No index" in captured.out
