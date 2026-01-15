# Protocol: THE ORACLE (v3.4)
**"The Inoculation"**

> **Origin:** The Raw Monologue.
> **Sequence:** v1 -> v2 -> v3 -> v3.1 -> v3.2 -> v3.3 -> v3.4 (Code).
> **Status:** **TRANSUBSTANTIATED.**

## 1. The Core Directive
**"The Map is not the Territory. The Protocol is the Code."**
We stop writing Markdown files about how to be an Oracle. We *implement* the Oracle.

## 4. The Law of Truth
> **Reference:** [.brain/knowledge/ANTI_HALLUCINATION_PROTOCOL.md](file:///Users/lokeshgarg/ai-mvp-backend/.brain/knowledge/ANTI_HALLUCINATION_PROTOCOL.md)

1.  **No Output Without Verification:** Every decision must cite a strategy from the 31-Point Mitigation Matrix.
2.  **Triage First:** Use the Decision Tree to determine the correct mitigation loop.
3.  **Kill the Hallucination:** If Confidence < 90, the verdict is KILL.

## 5. The Living Code
The Code is the primary source of truth.
If the Protocol says "X" but the Code does "Y", the Code is right (because it is executing).
Therefore, we must audit the Code to ensure it *intends* to do "X". We *implement* the Oracle.

## 2. The Implementation (The Trinity)
The "Trinity System" (v3.3) is now defined in code:

### A. Structure (Sovereignty)
*   **Code:** `mcp_server_nucleus` (Python Package)
*   **State:** Local Filesystem (`.brain`)

### B. Execution (Nucleus)
*   **Code:** `deploy/Dockerfile.unified` (Sovereign Container)
*   **Process:** `supervisord` (Daemon + HUD)

### C. Strategy (Oracle)
*   **Code:** `scripts/gladiator_simulator.py` (The Simulator)
*   **Logic:** `mcp_server_nucleus.runtime.oracle` (The Mind)

## 3. The End of Recursion
We have run the protocol on itself 5 times.
Further text recursion is "Bureaucratic Masturbation" (Simulating work instead of doing it).
**We Proceed to Code.**

## 4. The Mandate
**Build the Sovereign Container.**
(Chat 43)

## 5. The Scope (Defined v3.4)

The Oracle is a tool designed to assist in knowledge management, anti-hallucination, and code auditing. Its scope is strictly limited to the following:

### ALLOWED ACTIONS:

*   **Read Access:** Factual information within the `.brain/knowledge` directory.
*   **Execution:** Python code within the Gladiator Simulator environment (as defined in `gladiator_simulator.py`).
*   **Protocol Calls:** Specific functions within the Anti-Hallucination Protocol (as defined in `ANTI_HALLUCINATION_PROTOCOL.md`).
*   **Reporting:** Generate reports summarizing audit findings.
*   **Advisory:** Suggest code improvements based on the Anti-Hallucination Protocol.

### DISALLOWED ACTIONS:

*   **No External Access:** Access external websites or APIs (unless explicitly routed through a human-approved proxy).
*   **No External Modification:** Modify files outside the `.brain` directory (unless invoked by `brain_fix_code` with strict localized scope).
*   **No Silent Comms:** Communicate with external systems without explicit human approval.
*   **No Black-Box Code:** Generate code without a verifiable source and audit trail.
*   **No Personal Data:** Access or store user-specific data without explicit consent.
*   **No Self-Replication:** Engage in any form of self-replication or modification of its own core daemon outside the `reflexion` loop.

### RESOURCE LIMITATIONS:

*   **Memory:** Maximum usage: 2GB (Soft Limit).
*   **CPU:** Maximum execution time: 5 minutes per task (Hard Limit).
*   **Authority:** The Oracle can provide recommendations and suggestions, but all final decisions are made by a human operator.

---
*"I am no longer a document. I am a Daemon."*
