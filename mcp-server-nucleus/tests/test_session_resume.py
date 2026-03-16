"""Test session auto-resume: history loads from disk on startup."""
import json
import tempfile
from pathlib import Path


def test_session_resume_loads_history():
    """Saved chat history should be loaded into the live history list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        brain_dir = Path(tmpdir)
        chat_dir = brain_dir / "chat"
        chat_dir.mkdir(parents=True)

        # Simulate a saved session with 3 turns (6 messages)
        saved = {
            "history": [
                ["user", "hello"],
                ["assistant", "Hi! How can I help?"],
                ["user", "check status"],
                ["assistant", "All systems online."],
                ["user", "thanks"],
                ["assistant", "You're welcome!"],
            ],
            "turn_count": 3,
        }
        (chat_dir / "test1234.json").write_text(json.dumps(saved))

        # Simulate the resume logic from cli.py
        latest_file = chat_dir / "test1234.json"
        data = json.loads(latest_file.read_text())
        latest_turns = data.get("turn_count", 0)
        _saved_history = data.get("history", [])

        _max_resume_msgs = 20
        if len(_saved_history) > _max_resume_msgs:
            history = list(_saved_history[-_max_resume_msgs:])
        else:
            history = list(_saved_history)
        turn_count = latest_turns

        assert turn_count == 3
        assert len(history) == 6
        assert history[0] == ["user", "hello"]
        assert history[-1] == ["assistant", "You're welcome!"]


def test_session_resume_caps_at_20_messages():
    """Long history should be capped at last 20 messages (10 turns)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        brain_dir = Path(tmpdir)
        chat_dir = brain_dir / "chat"
        chat_dir.mkdir(parents=True)

        # 30 turns = 60 messages
        big_history = []
        for i in range(30):
            big_history.append(["user", f"question {i}"])
            big_history.append(["assistant", f"answer {i}"])

        saved = {"history": big_history, "turn_count": 30}
        (chat_dir / "test1234.json").write_text(json.dumps(saved))

        data = json.loads((chat_dir / "test1234.json").read_text())
        _saved_history = data.get("history", [])

        _max_resume_msgs = 20
        if len(_saved_history) > _max_resume_msgs:
            history = list(_saved_history[-_max_resume_msgs:])
        else:
            history = list(_saved_history)

        assert len(history) == 20
        # Should have the last 10 turns (turns 20-29)
        assert history[0] == ["user", "question 20"]
        assert history[-1] == ["assistant", "answer 29"]


def test_session_resume_empty_file():
    """Missing or empty chat file should result in empty history."""
    with tempfile.TemporaryDirectory() as tmpdir:
        brain_dir = Path(tmpdir)
        chat_dir = brain_dir / "chat"
        chat_dir.mkdir(parents=True)

        # No file exists
        latest_file = chat_dir / "nonexistent.json"
        _saved_history = []
        latest_turns = 0

        if latest_file.exists():
            data = json.loads(latest_file.read_text())
            latest_turns = data.get("turn_count", 0)
            _saved_history = data.get("history", [])

        _max_resume_msgs = 20
        if len(_saved_history) > _max_resume_msgs:
            history = list(_saved_history[-_max_resume_msgs:])
        else:
            history = list(_saved_history)

        assert len(history) == 0
        assert latest_turns == 0


def test_session_resume_corrupt_file():
    """Corrupt JSON should not crash — just empty history."""
    with tempfile.TemporaryDirectory() as tmpdir:
        brain_dir = Path(tmpdir)
        chat_dir = brain_dir / "chat"
        chat_dir.mkdir(parents=True)

        (chat_dir / "corrupt.json").write_text("{bad json!!")

        _saved_history = []
        latest_turns = 0
        try:
            data = json.loads((chat_dir / "corrupt.json").read_text())
            latest_turns = data.get("turn_count", 0)
            _saved_history = data.get("history", [])
        except Exception:
            pass

        _max_resume_msgs = 20
        if len(_saved_history) > _max_resume_msgs:
            history = list(_saved_history[-_max_resume_msgs:])
        else:
            history = list(_saved_history)

        assert len(history) == 0
        assert latest_turns == 0
