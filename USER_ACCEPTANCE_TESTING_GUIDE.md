# 🧪 Nucleus v0.6.0: User Acceptance Testing (UAT) Guide

This guide defines the **"Value Validation"** checks to run in Windsurf (or any Agentic IDE). These tests mimic real-world usage patterns for our core personas to ensure Nucleus delivers actual utility, not just security.

---

## 🎭 Persona 1: The "Architect" (Strategic Memory)
**Goal:** Verify the system can act as a "Second Brain" for complex technical decisions.
**Value:** Storing high-fidelity specifications, diagrams, and decisions without corruption.

### 🧪 Test Case 1.1: Cold Start & Schema Storage
> **Prompt:**
> "I am designing the schema for our User Profile system. We decided to use **PostgreSQL** with a JSONB column for `preferences`.
>
> Please save a memory of this decision (`architectural_decision`) with the following Mermaid diagram to visualize it:
> ```mermaid
> erDiagram
>     USER ||--o{ POST : writes
>     USER {
>         uuid id
>         string email
>         jsonb preferences
>     }
> ```
> Tags: Architecture, Database, V1"

**✅ Success Criteria:**
1.  Tool Used: `brain_write_engram`.
2.  Status: Success.
3.  **Critical**: The mermaid diagram code matches the input (no double-escaping of quotes).

### 🧪 Test Case 1.2: Recall & Evolution
> **Prompt:**
> "I forgot what database we picked for the User Profile. Query the memory for 'Architecture' context and tell me the decision. Also, show me the diagram."

**✅ Success Criteria:**
1.  Tool Used: `brain_query_engrams` (with `context="Architecture"` or implicit search).
2.  Result: Retrieves the "PostgreSQL" decision and correctly renders/displays the Mermaid diagram.

---

## 🤖 Persona 2: The "Agentic Swarm" (Tool Expansion)
**Goal:** Verify the system can extend its own capabilities (Sovereignty) via Federation.
**Value:** Models can "install" their own tools to solve new problems.

### 🧪 Test Case 2.1: Tool Discovery (Cold Start)
> **Prompt:**
> "I just installed Nucleus. Check what tools are available in the 'federation' category. I need to know if I can mount external servers."

**✅ Success Criteria:**
1.  Tool Used: `brain_list_tools` (ideally with `category="federation"`).
2.  Result: Lists `brain_mount_server` and `brain_list_mounted`.
3.  Value: The model *knows* it has these powers without being told explicitly.

### 🧪 Test Case 2.2: Async Mounting (Stability)
> **Prompt:**
> "I need a simple echo utility. Mount a new server named `dummy_echo` using the command `cat`.
> Once mounted, discover its tools (it probably has none, but check anyway) and then unmount it."

**✅ Success Criteria:**
1.  Tool Used: `brain_mount_server` -> `brain_discover_mounted_tools` -> `brain_unmount_server`.
2.  **Critical**: NO CRASHES. No "Event loop is running" errors.
3.  Value: Proves the async protocol (V9.3) is stable for complex agent workflows.

---

## 🕵️ Persona 3: The "Researcher" (Precision Retrieval)
**Goal:** Verify the system can filter noise and find needle-in-haystack insights.
**Value:** Saving time by retrieving *exact* context for the task at hand.

### 🧪 Test Case 3.1: Noise Filtering
> **Prompt:**
> "Save two items:
> 1. Key: `lunch_order`, Value: 'Pizza', Context: 'Trivial', Intensity: 1
> 2. Key: `launch_date`, Value: 'February 7th', Context: 'Strategy', Intensity: 10
>
> Now, query specifically for 'Strategy' items. Do NOT return the lunch order."

**✅ Success Criteria:**
1.  Tool Used: `brain_write_engram` (x2) -> `brain_query_engrams`.
2.  Result: Returns *only* the `launch_date` (or sorts it at the top).
3.  Value: Proves the model can trust the system to filter out "garbage" low-intensity memories.

---

## 📊 Summary Checklist
| Persona | Workflow | Value Check | Status |
| :--- | :--- | :--- | :--- |
| **Architect** | Write Diagram | Fidelity (No escaping bugs) | [ ] |
| **Architect** | Read Decision | Recall Accuracy | [ ] |
| **Agent** | Find Capability | Category Discovery | [ ] |
| **Agent** | Mount Server | Async Stability (No Crash) | [ ] |
| **Researcher**| Filter Noise | Context/Intensity Filtering | [ ] |
