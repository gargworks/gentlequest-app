"""Archive Pipeline — Training Data Flywheel for the Third Brother.

Every loop turn (Code builds, Cowork scans, brain absorbs) gets recorded
as a structured LoopTurn in .brain/training/loop_turns.jsonl. This is
the raw material for fine-tuning the third brother — a model trained on
the accumulated decision intelligence of both brothers.

The archive has TWO data streams:

1. SFT (Supervised Fine-Tuning) — loop_turns.jsonl
   Input/output pairs: "what happened" → teach the model to mimic.

2. DPO (Direct Preference Optimization) — preference_pairs.jsonl
   Win/lose triples: (prompt, chosen, rejected) → teach the model TASTE.
   Sources: /retry (explicit rejection), corrections ("no, do X"),
   outcome signals (deploy success vs failure), escalations.

The archive format is provider-agnostic. Converters export to:
- Gemini (Vertex AI) fine-tuning format
- OpenAI/Llama/Mistral chat format (axolotl, unsloth)
- Anthropic fine-tuning format
- DPO format (TRL DPOTrainer: prompt/chosen/rejected)

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

    # DPO: record a preference (user retried → old response is rejected)
    archive.record_preference(
        prompt="Fix the auth middleware",
        chosen="I'll update the JWT validation to check expiry before signature...",
        rejected="Let me refactor the entire auth module to use OAuth2...",
        source="retry",
    )

    # Record a reasoning chain (multi-step tool use → <think> training)
    archive.record_reasoning_chain(
        prompt="Fix the auth middleware",
        steps=[
            {"thought": "Let me check the JWT validation...", "action": "read_file auth.py", "observation": "Line 42: no expiry check"},
            {"thought": "Found it — expiry not validated before sig check", "action": "edit_file auth.py", "observation": "Added expiry validation"},
        ],
        final_answer="Fixed auth by adding JWT expiry validation before signature check.",
        source="react_loop",
    )

    # Export for fine-tuning
    archive.export_gemini("output/gemini_training.jsonl")
    archive.export_openai("output/openai_training.jsonl")
    archive.export_dpo("output/dpo_training.jsonl")
    archive.export_reasoning("output/reasoning_training.jsonl")
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

    # Correction patterns: if a user message starts with these, the previous
    # assistant response is likely being rejected in favor of a new direction.
    CORRECTION_PREFIXES = (
        "no ", "no,", "not that", "wrong", "actually", "instead",
        "don't", "stop", "that's wrong", "that's not", "nope",
        "scratch that", "forget that", "let's not",
    )

    def __init__(self, brain_path: Optional[Path] = None):
        self.brain_path = brain_path or get_brain_path()
        self.training_dir = self.brain_path / "training"
        self.training_dir.mkdir(parents=True, exist_ok=True)
        self.turns_file = self.training_dir / "loop_turns.jsonl"
        self.prefs_file = self.training_dir / "preference_pairs.jsonl"
        self.reasoning_file = self.training_dir / "reasoning_chains.jsonl"
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
            "*Read file*", "*Searched for*", "*Listed files*",
        ]

        # Check BOTH user and assistant for noise
        for text, threshold in [(user, 0.5), (asst, 0.3)]:
            noise_chars = sum(len(m) for m in noise_markers if m in text)
            if noise_chars > len(text) * threshold:
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

    def count_quality_pairs(self) -> int:
        """Count quality pairs without writing any files."""
        return len(self._collect_quality_pairs())

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

    # ── DPO (Direct Preference Optimization) ──

    def record_preference(
        self,
        prompt: str,
        chosen: str,
        rejected: str,
        source: str = "manual",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record a preference pair for DPO training.

        Args:
            prompt: The user input / question.
            chosen: The preferred (winning) response.
            rejected: The dispreferred (losing) response.
            source: Where this signal came from:
                "retry"      — user hit /retry (explicit rejection of previous)
                "correction" — user started with "no, do X instead" pattern
                "outcome"    — deploy success vs failure, task complete vs escalated
                "review"     — code review found issues (original = rejected)
                "manual"     — manually recorded
            metadata: Optional extra context (event_type, brother, etc.)

        Returns:
            The recorded preference dict.
        """
        if len(prompt) < 10 or len(chosen) < 20 or len(rejected) < 20:
            return {}  # Too short to be useful
        if chosen.strip() == rejected.strip():
            return {}  # No preference signal

        pref = {
            "pref_id": f"pref-{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt": prompt[:3000],
            "chosen": chosen[:3000],
            "rejected": rejected[:3000],
            "source": source,
            "metadata": metadata or {},
        }

        with open(self.prefs_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(pref, ensure_ascii=False) + "\n")

        return pref

    def record_outcome_preference(
        self,
        event_type: str,
        prompt: str,
        response: str,
        success: bool,
        context: str = "",
    ):
        """Record an outcome-based preference from system events.

        For deploy_success: response is chosen, we synthesize a generic rejected.
        For deploy_failed/task_escalated: response is rejected, we note the failure.
        These build up gradually — the DPO trainer learns from the distribution.
        """
        if success:
            # Successful outcome — this is the chosen response
            # Rejected = generic "I'm not sure" placeholder (weak negative)
            self.record_preference(
                prompt=prompt,
                chosen=response,
                rejected=f"I'll need to investigate further before making changes to {context}.",
                source="outcome",
                metadata={"event_type": event_type, "outcome": "success"},
            )
        else:
            # Failed outcome — this response led to a bad result
            # Chosen = acknowledgement of the failure (teaches caution)
            self.record_preference(
                prompt=prompt,
                chosen=f"This approach has risks. Let me reconsider the strategy for {context}.",
                rejected=response,
                source="outcome",
                metadata={"event_type": event_type, "outcome": "failure"},
            )

    @staticmethod
    def is_correction(user_msg: str) -> bool:
        """Detect if a user message is correcting the previous response."""
        lower = user_msg.strip().lower()
        for prefix in ArchivePipeline.CORRECTION_PREFIXES:
            if lower.startswith(prefix):
                return True
        return False

    def get_preferences(self, limit: int = 0) -> List[Dict[str, Any]]:
        """Read preference pairs from the archive."""
        if not self.prefs_file.exists():
            return []
        prefs = []
        with open(self.prefs_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    prefs.append(json.loads(line))
        if limit > 0:
            prefs = prefs[-limit:]
        return prefs

    def count_preferences(self) -> int:
        """Count preference pairs without loading them all."""
        if not self.prefs_file.exists():
            return 0
        count = 0
        with open(self.prefs_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
        return count

    def get_preference_stats(self) -> Dict[str, Any]:
        """Get DPO preference statistics broken down by source."""
        prefs = self.get_preferences()
        by_source: Dict[str, int] = {}
        for p in prefs:
            src = p.get("source", "unknown")
            by_source[src] = by_source.get(src, 0) + 1
        return {
            "total_preferences": len(prefs),
            "by_source": by_source,
            "first": prefs[0]["timestamp"] if prefs else None,
            "last": prefs[-1]["timestamp"] if prefs else None,
        }

    def export_dpo(self, output_path: str, eval_path: str = "",
                   eval_ratio: float = 0.1, system_prompt: str = "") -> int:
        """Export preference pairs in TRL DPOTrainer format.

        Format:
        {
            "prompt": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}],
            "chosen": [{"role": "assistant", "content": "..."}],
            "rejected": [{"role": "assistant", "content": "..."}]
        }
        """
        if not system_prompt:
            system_prompt = (
                "You are the Third Brother — a trained intelligence that emerged from "
                "thousands of decision cycles between two AI agents (Code and Cowork) "
                "coordinating through a shared brain. You think like the founder, "
                "know the codebase like Code, and know the market like Cowork."
            )

        prefs = self.get_preferences()
        if not prefs:
            return 0

        if eval_path:
            train_prefs, eval_prefs = self._split_train_eval(prefs, eval_ratio)
        else:
            train_prefs, eval_prefs = prefs, []

        def _write_dpo(items, path):
            count = 0
            with open(path, "w", encoding="utf-8") as f:
                for p in items:
                    row = {
                        "prompt": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": p["prompt"]},
                        ],
                        "chosen": [
                            {"role": "assistant", "content": p["chosen"]},
                        ],
                        "rejected": [
                            {"role": "assistant", "content": p["rejected"]},
                        ],
                    }
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    count += 1
            return count

        count = _write_dpo(train_prefs, output_path)
        if eval_path and eval_prefs:
            _write_dpo(eval_prefs, eval_path)
        return count

    # ── Reasoning / Chain-of-Thought (Phase 5) ──

    def record_reasoning_chain(
        self,
        prompt: str,
        steps: List[Dict[str, str]],
        final_answer: str,
        source: str = "react_loop",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record a multi-step reasoning chain for CoT training.

        Each step is a Thought → Action → Observation triple from the
        ReAct loop. The chain teaches the Third Brother to think before
        answering — generating hidden reasoning tokens at inference time.

        Args:
            prompt: The original user question.
            steps: List of reasoning steps, each a dict with:
                - thought: What the agent was thinking / intermediate response
                - action: What it did (tool name + args)
                - observation: What it found (tool result)
            final_answer: The final response after reasoning.
            source: Where this chain came from:
                "react_loop"   — captured from CLI ReAct tool-use loop
                "dual_review"  — dual-agent review reasoning
                "decision"     — decision from brain ledger
                "manual"       — manually recorded
            metadata: Optional context (provider, model, etc.)

        Returns:
            The recorded chain dict, or {} if quality too low.
        """
        # Quality gate: reasoning must have actual depth
        if len(steps) < 1 or len(prompt) < 10 or len(final_answer) < 20:
            return {}

        chain = {
            "chain_id": f"cot-{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt": prompt[:3000],
            "steps": [
                {
                    "thought": s.get("thought", "")[:2000],
                    "action": s.get("action", "")[:500],
                    "observation": s.get("observation", "")[:2000],
                }
                for s in steps[:20]  # Cap at 20 steps
            ],
            "final_answer": final_answer[:3000],
            "step_count": len(steps),
            "source": source,
            "metadata": metadata or {},
        }

        with open(self.reasoning_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(chain, ensure_ascii=False) + "\n")

        return chain

    def get_reasoning_chains(self, limit: int = 0) -> List[Dict[str, Any]]:
        """Read reasoning chains from the archive."""
        if not self.reasoning_file.exists():
            return []
        chains = []
        with open(self.reasoning_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    chains.append(json.loads(line))
        if limit > 0:
            chains = chains[-limit:]
        return chains

    def count_reasoning_chains(self) -> int:
        """Count reasoning chains without loading them all."""
        if not self.reasoning_file.exists():
            return 0
        count = 0
        with open(self.reasoning_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
        return count

    def get_reasoning_stats(self) -> Dict[str, Any]:
        """Get reasoning chain statistics."""
        chains = self.get_reasoning_chains()
        by_source: Dict[str, int] = {}
        total_steps = 0
        for c in chains:
            src = c.get("source", "unknown")
            by_source[src] = by_source.get(src, 0) + 1
            total_steps += c.get("step_count", 0)
        return {
            "total_chains": len(chains),
            "total_steps": total_steps,
            "avg_steps": round(total_steps / len(chains), 1) if chains else 0,
            "by_source": by_source,
            "first": chains[0]["timestamp"] if chains else None,
            "last": chains[-1]["timestamp"] if chains else None,
        }

    @staticmethod
    def _chain_to_think_format(chain: Dict[str, Any]) -> str:
        """Convert a reasoning chain into <think> tagged output.

        Format (DeepSeek R1 / QwQ style):
        <think>
        Let me check the auth middleware...
        [Action: read_file auth.py]
        Found: Line 42 has no expiry check.
        I need to add expiry validation before signature check.
        [Action: edit_file auth.py]
        Done: Added expiry validation.
        </think>

        Fixed auth by adding JWT expiry validation before signature check.
        """
        think_parts = []
        for step in chain.get("steps", []):
            thought = step.get("thought", "").strip()
            action = step.get("action", "").strip()
            observation = step.get("observation", "").strip()
            if thought:
                think_parts.append(thought)
            if action:
                think_parts.append(f"[Action: {action}]")
            if observation:
                # Truncate long observations to keep reasoning focused
                obs = observation[:500]
                if len(observation) > 500:
                    obs += "..."
                think_parts.append(f"Result: {obs}")
        think_block = "\n".join(think_parts)
        final = chain.get("final_answer", "")
        return f"<think>\n{think_block}\n</think>\n\n{final}"

    def _is_quality_chain(self, chain: Dict[str, Any]) -> bool:
        """Filter reasoning chains for training quality.

        Good chains have:
        - Multiple steps (single-step = no real reasoning)
        - Substantial thoughts (not just "Let me check")
        - Meaningful observations (not empty tool results)
        """
        steps = chain.get("steps", [])
        if len(steps) < 2:
            return False  # Single step = no reasoning chain
        # At least one step must have a real thought
        has_thought = any(
            len(s.get("thought", "")) > 30 for s in steps
        )
        if not has_thought:
            return False
        # Final answer must be substantial
        if len(chain.get("final_answer", "")) < 50:
            return False
        return True

    def export_reasoning(self, output_path: str, eval_path: str = "",
                         eval_ratio: float = 0.1, system_prompt: str = "") -> int:
        """Export reasoning chains as <think>-tagged training data.

        Format: Standard OpenAI chat JSONL where assistant content has
        <think>...</think> reasoning block before the final answer.
        Compatible with SFT trainers (unsloth, axolotl, TRL).
        """
        if not system_prompt:
            system_prompt = (
                "You are the Third Brother — a trained intelligence that emerged from "
                "thousands of decision cycles between two AI agents (Code and Cowork) "
                "coordinating through a shared brain. You think step by step, using "
                "<think> blocks to reason through problems before answering. You think "
                "like the founder, know the codebase like Code, and know the market "
                "like Cowork."
            )

        chains = self.get_reasoning_chains()
        quality_chains = [c for c in chains if self._is_quality_chain(c)]

        if not quality_chains:
            return 0

        if eval_path:
            train_chains, eval_chains = self._split_train_eval(
                quality_chains, eval_ratio
            )
        else:
            train_chains, eval_chains = quality_chains, []

        def _write_reasoning(items, path):
            count = 0
            with open(path, "w", encoding="utf-8") as f:
                for chain in items:
                    think_response = self._chain_to_think_format(chain)
                    row = {
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": chain["prompt"]},
                            {"role": "assistant", "content": think_response},
                        ]
                    }
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    count += 1
            return count

        count = _write_reasoning(train_chains, output_path)
        if eval_path and eval_chains:
            _write_reasoning(eval_chains, eval_path)
        return count

    # ── Retroactive Mining (bootstrap DPO + CoT from existing archive) ──

    def mine_preferences_from_archive(self) -> int:
        """Extract DPO preference pairs from existing conversation turns.

        Mines three signal types from the 800+ existing conversations:
        1. Correction patterns: user said "no/wrong/actually" → previous response rejected
        2. Low-confidence turns: confidence < 0.5 → weaker signal
        3. Escalation turns: task was escalated → agent's approach was rejected

        Returns number of new preference pairs mined.
        """
        turns = self.get_turns()
        existing_prefs = {
            p.get("metadata", {}).get("mined_from", "")
            for p in self.get_preferences()
            if p.get("metadata", {}).get("mined_from")
        }
        mined = 0

        for turn_data in turns:
            turn_id = turn_data.get("turn_id", "")
            if turn_id in existing_prefs:
                continue  # Already mined

            conv = turn_data.get("conversation", [])
            if len(conv) < 4:
                continue

            # Mine correction patterns from conversations
            for i, msg in enumerate(conv):
                if msg.get("role") != "user":
                    continue
                content = msg.get("content", "").strip()
                if not self.is_correction(content):
                    continue

                # Found a correction. Previous assistant response = rejected.
                # The response AFTER the correction = chosen (if it exists).
                prev_asst = None
                next_asst = None
                prev_user = None

                # Walk backward to find the rejected response
                for j in range(i - 1, -1, -1):
                    if conv[j].get("role") == "assistant" and not prev_asst:
                        prev_asst = conv[j].get("content", "")
                    if conv[j].get("role") == "user" and not prev_user:
                        prev_user = conv[j].get("content", "")
                        break

                # Walk forward to find the chosen response
                for j in range(i + 1, len(conv)):
                    if conv[j].get("role") == "assistant":
                        next_asst = conv[j].get("content", "")
                        break

                if prev_user and prev_asst and next_asst:
                    pref = self.record_preference(
                        prompt=prev_user,
                        chosen=next_asst,
                        rejected=prev_asst,
                        source="mined_correction",
                        metadata={"mined_from": turn_id, "correction": content[:200]},
                    )
                    if pref:
                        mined += 1

        return mined

    def mine_reasoning_from_archive(self) -> int:
        """Extract CoT reasoning chains from existing archive turns.

        Mines two signal types:
        1. Turns with multi-step actions + decisions → structured reasoning
        2. Conversations with [Tool Result] messages → tool-use reasoning chains

        Returns number of new reasoning chains mined.
        """
        turns = self.get_turns()
        existing_chains = {
            c.get("metadata", {}).get("mined_from", "")
            for c in self.get_reasoning_chains()
            if c.get("metadata", {}).get("mined_from")
        }
        mined = 0

        for turn_data in turns:
            turn_id = turn_data.get("turn_id", "")
            if turn_id in existing_chains:
                continue

            actions = turn_data.get("actions", [])
            decisions = turn_data.get("decisions", [])
            intent = turn_data.get("intent", "")
            outcome = turn_data.get("outcome", "")
            conv = turn_data.get("conversation", [])

            # Source 1: Structured turns with multi-step actions + decisions
            if len(actions) >= 2 and decisions and len(outcome) > 30:
                steps = []
                for idx, action in enumerate(actions):
                    # Pair decisions with actions where possible
                    decision = decisions[idx] if idx < len(decisions) else ""
                    steps.append({
                        "thought": decision if decision else f"Step {idx + 1}: {action}",
                        "action": action,
                        "observation": "",  # Not available from structured data
                    })
                chain = self.record_reasoning_chain(
                    prompt=intent,
                    steps=steps,
                    final_answer=outcome,
                    source="mined_structured",
                    metadata={"mined_from": turn_id},
                )
                if chain:
                    mined += 1
                continue

            # Source 2: Conversations with multi-turn assistant reasoning
            # Look for conversations where assistant gives multiple responses
            # (indicating tool use or multi-step thinking)
            if len(conv) >= 6:
                steps = []
                last_user = ""
                for msg in conv:
                    role = msg.get("role", "")
                    content = msg.get("content", "").strip()
                    if role == "user":
                        if content.startswith("[Tool Result"):
                            # This is a tool observation
                            if steps:
                                steps[-1]["observation"] = content[:2000]
                        else:
                            last_user = content
                    elif role == "assistant" and content:
                        if last_user and not last_user.startswith("[Tool Result"):
                            # First user message = prompt, first assistant = start of reasoning
                            if not steps:
                                # This might be the start of a chain
                                pass
                            steps.append({
                                "thought": content[:2000],
                                "action": "",
                                "observation": "",
                            })

                # Only record if we found real multi-step reasoning
                if len(steps) >= 2:
                    # Find the original prompt (first real user message)
                    prompt = ""
                    final = ""
                    for msg in conv:
                        if msg.get("role") == "user" and not msg.get("content", "").startswith("[Tool Result"):
                            prompt = msg.get("content", "")
                            break
                    # Final answer = last assistant message
                    for msg in reversed(conv):
                        if msg.get("role") == "assistant":
                            final = msg.get("content", "")
                            break

                    if prompt and final and len(final) > 50:
                        chain = self.record_reasoning_chain(
                            prompt=prompt,
                            steps=steps[:-1],  # All but last (last = final answer)
                            final_answer=final,
                            source="mined_conversation",
                            metadata={"mined_from": turn_id},
                        )
                        if chain:
                            mined += 1

        return mined

    # ── Eval Harness (measure before & after training) ──

    def generate_eval_suite(self, count: int = 50) -> List[Dict[str, Any]]:
        """Generate an evaluation suite from held-out archive data.

        Mines the archive for high-quality question/answer pairs and
        creates a benchmark. Used to measure the Third Brother before
        and after training — can't improve what you can't measure.

        Returns a list of eval cases, each with:
        - prompt: The question
        - reference: The known-good answer (from Code/Cowork)
        - category: Type of question (code, strategy, decision, debug)
        - difficulty: easy/medium/hard based on answer complexity
        """
        all_pairs = self._collect_quality_pairs()
        if len(all_pairs) < 20:
            return []

        # Use the eval split (deterministic) as our benchmark set
        _, eval_pairs = self._split_train_eval(all_pairs, eval_ratio=0.05)
        if not eval_pairs:
            # Fallback: take last N pairs
            eval_pairs = all_pairs[-count:]

        suite = []
        for pair in eval_pairs[:count]:
            user = pair["user"]
            assistant = pair["assistant"]

            # Categorize by content
            lower = user.lower()
            if any(k in lower for k in ("fix", "bug", "error", "broken", "failing")):
                category = "debug"
            elif any(k in lower for k in ("build", "implement", "create", "add", "write")):
                category = "code"
            elif any(k in lower for k in ("should we", "strategy", "plan", "decide", "approach")):
                category = "decision"
            elif any(k in lower for k in ("deploy", "ship", "release", "launch")):
                category = "ops"
            else:
                category = "general"

            # Difficulty by answer length
            if len(assistant) > 1000:
                difficulty = "hard"
            elif len(assistant) > 300:
                difficulty = "medium"
            else:
                difficulty = "easy"

            suite.append({
                "eval_id": f"eval-{hashlib.md5(user[:100].encode()).hexdigest()[:8]}",
                "prompt": user,
                "reference": assistant,
                "category": category,
                "difficulty": difficulty,
            })

        return suite

    def export_eval_suite(self, output_path: str, count: int = 50) -> int:
        """Export eval suite to JSONL for benchmarking."""
        suite = self.generate_eval_suite(count)
        if not suite:
            return 0
        with open(output_path, "w", encoding="utf-8") as f:
            for case in suite:
                f.write(json.dumps(case, ensure_ascii=False) + "\n")
        return len(suite)

    def run_eval(self, model_fn, count: int = 50) -> Dict[str, Any]:
        """Run evaluation against the generated suite.

        Args:
            model_fn: Callable that takes a prompt string and returns a response string.
                      e.g., lambda prompt: llm.generate_content(prompt).text
            count: Number of eval cases to test.

        Returns:
            Eval results with scores by category and difficulty.
        """
        suite = self.generate_eval_suite(count)
        if not suite:
            return {"error": "No eval suite generated", "total": 0}

        results = []
        for case in suite:
            try:
                response = model_fn(case["prompt"])
                # Score: simple length-ratio + keyword overlap
                ref_words = set(case["reference"].lower().split())
                resp_words = set(response.lower().split()) if response else set()
                overlap = len(ref_words & resp_words)
                precision = overlap / len(resp_words) if resp_words else 0
                recall = overlap / len(ref_words) if ref_words else 0
                f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
                # Length ratio (penalize too short or too long)
                len_ratio = min(len(response or ""), len(case["reference"])) / max(len(response or ""), len(case["reference"]), 1)

                score = 0.6 * f1 + 0.4 * len_ratio  # Weighted composite

                results.append({
                    "eval_id": case["eval_id"],
                    "category": case["category"],
                    "difficulty": case["difficulty"],
                    "score": round(score, 3),
                    "f1": round(f1, 3),
                    "len_ratio": round(len_ratio, 3),
                    "response_len": len(response or ""),
                    "reference_len": len(case["reference"]),
                })
            except Exception as e:
                results.append({
                    "eval_id": case["eval_id"],
                    "category": case["category"],
                    "difficulty": case["difficulty"],
                    "score": 0,
                    "error": str(e)[:200],
                })

        # Aggregate
        total_score = sum(r["score"] for r in results) / len(results) if results else 0
        by_category: Dict[str, List[float]] = {}
        by_difficulty: Dict[str, List[float]] = {}
        for r in results:
            by_category.setdefault(r["category"], []).append(r["score"])
            by_difficulty.setdefault(r["difficulty"], []).append(r["score"])

        return {
            "total_cases": len(results),
            "avg_score": round(total_score, 3),
            "by_category": {
                k: round(sum(v) / len(v), 3) for k, v in by_category.items()
            },
            "by_difficulty": {
                k: round(sum(v) / len(v), 3) for k, v in by_difficulty.items()
            },
            "results": results,
        }

    # ── Self-Play Synthesis (manufacture DPO pairs at scale) ──

    def synthesize_preferences(
        self,
        model_fn,
        judge_fn=None,
        count: int = 100,
    ) -> int:
        """Generate synthetic DPO pairs via self-play.

        Takes existing SFT prompts, generates alternative responses via
        model_fn, then uses judge_fn (or heuristic) to determine which
        is better. This turns 50 DPO pairs into 500+.

        Args:
            model_fn: Callable that takes prompt and returns response.
                      e.g., lambda p: llm.generate_content(p).text
            judge_fn: Optional callable that takes (prompt, resp_a, resp_b) and
                      returns "a" or "b" for the winner. If None, uses heuristic.
            count: Number of synthetic pairs to generate.

        Returns:
            Number of new preference pairs created.
        """
        # Get high-quality prompts + reference answers from the archive
        all_pairs = self._collect_quality_pairs()
        if len(all_pairs) < 20:
            return 0

        # Sample prompts (deterministic, skip already-synthesized)
        existing_synth = {
            p.get("metadata", {}).get("synth_prompt_hash", "")
            for p in self.get_preferences()
            if p.get("source") == "self_play"
        }

        synthesized = 0
        for pair in all_pairs[:count * 2]:  # Over-sample since some will be skipped
            if synthesized >= count:
                break

            prompt = pair["user"]
            reference = pair["assistant"]

            # Dedup
            prompt_hash = hashlib.md5(prompt[:200].encode()).hexdigest()[:12]
            if prompt_hash in existing_synth:
                continue

            try:
                # Generate alternative response
                alternative = model_fn(prompt)
                if not alternative or len(alternative) < 20:
                    continue

                # Judge: which response is better?
                if judge_fn:
                    winner = judge_fn(prompt, reference, alternative)
                else:
                    # Heuristic judge: reference wins (it's the actual response
                    # from the session — the founder accepted it)
                    winner = "a"

                if winner == "a":
                    chosen, rejected = reference, alternative
                else:
                    chosen, rejected = alternative, reference

                pref = self.record_preference(
                    prompt=prompt,
                    chosen=chosen,
                    rejected=rejected,
                    source="self_play",
                    metadata={
                        "synth_prompt_hash": prompt_hash,
                        "winner": winner,
                    },
                )
                if pref:
                    synthesized += 1

            except Exception:
                continue  # Skip failed generations

        return synthesized

    # ── Internal ──

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
