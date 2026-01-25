# Phase 56: Agentic Memory V2 (Firestore RAG)

## Goal
Implement "Deep Memory" for Nucleus Agents using Firestore Vector Search. This allows agents to retrieve relevant context from a massive archive of past interactions, documentation, and learnings, overcoming context window limits.

## Core Components

### 1. `FirestoreMemory` Adapter
A new class in `runtime/memory.py` (or similar) that handles:
- **Embedding Generation**: Using `google-genai` (Model: `text-embedding-004`).
- **Vector Storage**: Storing chunks in Firestore collection `nucleus_memory`.
- **Vector Search**: Using Firestore's `find_nearest` (KNN).

### 2. `MemoryOps` Implementation
Update `runtime/capabilities/memory_ops.py` to:
- Implement `brain_store_memory(content, metadata)`: Stores text with embedding.
- Implement `brain_search_memory(query)`: RAG retrieval.

## Schema
**Collection**: `nucleus_memory`
**Document**:
```json
{
  "content": "Text content...",
  "embedding": [0.1, -0.5, ...],  // Vector
  "metadata": {
    "source": "session_123",
    "timestamp": "2026-01-12T...",
    "category": "learning"
  }
}
```

## Proposed Changes

### [NEW] [mcp-server-nucleus/src/mcp_server_nucleus/runtime/vector_store.py](mcp-server-nucleus/src/mcp_server_nucleus/runtime/vector_store.py)
- Encapsulates `google-genai` client and `firestore` vector operations.

### [MODIFY] [mcp-server-nucleus/src/mcp_server_nucleus/runtime/capabilities/memory_ops.py](mcp-server-nucleus/src/mcp_server_nucleus/runtime/capabilities/memory_ops.py)
- Implement `execute_tool`.
- Add `brain_store_memory` tool.

## Verification
1.  **Test Script**: `scripts/verify_memory.py`
    - Store a fact: "The user prefers dark mode."
    - Search: "What are the user's UI preferences?"
    - Expect: Retrieval of the fact.
