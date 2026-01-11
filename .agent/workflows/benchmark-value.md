---
description: Run a comparative value benchmark (Generic vs Nucleus) for a feature.
---

# Omega Protocol: Value Benchmarking

**Purpose:** Quantify the "Nucleus Premium" by executing a task twice: once as a standard AI (Blind) and once as an Agentic AI (Nucleus).

## 1. Define the Task
Identify a pending feature (e.g., "Create a Contact Form").

## 2. Execute Task A: Generic Mode (Blind)
*   **Role:** "Standard Expert AI"
*   **Tools:** `write_to_file`, `replace_file_content` ONLY.
*   **Constraint:** DO NOT read `package.json`, `globals.css`, or `.brain/`. Make standard assumptions.
*   **Output:** `Generic[Component].tsx`

## 3. Execute Task B: Nucleus Mode (Context-Aware)
*   **Role:** "Nucleus Agent"
*   **Trigger Vectors:**
    *   **Chat:** Direct request in Antigravity.
    *   **Inbox:** Drop `.md` file in `.brain/inbox/`.
    *   **Cloud:** Hit `/api/autopilot`.
*   **Workflow:**
    1.  **Strategy:** Check/Update Strategy.
    2.  **Context:** Read `package.json`, styles, related code.
    3.  **Code:** Implement `Nucleus[Component].tsx`.
    4.  **Critic:** Run `brain_critique_code`.
    5.  **Event:** Emit `feature_registered`.

## 4. Evaluate & Score
Compare the two outputs on:
*   **Build Safety:** Does it import missing libs?
*   **Style Match:** Does it look like the app?
*   **Business Logic:** Does it respect the project vision?
*   **Accessibility:** Is it usable?
*   **Critic Score:** Run Critic on BOTH files.

## 5. Report
Update `NUCLEUS_GRAND_VERIFICATION_REPORT.md` with the comparison matrix.
