# Why Synthesizer Ignores Your Tools: An Analysis

> **Question:** "Why is [Synthesizer] not using the commands, the brain 50+ mcp command that we have given to you?"

---

## The Root Cause: Cognitive Overload & "Prompt Drift"

Even for an LLM, 50+ tools is a massive cognitive load. When an agent like Synthesizer is prompted, it sees a giant list of function definitions.

### 1. The "Paradox of Choice" for LLMs
When you give an LLM 50 tools, the probability of it using *any specific one* drops.
*   **Safety Bias:** LLMs are fine-tuned to be helpful and safe. Writing a markdown list feels "safer" and more robust than calling an external function that might error out.
*   **Instruction Dilution:** If the system prompt says "You are a helpful assistant" and then lists 50 complex database tools, the model defaults to "Assistant Mode" (chatting/writing) rather than "Operator Mode" (executing).

### 2. The "Invisible Tool" Problem
Tools like [brain_add_loop](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/__init__.py#3518-3558) often have abstract descriptions.
*   If the description says "Add a loop to the brain", the LLM evaluates: *"Is this a loop? Or just a task?"*
*   Uncertainty leads to fallback behavior: **Writing text.**

### 3. Agent Persona vs. Toolset Mismatch
Synthesizer is prompted to "Synthesize" (think, write, summarize). It is *not* prompted to "Execute" or "Manage Database".
*   **Critique:** You gave a "Thinker" agent a "Doer" toolset.
*   **Result:** It ignores the tools because they don't fit its primary directive.

---

## The Solution: Forced Tool Use & Thinning

To get Synthesizer (and others) to use the tools, we must:

1.  **Reduce the Toolset (Context Window Hygiene):**
    *   Don't dump 50 tools on every agent.
    *   Give Synthesizer *only* `read_file` and [brain_add_loop](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/__init__.py#3518-3558). It will use them if they are the only interaction methods.

2.  **Directive Prompts ("Chain of Action"):**
    *   Instead of "You have these tools...", use:
    *   *"You are a Database Operator. Your ONLY output should be tool calls. Do not chat. Translate the user's request into [brain_add_loop](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/__init__.py#3518-3558) calls."*

3.  **Active Correction (The "Critic"):**
    *   If Synthesizer outputs a markdown list, the system (or a Critic agent) should intercept it and say: *"Error: Output detected as text. Retry using [brain_add_loop](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/__init__.py#3518-3558) tool."*

## Recommendation

**Don't blame the model; blame the context.**
If we want tool usage, we must **constrain the agent** so that tool usage is the path of least resistance.

*   **Action:** Create a targeted "Librarian" agent whose *sole job* is to take Synthesizer's output and call the tools. Don't ask Synthesizer to do both thinking and filing.
