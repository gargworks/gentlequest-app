"""
Nucleus Artifact Siphon - Intellectual Context Extraction
==========================================================
Extracts ONLY high-value, semantic context (Markdown, logs, intent).
Strictly blocks binaries, symlinks, and redundant system snapshots.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Set

class ArtifactSiphon:
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            # Auto-detect project root by looking for .brain
            from .runtime.common import get_brain_path
            brain_path = get_brain_path()
            if brain_path.name == ".brain":
                self.project_root = brain_path.parent
            else:
                self.project_root = Path.cwd()
        else:
            self.project_root = project_root
            
        self.project_name = self.project_root.name
        self.brain_dir = self.project_root / ".brain"
        self.siphon_dir = self.brain_dir / "siphon"
        
        # Intellectual Protocol: Only text-based semantic files
        self.allowed_extensions = {".md", ".txt", ".resolved", ".json", ".log"}
        self.blocked_extensions = {".exe", ".db", ".bin", ".dylib", ".sfl4", ".exe"}
        
        # Sovereign Fingerprinting Signatures
        self.signatures = {
            self.project_name,
            "Nucleus",
            "mcp-server-nucleus",
            "ai-mvp-backend",
            "GentleQuest"
        }
        
    def is_semantic_context(self, file_path: Path) -> bool:
        """Verify if file is a text-based semantic artifact and NOT a symlink/binary."""
        if file_path.is_symlink():
            return False
        if file_path.suffix.lower() in self.blocked_extensions:
            return False
        if file_path.suffix.lower() not in self.allowed_extensions:
            return False
        if file_path.stat().st_size > 1_000_000: # Block files > 1MB (usually not session logs)
            return False
        return True

    def verify_affinity(self, content: str, file_path: Optional[Path] = None) -> bool:
        """Check if content or path contains project signatures."""
        content_lower = content.lower()
        path_str = str(file_path).lower() if file_path else ""
        
        for sig in self.signatures:
            sig_lower = sig.lower()
            if sig_lower in content_lower or sig_lower in path_str:
                return True
        return False

    def siphon_windsurf(self) -> List[str]:
        """Extract Windsurf text snapshots (MD, logs)."""
        tracker_home = Path.home() / ".codeium" / "windsurf" / "code_tracker"
        if not tracker_home.exists():
            return []
            
        project_dirs = [d for d in tracker_home.rglob(f"{self.project_name}_*") if d.is_dir()]
        extracted = []
        for project_dir in project_dirs:
            rel_path_str = str(project_dir.relative_to(project_dir.parents[1])).replace(os.sep, "_")
            target_base = self.siphon_dir / "windsurf" / "verified" / rel_path_str
            
            for file in project_dir.iterdir():
                if self.is_semantic_context(file):
                    target_base.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file, target_base / file.name)
                    extracted.append(f"verified/{rel_path_str}/{file.name}")
        return extracted

    def siphon_antigravity(self, limit: int = 5) -> List[str]:
        """Extract Antigravity session resolution logs (Text only)."""
        brain_home = Path.home() / ".gemini" / "antigravity" / "brain"
        if not brain_home.exists():
            return []
        
        sessions = sorted([d for d in brain_home.iterdir() if d.is_dir()], 
                         key=lambda x: x.stat().st_mtime, reverse=True)
            
        extracted = []
        for session in sessions[:limit]:
            target_dir = self.siphon_dir / "antigravity" / "verified" / session.name
            
            # Siphon only .resolved or .md files
            for file in session.iterdir():
                if self.is_semantic_context(file) and (file.suffix == ".md" or ".resolved" in file.name):
                    target_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file, target_dir / file.name)
                    extracted.append(f"verified/{session.name}/{file.name}")
        return extracted

    def siphon_claude(self) -> List[str]:
        """Siphon Claude project exports (The actual Thinking Threads)."""
        extracted = []
        # Look for the gold-mine project exports in project root
        for export_dir in self.project_root.glob("claude project export*"):
            if not export_dir.is_dir(): continue
            
            target_dir = self.siphon_dir / "claude" / "verified" / export_dir.name
            target_dir.mkdir(parents=True, exist_ok=True)
            
            for file in export_dir.rglob("*"):
                if self.is_semantic_context(file):
                    rel_file = file.relative_to(export_dir)
                    final_target = target_dir / rel_file
                    final_target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file, final_target)
                    extracted.append(f"verified/{export_dir.name}/{rel_file}")
        return extracted

    def generate_report(self, stats: Dict[str, List[str]]) -> Path:
        """Create a summary report of the INTELLECTUAL siphon."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_path = self.brain_dir / "vault" / f"siphon_snapshot_{timestamp}.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = [
            f"# Intellectual Context Siphon - {timestamp}",
            "\n> [!NOTE]",
            "> This is NOT a backup. Large binaries, symlinks, and global configs have been strictly excluded.",
            "\n## Semantic Summary",
        ]
        
        total = 0
        for tool, files in stats.items():
            if files:
                content.append(f"- **{tool}**: {len(files)} semantic artifacts extracted.")
                total += len(files)
            
        content.append(f"\n**Total Context Gained**: {total} text-based artifacts.")
        content.append("\n## Context Library")
        
        for tool, files in sorted(stats.items()):
            if not files: continue
            content.append(f"\n### {tool}")
            content.append("| Silo | Intellectual Artifact |")
            content.append("|:---|:---|")
            for f in sorted(files):
                if "/" in f:
                    silo, filename = f.split("/", 1)
                    content.append(f"| `{silo}` | `{filename}` |")
                else:
                    content.append(f"| `root` | `{f}` |")
        
        content.append("\n---")
        content.append(f"\n*Generated by Nucleus Siphon v1.2.0 (Intellectual Filter)*")
        report_path.write_text("\n".join(content))
        return report_path

def run_siphon():
    """CLI Entry Point for Intellectual Siphoning."""
    siphon = ArtifactSiphon()
    print(f"🧠 [Intellectual-Siphon] Extracting reasoning for '{siphon.project_name}'...")
    
    stats = {
        "Windsurf Snapshots": siphon.siphon_windsurf(),
        "Antigravity Logs": siphon.siphon_antigravity(),
        "Claude Thinking Threads": siphon.siphon_claude()
    }
    
    any_siphoned = False
    for tool, files in stats.items():
        if files:
            print(f"  ✅ {tool}: Extracted {len(files)} semantic artifacts.")
            any_siphoned = True
            
    if any_siphoned:
        report = siphon.generate_report(stats)
        print(f"\n🏁 Intellectual Siphon complete!")
        print(f"   Context Report: {report}")
    else:
        print("\n❌ No semantic context found. Siphon idle (Brute-force backup mode is OFF).")
