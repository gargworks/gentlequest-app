
import os
import sys
from pathlib import Path

# Setup Path
sys.path.append(os.path.join(os.getcwd(), 'mcp-server-nucleus', 'src'))

from mcp_server_nucleus.runtime.capabilities.synthesizer import brain_synthesize_status_report

print("Testing brain_synthesize_status_report()...")
result = brain_synthesize_status_report(os.getcwd())

if result.get("status") == "success":
    print("\n✅ REPORT GENERATED:\n")
    print(result.get("report"))
else:
    print(f"\n❌ FAILED: {result.get('message')}")
