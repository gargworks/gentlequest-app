"""Archive Pipeline — Training Data Flywheel for the Third Brother.

Every loop turn (Code builds, Cowork scans, brain absorbs) gets recorded
as a structured LoopTurn in .brain/training/loop_turns.jsonl. This is
the raw material for fine-tuning the third brother — a model trained on
the accumulated decision intelligence of both brothers.

The archive format is provider-agnostic. Converters export to:
- Gemini (Vertex AI) fine-tuning format
- OpenAI/Llama/Mistral chat format (axolotl, unsloth)
- Anthropic fine-tuning format

Usage:
    from .archive_pipeline import ArchivePipeline

    archive = ArchivePipeline()
    archive.record_turn(
        brother="code",
        intent="Fix MCP engram writes",
        actions=["read .brain/handoff.md", "grep for env var mismatch", "fix PR #14"],
        tools_used=["nucleus_engrams", "nucleus_tasks"],
        decisions=["env var was NUCLEAR_ not NUCLEUS_ — typo fix, not design change"],
        outcome="MCP engram writes work. Cowork can now write to brain via MCP tools.",
        signal_absorbed=["competitive_landscape_2026_03_17.md"],
        signal_produced=["handoff.md updated for turn 2"],
        confidence=0.95
    )

    # Export for fine-tuning
    archive.export_gemini("output/gemini_training.jsonl")
    archive.export_openai("output/openai_training.jsonl")
"""

import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from .common import get_brain_path


class LoopTurn:
    """One turn of the Code^Cowork exponential loop."""

    def __init__(
        self,
        brother: str,               # "code" | "cowork" | "father"
        intent: str,                 # What this turn set out to do
        actions: List[str],          # What actually happened (human-readable)
        tools_used: List[str],       # MCP tools invoked
        decisions: List[str],        # Key judgment calls made
        outcome: str,                # Result summary
        signal_absorbed: List[str],  # Engrams/files read from brain
        signal_produced: List[str],  # Engrams/files written to brain
        confidence: float = 1.0,     # How confident in the outcome (0-1)
        context: Optional[str] = None,  # Extra context (e.g., "responding to Cowork's competitive scan")
        conversation: Optional[List[Dict[str, str]]] = None,  # Full chat: [{"role": "user", "content": "..."}, ...]
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.turn_id = f"turn-{uuid.uuid4().hex[:12]}"
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.brother = brother
        self.intent = intent
        self.actions = actions
        self.tools_used = tools_used
        self.decisions = decisions
        self.outcome = outcome
        self.signal_absorbed = signal_absorbed
        self.signal_produced = signal_produced
        self.confidence = confidence
        self.context = context or ""
        self.conversation = conversation or []  # Father's words + brother's responses
        self.metadata = metadata or {}

        # Content hash for dedup
        content = f"{brother}:{intent}:{outcome}"
        self.content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "timestamp": self.timestamp,
            "brother": self.brother,
            "intent": self.intent,
            "actions": self.actions,
            "tools_used": self.tools_used,
            "decisions": self.decisions,
            "outcome": self.outcome,
            "signal_absorbed": self.signal_absorbed,
            "signal_produced": self.signal_produced,
            "confidence": self.confidence,
            "context": self.context,
            "content_hash": self.content_hash,
            "conversation": self.conversation,
            "metadata": self.metadata,
        }

    def to_conversation_pairs(self) -> List[Dict[str, str]]:
        """Convert to user/assistant conversation pairs for training.

        If real conversation is available (father's actual words + brother's responses),
        use those directly — they're the richest training signal.
        Otherwise, synthesize from intent/decisions/outcome.
        """
        # Best case: real conversation recorded
        if self.conversation:
            pairs = []
            user_buf, asst_buf = "", ""
            for msg in self.conversation:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if not content or len(content) < 5:
                    continue
                if role == "user":
                    if user_buf and asst_buf:
                        pairs.append({"user": user_buf.strip(), "assistant": asst_buf.strip()})
                        asst_buf = ""
                    user_buf = content
                elif role in ("assistant", "model"):
                    asst_buf += content + "\n"
            if user_buf and asst_buf:
                pairs.append({"user": user_buf.strip(), "assistant": asst_buf.strip()})
            if pairs:
                return pairs

        # Fallback: synthesize from structured fields
        user_msg = self.intent
        if self.context:
            user_msg = f"{self.context}\n\n{self.intent}"
        if self.signal_absorbed:
            user_msg += f"\n\nContext from brain: {', '.join(self.signal_absorbed)}"

        assistant_msg = ""
        if self.decisions:
            assistant_msg += "Decisions:\n" + "\n".join(f"- {d}" for d in self.decisions) + "\n\n"
        if self.actions:
            assistant_msg += "Actions:\n" + "\n".join(f"- {a}" for a in self.actions) + "\n\n"
        assistant_msg += f"Outcome: {self.outcome}"

        return [{"user": user_msg.strip(), "assistant": assistant_msg.strip()}]


