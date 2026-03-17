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

    @staticmethod
    def _is_quality_pair(pair: Dict[str, str]) -> bool:
        """Filter out low-quality training pairs."""
        user = pair.get("user", "")
        asst = pair.get("assistant", "")

        # Too short to be useful
        if len(user) < 20 or len(asst) < 50:
            return False

        # MCP noise (tool execution artifacts, not real conversation)
        noise_markers = [
            "*Running MCP tool*", "*Edited relevant file*",
            "*Viewed [", "*Created file*", "*Grep search*",
        ]
        # If user message is mostly noise markers (>50% of content)
        noise_chars = sum(len(m) for m in noise_markers if m in user)
        if noise_chars > len(user) * 0.5:
            return False

        # Placeholder / continuation-only messages
        if user.strip().lower() in ("continue", "continue.", "continue...", "yes", "ok", "go"):
            return False

        return True

    def _collect_quality_pairs(self) -> List[Dict[str, str]]:
        """Collect all quality-filtered conversation pairs from the archive."""
        turns = self.get_turns()
        pairs = []
        for turn_data in turns:
            turn = self._dict_to_turn(turn_data)
            for pair in turn.to_conversation_pairs():
                if self._is_quality_pair(pair):
                    pairs.append(pair)
        return pairs

    @staticmethod
    def _split_train_eval(pairs: List, eval_ratio: float = 0.1, seed: int = 42) -> tuple:
        """Deterministic train/eval split. Returns (train_pairs, eval_pairs)."""
        if len(pairs) < 20 or eval_ratio <= 0:
            return pairs, []
        # Deterministic shuffle via hash-based ordering (no random import needed)
        scored = []
        for i, p in enumerate(pairs):
            h = hashlib.md5(f"{seed}:{i}".encode()).hexdigest()
            scored.append((h, p))
        scored.sort(key=lambda x: x[0])
        eval_count = max(1, int(len(scored) * eval_ratio))
        eval_pairs = [s[1] for s in scored[:eval_count]]
        train_pairs = [s[1] for s in scored[eval_count:]]
        return train_pairs, eval_pairs

    def export_gemini(self, output_path: str, eval_path: str = "", eval_ratio: float = 0.1) -> int:
        """Export as Gemini (Vertex AI) fine-tuning JSONL.

        Format: {"contents": [{"role": "user", "parts": [{"text": "..."}]},
                               {"role": "model", "parts": [{"text": "..."}]}]}
        If eval_path is set, writes a held-out eval split alongside training data.
        """
        all_pairs = self._collect_quality_pairs()
        if eval_path:
            train_pairs, eval_pairs = self._split_train_eval(all_pairs, eval_ratio)
        else:
            train_pairs, eval_pairs = all_pairs, []

        def _write_gemini(pairs, path):
            count = 0
            with open(path, "w", encoding="utf-8") as f:
                for pair in pairs:
                    row = {
                        "contents": [
                            {"role": "user", "parts": [{"text": pair["user"]}]},
                            {"role": "model", "parts": [{"text": pair["assistant"]}]},
                        ]
                    }
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    count += 1
            return count

        count = _write_gemini(train_pairs, output_path)
        if eval_path and eval_pairs:
            _write_gemini(eval_pairs, eval_path)
        return count

    def export_openai(self, output_path: str, system_prompt: str = "",
                      eval_path: str = "", eval_ratio: float = 0.1) -> int:
        """Export as OpenAI/Llama/Mistral chat JSONL.

        Format: {"messages": [{"role": "system", "content": "..."},
                               {"role": "user", "content": "..."},
                               {"role": "assistant", "content": "..."}]}
        If eval_path is set, writes a held-out eval split alongside training data.
        """
        if not system_prompt:
            system_prompt = (
                "You are the Third Brother — a trained intelligence that emerged from "
                "thousands of decision cycles between two AI agents (Code and Cowork) "
                "coordinating through a shared brain. You think like the founder, "
                "know the codebase like Code, and know the market like Cowork."
            )
        all_pairs = self._collect_quality_pairs()
        if eval_path:
            train_pairs, eval_pairs = self._split_train_eval(all_pairs, eval_ratio)
        else:
            train_pairs, eval_pairs = all_pairs, []

        def _write_openai(pairs, path):
            count = 0
            with open(path, "w", encoding="utf-8") as f:
                for pair in pairs:
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": pair["user"]},
                        {"role": "assistant", "content": pair["assistant"]},
                    ]
                    f.write(json.dumps({"messages": messages}, ensure_ascii=False) + "\n")
                    count += 1
            return count

        count = _write_openai(train_pairs, output_path)
        if eval_path and eval_pairs:
            _write_openai(eval_pairs, eval_path)
        return count

    def export_anthropic(self, output_path: str,
                         eval_path: str = "", eval_ratio: float = 0.1) -> int:
        """Export as Anthropic fine-tuning JSONL.

        Format: {"messages": [{"role": "user", "content": "..."},
                               {"role": "assistant", "content": "..."}]}
        If eval_path is set, writes a held-out eval split alongside training data.
        """
        all_pairs = self._collect_quality_pairs()
        if eval_path:
            train_pairs, eval_pairs = self._split_train_eval(all_pairs, eval_ratio)
        else:
            train_pairs, eval_pairs = all_pairs, []

        def _write_anthropic(pairs, path):
            count = 0
            with open(path, "w", encoding="utf-8") as f:
                for pair in pairs:
                    row = {
                        "messages": [
                            {"role": "user", "content": pair["user"]},
                            {"role": "assistant", "content": pair["assistant"]},
                        ]
                    }
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    count += 1
            return count

        count = _write_anthropic(train_pairs, output_path)
        if eval_path and eval_pairs:
            _write_anthropic(eval_pairs, eval_path)
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

    # ── Ingest: bulk import from conversation transcripts ──

    def ingest_gemini_conversation(self, filepath: str, brother: str = "code") -> int:
        """Import a Gemini CLI conversation JSON into the archive.

        Gemini format: [{"role": "user"/"model", "parts": [{"text": "..."}]}]
        Chunks into ~10-turn windows, each becoming one LoopTurn with real
        conversation data (richest training signal).
        """
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return 0

        # Build conversation pairs
        conversation = []
        for msg in data:
            role = msg.get("role", "")
            parts = msg.get("parts", [])
            text = parts[0].get("text", "") if parts else ""
            if not text or len(text) < 5:
                continue
            if role == "user":
                conversation.append({"role": "user", "content": text[:3000]})
            elif role == "model":
                conversation.append({"role": "assistant", "content": text[:3000]})

        # Chunk into windows of ~20 messages (10 user/assistant pairs)
        WINDOW = 20
        count = 0
        existing_hashes = self._get_existing_hashes()
        fname = Path(filepath).stem

        for i in range(0, len(conversation), WINDOW):
            chunk = conversation[i:i + WINDOW]
            if len(chunk) < 4:  # Skip tiny fragments
                continue

            # Extract intent from first user message
            first_user = next((m["content"][:100] for m in chunk if m["role"] == "user"), "Gemini session")
            # Dedup by content hash
            content_sig = f"{brother}:{first_user}:{fname}:{i}"
            content_hash = hashlib.sha256(content_sig.encode()).hexdigest()[:16]
            if content_hash in existing_hashes:
                continue

            turn = self.record_turn(
                brother=brother,
                intent=first_user,
                actions=[],
                tools_used=[],
                decisions=[],
                outcome=f"Gemini session chunk {i // WINDOW + 1} ({len(chunk)} messages)",
                signal_absorbed=[],
                signal_produced=[],
                confidence=0.7,
                context=f"Ingested from {fname}",
                conversation=chunk,
                metadata={"source": filepath, "chunk_index": i // WINDOW},
            )
            count += 1

        return count

    def ingest_claude_markdown(self, filepath: str, brother: str = "code") -> int:
        """Import a Claude project export markdown conversation.

        These are markdown files with ## Human / ## Assistant sections.
        """
        text = Path(filepath).read_text(encoding="utf-8")
        conversation = []
        current_role = None
        current_content = []

        for line in text.split("\n"):
            stripped = line.strip()
            is_user = (
                stripped.startswith("## Human") or stripped.startswith("**Human**")
                or stripped == "### User Input"
            )
            is_assistant = (
                stripped.startswith("## Assistant") or stripped.startswith("**Assistant**")
                or stripped.startswith("### Planner Response")
                or stripped.startswith("### Assistant Response")
                or stripped.startswith("### Model Response")
            )
            if is_user:
                if current_role and current_content:
                    content = "\n".join(current_content).strip()
                    if len(content) > 5:
                        conversation.append({"role": current_role, "content": content[:3000]})
                current_role = "user"
                current_content = []
            elif is_assistant:
                if current_role and current_content:
                    content = "\n".join(current_content).strip()
                    if len(content) > 5:
                        conversation.append({"role": current_role, "content": content[:3000]})
                current_role = "assistant"
                current_content = []
            elif current_role:
                current_content.append(line)

        # Flush last block
        if current_role and current_content:
            content = "\n".join(current_content).strip()
            if len(content) > 5:
                conversation.append({"role": current_role, "content": content[:3000]})

        if len(conversation) < 4:
            return 0

        # Chunk and record
        WINDOW = 20
        count = 0
        existing_hashes = self._get_existing_hashes()
        fname = Path(filepath).stem

        for i in range(0, len(conversation), WINDOW):
            chunk = conversation[i:i + WINDOW]
            if len(chunk) < 4:
                continue

            first_user = next((m["content"][:100] for m in chunk if m["role"] == "user"), fname)
            content_sig = f"{brother}:{first_user}:{fname}:{i}"
            content_hash = hashlib.sha256(content_sig.encode()).hexdigest()[:16]
            if content_hash in existing_hashes:
                continue

            turn = self.record_turn(
                brother=brother,
                intent=first_user,
                actions=[],
                tools_used=[],
                decisions=[],
                outcome=f"Claude session chunk {i // WINDOW + 1} ({len(chunk)} messages)",
                signal_absorbed=[],
                signal_produced=[],
                confidence=0.7,
                context=f"Ingested from {fname}",
                conversation=chunk,
                metadata={"source": filepath, "chunk_index": i // WINDOW},
            )
            count += 1

        return count

    def ingest_thread_archive(self, thread_path: str = "", brother: str = "code") -> int:
        """Bridge thread.jsonl (RAG archive) into loop_turns.jsonl (training archive).

        thread.jsonl format: {"ts": "...", "role": "user|assistant", "content": "...", ...}
        Groups sequential user/assistant pairs into conversation windows and records them.
        Deduplicates by content hash to avoid re-ingesting already-recorded sessions.
        """
        if not thread_path:
            thread_path = str(self.brain_path / "chat" / "archive" / "thread.jsonl")
        if not Path(thread_path).exists():
            return 0

        # Read thread entries
        entries = []
        with open(thread_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))

        if len(entries) < 4:
            return 0

        # Convert to conversation format
        conversation = []
        for entry in entries:
            role = entry.get("role", "")
            content = entry.get("content", "")
            if role in ("user", "assistant") and content and len(content) > 3:
                conversation.append({"role": role, "content": content[:3000]})

        # Chunk and record (same windowing as other ingest methods)
        WINDOW = 20
        count = 0
        existing_hashes = self._get_existing_hashes()

        for i in range(0, len(conversation), WINDOW):
            chunk = conversation[i:i + WINDOW]
            if len(chunk) < 4:
                continue

            first_user = next((m["content"][:100] for m in chunk if m["role"] == "user"), "Chat session")
            content_sig = f"{brother}:thread:{first_user}:{i}"
            content_hash = hashlib.sha256(content_sig.encode()).hexdigest()[:16]
            if content_hash in existing_hashes:
                continue

            self.record_turn(
                brother=brother,
                intent=first_user,
                actions=[],
                tools_used=[],
                decisions=[],
                outcome=f"Thread archive chunk {i // WINDOW + 1} ({len(chunk)} messages)",
                signal_absorbed=[],
                signal_produced=[],
                confidence=0.7,
                context="Ingested from thread.jsonl",
                conversation=chunk,
                metadata={"source": thread_path, "chunk_index": i // WINDOW},
            )
            count += 1

        return count

    def should_retrain(self) -> Dict[str, Any]:
        """Check if there's enough new data since last training to justify retraining."""
        stats = self.get_stats()
        total = stats.get("total_turns", 0)

        # Check last training timestamp
        last_train_file = self.training_dir / "last_train.json"
        if last_train_file.exists():
            last_train = json.loads(last_train_file.read_text(encoding="utf-8"))
            last_count = last_train.get("turn_count", 0)
            new_turns = total - last_count
        else:
            last_count = 0
            new_turns = total

        # Retrain if 20%+ new data or 100+ new turns
        threshold_pct = max(int(last_count * 0.2), 50) if last_count > 0 else 50
        should = new_turns >= threshold_pct

        return {
            "should_retrain": should,
            "total_turns": total,
            "last_trained_at": last_count,
            "new_turns": new_turns,
            "threshold": threshold_pct,
            "reason": f"{new_turns} new turns since last train ({threshold_pct} needed)" if not should
                     else f"{new_turns} new turns — retrain recommended",
        }

    def mark_trained(self, turn_count: int = 0, model_path: str = "",
                     base_model: str = "", target: str = "",
                     hyperparams: Optional[Dict] = None):
        """Mark the current archive as trained (resets retrain counter).

        Also records model metadata for versioning. Previous training runs
        are preserved in a training_history.jsonl file.
        """
        if not turn_count:
            turn_count = self.get_stats().get("total_turns", 0)

        record = {
            "turn_count": turn_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_path": model_path,
            "base_model": base_model,
            "target": target,  # "local", "gemini", "openai"
        }
        if hyperparams:
            record["hyperparams"] = hyperparams

        # Write current checkpoint
        last_train_file = self.training_dir / "last_train.json"
        last_train_file.write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Append to training history (never overwritten)
        history_file = self.training_dir / "training_history.jsonl"
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _get_existing_hashes(self) -> set:
        """Get content hashes of all existing turns for dedup."""
        turns = self.get_turns()
        return {t.get("content_hash", "") for t in turns}

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
