"""
Nucleus Context Distillation Engine
====================================
Implements the Sovereign Context Recombination Protocol (SCRP) MVE.

Extracts Deterministic Context Atoms (DCAs) from AI assistant
conversation artifacts and stores them as structured JSON-LD
in the Decision System of Record (DSoR).

DCA Schema v1:
    @context: "https://nucleus.dev/dca/v1"
    @type: "DecisionAtom"
    decision: str          - What was decided
    rationale: str         - Why it was decided
    evidence: list[str]    - Supporting evidence
    alternatives: list[str] - Considered alternatives
    confidence: float      - 0.0-1.0
    source_tool: str       - Origin IDE/tool
    source_session: str    - Session/conversation ID
    timestamp: str         - ISO 8601
    tags: list[str]        - Semantic categories
    sha256: str            - Content hash for dedup

This module is the "Distillator" agent referenced in the SCRP
Design Thinking protocol (Stages 2-8, Claims C11-C31).
"""

import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


# ============================================================================
# DCA SCHEMA V1 (JSON-LD)
# ============================================================================

DCA_CONTEXT = "https://nucleusos.dev/dca/v1"
DCA_TYPE = "DecisionAtom"
VIBE_TYPE = "VibeEngram"

DCA_SCHEMA = {
    "@context": DCA_CONTEXT,
    "@type": DCA_TYPE,
    "required": ["decision", "rationale", "source_tool", "source_session", "timestamp"],
    "properties": {
        "decision": {"type": "string", "description": "What was decided"},
        "rationale": {"type": "string", "description": "Why it was decided"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "alternatives": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "source_tool": {"type": "string"},
        "source_session": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "sha256": {"type": "string"}
    }
}


class DecisionAtom:
    """A single Deterministic Context Atom (DCA) — the fundamental unit of SCRP."""

    def __init__(
        self,
        decision: str,
        rationale: str,
        source_tool: str,
        source_session: str,
        evidence: Optional[List[str]] = None,
        alternatives: Optional[List[str]] = None,
        confidence: float = 0.8,
        tags: Optional[List[str]] = None,
        timestamp: Optional[str] = None,
    ):
        """Initialize a DecisionAtom.

        Args:
            decision (str): What was decided.
            rationale (str): Why it was decided.
            source_tool (str): Origin IDE/tool (e.g., "antigravity", "claude").
            source_session (str): Session/conversation ID.
            evidence (Optional[List[str]]): Supporting evidence.
            alternatives (Optional[List[str]]): Considered alternatives.
            confidence (float): Confidence score 0.0-1.0. Default 0.8.
            tags (Optional[List[str]]): Semantic categories.
            timestamp (Optional[str]): ISO 8601 timestamp. Defaults to now.
        """
        self.decision = decision
        self.rationale = rationale
        self.source_tool = source_tool
        self.source_session = source_session
        self.evidence = evidence or []
        self.alternatives = alternatives or []
        self.confidence = confidence
        self.tags = tags or []
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.sha256 = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute content-addressable hash for deduplication.

        Returns:
            str: First 16 characters of SHA256 hash of decision+rationale+source.
        """
        content = f"{self.decision}|{self.rationale}|{self.source_tool}|{self.source_session}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def to_jsonld(self) -> Dict[str, Any]:
        """Serialize to JSON-LD format.

        Returns:
            Dict[str, Any]: JSON-LD object with @context, @type, and all fields.
        """
        return {
            "@context": DCA_CONTEXT,
            "@type": DCA_TYPE,
            "decision": self.decision,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "alternatives": self.alternatives,
            "confidence": self.confidence,
            "source_tool": self.source_tool,
            "source_session": self.source_session,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "sha256": self.sha256,
        }

    def to_adr(self) -> str:
        """Auto-generate a human-readable Architecture Decision Record (C28).

        Returns:
            str: Markdown-formatted ADR with context, evidence, and alternatives.
        """
        adr = [
            f"# ADR: {self.decision[:80]}",
            f"\n**Date**: {self.timestamp[:10]}",
            f"**Status**: Accepted (Confidence: {self.confidence:.0%})",
            f"**Source**: {self.source_tool} ({self.source_session[:12]}...)",
            f"\n## Context\n{self.rationale}",
        ]
        if self.evidence:
            adr.append("\n## Evidence")
            for e in self.evidence:
                adr.append(f"- {e}")
        if self.alternatives:
            adr.append("\n## Alternatives Considered")
            for a in self.alternatives:
                adr.append(f"- {a}")
        if self.tags:
            adr.append(f"\n**Tags**: {', '.join(self.tags)}")
        return "\n".join(adr)


class VibeEngram:
    """
    A Latent Vibe Engram — captures personality/style consistency (C07).
    Few-shot examples of the user's communication style.
    """

    def __init__(
        self,
        patterns: List[str],
        tone: str,
        vocabulary: List[str],
        source_tool: str,
        source_session: str,
    ):
        """Initialize a VibeEngram.

        Args:
            patterns (List[str]): Communication patterns detected.
            tone (str): Dominant tone (e.g., "formal", "casual").
            vocabulary (List[str]): Characteristic vocabulary.
            source_tool (str): Origin IDE/tool.
            source_session (str): Session/conversation ID.
        """
        self.patterns = patterns
        self.tone = tone
        self.vocabulary = vocabulary
        self.source_tool = source_tool
        self.source_session = source_session
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_jsonld(self) -> Dict[str, Any]:
        """Serialize VibeEngram to JSON-LD format.

        Returns:
            Dict[str, Any]: JSON-LD object with @context, @type, and vibe fields.
        """
        return {
            "@context": DCA_CONTEXT,
            "@type": VIBE_TYPE,
            "patterns": self.patterns,
            "tone": self.tone,
            "vocabulary": self.vocabulary,
            "source_tool": self.source_tool,
            "source_session": self.source_session,
            "timestamp": self.timestamp,
        }


# ============================================================================
# PATTERN EXTRACTORS — Signal detection in raw artifacts
# ============================================================================

# Regex patterns for detecting decisions in Antigravity/IDE artifacts
DECISION_PATTERNS = [
    # Implementation plan sections
    re.compile(r"##\s*(?:Proposed )?Changes?\s*\n([\s\S]*?)(?=\n##|\Z)", re.IGNORECASE),
    # Design decisions
    re.compile(r"\*\*(?:Decision|Design Decision|ADR)\*\*:?\s*(.+?)(?:\n|$)", re.IGNORECASE),
    # User review items
    re.compile(r">\s*\[!(?:IMPORTANT|WARNING|CAUTION)\]\s*\n>\s*(.+?)(?:\n|$)", re.IGNORECASE),
    # Task completions with context
    re.compile(r"- \[x\]\s+(.+?)(?:\n|$)"),
    # Key architectural notes
    re.compile(r"\*\*(?:Key|Critical|Architecture|Schema)\*\*:?\s*(.+?)(?:\n|$)", re.IGNORECASE),
]

# Patterns for detecting rationale
RATIONALE_PATTERNS = [
    re.compile(r"\*\*(?:Reason|Because|Rationale|Why)\*\*:?\s*(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"(?:because|since|reason:)\s+(.+?)(?:\.|$)", re.IGNORECASE),
]

# Patterns for evidence
EVIDENCE_PATTERNS = [
    re.compile(r"\*\*Evidence\*\*:?\s*(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"Source:\s*(.+?)(?:\n|$)", re.IGNORECASE),
]


# ============================================================================
# ANTIGRAVITY ADAPTER — Parse .gemini/antigravity/brain/ artifacts
# ============================================================================

class AntigravityAdapter:
    """
    Adapter for extracting DCAs from Antigravity (Gemini IDE) conversation artifacts.
    Targets:
      - implementation_plan.md
      - task.md
      - walkthrough.md
      - Any .md files in the brain directory
    """

    TOOL_NAME = "antigravity"
    PRIORITY_FILES = [
        "implementation_plan.md",
        "task.md",
        "walkthrough.md",
    ]

    def __init__(self, brain_root: Optional[Path] = None):
        """Initialize AntigravityAdapter.

        Args:
            brain_root (Optional[Path]): Path to Antigravity brain directory.
                Defaults to ~/.gemini/antigravity/brain.
        """
        self.brain_root = brain_root or (Path.home() / ".gemini" / "antigravity" / "brain")

    def discover_sessions(self, limit: int = 5) -> List[Path]:
        """Discover the N most recent Antigravity sessions.

        Args:
            limit (int): Maximum sessions to return. Default 5.

        Returns:
            List[Path]: Session directories sorted by modification time (newest first).
        """
        if not self.brain_root.exists():
            return []

        sessions = sorted(
            [d for d in self.brain_root.iterdir() if d.is_dir() and not d.name.startswith(".")],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )
        return sessions[:limit]

    def extract_from_session(self, session_path: Path) -> List[DecisionAtom]:
        """Extract DCAs from a single Antigravity session.

        Args:
            session_path (Path): Path to session directory.

        Returns:
            List[DecisionAtom]: Extracted decision atoms.
        """
        atoms = []
        session_id = session_path.name

        # Priority files first, then other .md files
        files_to_scan = []
        for pf in self.PRIORITY_FILES:
            fp = session_path / pf
            if fp.exists():
                files_to_scan.append(fp)

        # Add other .md files
        for md_file in sorted(session_path.glob("*.md")):
            if md_file.name not in self.PRIORITY_FILES and md_file.stat().st_size < 500_000:
                files_to_scan.append(md_file)

        for file_path in files_to_scan:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                file_atoms = self._extract_decisions(content, session_id, file_path.name)
                atoms.extend(file_atoms)
            except Exception:
                continue

        return atoms

    def _extract_decisions(self, content: str, session_id: str, filename: str) -> List[DecisionAtom]:
        """Extract decision atoms from markdown content using pattern matching.

        Args:
            content (str): Markdown content to parse.
            session_id (str): Session identifier.
            filename (str): Source filename for context.

        Returns:
            List[DecisionAtom]: Extracted and deduplicated decision atoms.
        """
        atoms = []
        seen_hashes = set()

        # Strategy 1: Extract from implementation_plan.md style documents
        if "implementation_plan" in filename.lower() or "## Proposed Changes" in content:
            atoms.extend(self._extract_from_plan(content, session_id))

        # Strategy 2: Extract from task.md completed items
        if "task" in filename.lower():
            atoms.extend(self._extract_from_tasks(content, session_id))

        # Strategy 3: General decision pattern matching
        for pattern in DECISION_PATTERNS:
            for match in pattern.finditer(content):
                decision_text = match.group(1).strip()
                if len(decision_text) < 15 or len(decision_text) > 500:
                    continue

                # Try to find rationale nearby
                rationale = self._find_nearby_rationale(content, match.start())

                atom = DecisionAtom(
                    decision=decision_text,
                    rationale=rationale or "Extracted from artifact; rationale inferred from context.",
                    source_tool=self.TOOL_NAME,
                    source_session=session_id,
                    confidence=0.6,
                    tags=self._infer_tags(decision_text, filename),
                )

                if atom.sha256 not in seen_hashes:
                    seen_hashes.add(atom.sha256)
                    atoms.append(atom)

        # Dedup
        final_atoms = []
        final_hashes = set()
        for atom in atoms:
            if atom.sha256 not in final_hashes:
                final_hashes.add(atom.sha256)
                final_atoms.append(atom)

        return final_atoms

    def _extract_from_plan(self, content: str, session_id: str) -> List[DecisionAtom]:
        """Extract structured decisions from implementation plan format.

        Args:
            content (str): Implementation plan markdown content.
            session_id (str): Session identifier.

        Returns:
            List[DecisionAtom]: Decision atoms for file modifications.
        """
        atoms = []
        # Look for file modification entries
        file_entries = re.finditer(
            r"####\s*\[(?:MODIFY|NEW|DELETE)\]\s*\[(.+?)\].*?\n([\s\S]*?)(?=\n####|\n##|\Z)",
            content,
        )
        for entry in file_entries:
            filename = entry.group(1)
            details = entry.group(2).strip()
            if details:
                atoms.append(DecisionAtom(
                    decision=f"Modify {filename}: {details[:200]}",
                    rationale="Specified in implementation plan.",
                    source_tool=self.TOOL_NAME,
                    source_session=session_id,
                    confidence=0.9,
                    tags=["implementation", "file-change"],
                ))
        return atoms

    def _extract_from_tasks(self, content: str, session_id: str) -> List[DecisionAtom]:
        """Extract completed decisions from task.md format.

        Args:
            content (str): Task markdown content.
            session_id (str): Session identifier.

        Returns:
            List[DecisionAtom]: Decision atoms for completed tasks.
        """
        atoms = []
        completed = re.finditer(r"- \[x\]\s+(.+?)$", content, re.MULTILINE)
        for task in completed:
            text = task.group(1).strip()
            if len(text) > 15:
                atoms.append(DecisionAtom(
                    decision=f"Completed: {text[:200]}",
                    rationale="Task was completed as part of the development plan.",
                    source_tool=self.TOOL_NAME,
                    source_session=session_id,
                    confidence=0.85,
                    tags=["task-completion"],
                ))
        return atoms

    def _find_nearby_rationale(self, content: str, position: int) -> Optional[str]:
        """Search for rationale text near a decision.

        Args:
            content (str): Full content to search.
            position (int): Character position of the decision.

        Returns:
            Optional[str]: Rationale text if found, else None.
        """
        # Look in a 500-char window after the decision
        window = content[position:position + 500]
        for pattern in RATIONALE_PATTERNS:
            match = pattern.search(window)
            if match:
                return match.group(1).strip()
        return None

    def _infer_tags(self, text: str, filename: str) -> List[str]:
        """Infer semantic tags from decision text and filename.

        Args:
            text (str): Decision text to analyze.
            filename (str): Source filename for context.

        Returns:
            List[str]: Inferred tags (e.g., "architecture", "deployment").
        """
        tags = []
        text_lower = text.lower()

        tag_keywords = {
            "architecture": ["architecture", "design", "pattern", "schema", "structure"],
            "deployment": ["deploy", "render", "cloud", "docker", "production"],
            "testing": ["test", "verify", "assert", "benchmark"],
            "security": ["security", "auth", "encrypt", "sign", "audit"],
            "performance": ["performance", "latency", "speed", "optimize"],
            "api": ["api", "endpoint", "route", "handler"],
            "data": ["database", "schema", "migration", "model"],
            "ui": ["ui", "frontend", "component", "design"],
        }

        for tag, keywords in tag_keywords.items():
            if any(kw in text_lower for kw in keywords):
                tags.append(tag)

        if "plan" in filename.lower():
            tags.append("planned")
        if "walkthrough" in filename.lower():
            tags.append("verified")

        return tags


# ============================================================================
# CLAUDE ADAPTER — Parse Claude project exports
# ============================================================================

class ClaudeAdapter:
    """
    Adapter for extracting DCAs from Claude project exports.
    Targets:
      - Individual conversation .md files (named like "ag0103main-Refining...")
      - conversations.json (structured message data — parsed lazily)
      - Siphoned artifacts in .brain/siphon/claude/
    """

    TOOL_NAME = "claude"

    def __init__(self, project_root: Optional[Path] = None, brain_path: Optional[Path] = None):
        """Initialize ClaudeAdapter.

        Args:
            project_root (Optional[Path]): Path to project root for export discovery.
                Defaults to current working directory.
            brain_path (Optional[Path]): Path to brain directory for siphoned artifacts.
        """
        self.project_root = project_root or Path.cwd()
        self.brain_path = brain_path

    def discover_sessions(self, limit: int = 5) -> List[Path]:
        """Discover Claude export directories and siphoned artifacts.

        Args:
            limit (int): Maximum sessions to return. Default 5.

        Returns:
            List[Path]: Session directories sorted by modification time (newest first).
        """
        sessions = []

        # 1. Claude project export dirs in the project root
        for export_dir in sorted(
            self.project_root.glob("claude project export*"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        ):
            if export_dir.is_dir():
                sessions.append(export_dir)

        # 2. Siphoned Claude artifacts in .brain/siphon/claude/
        if self.brain_path:
            siphon_claude = self.brain_path / "siphon" / "claude" / "verified"
            if siphon_claude.exists():
                for d in sorted(
                    [x for x in siphon_claude.iterdir() if x.is_dir()],
                    key=lambda x: x.stat().st_mtime,
                    reverse=True,
                ):
                    sessions.append(d)

        return sessions[:limit]

    def extract_from_session(self, session_path: Path) -> List[DecisionAtom]:
        """Extract DCAs from a Claude export directory.

        Args:
            session_path (Path): Path to Claude export directory.

        Returns:
            List[DecisionAtom]: Extracted and deduplicated decision atoms.
        """
        atoms = []
        session_id = session_path.name[:40]

        # Scan all .md files (individual conversation exports)
        for md_file in sorted(session_path.glob("*.md")):
            if md_file.stat().st_size > 1_000_000:  # Skip >1MB
                continue
            try:
                content = md_file.read_text(encoding="utf-8", errors="replace")
                file_atoms = self._extract_from_claude_md(content, session_id, md_file.name)
                atoms.extend(file_atoms)
            except Exception:
                continue

        # Try conversations.json for structured extraction
        conv_json = session_path / "conversations.json"
        if conv_json.exists() and conv_json.stat().st_size < 5_000_000:
            try:
                atoms.extend(self._extract_from_conversations_json(conv_json, session_id))
            except Exception:
                pass

        return self._dedup(atoms)

    def _extract_from_claude_md(self, content: str, session_id: str, filename: str) -> List[DecisionAtom]:
        """Extract decisions from Claude conversation markdown.

        Args:
            content (str): Claude conversation markdown content.
            session_id (str): Session identifier.
            filename (str): Source filename for context.

        Returns:
            List[DecisionAtom]: Extracted decision atoms.
        """
        atoms = []

        # Claude export uses multiple heading formats depending on export version:
        # - "### User Input" / "### Assistant" (claude project export)
        # - "## Human:" / "## Assistant:" (API-style)
        # - "## User Input" / "## Response" (older exports)
        # Try all known patterns
        assistant_patterns = [
            # Claude project export format (most common)
            re.compile(
                r"(?:^|\n)#{2,3}\s*(?:Assistant|Response)\s*\n([\s\S]*?)(?=\n#{2,3}\s*(?:User Input|Human|User)|$)",
                re.IGNORECASE,
            ),
            # API-style format
            re.compile(
                r"(?:^|\n)#{2,3}\s*(?:Assistant|Claude|A):?\s*\n([\s\S]*?)(?=\n#{2,3}\s*(?:Human|User|H):|$)",
                re.IGNORECASE,
            ),
        ]

        assistant_text_found = False
        for pattern in assistant_patterns:
            for block in pattern.finditer(content):
                assistant_text_found = True
                block_text = block.group(1)
                for dp in DECISION_PATTERNS:
                    for match in dp.finditer(block_text):
                        text = match.group(1).strip()
                        if 15 < len(text) < 500:
                            atoms.append(DecisionAtom(
                                decision=text,
                                rationale="Extracted from Claude conversation.",
                                source_tool=self.TOOL_NAME,
                                source_session=session_id,
                                confidence=0.6,
                                tags=_infer_tags_generic(text, filename),
                            ))

        # Fallback: if no assistant blocks found, apply patterns to entire content
        if not assistant_text_found:
            for dp in DECISION_PATTERNS:
                for match in dp.finditer(content):
                    text = match.group(1).strip()
                    if 15 < len(text) < 500:
                        atoms.append(DecisionAtom(
                            decision=text,
                            rationale="Extracted from Claude conversation artifact.",
                            source_tool=self.TOOL_NAME,
                            source_session=session_id,
                            confidence=0.55,
                            tags=_infer_tags_generic(text, filename),
                        ))

        # Extract completed tasks
        completed = re.finditer(r"- \[x\]\s+(.+?)$", content, re.MULTILINE)
        for task in completed:
            text = task.group(1).strip()
            if len(text) > 15:
                atoms.append(DecisionAtom(
                    decision=f"Completed: {text[:200]}",
                    rationale="Task completed in Claude session.",
                    source_tool=self.TOOL_NAME,
                    source_session=session_id,
                    confidence=0.85,
                    tags=["task-completion"],
                ))

        # Extract code decisions from inline comments
        code_decisions = re.finditer(
            r"```(?:python|javascript|typescript|bash)\n.*?(?:# (?:DECISION|ADR|TODO|FIXME):?\s*(.+?))\n.*?```",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        for cd in code_decisions:
            text = cd.group(1).strip()
            if text:
                atoms.append(DecisionAtom(
                    decision=text,
                    rationale="Inline code comment decision from Claude conversation.",
                    source_tool=self.TOOL_NAME,
                    source_session=session_id,
                    confidence=0.7,
                    tags=["code-decision"],
                ))

        return atoms

    def _extract_from_conversations_json(self, json_path: Path, session_id: str) -> List[DecisionAtom]:
        """Extract decisions from Claude's conversations.json structured format.

        Args:
            json_path (Path): Path to conversations.json file.
            session_id (str): Session identifier.

        Returns:
            List[DecisionAtom]: Extracted decision atoms from structured data.
        """
        atoms = []
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            return []

        conversations = data if isinstance(data, list) else [data]

        for conv in conversations[:20]:  # Cap at 20 conversations to avoid OOM
            conv_name = conv.get("name", conv.get("title", "unknown"))
            messages = conv.get("chat_messages", conv.get("messages", []))

            for msg in messages:
                sender = msg.get("sender", msg.get("role", ""))
                text = msg.get("text", msg.get("content", ""))

                if sender.lower() not in ("assistant", "claude"):
                    continue
                if not text or len(text) < 50:
                    continue

                # Extract high-signal decisions from assistant messages
                for pattern in DECISION_PATTERNS:
                    for match in pattern.finditer(text):
                        decision_text = match.group(1).strip()
                        if 15 < len(decision_text) < 500:
                            atoms.append(DecisionAtom(
                                decision=decision_text,
                                rationale=f"From Claude conversation: {conv_name[:60]}",
                                source_tool=self.TOOL_NAME,
                                source_session=f"{session_id}:{conv_name[:30]}",
                                confidence=0.65,
                                tags=_infer_tags_generic(decision_text, conv_name),
                            ))

        return atoms

    @staticmethod
    def _dedup(atoms: List[DecisionAtom]) -> List[DecisionAtom]:
        """Deduplicate atoms by sha256 hash.

        Args:
            atoms (List[DecisionAtom]): List of atoms to deduplicate.

        Returns:
            List[DecisionAtom]: Unique atoms with first occurrence kept.
        """
        seen = set()
        unique = []
        for atom in atoms:
            if atom.sha256 not in seen:
                seen.add(atom.sha256)
                unique.append(atom)
        return unique


# ============================================================================
# WINDSURF ADAPTER — Parse Windsurf/Codeium artifacts
# ============================================================================

class WindsurfAdapter:
    """
    Adapter for extracting DCAs from Windsurf (Codeium) artifacts.
    Targets:
      - .brain/siphon/windsurf/verified/ (pre-siphoned snapshots)
      - ~/.codeium/windsurf/code_tracker/ (raw tracker data)
    """

    TOOL_NAME = "windsurf"

    def __init__(self, project_root: Optional[Path] = None, brain_path: Optional[Path] = None):
        """Initialize WindsurfAdapter.

        Args:
            project_root (Optional[Path]): Path to project root. Defaults to cwd.
            brain_path (Optional[Path]): Path to brain directory for siphoned artifacts.
        """
        self.project_root = project_root or Path.cwd()
        self.brain_path = brain_path
        self.project_name = self.project_root.name

    def discover_sessions(self, limit: int = 5) -> List[Path]:
        """Discover Windsurf session directories.

        Args:
            limit (int): Maximum sessions to return. Default 5.

        Returns:
            List[Path]: Session directories sorted by modification time (newest first).
        """
        sessions = []

        # 1. Pre-siphoned artifacts
        if self.brain_path:
            siphon_ws = self.brain_path / "siphon" / "windsurf" / "verified"
            if siphon_ws.exists():
                for d in sorted(
                    [x for x in siphon_ws.iterdir() if x.is_dir()],
                    key=lambda x: x.stat().st_mtime,
                    reverse=True,
                ):
                    sessions.append(d)

        # 2. Raw code_tracker data
        tracker_home = Path.home() / ".codeium" / "windsurf" / "code_tracker"
        if tracker_home.exists():
            for d in sorted(
                [x for x in tracker_home.rglob(f"{self.project_name}_*") if x.is_dir()],
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            ):
                sessions.append(d)

        return sessions[:limit]

    def extract_from_session(self, session_path: Path) -> List[DecisionAtom]:
        """Extract DCAs from a Windsurf session directory.

        Args:
            session_path (Path): Path to Windsurf session directory.

        Returns:
            List[DecisionAtom]: Extracted and deduplicated decision atoms.
        """
        atoms = []
        session_id = session_path.name[:40]

        # Scan .md and .txt files
        for ext in ("*.md", "*.txt", "*.resolved"):
            for file_path in sorted(session_path.glob(ext)):
                if file_path.stat().st_size > 500_000:
                    continue
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                    file_atoms = self._extract_from_windsurf_file(content, session_id, file_path.name)
                    atoms.extend(file_atoms)
                except Exception:
                    continue

        return self._dedup(atoms)

    def _extract_from_windsurf_file(self, content: str, session_id: str, filename: str) -> List[DecisionAtom]:
        """Extract decisions from Windsurf snapshot files.

        Args:
            content (str): File content to parse.
            session_id (str): Session identifier.
            filename (str): Source filename for context.

        Returns:
            List[DecisionAtom]: Extracted decision atoms.
        """
        atoms = []

        # Windsurf chat exports typically contain conversation in raw format
        # Look for decision patterns
        for pattern in DECISION_PATTERNS:
            for match in pattern.finditer(content):
                text = match.group(1).strip()
                if 15 < len(text) < 500:
                    atoms.append(DecisionAtom(
                        decision=text,
                        rationale="Extracted from Windsurf conversation snapshot.",
                        source_tool=self.TOOL_NAME,
                        source_session=session_id,
                        confidence=0.55,
                        tags=_infer_tags_generic(text, filename),
                    ))

        # Extract from task completions
        completed = re.finditer(r"- \[x\]\s+(.+?)$", content, re.MULTILINE)
        for task in completed:
            text = task.group(1).strip()
            if len(text) > 15:
                atoms.append(DecisionAtom(
                    decision=f"Completed: {text[:200]}",
                    rationale="Task completed in Windsurf session.",
                    source_tool=self.TOOL_NAME,
                    source_session=session_id,
                    confidence=0.8,
                    tags=["task-completion"],
                ))

        return atoms

    @staticmethod
    def _dedup(atoms: List[DecisionAtom]) -> List[DecisionAtom]:
        """Deduplicate atoms by sha256 hash.

        Args:
            atoms (List[DecisionAtom]): List of atoms to deduplicate.

        Returns:
            List[DecisionAtom]: Unique atoms with first occurrence kept.
        """
        seen = set()
        unique = []
        for atom in atoms:
            if atom.sha256 not in seen:
                seen.add(atom.sha256)
                unique.append(atom)
        return unique


# ============================================================================
# SHARED TAG INFERENCE (used by Claude and Windsurf adapters)
# ============================================================================

def _infer_tags_generic(text: str, filename: str) -> List[str]:
    """Shared tag inference for all adapters.

    Args:
        text (str): Decision text to analyze.
        filename (str): Source filename for context.

    Returns:
        List[str]: Inferred tags (e.g., "architecture", "deployment").
    """
    tags = []
    text_lower = text.lower()

    tag_keywords = {
        "architecture": ["architecture", "design", "pattern", "schema", "structure"],
        "deployment": ["deploy", "render", "cloud", "docker", "production"],
        "testing": ["test", "verify", "assert", "benchmark"],
        "security": ["security", "auth", "encrypt", "sign", "audit"],
        "performance": ["performance", "latency", "speed", "optimize"],
        "api": ["api", "endpoint", "route", "handler"],
        "data": ["database", "schema", "migration", "model"],
        "ui": ["ui", "frontend", "component", "design"],
    }

    for tag, keywords in tag_keywords.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)

    if "plan" in filename.lower():
        tags.append("planned")
    if "walkthrough" in filename.lower():
        tags.append("verified")

    return tags


# ============================================================================
# DISTILLATION ENGINE
# ============================================================================

class DistillationEngine:
    """
    Core distillation engine — orchestrates adapter → DCA → storage.
    Implements the "Distillator" agent from the SCRP protocol.
    """

    def __init__(self, brain_path: Optional[Path] = None):
        """Initialize DistillationEngine.

        Args:
            brain_path (Optional[Path]): Path to brain directory.
                Defaults to get_brain_path() result.
        """
        from .runtime.common import get_brain_path
        self.brain_path = brain_path or get_brain_path()
        self.distill_dir = self.brain_path / "distill"
        self.distill_dir.mkdir(parents=True, exist_ok=True)

        # Detect project root for Claude adapter
        project_root = self.brain_path.parent if self.brain_path.name == ".brain" else Path.cwd()

        self.adapters = {
            "antigravity": AntigravityAdapter(),
            "claude": ClaudeAdapter(project_root=project_root, brain_path=self.brain_path),
            "windsurf": WindsurfAdapter(project_root=project_root, brain_path=self.brain_path),
        }

    def distill(
        self,
        source: str = "all",
        session_limit: int = 3,
        output_format: str = "jsonld",
    ) -> Dict[str, Any]:
        """Run the full distillation pipeline.

        Args:
            source (str): Which tool to distill from ("antigravity", "claude", "windsurf", "all").
            session_limit (int): Max sessions to process per tool. Default 3.
            output_format (str): "jsonld", "engram", or "both". Default "jsonld".

        Returns:
            Dict[str, Any]: Results containing total_atoms, duplicates_removed,
                by_source stats, output_paths, and timestamp.
        """
        all_atoms: List[DecisionAtom] = []
        stats: Dict[str, int] = {}

        # Discover and extract
        adapters_to_use = (
            self.adapters.values()
            if source == "all"
            else [self.adapters[source]]
            if source in self.adapters
            else []
        )

        for adapter in adapters_to_use:
            sessions = adapter.discover_sessions(limit=session_limit)
            tool_atoms = []
            for session in sessions:
                session_atoms = adapter.extract_from_session(session)
                tool_atoms.extend(session_atoms)
            stats[adapter.TOOL_NAME] = len(tool_atoms)
            all_atoms.extend(tool_atoms)

        # Global dedup by sha256
        seen = set()
        unique_atoms = []
        for atom in all_atoms:
            if atom.sha256 not in seen:
                seen.add(atom.sha256)
                unique_atoms.append(atom)

        # Write outputs
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_paths = {}

        if output_format in ("jsonld", "both"):
            jsonld_path = self._write_jsonld(unique_atoms, timestamp)
            output_paths["jsonld"] = str(jsonld_path)

        if output_format in ("engram", "both"):
            engram_path = self._write_engram(unique_atoms, timestamp)
            output_paths["engram"] = str(engram_path)

        # Always write the engram for human consumption
        if "engram" not in output_paths:
            engram_path = self._write_engram(unique_atoms, timestamp)
            output_paths["engram"] = str(engram_path)

        return {
            "total_atoms": len(unique_atoms),
            "duplicates_removed": len(all_atoms) - len(unique_atoms),
            "by_source": stats,
            "output_paths": output_paths,
            "timestamp": timestamp,
        }

    def _write_jsonld(self, atoms: List[DecisionAtom], timestamp: str) -> Path:
        """Write atoms as JSON-LD (one object per line).

        Args:
            atoms (List[DecisionAtom]): Atoms to write.
            timestamp (str): Timestamp for filename.

        Returns:
            Path: Path to written JSONL file.
        """
        path = self.distill_dir / f"dca_{timestamp}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for atom in atoms:
                f.write(json.dumps(atom.to_jsonld(), ensure_ascii=False) + "\n")
        return path

    def _write_engram(self, atoms: List[DecisionAtom], timestamp: str) -> Path:
        """Write a Sovereign Context Engram — the human-readable summary.

        Args:
            atoms (List[DecisionAtom]): Atoms to summarize.
            timestamp (str): Timestamp for filename.

        Returns:
            Path: Path to written markdown engram file.
        """
        path = self.distill_dir / f"engram_{timestamp}.md"

        # Group by tag
        tagged: Dict[str, List[DecisionAtom]] = {}
        for atom in atoms:
            primary_tag = atom.tags[0] if atom.tags else "general"
            tagged.setdefault(primary_tag, []).append(atom)

        lines = [
            f"# 🧠 Sovereign Context Engram",
            f"\n**Generated**: {timestamp}",
            f"**Atoms**: {len(atoms)}",
            f"**Protocol**: SCRP DCA Schema v1",
            "\n---",
            "\n> This engram is a high-density context transfer document.",
            "> Feed it to a new AI session to restore decision context.",
            "\n---\n",
        ]

        for tag, tag_atoms in sorted(tagged.items()):
            lines.append(f"## {tag.title()} ({len(tag_atoms)} decisions)\n")
            for atom in sorted(tag_atoms, key=lambda a: a.confidence, reverse=True):
                confidence_emoji = "🟢" if atom.confidence >= 0.8 else "🟡" if atom.confidence >= 0.6 else "🔴"
                lines.append(f"- {confidence_emoji} **{atom.decision[:120]}**")
                lines.append(f"  - *{atom.rationale[:200]}*")
                if atom.evidence:
                    lines.append(f"  - Evidence: {'; '.join(atom.evidence[:3])}")
                lines.append("")

        lines.append("---")
        lines.append(f"\n*Generated by Nucleus Distillation Engine v1.0.0 (SCRP MVE)*")

        path.write_text("\n".join(lines), encoding="utf-8")
        return path


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def run_distill(source: str = "all", limit: int = 3, output: str = "both") -> Dict[str, Any]:
    """CLI entry point for context distillation.

    Args:
        source (str): Which tool to distill from. Default "all".
        limit (int): Max sessions to process per tool. Default 3.
        output (str): Output format ("jsonld", "engram", "both"). Default "both".

    Returns:
        Dict[str, Any]: Distillation results with stats and output paths.
    """
    engine = DistillationEngine()
    print(f"🧬 [Distill] Extracting Decision Context Atoms from {source}...")

    result = engine.distill(source=source, session_limit=limit, output_format=output)

    print(f"\n📊 Distillation Results:")
    print(f"   Total DCAs: {result['total_atoms']}")
    print(f"   Duplicates removed: {result['duplicates_removed']}")
    for tool, count in result["by_source"].items():
        print(f"   {tool}: {count} atoms")

    print(f"\n📁 Output Files:")
    for fmt, path in result["output_paths"].items():
        print(f"   {fmt}: {path}")

    return result