class ArchivePipeline:
    """Append-only archive of loop turns. The training data flywheel."""

    def __init__(self, brain_path: Optional[Path] = None):
        self.brain_path = brain_path or get_brain_path()
        self.training_dir = self.brain_path / "training"
        self.training_dir.mkdir(parents=True, exist_ok=True)
        self.turns_file = self.training_dir / "loop_turns.jsonl"
        self.stats_file = self.training_dir / "stats.json"

    def record_turn(self, **kwargs) -> LoopTurn:
        """Record a loop turn to the archive."""
        turn = LoopTurn(**kwargs)

        with open(self.turns_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(turn.to_dict(), ensure_ascii=False) + "\n")

        self._update_stats(turn)
        return turn

    def get_turns(self, limit: int = 0) -> List[Dict[str, Any]]:
        """Read turns from the archive."""
        if not self.turns_file.exists():
            return []
        turns = []
        with open(self.turns_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    turns.append(json.loads(line))
        if limit > 0:
            turns = turns[-limit:]
        return turns

    def get_stats(self) -> Dict[str, Any]:
        """Get archive statistics."""
        if self.stats_file.exists():
            return json.loads(self.stats_file.read_text(encoding="utf-8"))
        return {"total_turns": 0, "by_brother": {}, "first_turn": None, "last_turn": None}

    # ── Export converters ──

    def export_gemini(self, output_path: str) -> int:
        """Export as Gemini (Vertex AI) fine-tuning JSONL.

        Format: {"contents": [{"role": "user", "parts": [{"text": "..."}]},
                               {"role": "model", "parts": [{"text": "..."}]}]}
        """
        turns = self.get_turns()
        count = 0
        with open(output_path, "w", encoding="utf-8") as f:
            for turn_data in turns:
                turn = self._dict_to_turn(turn_data)
                for pair in turn.to_conversation_pairs():
                    gemini_row = {
                        "contents": [
                            {"role": "user", "parts": [{"text": pair["user"]}]},
                            {"role": "model", "parts": [{"text": pair["assistant"]}]},
                        ]
                    }
                    f.write(json.dumps(gemini_row, ensure_ascii=False) + "\n")
                    count += 1
        return count

    def export_openai(self, output_path: str, system_prompt: str = "") -> int:
        """Export as OpenAI/Llama/Mistral chat JSONL.

        Format: {"messages": [{"role": "system", "content": "..."},
                               {"role": "user", "content": "..."},
                               {"role": "assistant", "content": "..."}]}
        """
        if not system_prompt:
            system_prompt = (
                "You are the Third Brother — a trained intelligence that emerged from "
                "thousands of decision cycles between two AI agents (Code and Cowork) "
                "coordinating through a shared brain. You think like the founder, "
                "know the codebase like Code, and know the market like Cowork."
            )
        turns = self.get_turns()
        count = 0
        with open(output_path, "w", encoding="utf-8") as f:
            for turn_data in turns:
                turn = self._dict_to_turn(turn_data)
                for pair in turn.to_conversation_pairs():
                    messages = [{"role": "system", "content": system_prompt}]
                    messages.append({"role": "user", "content": pair["user"]})
                    messages.append({"role": "assistant", "content": pair["assistant"]})
                    f.write(json.dumps({"messages": messages}, ensure_ascii=False) + "\n")
                    count += 1
        return count

    def export_anthropic(self, output_path: str) -> int:
        """Export as Anthropic fine-tuning JSONL.

        Format: {"messages": [{"role": "user", "content": "..."},
                               {"role": "assistant", "content": "..."}]}
        """
        turns = self.get_turns()
        count = 0
        with open(output_path, "w", encoding="utf-8") as f:
            for turn_data in turns:
                turn = self._dict_to_turn(turn_data)
                for pair in turn.to_conversation_pairs():
                    row = {
                        "messages": [
                            {"role": "user", "content": pair["user"]},
                            {"role": "assistant", "content": pair["assistant"]},
                        ]
                    }
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    count += 1
        return count

    # ── Internal ──

    def _update_stats(self, turn: LoopTurn):
        stats = self.get_stats()
        stats["total_turns"] = stats.get("total_turns", 0) + 1
        by_bro = stats.get("by_brother", {})
        by_bro[turn.brother] = by_bro.get(turn.brother, 0) + 1
        stats["by_brother"] = by_bro
        if not stats.get("first_turn"):
            stats["first_turn"] = turn.timestamp
        stats["last_turn"] = turn.timestamp
        self.stats_file.write_text(
            json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _dict_to_turn(self, d: Dict[str, Any]) -> LoopTurn:
        """Reconstruct a LoopTurn from a dict (for export)."""
        turn = LoopTurn(
            brother=d["brother"],
            intent=d["intent"],
            actions=d.get("actions", []),
            tools_used=d.get("tools_used", []),
            decisions=d.get("decisions", []),
            outcome=d["outcome"],
            signal_absorbed=d.get("signal_absorbed", []),
            signal_produced=d.get("signal_produced", []),
            confidence=d.get("confidence", 1.0),
            context=d.get("context", ""),
            conversation=d.get("conversation", []),
            metadata=d.get("metadata", {}),
        )
        turn.turn_id = d.get("turn_id", turn.turn_id)
        turn.timestamp = d.get("timestamp", turn.timestamp)
        turn.content_hash = d.get("content_hash", turn.content_hash)
        return turn
