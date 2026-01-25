# 🧬 Design Journal - Phase 9: Knowledge Retrieval (The Memory Bank)

## 1. Context
Agents currently have "short-term memory" (the context window).
They lack "long-term memory" (access to historical decisions, patterns, or context).
We have `.brain/memory/*.md`, but agents don't know how to query it effectively.

## 2. Problem
A `Developer` agent might solve a bug that was already solved 2 weeks ago.
A `Strategist` might propose a pivot that violates the "Immutable Principles" in `context.md`.
Agents are "amnesic" beyond the current session.

## 3. Solution (The Memory Bank)
We need a **Retrieval System** that allows agents to:
1.  **Search**: "Has this error occurred before?" (Query `learnings.md`).
2.  **Recall**: "What are our design principles?" (Read `context.md`, `patterns.md`).
3.  **Synthesize**: "What is the history of this feature?" (Search `decisions.md`).

## 4. Architecture
*   **Cluster**: `Memory`
*   **Tool 1**: `brain_search_memory(query)`
    *   Uses `ripgrep` to search `.brain/memory/` and `.brain/ledger/decisions.md`.
    *   Returns snippets with file context.
*   **Tool 2**: `brain_read_memory(category)`
    *   Reads specifically `context`, `patterns`, `learnings`, or `decisions`.
    *   Returns full content (chunked if too large).

## 5. Implementation Plan
1.  **Tool**: `brain_search_memory` (Wrapper around `rg`).
2.  **Tool**: `brain_read_memory` (Wrapper around `read_file` with preset paths).
3.  **Integration**: Update `Librarian` persona (and `Synthesizer`) to use these.
4.  **Verification**: Test retrieval of specific facts (e.g., "What is the Nucleus Vision?").
