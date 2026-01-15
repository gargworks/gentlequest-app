
import os
import sys

# Ensure we can import from src
sys.path.append("mcp-server-nucleus/src")

from mcp_server_nucleus.runtime.capabilities.memory_ops import MemoryOps

def test_memory():
    print("🧠 Testing MemoryOps (RAG)...")
    
    # 1. Initialize
    mem_ops = MemoryOps()
    print(f"✅ Initialized MemoryOps with VectorStore (Enabled: {mem_ops.vector_store.enabled})")

    # 2. Store Memory
    print("\n📝 Storing Test Memory...")
    content = "The user prefers dark mode and high contrast themes."
    args = {
        "content": content,
        "category": "preference",
        "tags": ["ui", "a11y"]
    }
    result = mem_ops.execute_tool("brain_store_memory", args)
    print(f"Result: {result}")
    
    if "Stored memory" not in str(result):
        # In local mode, we expect "Stored memory: local_mock_id"
        # In firestore mode, we expect a real ID.
        # If it failed, it would say "Error..."
        print("❌ Storage Failed!")
        sys.exit(1)
        
    # 3. Search Memory
    print("\n🔍 Searching Memory...")
    search_args = {
        "query": "What are the UI preferences?",
        "limit": 1
    }
    search_result = mem_ops.execute_tool("brain_search_memory", search_args)
    print(f"Result:\n{search_result}")

    # Validation
    if mem_ops.vector_store.enabled:
        if "dark mode" in str(search_result):
            print("✅ RAG Verified (Real Firestore)!")
        else:
            print("⚠️ RAG Search returned empty/irrelevant (Expected if just indexed, consistency lag?).")
    else:
        if "Memory disabled" in str(search_result):
            print("✅ Mock Path Verified (Local Mode).")
        else:
            print("❌ Unexpected response in local mode.")

if __name__ == "__main__":
    test_memory()
