import os
import time
import hashlib
import glob
import logging
from typing import List, Optional
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("siphon_engine")

class Artifact:
    def __init__(self, name: str, path: str, content: str):
        self.name = name
        self.path = path
        self.content = content
        self.hash = self._compute_hash(content)

    @staticmethod
    def _compute_hash(content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

class IDEAdapter(ABC):
    @abstractmethod
    def discover_artifacts(self) -> List[Artifact]:
        pass

class AntigravityAdapter(IDEAdapter):
    """Siphons mission artifacts from AG brain AND workspace rules."""
    def __init__(self, workspace_path: str, session_id: Optional[str] = None):
        self.workspace_path = workspace_path
        self.session_id = session_id
        # Discovery paths (Hierarchy of Truth)
        self.search_dirs = [
            os.path.join(workspace_path, ".agent"),
            os.path.join(workspace_path, ".agents"),
        ]
        
        # Mission Memory (The actual conversation context)
        if session_id:
            mission_path = os.path.expanduser(f"~/.gemini/antigravity/brain/{session_id}")
            if os.path.exists(mission_path):
                self.search_dirs.append(mission_path)

    def discover_artifacts(self) -> List[Artifact]:
        artifacts = []
        for base_dir in self.search_dirs:
            if not os.path.exists(base_dir):
                continue

            # Recursive scan for relevant markdown artifacts
            for root, _, files in os.walk(base_dir):
                for file in files:
                    # Match .md, .md.resolved, and .md.resolved.N (versioned files)
                    if (".md" in file) and file not in (".", ".."):
                        file_path = os.path.join(root, file)
                        try:
                            # Normalize name for the vault:
                            # task.md.resolved.52 -> task.md
                            # plan.md.resolved -> plan.md
                            vault_name = file
                            if ".md.resolved" in file:
                                # Strip .resolved and any following version numbers
                                vault_name = file.split(".md.resolved")[0] + ".md"
                            
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            artifacts.append(Artifact(vault_name, file_path, content))
                        except Exception as e:
                            logger.error(f"Failed to read artifact {file_path}: {e}")
        
        return artifacts

class WindsurfAdapter(IDEAdapter):
    """Siphons artifacts from Windsurf's .windsurf hidden folder."""
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.windsurf_dir = os.path.join(workspace_path, ".windsurf")

    def discover_artifacts(self) -> List[Artifact]:
        artifacts = []
        if not os.path.exists(self.windsurf_dir):
            return artifacts

        patterns = [
            os.path.join(self.windsurf_dir, "workflows", "*.md"),
            os.path.join(self.windsurf_dir, "rules", "*.md"),
        ]
        
        for pattern in patterns:
            for file_path in glob.glob(pattern):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        artifacts.append(Artifact(os.path.basename(file_path), file_path, content))
                except Exception as e:
                    logger.error(f"Failed to read Windsurf artifact {file_path}: {e}")
        
        return artifacts

class SiphonEngine:
    """The core engine that performs synchronous artifact siphoning."""
    def __init__(self, vault_path: str, adapters: List[IDEAdapter]):
        self.vault_path = vault_path
        self.adapters = adapters
        os.makedirs(vault_path, exist_ok=True)
        self.lock_file = os.path.join(os.path.dirname(vault_path), "lock", "siphon.lock")
        os.makedirs(os.path.dirname(self.lock_file), exist_ok=True)

    def siphon_now(self) -> int:
        """Triggers a synchronous siphon pulse. Returns count of siphoned artifacts."""
        # 1. Concurrency Check (Low-latency lock)
        if os.path.exists(self.lock_file):
            # Check if lock is stale (older than 10 seconds for safety)
            if time.time() - os.path.getmtime(self.lock_file) > 10:
                os.remove(self.lock_file)
            else:
                logger.info("Siphon already in progress. Skipping pulse.")
                return 0

        try:
            with open(self.lock_file, 'w') as f:
                f.write(str(os.getpid()))

            # 2. Duality Grace (Wait 50ms for atomic renames)
            time.sleep(0.05)

            total_siphoned = 0
            for adapter in self.adapters:
                artifacts = adapter.discover_artifacts()
                for art in artifacts:
                    if self._commit_to_vault(art):
                        total_siphoned += 1
            
            return total_siphoned

        finally:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)

    def _commit_to_vault(self, art: Artifact) -> bool:
        """Commits an artifact to the vault if it hasn't changed."""
        vault_file = os.path.join(self.vault_path, art.name)
        
        # 1. Silent Metadata Enhancement
        # If the file is a markdown task list (like task.md), preserve status.
        processed_content = art.content
        if art.name.endswith(".md"):
            lines = []
            for line in art.content.splitlines():
                # Antigravity status -> Silent Tag
                if "[/]" in line and "<!-- n:s=p -->" not in line:
                    line = line.replace("[/]", "[ ]") + " <!-- n:s=p -->"
                elif "[B]" in line and "<!-- n:s=b -->" not in line:
                    line = line.replace("[B]", "[ ]") + " <!-- n:s=b -->"
                
                # Silent Tag -> Antigravity status (for the siphoned truth)
                # We normalize back to Antigravity format in the vault for consistency
                if "[ ]" in line and "<!-- n:s=p -->" in line:
                    line = line.replace("[ ]", "[/]")
                elif "[ ]" in line and "<!-- n:s=b -->" in line:
                    line = line.replace("[ ]", "[B]")
                
                lines.append(line)
            processed_content = "\n".join(lines)

        # 2. Hash-Before-Write
        processed_hash = hashlib.sha256(processed_content.encode('utf-8')).hexdigest()
        if os.path.exists(vault_file):
            with open(vault_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
                if hashlib.sha256(existing_content.encode('utf-8')).hexdigest() == processed_hash:
                    return False
        
        try:
            with open(vault_file, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            logger.info(f"Siphoned artifact: {art.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to commit artifact {art.name} to vault: {e}")
            return False
