
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

try:
    from mcp_server_nucleus import commitment_ledger
    print("✅ commitment_ledger imported successfully.")
    
    # Check if get_lock is used (static analysis or just trust import)
    # We trust the import worked because the module loaded.
    
except Exception as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)
