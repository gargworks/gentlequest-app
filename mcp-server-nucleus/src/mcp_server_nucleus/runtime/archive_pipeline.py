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

    @staticmethod
    def _score_heuristic(response: str, reference: str) -> Dict[str, float]:
        """Offline heuristic scoring (no LLM needed). Fallback when no judge."""
        ref_words = set(reference.lower().split())
        resp_words = set(response.lower().split()) if response else set()
        overlap = len(ref_words & resp_words)
        precision = overlap / len(resp_words) if resp_words else 0
        recall = overlap / len(ref_words) if ref_words else 0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
        len_ratio = min(len(response or ""), len(reference)) / max(len(response or ""), len(reference), 1)
        score = 0.6 * f1 + 0.4 * len_ratio
        return {"score": round(score, 3), "f1": round(f1, 3), "len_ratio": round(len_ratio, 3),
                "method": "heuristic"}

    @staticmethod
    def _score_llm_judge(prompt: str, response: str, reference: str,
                         judge_fn) -> Dict[str, float]:
        """LLM-as-Judge scoring. Asks an LLM to rate 1-5 on correctness,
        helpfulness, and completeness. Returns normalized 0-1 score."""
        judge_prompt = f"""Rate this AI response on a scale of 1-5 for each criterion.

USER QUESTION:
{prompt[:1000]}

REFERENCE (known-good answer):
{reference[:1500]}

RESPONSE TO EVALUATE:
{response[:1500]}

CRITERIA (rate each 1-5):
1. Correctness: Is the response factually and technically accurate compared to the reference?
2. Helpfulness: Does it address what the user actually asked?
3. Completeness: Does it cover the key points from the reference?

Reply with ONLY three numbers separated by commas, like: 4,3,5"""

        try:
            verdict = judge_fn(judge_prompt).strip()
            # Parse "4,3,5" format
            nums = []
            for part in verdict.replace(" ", "").split(","):
                for ch in part:
                    if ch.isdigit():
                        nums.append(int(ch))
                        break
                if len(nums) >= 3:
                    break

            if len(nums) >= 3:
                # Weighted: correctness 40%, helpfulness 30%, completeness 30%
                raw = 0.4 * nums[0] + 0.3 * nums[1] + 0.3 * nums[2]
                score = round((raw - 1) / 4, 3)  # Normalize 1-5 → 0-1
                return {"score": score, "correctness": nums[0], "helpfulness": nums[1],
                        "completeness": nums[2], "method": "llm_judge"}
            else:
                # Couldn't parse — fall back
                return {"score": 0.5, "method": "llm_judge_parse_error"}
        except Exception:
            return {"score": 0.5, "method": "llm_judge_error"}

    def run_eval(self, model_fn, count: int = 50,
                 judge_fn=None) -> Dict[str, Any]:
        """Run evaluation against the generated suite.

        Args:
            model_fn: Callable that takes a prompt string and returns a response string.
                      e.g., lambda prompt: llm.generate_content(prompt).text
            count: Number of eval cases to test.
            judge_fn: Optional LLM judge for scoring. If provided, uses LLM-as-Judge
                      (accurate for code/decision tasks). If None, uses word-overlap
                      heuristic (fast, offline, good for relative comparison).

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

                if judge_fn:
                    score_data = self._score_llm_judge(
                        case["prompt"], response, case["reference"], judge_fn
                    )
                else:
                    score_data = self._score_heuristic(response, case["reference"])

                results.append({
                    "eval_id": case["eval_id"],
                    "category": case["category"],
                    "difficulty": case["difficulty"],
                    "response_len": len(response or ""),
                    "reference_len": len(case["reference"]),
                    **score_data,
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

        scoring_method = results[0].get("method", "heuristic") if results else "none"

        return {
            "total_cases": len(results),
            "avg_score": round(total_score, 3),
            "scoring_method": scoring_method,
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
                    # Heuristic: compare specificity + length. Reference has a
                    # slight home-field advantage (it was accepted in session).
                    ref_score = self._score_pair(prompt, reference)
                    alt_score = self._score_pair(prompt, alternative)
                    if alt_score > ref_score + 0.1:
                        winner = "b"  # Alternative is meaningfully better
                    else:
                        winner = "a"  # Reference wins ties

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

    # ── LLM-as-Judge (replace heuristic with actual quality evaluation) ──

    @staticmethod
    def build_judge_fn(judge_model_fn) -> callable:
        """Build a judge function that uses an LLM to evaluate response quality.

        The judge sees both responses (randomized order) and picks the better one.
        This is how Anthropic, OpenAI, and DeepSeek actually train — not heuristics.

        Args:
            judge_model_fn: Callable that takes a prompt and returns a response.

        Returns:
            A judge function compatible with synthesize_preferences(judge_fn=...).
        """
        def judge(prompt: str, resp_a: str, resp_b: str) -> str:
            # Randomize presentation order to eliminate position bias
            import random
            if random.random() < 0.5:
                first, second = resp_a, resp_b
                mapping = {"1": "a", "2": "b"}
            else:
                first, second = resp_b, resp_a
                mapping = {"1": "b", "2": "a"}

            judge_prompt = f"""You are an expert judge evaluating AI assistant responses.

TASK: Given a user prompt and two responses, decide which response is better.

USER PROMPT:
{prompt[:1500]}

RESPONSE 1:
{first[:2000]}

RESPONSE 2:
{second[:2000]}

CRITERIA:
- Correctness: Is the response factually and technically accurate?
- Helpfulness: Does it actually address what the user asked?
- Completeness: Does it cover the key points without being bloated?
- Clarity: Is it well-structured and easy to follow?

