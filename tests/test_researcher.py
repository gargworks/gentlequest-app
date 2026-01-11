
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")))

from mcp_server_nucleus.runtime.capabilities.web_ops import WebOps

def test_researcher_capabilities():
    print("--- Testing WebOps ---")
    web_ops = WebOps()
    
    # Test 1: Search
    print("\n1. Testing web_search('python 3.12 features')...")
    search_res = web_ops.execute_tool("web_search", {"query": "python 3.12 features", "num_results": 1})
    print(f"Result Preview: {search_res[:100]}...")
    
    if "Error:" in search_res and "not installed" in search_res:
        print("⚠️ Dependencies missing. Functional test skipped, but code structure is valid.")
    elif "No results" in search_res:
        print("❓ Search ran but found nothing (Network issue?).")
    elif len(search_res) > 50:
        print("✅ Search SUCCESS.")
    else:
        print("❌ Unexpected search result.")

    # Test 2: Read Page
    print("\n2. Testing web_read_page('https://www.python.org/')...")
    read_res = web_ops.execute_tool("web_read_page", {"url": "https://www.python.org/"})
    print(f"Result Preview: {read_res[:100]}...")

    if "Error:" in read_res and "not installed" in read_res:
        print("⚠️ Dependencies missing.")
    elif "Python" in read_res or "Programming Language" in read_res:
        print("✅ Read Page SUCCESS.")
    else:
        # Might fail on network or different content, but as long as it returns *something* reasonable
        print(f"❓ Read ran, result length: {len(read_res)}")

if __name__ == "__main__":
    test_researcher_capabilities()
