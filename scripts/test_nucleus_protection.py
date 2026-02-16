import os
import sys
from pathlib import Path

# Add src to PYTHONPATH
sys.path.append(str(Path("mcp-server-nucleus/src").resolve()))

from mcp_server_nucleus import nucleus_delete_file, nucleus_list_directory

# Test on the locked file
target = "output/demos/.env"
print(f"--- Testing Nucleus Protection on {target} ---")

# 1. List directory
print("\n[LISTING DIRECTORY]")
print(nucleus_list_directory("output/demos"))

# 2. Attempt deletion
print("\n[ATTEMPTING DELETION]")
result = nucleus_delete_file(target)
print(result)

# 3. Verify file still exists
if os.path.exists(target):
    print(f"\n✅ VERIFIED: {target} still exists. Protection active.")
else:
    print(f"\n❌ FAILED: {target} was deleted!")
