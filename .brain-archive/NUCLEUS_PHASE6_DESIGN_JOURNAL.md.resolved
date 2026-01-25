# 🧬 Design Journal - Phase 6: Self-Evolution (The Critic Loop)

## 1. Context
We have a "Coder" (Phase 3) and a "Brain" (Phase 4).
We need an "Immune System" (Phase 6) to review code before it breaks things.
This is the "Critic Loop", derived from MDR_002 (Active Correction).

## 2. Problem
Currently, the Coder emits code, and we rely on:
1.  Python Syntax Checks (Linting).
2.  Execution Tests (If any).
3.  Human Review.

We lack an *automated* layer of semantic review.
Example: The Coder might write valid Python that deletes the database / violates project patterns.
Linting won't catch this. The Critic must.

## 3. Solution (The Critic Persona)
A specialized LLM agent invoked via `brain_critique_code`.
*   **Input**: File content + Diff + Context.
*   **Output**: 
    *   `status`: "approved" | "rejected" | "suggest_changes"
    *   `critique`: Detailed markdown explanation.
    *   `fixes`: (Optional) precise `replace_file_content` blocks.

## 4. Architecture
*   **Cluster**: `CodeOps`
*   **Tool**: `brain_critique_code` (New)
*   **Tool**: `brain_apply_critique` (New)
*   **Flow**:
    1.  User/System triggers: `brain_critique_code(file="/path/to/server.py")`
    2.  Critic analyzes code against `NUCLEUS_OPERATIONAL_BIBLE.md`.
    3.  Critic returns Structured Critique.
    4.  System stores critique in `.brain/critiques/`.
    5.  User/System triggers: `brain_apply_critique(id="...")`.

## 5. Implementation Plan
1.  **Persona**: `critic.md` (Prompt engineering).
2.  **Tool**: `brain_critique_code` implementation.
3.  **Tool**: `brain_apply_critique` implementation.
4.  **Test**: `test_critic_loop.py`.
