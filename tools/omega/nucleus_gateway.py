
import sys
import os
import time
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

try:
    from mcp_server_nucleus import _emit_event
except ImportError:
    # Fallback for verification
    def _emit_event(t, e, d): print(f"EMIT: {t} {json.dumps(d)}")

INBOX_PATH = Path("/Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/inbox")

def check_inbox():
    if not INBOX_PATH.exists():
        INBOX_PATH.mkdir(parents=True)
        print(f"Created Inbox at {INBOX_PATH}")
        return

    print(f"Scanning Inbox: {INBOX_PATH}")
    for file in INBOX_PATH.glob("*.md"):
        print(f"Found Trigger: {file.name}")
        content = file.read_text()
        
        # Emit Event
        _emit_event("task_received", "inbox_gateway", {
            "source": "file_drop",
            "filename": file.name,
            "content_preview": content[:100]
        })
        
        # Archive it to acknowledge
        archive_path = INBOX_PATH.parent / "archive"
        archive_path.mkdir(exist_ok=True)
        file.rename(archive_path / f"{int(time.time())}_{file.name}")
        print(f"Processed & Archived: {file.name}")

if __name__ == "__main__":
    check_inbox()
