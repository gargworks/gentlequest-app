"""
Nucleus Artifact Management
===========================
Read and write files in the .brain/artifacts directory.
"""

import os
from pathlib import Path
from typing import Optional, List

BRAIN_ROOT = Path(os.getenv("NUCLEUS_BRAIN_PATH", ".brain"))
ARTIFACTS_DIR = BRAIN_ROOT / "artifacts"


def read_artifact(path: str) -> Optional[str]:
    """
    Read contents of an artifact file.
    
    Args:
        path: Relative path within .brain/artifacts (e.g., "ideas/inbox.md")
        
    Returns:
        File contents as string, or None if file doesn't exist
    """
    try:
        file_path = ARTIFACTS_DIR / path
        if file_path.exists():
            return file_path.read_text()
        return None
    except Exception as e:
        print(f"Artifact read error: {e}")
        return None


def write_artifact(path: str, content: str, append: bool = False) -> bool:
    """
    Write content to an artifact file.
    
    Args:
        path: Relative path within .brain/artifacts (e.g., "ideas/inbox.md")
        content: Content to write
        append: If True, append to existing file instead of overwriting
        
    Returns:
        True if successful
    """
    try:
        file_path = ARTIFACTS_DIR / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if append:
            with open(file_path, "a") as f:
                f.write(content)
        else:
            file_path.write_text(content)
        
        return True
    except Exception as e:
        print(f"Artifact write error: {e}")
        return False


def list_artifacts(folder: Optional[str] = None) -> List[str]:
    """
    List artifact files in a folder.
    
    Args:
        folder: Optional subfolder within .brain/artifacts
        
    Returns:
        List of relative file paths
    """
    try:
        search_dir = ARTIFACTS_DIR / folder if folder else ARTIFACTS_DIR
        if not search_dir.exists():
            return []
        
        artifacts = []
        for item in search_dir.rglob("*"):
            if item.is_file():
                artifacts.append(str(item.relative_to(ARTIFACTS_DIR)))
        return sorted(artifacts)
    except Exception as e:
        print(f"Artifact list error: {e}")
        return []