Reply with ONLY "1" or "2" (the number of the better response). If they are equal, reply "1"."""

            try:
                verdict = judge_model_fn(judge_prompt).strip()
                # Extract just the number
                for char in verdict:
                    if char in ("1", "2"):
                        return mapping[char]
                return "a"  # Default: reference wins
            except Exception:
                return "a"

        return judge

    # ── Iterative Self-Play / SPIN (use trained model against itself) ──

    def iterative_self_play(
        self,
        current_model_fn,
        base_model_fn,
        judge_fn=None,
        count: int = 100,
        round_num: int = 1,
    ) -> Dict[str, Any]:
        """SPIN-style iterative self-play: trained model vs base model.

        After training the Third Brother (round N), generate responses from both
        the trained model and the base model. Judge which is better. Create DPO
        pairs. Retrain (round N+1). This is the flywheel that DeepSeek R1 uses.

        REQUIRES judge_fn. Without a judge, SPIN creates DPO pairs where the
        trained model always "wins" — even on prompts where it's worse. This
        teaches the model that its mistakes are correct. Use build_judge_fn().

        Args:
            current_model_fn: The current (trained) model.
            base_model_fn: The base (pre-training) model.
            judge_fn: LLM judge (use build_judge_fn). REQUIRED.
            count: Number of comparisons to generate.
            round_num: Which iteration of self-play this is.

        Returns:
            Stats: {generated, current_wins, base_wins, ties, round}.
        """
        if not judge_fn:
            return {"error": "SPIN requires --judge. Without a judge, the trained model "
                             "always 'wins' — even when it's wrong. This teaches the model "
                             "that its mistakes are correct. Pass --judge <provider>.",
                    "generated": 0}

        all_pairs = self._collect_quality_pairs()
        if len(all_pairs) < 20:
            return {"error": "Not enough data", "generated": 0}

        existing_spin = {
            p.get("metadata", {}).get("spin_prompt_hash", "")
            for p in self.get_preferences()
            if p.get("source") == "spin" and
               p.get("metadata", {}).get("spin_round") == round_num
        }

        stats = {"generated": 0, "current_wins": 0, "base_wins": 0,
                 "ties": 0, "round": round_num}

        for pair in all_pairs[:count * 2]:
            if stats["generated"] >= count:
                break

            prompt = pair["user"]
            prompt_hash = hashlib.md5(
                (prompt[:200] + f"_r{round_num}").encode()
            ).hexdigest()[:12]
            if prompt_hash in existing_spin:
                continue

            try:
                current_resp = current_model_fn(prompt)
                base_resp = base_model_fn(prompt)
                if not current_resp or not base_resp:
                    continue
                if len(current_resp) < 20 or len(base_resp) < 20:
                    continue

                # Judge (guaranteed non-None — checked at top)
                winner = judge_fn(prompt, current_resp, base_resp)

                if winner == "a":
                    chosen, rejected = current_resp, base_resp
                    stats["current_wins"] += 1
                elif winner == "b":
                    chosen, rejected = base_resp, current_resp
                    stats["base_wins"] += 1
                else:
                    stats["ties"] += 1
                    continue

                pref = self.record_preference(
                    prompt=prompt,
                    chosen=chosen,
                    rejected=rejected,
                    source="spin",
                    metadata={
                        "spin_prompt_hash": prompt_hash,
                        "spin_round": round_num,
                        "winner": "current" if winner == "a" else "base",
                    },
                )
                if pref:
                    stats["generated"] += 1

            except Exception:
                continue

        return stats

    # ── Active Learning (target weakness, synthesize gap-filling data) ──

    def identify_weaknesses(self, eval_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze eval results to find where the model is weakest.

        Returns targeted prompts for gap-filling synthesis.

        Args:
            eval_results: Output from run_eval().

        Returns:
            List of weakness descriptors with target prompts.
        """
        weaknesses = []

        # Find weak categories (below average)
        avg = eval_results.get("avg_score", 0)
        for cat, score in eval_results.get("by_category", {}).items():
            if score < avg * 0.8:  # 20% below average
                weaknesses.append({
                    "type": "category",
                    "name": cat,
                    "score": score,
                    "gap": round(avg - score, 3),
                    "priority": "high" if score < avg * 0.5 else "medium",
                })

        # Find weak difficulties
        for diff, score in eval_results.get("by_difficulty", {}).items():
            if score < avg * 0.7:
                weaknesses.append({
                    "type": "difficulty",
                    "name": diff,
                    "score": score,
                    "gap": round(avg - score, 3),
                    "priority": "high",
                })

        # Find individual failures (score < 0.2)
        failed_cases = [
            r for r in eval_results.get("results", [])
            if r.get("score", 0) < 0.2
        ]
        if failed_cases:
            weaknesses.append({
                "type": "failures",
                "name": f"{len(failed_cases)} hard failures",
                "score": 0,
                "gap": avg,
                "priority": "critical",
                "eval_ids": [r["eval_id"] for r in failed_cases[:20]],
            })

        return sorted(weaknesses, key=lambda w: w["gap"], reverse=True)

    def synthesize_for_weaknesses(
        self,
        model_fn,
        eval_results: Dict[str, Any],
        count_per_weakness: int = 20,
    ) -> Dict[str, Any]:
        """Active learning: generate targeted training data for weak areas.

        Uses eval results to identify gaps, then generates prompts and
        reference answers specifically for those categories/difficulties.

        Args:
            model_fn: LLM to generate prompts and reference answers.
            eval_results: Output from run_eval().
            count_per_weakness: How many pairs to generate per weakness.

        Returns:
            Stats: {total_generated, by_weakness: [{name, generated}]}.
        """
        weaknesses = self.identify_weaknesses(eval_results)
        if not weaknesses:
            return {"total_generated": 0, "weaknesses_found": 0}

        # Category → prompt generation instructions
        CATEGORY_PROMPTS = {
            "debug": "Write a realistic debugging question about a {lang} application. "
                     "Include an error message or stack trace. Then provide the correct fix.",
            "code": "Write a realistic coding task: implement a function or feature in {lang}. "
                    "Then provide the correct, clean implementation.",
            "decision": "Write a realistic technical decision question (e.g., architecture, "
                        "tool choice, design pattern). Then provide a well-reasoned recommendation.",
            "ops": "Write a realistic DevOps/deployment question (CI/CD, Docker, cloud). "
                   "Then provide the correct procedure or fix.",
            "general": "Write a realistic software engineering question. "
                       "Then provide a helpful, accurate answer.",
        }
        LANGS = ["Python", "TypeScript", "Go", "Rust", "JavaScript"]

        stats = {"total_generated": 0, "weaknesses_found": len(weaknesses),
                 "by_weakness": []}

        for weakness in weaknesses[:5]:  # Top 5 weaknesses
            w_name = weakness["name"]
            generated = 0

            if weakness["type"] == "category" and w_name in CATEGORY_PROMPTS:
                template = CATEGORY_PROMPTS[w_name]
                for i in range(count_per_weakness):
                    lang = LANGS[i % len(LANGS)]
                    gen_prompt = (
                        f"{template.format(lang=lang)}\n\n"
                        f"Format your response as:\n"
                        f"QUESTION: <the question>\n"
                        f"ANSWER: <the answer>"
                    )
                    try:
                        raw = model_fn(gen_prompt)
                        if not raw or "QUESTION:" not in raw or "ANSWER:" not in raw:
                            continue
                        parts = raw.split("ANSWER:", 1)
                        question = parts[0].replace("QUESTION:", "").strip()
                        answer = parts[1].strip()
                        if len(question) < 20 or len(answer) < 50:
                            continue

                        # Record as a high-quality SFT turn
                        self.record_turn(
                            brother="synthesis",
                            intent=f"active_learning_{w_name}",
                            actions=[f"Generated {w_name} training pair"],
                            tools_used=["active_learning"],
                            decisions=[f"Target weakness: {w_name}"],
                            outcome="Synthetic training pair",
                            signal_absorbed=[],
                            signal_produced=[],
                            confidence=0.7,
                            context=f"Active learning for {w_name} (gap={weakness['gap']})",
                            conversation=[
                                {"role": "user", "content": question},
                                {"role": "assistant", "content": answer},
                            ],
                        )
                        generated += 1
                    except Exception:
                        continue

            elif weakness["type"] == "failures":
                # Re-generate better answers for failed eval cases
                suite = self.generate_eval_suite(100)
                failed_ids = set(weakness.get("eval_ids", []))
                for case in suite:
                    if case["eval_id"] not in failed_ids:
                        continue
                    if generated >= count_per_weakness:
                        break
                    try:
                        # Ask the model for a better answer
                        better_prompt = (
                            f"Give the best possible answer to this question. "
                            f"Be thorough, accurate, and well-structured.\n\n"
                            f"Question: {case['prompt']}"
                        )
                        better_answer = model_fn(better_prompt)
                        if not better_answer or len(better_answer) < 50:
                            continue

                        # Create SFT pair instead of DPO — we don't know for
                        # certain the model's answer is better than the reference.
                        # DPO with inverted preferences (marking real session data
                        # as "rejected") teaches the model to prefer slop over
                        # authentic answers. SFT is safer: "here's another example."
                        self.record_turn(
                            brother="synthesis",
                            intent=f"active_learning_{w_name}_regen",
                            actions=[f"Regenerated answer for failed eval {case['eval_id']}"],
                            tools_used=["active_learning"],
                            decisions=[f"Target weakness: {w_name}"],
                            outcome="Regenerated training pair",
                            signal_absorbed=[],
                            signal_produced=[],
                            confidence=0.6,
                            context=f"Active learning regen for {w_name}",
                            conversation=[
                                {"role": "user", "content": case["prompt"]},
                                {"role": "assistant", "content": better_answer},
                            ],
                        )
                        generated += 1
                    except Exception:
                        continue

            stats["by_weakness"].append({"name": w_name, "generated": generated})
            stats["total_generated"] += generated

        return stats

    # ── Training Conductor (full autonomous training loop) ──

    def training_status(self) -> Dict[str, Any]:
        """Comprehensive training readiness assessment.

        Returns a complete picture of where the training pipeline stands,
        what's ready, what's needed, and what the next action should be.
        """
        stats = self.get_stats()
        total_turns = stats.get("total_turns", 0)
        retrain = self.should_retrain()
        dpo_count = self.count_preferences()
        cot_count = self.count_reasoning_chains()
        cot_quality = sum(1 for c in self.get_reasoning_chains()
                         if self._is_quality_chain(c))

        # Count by source
        prefs = self.get_preferences()
        dpo_by_source: Dict[str, int] = {}
        for p in prefs:
            src = p.get("source", "unknown")
            dpo_by_source[src] = dpo_by_source.get(src, 0) + 1

        # Determine phases ready
        sft_ready = total_turns >= 50
        dpo_ready = dpo_count >= 20
        cot_ready = cot_quality >= 20
        eval_ready = total_turns >= 20

        # Check for existing eval results
        eval_results_path = self.training_dir / "eval_results.json"
        has_eval_baseline = eval_results_path.exists()
        baseline_score = None
        if has_eval_baseline:
            try:
                baseline = json.loads(eval_results_path.read_text())
                baseline_score = baseline.get("avg_score")
            except Exception:
                pass

        # Check trained marker
        trained_marker = self.training_dir / "last_train.json"
        last_trained = None
        trained_at_turns = 0
        if trained_marker.exists():
            try:
                marker = json.loads(trained_marker.read_text())
                last_trained = marker.get("timestamp")
                trained_at_turns = marker.get("total_turns", 0)
            except Exception:
                pass

        new_turns_since_train = total_turns - trained_at_turns

        # Determine next recommended action
        next_action = self._recommend_next_action(
            total_turns=total_turns,
            dpo_count=dpo_count,
            cot_quality=cot_quality,
            has_eval_baseline=has_eval_baseline,
            baseline_score=baseline_score,
            new_turns_since_train=new_turns_since_train,
            dpo_by_source=dpo_by_source,
        )

        return {
            "sft": {"turns": total_turns, "ready": sft_ready},
            "dpo": {"total": dpo_count, "by_source": dpo_by_source, "ready": dpo_ready},
            "cot": {"total": cot_count, "quality": cot_quality, "ready": cot_ready},
            "eval": {
                "ready": eval_ready,
                "has_baseline": has_eval_baseline,
                "baseline_score": baseline_score,
            },
            "training": {
                "last_trained": last_trained,
                "trained_at_turns": trained_at_turns,
                "new_since_train": new_turns_since_train,
                "should_retrain": retrain["should_retrain"],
            },
            "next_action": next_action,
        }

    def _recommend_next_action(
        self,
        total_turns: int,
        dpo_count: int,
        cot_quality: int,
        has_eval_baseline: bool,
        baseline_score: float,
        new_turns_since_train: int,
        dpo_by_source: Dict[str, int],
    ) -> Dict[str, Any]:
        """Decision engine: what should the training pipeline do next?

        This is the brain of the conductor — it looks at the current state
        and recommends the highest-impact next action.
        """
        synth_count = dpo_by_source.get("self_play", 0)
        spin_count = dpo_by_source.get("spin", 0)
        active_count = dpo_by_source.get("active_learning", 0)

        # Priority 1: Not enough data at all
        if total_turns < 50:
            return {
                "action": "accumulate",
                "reason": f"Need 50+ SFT turns (have {total_turns}). Keep using Nucleus.",
                "command": None,
                "priority": "low",
            }

        # Priority 2: Mine existing data
        if dpo_count < 20:
            return {
                "action": "mine",
                "reason": f"Need 20+ DPO pairs (have {dpo_count}). Mine from corrections.",
                "command": "nucleus archive mine",
                "priority": "high",
            }

        # Priority 3: No eval baseline yet (but don't block training if data is rich)
        if not has_eval_baseline and total_turns < 200:
            return {
                "action": "eval_baseline",
                "reason": "No eval baseline. Measure before training.",
                "command": "nucleus archive eval --run gemini",
                "priority": "high",
            }
        if not has_eval_baseline and total_turns >= 200:
            # Enough data to train — eval baseline against base model first is optional
            return {
                "action": "train",
                "reason": f"{total_turns} turns ready. Train first, then eval the result.",
                "command": "python scripts/train_third_brother.py --mine-first --register --auto-shadow",
                "priority": "critical",
            }

        # Priority 4: Not enough synthetic DPO
        if synth_count < 100 and dpo_count < 200:
            return {
                "action": "synthesize",
                "reason": f"Only {synth_count} synthetic DPO pairs. Need 100+ for strong alignment.",
                "command": "nucleus archive synthesize --judge gemini --count 200",
                "priority": "high",
            }

        # Priority 5: Ready to train (or retrain)
        if new_turns_since_train > 100 or (new_turns_since_train > 0 and not has_eval_baseline):
            return {
                "action": "train",
                "reason": f"{new_turns_since_train} new turns since last training. Time to retrain.",
                "command": "python scripts/train_third_brother.py --mine-first --register --auto-shadow",
                "priority": "critical",
            }

        # Priority 6: After training, run eval
        if has_eval_baseline and baseline_score and baseline_score < 0.5:
            return {
                "action": "active_learn",
                "reason": f"Baseline score {baseline_score} is low. Target weaknesses.",
                "command": "nucleus archive active-learn --eval-provider local --provider gemini",
                "priority": "high",
            }

        # Priority 7: SPIN (after first successful training)
        if spin_count == 0 and total_turns > 200:
            return {
                "action": "spin",
                "reason": "No SPIN rounds yet. Self-play iteration will compound quality.",
                "command": "nucleus archive spin --current local --base gemini --judge gemini",
                "priority": "medium",
            }

        # Priority 8: Active learning for refinement
        if active_count < 50:
            return {
                "action": "active_learn",
                "reason": f"Only {active_count} active learning pairs. Target more weaknesses.",
                "command": "nucleus archive active-learn --provider gemini",
                "priority": "medium",
            }

        # Steady state: keep accumulating
        return {
            "action": "accumulate",
            "reason": "Pipeline is healthy. Keep using Nucleus to accumulate more signal.",
            "command": None,
            "priority": "low",
        }

    def run_full_pipeline(
        self,
        model_fn=None,
        judge_fn=None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Run the full training pipeline end-to-end.

        This is the Training Conductor. It:
        1. Mines existing data (DPO + CoT)
        2. Synthesizes DPO pairs (if model_fn provided)
        3. Exports all training data
        4. Reports readiness for training

        Does NOT run actual training (that requires GPU/Ollama).
        Use dry_run=True to see what would happen without writing.

        Args:
            model_fn: LLM for synthesis. If None, skips synthesis.
            judge_fn: LLM judge for synthesis. If None, uses heuristic.
            dry_run: If True, only report what would happen.

        Returns:
            Pipeline execution report.
        """
        report = {
            "steps": [],
            "dry_run": dry_run,
        }

        # Step 1: Mine
        if not dry_run:
            mined_dpo = self.mine_preferences_from_archive()
            mined_cot = self.mine_reasoning_from_archive()
            report["steps"].append({
                "step": "mine",
                "mined_dpo": mined_dpo,
                "mined_cot": mined_cot,
            })
        else:
            report["steps"].append({"step": "mine", "status": "would mine"})

        # Step 2: Synthesize (if model available)
        if model_fn and not dry_run:
            synth_count = self.synthesize_preferences(
                model_fn=model_fn,
                judge_fn=judge_fn,
                count=200,
            )
            report["steps"].append({
                "step": "synthesize",
                "new_pairs": synth_count,
            })
        elif model_fn:
            report["steps"].append({"step": "synthesize", "status": "would synthesize 200"})
        else:
            report["steps"].append({"step": "synthesize", "status": "skipped (no model_fn)"})

        # Step 3: Export all training data
        out_dir = self.training_dir / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)

        if not dry_run:
            sft_count = self.export_openai(
                str(out_dir / "sft_training.jsonl"),
            )
            dpo_count = self.export_dpo(
                str(out_dir / "dpo_training.jsonl"),
            )
            cot_count = self.export_reasoning(
                str(out_dir / "cot_training.jsonl"),
            )
            eval_count = self.export_eval_suite(
                str(out_dir / "eval_suite.jsonl"),
            )
            report["steps"].append({
                "step": "export",
                "sft_pairs": sft_count,
                "dpo_pairs": dpo_count,
                "cot_chains": cot_count,
                "eval_cases": eval_count,
                "output_dir": str(out_dir),
            })
        else:
            report["steps"].append({"step": "export", "status": "would export to " + str(out_dir)})

        # Step 4: Training readiness
        status = self.training_status()
        report["status"] = status
        report["next_action"] = status["next_action"]

        return report

    # ── Constitutional AI / RLAIF (self-critique → self-revision → DPO) ──

    CONSTITUTION = [
        "Is the response technically accurate? If not, what is wrong?",
        "Does the response directly address what the user asked, or does it go off-topic?",
        "Is the response complete without being unnecessarily verbose?",
        "Does the response follow coding best practices (if code is involved)?",
        "Would a senior engineer approve this response, or would they send it back?",
    ]

    def constitutional_revise(
        self,
        model_fn,
        count: int = 100,
        principles: Optional[List[str]] = None,
    ) -> int:
        """Constitutional AI: self-critique and self-revision to create DPO pairs.

        For each archive turn:
        1. Take the original assistant response
        2. Ask the model to critique it against constitutional principles
        3. Ask the model to revise the response based on the critique
        4. Record (prompt, revised, original) as a DPO pair

        This is how Anthropic trains Claude — no human labelers needed.

        Args:
            model_fn: LLM for critique and revision.
            count: Number of turns to process.
            principles: Custom principles (default: built-in CONSTITUTION).

        Returns:
            Number of new DPO pairs created.
        """
        rules = principles or self.CONSTITUTION
        all_pairs = self._collect_quality_pairs()
        if len(all_pairs) < 20:
            return 0

        existing_constitutional = {
            p.get("metadata", {}).get("constitutional_hash", "")
            for p in self.get_preferences()
            if p.get("source") == "constitutional"
        }

        created = 0
        for pair in all_pairs[:count * 2]:
            if created >= count:
                break

            prompt = pair["user"]
            original = pair["assistant"]
            pair_hash = hashlib.md5(
                (prompt[:100] + original[:100]).encode()
            ).hexdigest()[:12]

            if pair_hash in existing_constitutional:
                continue

            try:
                # Step 1: Critique
                critique_prompt = (
                    f"You are a strict code reviewer. Critique this AI response.\n\n"
                    f"USER QUESTION:\n{prompt[:1500]}\n\n"
                    f"AI RESPONSE:\n{original[:2000]}\n\n"
                    f"EVALUATE AGAINST THESE PRINCIPLES:\n"
                )
                for i, rule in enumerate(rules, 1):
                    critique_prompt += f"{i}. {rule}\n"
                critique_prompt += (
                    "\nList specific issues found. If the response is already "
                    "excellent, say 'NO ISSUES FOUND'."
                )

                critique = model_fn(critique_prompt)
                if not critique:
                    continue

                # If no issues, skip (response is already good)
                if "NO ISSUES FOUND" in critique.upper():
                    continue

                # Step 2: Revise
                revise_prompt = (
                    f"Revise this AI response to fix the issues identified.\n\n"
                    f"USER QUESTION:\n{prompt[:1500]}\n\n"
                    f"ORIGINAL RESPONSE:\n{original[:2000]}\n\n"
                    f"CRITIQUE:\n{critique[:1500]}\n\n"
                    f"Write the REVISED response only. Do not include the critique."
                )

                revised = model_fn(revise_prompt)
                if not revised or len(revised) < 30:
                    continue

                # Skip if revision is too similar (no real improvement)
                orig_words = set(original.lower().split())
                rev_words = set(revised.lower().split())
                if orig_words and rev_words:
                    jaccard = len(orig_words & rev_words) / len(orig_words | rev_words)
                    if jaccard > 0.95:  # Too similar — revision didn't change much
                        continue

                # Step 3: Record DPO pair (revised is chosen, original is rejected)
                pref = self.record_preference(
                    prompt=prompt,
                    chosen=revised,
                    rejected=original,
                    source="constitutional",
                    metadata={
                        "constitutional_hash": pair_hash,
                        "critique_summary": critique[:500],
                        "principles_used": len(rules),
                    },
                )
                if pref:
                    created += 1

            except Exception:
                continue

        return created

    # ── Data Quality Scoring (auto-score and filter training data) ──

    def score_training_data(self) -> Dict[str, Any]:
        """Score every training example on quality dimensions.

        Returns aggregate quality stats and identifies low-quality data
        that should be filtered before training.

        Scoring dimensions:
        - length: Reasonable length (not too short, not bloated)
        - specificity: Contains concrete details, not vague
        - diversity: Low overlap with other examples (dedup signal)
        - completeness: Both sides of the conversation are substantive
        """
        all_pairs = self._collect_quality_pairs()
        if not all_pairs:
            return {"total": 0, "scored": 0}

        scored = []
        all_prompts_words = []

        for pair in all_pairs:
            user = pair["user"]
            assistant = pair["assistant"]
            quality = round(self._score_pair(user, assistant), 3)

            scored.append({
                "prompt_preview": user[:80],
                "quality": quality,
                "user_len": len(user),
                "assistant_len": len(assistant),
            })
            all_prompts_words.append(set(user.lower().split()))

        # Diversity pass: penalize near-duplicates
        for i, item in enumerate(scored):
            if i == 0:
                item["diversity_score"] = 1.0
                continue
            max_overlap = 0.0
            words_i = all_prompts_words[i]
            for j in range(max(0, i - 50), i):  # Check last 50 neighbors
                words_j = all_prompts_words[j]
                if words_i and words_j:
                    overlap = len(words_i & words_j) / max(len(words_i | words_j), 1)
                    max_overlap = max(max_overlap, overlap)
            item["diversity_score"] = round(1.0 - max_overlap, 2)
            # Blend diversity into the base quality score (20% weight)
            base = item["quality"]
            item["quality"] = round(
                0.80 * base + 0.20 * item["diversity_score"],
                3,
            )

        # Aggregate
        qualities = [s["quality"] for s in scored]
        avg_quality = sum(qualities) / len(qualities) if qualities else 0
        high_quality = sum(1 for q in qualities if q >= 0.6)
        low_quality = sum(1 for q in qualities if q < 0.3)

        return {
            "total": len(scored),
            "avg_quality": round(avg_quality, 3),
            "high_quality": high_quality,
            "low_quality": low_quality,
            "quality_distribution": {
                "excellent": sum(1 for q in qualities if q >= 0.8),
                "good": sum(1 for q in qualities if 0.6 <= q < 0.8),
                "fair": sum(1 for q in qualities if 0.3 <= q < 0.6),
                "poor": sum(1 for q in qualities if q < 0.3),
            },
            "worst_5": sorted(scored, key=lambda s: s["quality"])[:5],
        }

    def export_filtered(
        self,
        output_path: str,
        min_quality: float = 0.4,
        format: str = "openai",
        curriculum: bool = False,
    ) -> Dict[str, int]:
        """Export only training data above a quality threshold.

        Args:
            output_path: Path for filtered export.
            min_quality: Minimum quality score (0-1). Default 0.4.
            format: Export format (openai/gemini/anthropic).
            curriculum: If True, sort easy→hard for curriculum learning.

        Returns:
            {total, exported, filtered_out, eval_excluded, snapshot}.
        """
        all_pairs = self._collect_quality_pairs()
        if not all_pairs:
            return {"total": 0, "exported": 0, "filtered_out": 0,
                    "eval_excluded": 0}

        # Contamination firewall: exclude eval prompts from training
        eval_hashes = self._get_eval_prompt_hashes()
        clean_pairs = []
        eval_excluded = 0
        for pair in all_pairs:
            h = hashlib.md5(pair["user"][:100].encode()).hexdigest()[:8]
            if f"eval-{h}" in eval_hashes:
                eval_excluded += 1
            else:
                clean_pairs.append(pair)

        # Score using same formula as score_training_data
        scored_items = [(pair, self._score_pair(pair["user"], pair["assistant"]))
                        for pair in clean_pairs]

        # Filter by quality
        passed = [(p, q) for p, q in scored_items if q >= min_quality]
        filtered_out = len(scored_items) - len(passed)

        # Curriculum ordering: easy→hard (short answers first, then longer)
        if curriculum:
            passed.sort(key=lambda x: len(x[0]["assistant"]))

        # System prompt for identity (matches export_openai)
        sys_msg = (
            "You are the Third Brother — a trained intelligence that emerged from "
            "thousands of decision cycles between two AI agents (Code and Cowork) "
            "coordinating through a shared brain."
        )

        with open(output_path, "w", encoding="utf-8") as f:
            for pair, _ in passed:
                if format == "openai":
                    entry = {"messages": [
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": pair["user"]},
                        {"role": "assistant", "content": pair["assistant"]},
                    ]}
                elif format == "gemini":
                    entry = {"contents": [
                        {"role": "user", "parts": [{"text": pair["user"]}]},
                        {"role": "model", "parts": [{"text": pair["assistant"]}]},
                    ]}
                else:
                    entry = {"messages": [
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": pair["user"]},
                        {"role": "assistant", "content": pair["assistant"]},
                    ]}
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        # Snapshot: save a manifest of what went into this export
        snapshot = self._save_export_snapshot(
            output_path, len(passed), eval_excluded, filtered_out,
            min_quality, format, curriculum
        )

        return {
            "total": len(all_pairs),
            "exported": len(passed),
            "filtered_out": filtered_out,
            "eval_excluded": eval_excluded,
            "min_quality": min_quality,
            "curriculum": curriculum,
            "snapshot": snapshot,
        }

    def _get_eval_prompt_hashes(self) -> set:
        """Get eval_id hashes for contamination checking.

        Returns the set of eval_ids from the most recent eval suite.
        These prompts must never appear in training data.
        """
        eval_hashes = set()
        # Check exported eval files
        exports_dir = self.training_dir / "exports"
        if exports_dir.exists():
            for f in exports_dir.iterdir():
                if "eval" in f.name and f.suffix == ".jsonl":
                    try:
                        for line in f.read_text().strip().split("\n"):
                            if line.strip():
                                entry = json.loads(line)
                                eid = entry.get("eval_id", "")
                                if eid:
                                    eval_hashes.add(eid)
                    except (json.JSONDecodeError, OSError):
                        continue
        # Also generate fresh from current data (covers case where no export exists)
        if not eval_hashes:
            suite = self.generate_eval_suite(100)
            eval_hashes = {case["eval_id"] for case in suite}
        return eval_hashes

    def _save_export_snapshot(
        self, output_path: str, exported: int, eval_excluded: int,
        filtered_out: int, min_quality: float, format: str, curriculum: bool,
    ) -> str:
        """Save a snapshot manifest for reproducibility.

        Records exactly what data went into an export so any training
        run can be traced back to its exact inputs.
        """
        snapshots_dir = self.training_dir / "snapshots"
        snapshots_dir.mkdir(parents=True, exist_ok=True)

        # Snapshot ID: timestamp-based
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        snap_id = f"snap_{ts}"
        snap_path = snapshots_dir / f"{snap_id}.json"

        # Compute content hash of the exported file for integrity
        content_hash = ""
        try:
            import hashlib as _hl
            h = _hl.sha256()
            with open(output_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            content_hash = h.hexdigest()[:16]
        except OSError:
            pass

        manifest = {
            "snapshot_id": snap_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "output_path": str(output_path),
            "format": format,
            "exported_pairs": exported,
            "eval_excluded": eval_excluded,
            "quality_filtered_out": filtered_out,
            "min_quality": min_quality,
            "curriculum": curriculum,
            "content_hash": content_hash,
            "archive_stats": self.get_stats(),
        }

        snap_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        return snap_id

    # ── Model Registry (version tracking + lineage) ──

    def register_model(
        self,
        version: str,
        base_model: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Register a new model version in the registry.

        Called after training. Records what data went in, what params were used,
        so you can trace any model version back to its exact training run.

        Args:
            version: Version string (e.g., "v1", "v2.1").
            base_model: Base model used (e.g., "llama3.2:3b", "qwen2.5:7b").
            params: Training params (epochs, lr, batch_size, etc.).

        Returns:
            The registered model entry.
        """
        registry_path = self.training_dir / "model_registry.jsonl"
        registry_path.parent.mkdir(parents=True, exist_ok=True)

        stats = self.get_stats()
        entry = {
            "version": version,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "base_model": base_model,
            "params": params or {},
            "data": {
                "sft_turns": stats.get("total_turns", 0),
                "dpo_pairs": self.count_preferences(),
                "cot_chains": self.count_reasoning_chains(),
            },
            "eval_scores": {},  # Filled in after eval
            "status": "registered",  # registered → shadow → canary → primary → retired
            "promoted_at": None,
            "retired_at": None,
        }

        with open(registry_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return entry

    def get_registry(self) -> List[Dict[str, Any]]:
        """Get all registered model versions."""
        registry_path = self.training_dir / "model_registry.jsonl"
        if not registry_path.exists():
            return []
        entries = []
        for line in registry_path.read_text().strip().split("\n"):
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries

    def update_model_status(
        self,
        version: str,
        status: str,
        eval_scores: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update a model's status in the registry.

        Args:
            version: Version to update.
            status: New status (shadow/canary/primary/retired).
            eval_scores: Optional eval results to attach.

        Returns:
            True if updated, False if version not found.
        """
        registry = self.get_registry()
        updated = False
        for entry in registry:
            if entry["version"] == version:
                entry["status"] = status
                if status in ("canary", "primary"):
                    entry["promoted_at"] = datetime.now(timezone.utc).isoformat()
                elif status == "retired":
                    entry["retired_at"] = datetime.now(timezone.utc).isoformat()
                if eval_scores:
                    entry["eval_scores"] = eval_scores
                updated = True
                break

        if updated:
            registry_path = self.training_dir / "model_registry.jsonl"
            with open(registry_path, "w", encoding="utf-8") as f:
                for entry in registry:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return updated

    def get_active_model(self) -> Optional[Dict[str, Any]]:
        """Get the currently active (primary or canary) model version."""
        registry = self.get_registry()
        # Prefer primary, fallback to canary
        for status in ("primary", "canary", "shadow"):
            for entry in reversed(registry):
                if entry.get("status") == status:
                    return entry
        return None

    # ── Shadow Mode (parallel inference for free DPO pairs) ──

    def shadow_compare(
        self,
        prompt: str,
        primary_response: str,
        shadow_fn,
        judge_fn=None,
    ) -> Optional[Dict[str, Any]]:
        """Run shadow inference and compare with primary response.

        Called during live chat: the primary LLM serves the user,
        the shadow (Third Brother) generates in parallel. The comparison
        becomes a DPO pair — free training data from production.

        Args:
            prompt: The user's prompt.
            primary_response: What the primary LLM returned.
            shadow_fn: Shadow model callable (e.g., Third Brother via Ollama).
            judge_fn: Optional LLM judge. If None, primary always wins.

        Returns:
            Comparison result, or None if shadow failed.
        """
        try:
            shadow_response = shadow_fn(prompt)
            if not shadow_response or len(shadow_response) < 20:
                return None

            # Judge
            if judge_fn:
                winner = judge_fn(prompt, primary_response, shadow_response)
                judged = True
            else:
                winner = "a"  # Primary (the one the user saw) wins by default
                judged = False

            if winner == "a":
                chosen, rejected = primary_response, shadow_response
                shadow_won = False
            else:
                chosen, rejected = shadow_response, primary_response
                shadow_won = True

            # Record as DPO pair
            pref = self.record_preference(
                prompt=prompt,
                chosen=chosen,
                rejected=rejected,
                source="shadow",
                metadata={
                    "shadow_won": shadow_won,
                    "primary_len": len(primary_response),
                    "shadow_len": len(shadow_response),
                    "judged": judged,
                },
            )

            return {
                "shadow_won": shadow_won,
                "pref_id": pref.get("pref_id") if pref else None,
                "primary_len": len(primary_response),
                "shadow_len": len(shadow_response),
            }

        except Exception:
            return None

    def get_shadow_stats(self, since: Optional[str] = None) -> Dict[str, Any]:
        """Get shadow mode performance statistics.

        Args:
            since: ISO timestamp. Only count comparisons after this time.
                   Used by graduation_check to isolate canary-phase stats.
        """
        prefs = self.get_preferences()
        shadow_prefs = [p for p in prefs if p.get("source") == "shadow"]
        if since:
            shadow_prefs = [p for p in shadow_prefs if p.get("timestamp", "") >= since]
        if not shadow_prefs:
            return {"total": 0, "shadow_wins": 0, "primary_wins": 0, "win_rate": 0}

        shadow_wins = sum(
            1 for p in shadow_prefs
            if p.get("metadata", {}).get("shadow_won", False)
        )
        primary_wins = len(shadow_prefs) - shadow_wins

        return {
            "total": len(shadow_prefs),
            "shadow_wins": shadow_wins,
            "primary_wins": primary_wins,
            "win_rate": round(shadow_wins / len(shadow_prefs), 3) if shadow_prefs else 0,
        }

    # ── Graduation Protocol (Shadow → Canary → Primary) ──

    def graduation_check(self, min_shadow_comparisons: int = 50,
                         min_win_rate: float = 0.3,
                         canary_win_rate: float = 0.5) -> Dict[str, Any]:
        """Check if the Third Brother should be promoted.

        Graduation ladder:
        1. Shadow → Canary: After min_shadow_comparisons with win_rate >= min_win_rate
        2. Canary → Primary: After canary phase shows win_rate >= canary_win_rate

        Args:
            min_shadow_comparisons: Minimum shadow comparisons before canary (default: 50).
            min_win_rate: Minimum shadow win rate for canary promotion (default: 0.3).
            canary_win_rate: Win rate required for primary promotion (default: 0.5).

        Returns:
            Graduation recommendation.
        """
        active_model = self.get_active_model()
        current_status = active_model.get("status", "registered") if active_model else "none"
        # For canary phase, only count stats since promotion to canary
        promoted_at = active_model.get("promoted_at") if active_model else None
        shadow_stats = self.get_shadow_stats(
            since=promoted_at if current_status == "canary" else None
        )

        result = {
            "current_status": current_status,
            "shadow_stats": shadow_stats,
            "recommendation": "hold",
            "reason": "",
        }

        if current_status == "none" or current_status == "registered":
            result["recommendation"] = "start_shadow"
            result["reason"] = "No active model. Deploy to shadow mode first."
            return result

        # Regression gate: block any promotion if eval scores dropped
        regression = self.regression_check(
            active_model.get("version") if active_model else None
        )
        result["regression"] = regression
        if regression["regressed"]:
            result["recommendation"] = "blocked_regression"
            result["reason"] = (
                f"BLOCKED: {regression['details']} "
                f"Fix the regression before promoting."
            )
            return result

        if current_status == "shadow":
            if shadow_stats["total"] < min_shadow_comparisons:
                result["recommendation"] = "hold"
                result["reason"] = (
                    f"Need {min_shadow_comparisons} shadow comparisons "
                    f"(have {shadow_stats['total']}). Keep accumulating."
                )
            elif shadow_stats["win_rate"] >= min_win_rate:
                result["recommendation"] = "promote_canary"
                result["reason"] = (
                    f"Shadow win rate {shadow_stats['win_rate']:.1%} >= "
                    f"{min_win_rate:.0%} threshold. Ready for canary."
                )
            else:
                result["recommendation"] = "retrain"
                result["reason"] = (
                    f"Shadow win rate {shadow_stats['win_rate']:.1%} < "
                    f"{min_win_rate:.0%}. Needs more training."
                )
            return result

        if current_status == "canary":
            # In canary, shadow stats represent canary performance
            if shadow_stats["win_rate"] >= canary_win_rate:
                result["recommendation"] = "promote_primary"
                result["reason"] = (
                    f"Canary win rate {shadow_stats['win_rate']:.1%} >= "
                    f"{canary_win_rate:.0%}. Ready for primary!"
                )
            else:
                result["recommendation"] = "hold"
                result["reason"] = (
                    f"Canary win rate {shadow_stats['win_rate']:.1%} < "
                    f"{canary_win_rate:.0%}. Needs improvement."
                )
            return result

        if current_status == "primary":
            result["recommendation"] = "monitor"
            result["reason"] = "Model is primary. Monitor for regression."
            return result

        return result

    # ── Regression Gate (block promotion if model got worse) ──

    def regression_check(self, version: Optional[str] = None) -> Dict[str, Any]:
        """Compare a model's eval scores against the previous version.

        If the new version scored lower than the previous, this is a regression
        and graduation should be blocked.

        Args:
            version: Version to check. If None, checks the most recent.

        Returns:
            {regressed: bool, delta: float, current: {...}, previous: {...}, details: str}
        """
        registry = self.get_registry()
        if len(registry) < 2:
            return {"regressed": False, "delta": 0,
                    "details": "Not enough model versions to compare."}

        # Find current and previous
        if version:
            current = next((e for e in registry if e["version"] == version), None)
            if not current:
                return {"regressed": False, "delta": 0,
                        "details": f"Version {version} not found in registry."}
            # Previous = the one registered right before this version
            idx = next((i for i, e in enumerate(registry) if e["version"] == version), -1)
            previous = registry[idx - 1] if idx > 0 else None
        else:
            current = registry[-1]
            previous = registry[-2]

        if not previous:
            return {"regressed": False, "delta": 0,
                    "details": "No previous version to compare against."}

        cur_scores = current.get("eval_scores", {})
        prev_scores = previous.get("eval_scores", {})

        if not cur_scores or not prev_scores:
            missing = []
            if not cur_scores:
                missing.append(f"{current['version']} (current)")
            if not prev_scores:
                missing.append(f"{previous['version']} (previous)")
            return {"regressed": False, "delta": 0,
                    "details": f"Missing eval scores for: {', '.join(missing)}. "
                               f"Run eval before checking regression."}

        cur_avg = cur_scores.get("avg_score", 0)
        prev_avg = prev_scores.get("avg_score", 0)
        delta = round(cur_avg - prev_avg, 3)
        regressed = delta < -0.02  # Allow 2% noise margin

        # Per-category regression check
        category_regressions = []
        cur_cats = cur_scores.get("by_category", {})
        prev_cats = prev_scores.get("by_category", {})
        for cat in set(cur_cats) | set(prev_cats):
            c = cur_cats.get(cat, 0)
            p = prev_cats.get(cat, 0)
            if p > 0 and c < p - 0.05:  # 5% category-level threshold
                category_regressions.append(
                    f"{cat}: {p:.3f} → {c:.3f} ({c - p:+.3f})"
                )

        if regressed:
            details = (f"REGRESSION: {previous['version']} ({prev_avg:.3f}) → "
                       f"{current['version']} ({cur_avg:.3f}), delta={delta:+.3f}")
        elif category_regressions:
            details = (f"Overall OK (delta={delta:+.3f}) but category regressions: "
                       + "; ".join(category_regressions))
        else:
            details = (f"No regression: {previous['version']} ({prev_avg:.3f}) → "
                       f"{current['version']} ({cur_avg:.3f}), delta={delta:+.3f}")

        return {
            "regressed": regressed,
            "delta": delta,
            "current": {"version": current["version"], "avg_score": cur_avg},
            "previous": {"version": previous["version"], "avg_score": prev_avg},
            "category_regressions": category_regressions,
            "details": details,
        }

    # ── Internal ──

    @staticmethod
    def _score_pair(user: str, assistant: str) -> float:
        """Score a single training pair on quality. Used by both
        score_training_data() and export_filtered() for consistency."""
        u_len, a_len = len(user), len(assistant)

        # Length score
        if 20 <= u_len <= 2000 and 50 <= a_len <= 5000:
            length_score = 1.0
        elif u_len < 10 or a_len < 20:
            length_score = 0.1
        else:
            length_score = 0.5

        # Specificity (concrete tokens)
        specific = sum(1 for w in assistant.split()
                       if any(c in w for c in "/.(){}[]0123456789_"))
        total = len(assistant.split()) or 1
        specificity_score = min(specific / total * 5, 1.0)

        # Completeness
        if u_len > 30 and a_len > 100:
            completeness_score = 1.0
        elif u_len > 15 and a_len > 50:
            completeness_score = 0.7
        else:
            completeness_score = 0.3

        return 0.3 * length_score + 0.4 * specificity_score + 0.3 * completeness_score

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
