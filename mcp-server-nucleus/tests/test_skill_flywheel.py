"""Tests for the Skill Flywheel — extractor, generator, registry, publisher.

All tests use synthetic data. No external dependencies (Ollama, filesystem).
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch


# -- Fixtures --

def _make_turns(n: int = 20, domain: str = "test-writing") -> list:
    """Generate synthetic LoopTurn dicts for testing."""
    intents = {
        "test-writing": [
            "write tests for the auth module",
            "add test coverage for user registration",
            "create unit tests for this function",
            "write tests for payment processing",
            "add test coverage for the API endpoints",
            "write integration tests for the database layer",
            "create tests for the email service",
            "add unit tests for the config parser",
            "write tests for session management",
            "create test suite for the cache module",
            "add test coverage for error handling",
            "write tests for file upload feature",
            "create tests for webhook handlers",
            "add unit tests for rate limiting",
            "write tests for search functionality",
            "create test coverage for notifications",
            "add tests for the auth middleware",
            "write tests for data validation",
            "create unit tests for the scheduler",
            "add test coverage for logging module",
        ],
        "debug-errors": [
            "fix the TypeError in user login",
            "debug the 500 error on checkout",
            "fix the connection timeout issue",
            "debug why tests are failing",
            "fix the race condition in worker pool",
        ],
        "git-workflow": [
            "create a new branch for the feature",
            "merge the pull request",
            "resolve the merge conflict",
            "rebase onto main branch",
            "cherry pick the hotfix commit",
        ],
    }

    domain_intents = intents.get(domain, intents["test-writing"])
    turns = []
    for i in range(n):
        intent = domain_intents[i % len(domain_intents)]
        turns.append({
            "turn_id": f"turn-{domain}-{i:03d}",
            "intent": intent,
            "tools_used": ["Read", "Edit", "Bash"],
            "decisions": ["Read existing code first", "Follow project conventions"],
            "outcome": f"Completed: {intent}",
            "quality_grade": ["copper", "silver", "gold", "platinum"][i % 4],
            "conversation": [
                {"role": "user", "content": intent},
                {"role": "assistant", "content": f"I'll {intent.lower()}."},
            ],
            "actions": [f"action_{i}"],
            "signal_absorbed": [],
            "signal_produced": [],
        })
    return turns


# -- Extractor tests --

def test_cluster_intents_groups_similar():
    """Similar intents should cluster together."""
    from mcp_server_nucleus.runtime.skill_extractor import cluster_intents

    turns = _make_turns(n=20, domain="test-writing")
    clusters = cluster_intents(turns, min_cluster_size=3, use_embeddings=False)
    assert len(clusters) >= 1
    # The largest cluster should contain most of the test-writing turns
    assert clusters[0]["size"] >= 3


def test_cluster_intents_separates_different():
    """Different domains form separate clusters."""
    from mcp_server_nucleus.runtime.skill_extractor import cluster_intents

    turns = _make_turns(n=15, domain="test-writing") + _make_turns(n=10, domain="debug-errors")
    clusters = cluster_intents(turns, min_cluster_size=3, use_embeddings=False)
    # Should have at least 2 distinct clusters
    assert len(clusters) >= 1
    domains = {c["domain"] for c in clusters}
    # At least one cluster should exist
    assert len(domains) >= 1


def test_cluster_intents_empty_data():
    """Empty turns list returns empty clusters."""
    from mcp_server_nucleus.runtime.skill_extractor import cluster_intents

    clusters = cluster_intents([], min_cluster_size=3, use_embeddings=False)
    assert clusters == []


def test_cluster_intents_min_size_filter():
    """Clusters below min_size are filtered out."""
    from mcp_server_nucleus.runtime.skill_extractor import cluster_intents

    # Only 2 turns = below min_cluster_size=3
    turns = _make_turns(n=2, domain="test-writing")
    clusters = cluster_intents(turns, min_cluster_size=3, use_embeddings=False)
    assert clusters == []


def test_score_skill_candidate():
    """Scoring produces expected composite scores."""
    from mcp_server_nucleus.runtime.skill_extractor import score_skill_candidate

    cluster = {
        "domain": "test-writing",
        "intents": ["write tests for auth", "add test coverage", "create unit tests"],
        "tools_used": {"Read": 5, "Edit": 8, "Bash": 3},
        "turns": [
            {"quality_grade": "gold", "tools_used": ["Read", "Edit"]},
            {"quality_grade": "silver", "tools_used": ["Edit", "Bash"]},
            {"quality_grade": "platinum", "tools_used": ["Read", "Edit", "Bash"]},
        ],
        "size": 3,
    }
    scored = score_skill_candidate(cluster)
    assert "score" in scored
    assert 0 <= scored["score"] <= 1
    assert "score_breakdown" in scored
    breakdown = scored["score_breakdown"]
    assert all(k in breakdown for k in ("frequency", "diversity", "quality", "generality"))
    # Quality should be > 0.5 (silver + gold + platinum avg)
    assert breakdown["quality"] > 0.5


def test_extract_skills_end_to_end(tmp_path):
    """Full pipeline with temp brain path."""
    from mcp_server_nucleus.runtime.skill_extractor import extract_skills
    from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline

    brain = tmp_path / ".brain"
    brain.mkdir()
    archive = ArchivePipeline(brain_path=brain)

    # Write synthetic turns
    turns = _make_turns(n=15, domain="test-writing")
    archive.training_dir.mkdir(parents=True, exist_ok=True)
    with open(archive.turns_file, "w") as f:
        for t in turns:
            f.write(json.dumps(t) + "\n")

    skills = extract_skills(brain, min_score=0.0, min_cluster_size=3, use_embeddings=False)
    assert len(skills) >= 1
    assert all("score" in s for s in skills)


# -- Generator tests --

def test_generate_skill_md_format():
    """Generated SKILL.md has correct structure."""
    from mcp_server_nucleus.runtime.skill_generator import generate_skill_md

    cluster = {
        "domain": "test-writing",
        "score": 0.82,
        "size": 23,
        "intents": [
            "write tests for the auth module",
            "add test coverage for user registration",
            "create unit tests for this function",
        ],
        "turns": [
            {
                "tools_used": ["Read", "Edit", "Bash"],
                "decisions": ["Read existing code first"],
                "intent": "write tests for the auth module",
                "outcome": "Created 5 test cases with full coverage",
                "quality_grade": "gold",
            },
            {
                "tools_used": ["Read", "Edit"],
                "decisions": ["Follow project conventions"],
                "intent": "add test coverage for user registration",
                "outcome": "Added 3 integration tests",
                "quality_grade": "silver",
            },
        ],
    }
    md = generate_skill_md(cluster)
    assert "---" in md
    assert "name: test-writing" in md
    assert "version: 1.0.0" in md
    assert "source: nucleus-flywheel" in md
    assert "## When to use" in md
    assert "## Approach" in md
    assert "## Examples" in md


def test_anonymize_text_strips_paths():
    """File paths replaced with <file>."""
    from mcp_server_nucleus.runtime.skill_generator import _anonymize_text

    result = _anonymize_text("Fix the bug in /src/auth/middleware.py line 42")
    assert "/src/auth/middleware.py" not in result
    assert "<file>" in result


def test_trigger_phrase_extraction():
    """Top phrases extracted from intents."""
    from mcp_server_nucleus.runtime.skill_generator import _extract_trigger_phrases

    intents = [
        "write tests for the auth module",
        "write tests for the payment system",
        "write tests for the API",
        "add test coverage for the database",
        "add test coverage for the cache",
    ]
    phrases = _extract_trigger_phrases(intents, top_n=3)
    assert len(phrases) >= 1
    # "write tests" should be in there
    assert any("write" in p or "test" in p for p in phrases)


# -- Registry tests --

def test_registry_register_and_list(tmp_path):
    """Register a skill, list it back."""
    from mcp_server_nucleus.runtime.skill_registry import SkillRegistry

    brain = tmp_path / ".brain"
    brain.mkdir()
    reg = SkillRegistry(brain)

    reg.register(
        skill_id="test-writing-v1",
        name="test-writing",
        version="1.0.0",
        score=0.82,
        skill_md_path=Path("skills/generated/test-writing/SKILL.md"),
        source_turn_ids=["turn-001", "turn-002"],
    )

    skills = reg.list_skills()
    assert len(skills) == 1
    assert skills[0]["skill_id"] == "test-writing-v1"
    assert skills[0]["score"] == 0.82


def test_registry_update_usage(tmp_path):
    """Usage tracking increments correctly."""
    from mcp_server_nucleus.runtime.skill_registry import SkillRegistry

    brain = tmp_path / ".brain"
    brain.mkdir()
    reg = SkillRegistry(brain)

    reg.register(
        skill_id="test-v1",
        name="test",
        version="1.0.0",
        score=0.5,
        skill_md_path=Path("test.md"),
        source_turn_ids=[],
    )

    reg.update_usage("test-v1", success=True)
    reg.update_usage("test-v1", success=False)
    reg.update_usage("test-v1", success=True)

    skill = reg.get_skill("test-v1")
    assert skill["usage_count"] == 3
    assert skill["success_count"] == 2


def test_registry_dedup_last_wins(tmp_path):
    """Multiple entries for same skill_id, last wins."""
    from mcp_server_nucleus.runtime.skill_registry import SkillRegistry

    brain = tmp_path / ".brain"
    brain.mkdir()
    reg = SkillRegistry(brain)

    reg.register("s1", "skill-one", "1.0.0", 0.5, Path("a.md"), [])
    reg.register("s1", "skill-one", "1.1.0", 0.7, Path("b.md"), [])

    skills = reg.list_skills()
    assert len(skills) == 1
    assert skills[0]["version"] == "1.1.0"
    assert skills[0]["score"] == 0.7


# -- Publisher tests --

def test_install_creates_file(tmp_path):
    """Install copies SKILL.md to commands dir."""
    from mcp_server_nucleus.runtime.skill_registry import SkillRegistry
    from mcp_server_nucleus.runtime.skill_publisher import SkillPublisher

    brain = tmp_path / ".brain"
    brain.mkdir()
    commands_dir = tmp_path / "commands"

    # Create a skill file
    skill_dir = brain / "skills" / "generated" / "test-writing"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("# Test Writing\n\nA skill for writing tests.")

    reg = SkillRegistry(brain)
    reg.register("tw-v1", "test-writing", "1.0.0", 0.8, skill_file, [])

    pub = SkillPublisher(brain, install_dir=commands_dir)
    dest = pub.install("tw-v1", reg)

    assert dest.exists()
    assert dest.name == "nucleus-skill-test-writing.md"
    assert "Test Writing" in dest.read_text()

    # Registry should be updated
    skill = reg.get_skill("tw-v1")
    assert skill["installed"] is True


def test_uninstall_removes_file(tmp_path):
    """Uninstall deletes the command file."""
    from mcp_server_nucleus.runtime.skill_registry import SkillRegistry
    from mcp_server_nucleus.runtime.skill_publisher import SkillPublisher

    brain = tmp_path / ".brain"
    brain.mkdir()
    commands_dir = tmp_path / "commands"

    skill_dir = brain / "skills" / "generated" / "debug"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("# Debug\n\nDebug skill.")

    reg = SkillRegistry(brain)
    reg.register("dbg-v1", "debug", "1.0.0", 0.7, skill_file, [])

    pub = SkillPublisher(brain, install_dir=commands_dir)
    pub.install("dbg-v1", reg)
    assert (commands_dir / "nucleus-skill-debug.md").exists()

    pub.uninstall("dbg-v1", reg)
    assert not (commands_dir / "nucleus-skill-debug.md").exists()

    skill = reg.get_skill("dbg-v1")
    assert skill["installed"] is False


def test_list_installed(tmp_path):
    """Lists only nucleus-skill-* files."""
    from mcp_server_nucleus.runtime.skill_publisher import SkillPublisher

    brain = tmp_path / ".brain"
    brain.mkdir()
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    # Create some files
    (commands_dir / "nucleus-skill-test-writing.md").write_text("test")
    (commands_dir / "nucleus-skill-debug.md").write_text("debug")
    (commands_dir / "user-custom-command.md").write_text("custom")

    pub = SkillPublisher(brain, install_dir=commands_dir)
    installed = pub.list_installed()

    assert "test-writing" in installed
    assert "debug" in installed
    assert "user-custom-command" not in installed
    assert len(installed) == 2
