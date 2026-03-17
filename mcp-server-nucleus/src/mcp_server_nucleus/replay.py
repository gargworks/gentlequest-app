"""
Nucleus Context Replay Engine
===============================
The "receiver" half of the SCRP distill→replay loop.

Takes Deterministic Context Atoms (DCAs) from a distillation run
and generates a context injection payload for a fresh AI session.

Replay modes:
  - "system_prompt": Generate a system prompt fragment with all DCAs
  - "engram_deposit": Write DCAs into the Brain's EngramVault
  - "brain_seed": Create a `.brain/replay/` folder with structured context

This module completes the MVE pipeline:
  distill (extract) → replay (inject) → measure (H1 validation)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional


class ReplayEngine:
    """
    Loads DCAs from a distillation output and replays them into
    a target environment (system prompt, engram vault, or brain seed).
    """

    def __init__(self, brain_path: Optional[Path] = None):
        from .runtime.common import get_brain_path
        self.brain_path = brain_path or get_brain_path()
        self.distill_dir = self.brain_path / "distill"
        self.replay_dir = self.brain_path / "replay"
        self.replay_dir.mkdir(parents=True, exist_ok=True)

    def load_atoms(self, source_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Load DCAs from a JSONL file. If no path given, use the latest distillation.
        """
        if source_path is None:
            # Auto-discover latest distillation
            jsonl_files = sorted(self.distill_dir.glob("dca_*.jsonl"), reverse=True)
            if not jsonl_files:
                return []
            source_path = jsonl_files[0]

        atoms = []
        with open(source_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        atoms.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return atoms

    def filter_atoms(
        self,
        atoms: List[Dict[str, Any]],
        min_confidence: float = 0.0,
        tags: Optional[List[str]] = None,
        max_atoms: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Filter and prioritize atoms for replay injection.

        Sorting: highest confidence first, then by tag relevance.
        """
        filtered = atoms

        # Confidence filter
        if min_confidence > 0:
            filtered = [a for a in filtered if a.get("confidence", 0) >= min_confidence]

        # Tag filter
        if tags:
            tag_set = set(tags)
            filtered = [a for a in filtered if tag_set.intersection(set(a.get("tags", [])))]

        # Sort by confidence descending
        filtered.sort(key=lambda a: a.get("confidence", 0), reverse=True)

        # Cap
        return filtered[:max_atoms]

    def replay_as_system_prompt(
        self,
        atoms: Optional[List[Dict[str, Any]]] = None,
        min_confidence: float = 0.6,
        max_atoms: int = 50,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a system prompt fragment that encodes the DCAs
        for injection into a fresh AI session.

        This is the core of the H1 hypothesis test:
        "DCAs reduce context re-derivation by >80%"
        """
        if atoms is None:
            atoms = self.load_atoms()

        filtered = self.filter_atoms(atoms, min_confidence=min_confidence, tags=tags, max_atoms=max_atoms)

        if not filtered:
            return "# No Decision Context Atoms available.\n"

        lines = [
            "# Sovereign Context Replay — Decision Context Atoms",
            "",
            "> These are verified decisions from prior sessions.",
            "> Do NOT re-derive or question these unless the user explicitly asks to revisit them.",
            "> Build upon them as established facts.",
            "",
            f"**Total Atoms**: {len(filtered)}",
            f"**Min Confidence**: {min_confidence:.0%}",
            f"**Replay Timestamp**: {datetime.now(timezone.utc).isoformat()[:19]}Z",
            "",
            "---",
            "",
        ]

        # Group by primary tag
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for atom in filtered:
            tag = atom.get("tags", ["general"])[0] if atom.get("tags") else "general"
            grouped.setdefault(tag, []).append(atom)

        for tag, tag_atoms in sorted(grouped.items()):
            lines.append(f"## {tag.title()}")
            lines.append("")
            for atom in tag_atoms:
                conf = atom.get("confidence", 0)
                icon = "🟢" if conf >= 0.8 else "🟡" if conf >= 0.6 else "🔴"
                lines.append(f"- {icon} **{atom['decision'][:150]}**")
                if atom.get("rationale") and atom["rationale"] != "Extracted from artifact; rationale inferred from context.":
                    lines.append(f"  - Why: {atom['rationale'][:200]}")
                if atom.get("evidence"):
                    lines.append(f"  - Evidence: {'; '.join(atom['evidence'][:3])}")
            lines.append("")

        lines.append("---")
        lines.append("*Injected by Nucleus SCRP Replay Engine v1.0.0*")

        return "\n".join(lines)

    def replay_to_engrams(
        self,
        atoms: Optional[List[Dict[str, Any]]] = None,
        min_confidence: float = 0.7,
        max_atoms: int = 30,
    ) -> Dict[str, Any]:
        """
        Write DCAs into the Brain's EngramVault for persistent memory.
        """
        from .runtime.dsor import EngramVault

        if atoms is None:
            atoms = self.load_atoms()

        filtered = self.filter_atoms(atoms, min_confidence=min_confidence, max_atoms=max_atoms)

        session_id = f"replay_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        vault = EngramVault(session_id=session_id, brain_path=self.brain_path)

        deposited = 0
        for atom in filtered:
            vault.deposit(
                key=f"dca_{atom.get('sha256', 'unknown')[:8]}",
                value=atom["decision"],
                source_agent="scrp_replay",
                metadata={
                    "rationale": atom.get("rationale", ""),
                    "confidence": atom.get("confidence", 0),
                    "tags": atom.get("tags", []),
                    "source_tool": atom.get("source_tool", "unknown"),
                    "source_session": atom.get("source_session", "unknown"),
                },
            )
            deposited += 1

        return {
            "session_id": session_id,
            "deposited": deposited,
            "vault_path": str(vault.vault_file),
        }

    def replay_as_brain_seed(
        self,
        atoms: Optional[List[Dict[str, Any]]] = None,
        min_confidence: float = 0.5,
        max_atoms: int = 100,
    ) -> Dict[str, Any]:
        """
        Create a self-contained brain seed folder that can be copied
        to a new project or machine for full context recovery.
        """
        if atoms is None:
            atoms = self.load_atoms()

        filtered = self.filter_atoms(atoms, min_confidence=min_confidence, max_atoms=max_atoms)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        seed_dir = self.replay_dir / f"seed_{timestamp}"
        seed_dir.mkdir(parents=True, exist_ok=True)

        # 1. Write the system prompt
        prompt = self.replay_as_system_prompt(filtered, min_confidence=min_confidence, max_atoms=max_atoms)
        prompt_path = seed_dir / "context_replay.md"
        prompt_path.write_text(prompt, encoding="utf-8")

        # 2. Write the raw JSONL for programmatic use
        jsonl_path = seed_dir / "atoms.jsonl"
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for atom in filtered:
                f.write(json.dumps(atom, ensure_ascii=False) + "\n")

        # 3. Write a manifest
        manifest = {
            "version": "1.0.0",
            "protocol": "SCRP DCA Schema v1",
            "created": datetime.now(timezone.utc).isoformat(),
            "atom_count": len(filtered),
            "min_confidence": min_confidence,
            "files": {
                "context_replay": "context_replay.md",
                "atoms": "atoms.jsonl",
            },
        }
        manifest_path = seed_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        return {
            "seed_dir": str(seed_dir),
            "atom_count": len(filtered),
            "files": [str(prompt_path), str(jsonl_path), str(manifest_path)],
        }


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def run_replay(
    mode: str = "system_prompt",
    source: Optional[str] = None,
    min_confidence: float = 0.6,
    max_atoms: int = 50,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """CLI entry point for context replay."""
    engine = ReplayEngine()

    source_path = Path(source) if source else None
    atoms = engine.load_atoms(source_path)

    if not atoms:
        print("❌ No DCAs found. Run `nucleus distill` first.")
        return {"error": "No DCAs found"}

    print(f"🔄 [Replay] Loaded {len(atoms)} DCAs. Mode: {mode}")

    if mode == "system_prompt":
        prompt = engine.replay_as_system_prompt(
            atoms, min_confidence=min_confidence, max_atoms=max_atoms, tags=tags
        )
        # Write to replay dir
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = engine.replay_dir / f"prompt_{timestamp}.md"
        output_path.write_text(prompt, encoding="utf-8")

        print(f"\n📋 System Prompt generated ({len(prompt)} chars)")
        print(f"   Output: {output_path}")
        print(f"\n--- PREVIEW (first 1000 chars) ---")
        print(prompt[:1000])
        if len(prompt) > 1000:
            print(f"\n... [{len(prompt) - 1000} more chars]")

        return {"mode": mode, "output": str(output_path), "chars": len(prompt)}

    elif mode == "engram":
        result = engine.replay_to_engrams(
            atoms, min_confidence=min_confidence, max_atoms=max_atoms
        )
        print(f"\n🧠 Deposited {result['deposited']} DCAs into EngramVault")
        print(f"   Session: {result['session_id']}")
        print(f"   Vault: {result['vault_path']}")
        return result

    elif mode == "seed":
        result = engine.replay_as_brain_seed(
            atoms, min_confidence=min_confidence, max_atoms=max_atoms
        )
        print(f"\n🌱 Brain Seed created with {result['atom_count']} atoms")
        print(f"   Seed Dir: {result['seed_dir']}")
        for f in result["files"]:
            print(f"   📄 {Path(f).name}")
        return result

    else:
        print(f"❌ Unknown mode: {mode}")
        return {"error": f"Unknown mode: {mode}"}
