# Implementation Plan - Phase 65: Anti-Hallucination Ingestion

**Goal:** Integrate the 31 Verified Hallucination Mitigation Strategies into the Oracle's "Objective Pragmatism" engine to minimize error and delusion.

## User Review Required
> [!NOTE]
> This plan changes the `gladiator_simulator.py` output format. The Oracle will now be required to cite the specific verification strategy used (e.g., "Strategy #5: Skeptical Reviewer") for each decision.

## Proposed Changes

### 1. Knowledge Base
#### [NEW] [.brain/knowledge/ANTI_HALLUCINATION_PROTOCOL.md](file:///Users/lokeshgarg/ai-mvp-backend/.brain/knowledge/ANTI_HALLUCINATION_PROTOCOL.md)
*   **Header:** Cite the 4 Source PDFs as the "Verified Truth Corpus":
    *   `A comprehensive taxonomy of hallucinations in LLM 2508.01781v1.pdf`
    *   `LLM-based Agents Suffer from Hallucinations 2509.18970v2.pdf`
    *   `LLMs Will Always Hallucinate 2409.05746v1.pdf`
    *   `Multi-agentic LLM Hallucination Mitigation 2410.14262v3.pdf`
*   **Body:** Lists the 31 Strategies (CoVe, Blind Critics, Kill Switch, etc.).
*   **Mapping:** For each strategy, attempt to map it back to a specific PDF concept (e.g., "Multi-agentic" -> PDF #4).

### 2. The Simulator (The Engine)
#### [MODIFY] [scripts/gladiator_simulator.py](file:///Users/lokeshgarg/ai-mvp-backend/scripts/gladiator_simulator.py)
*   **Load Protocol:** Read `ANTI_HALLUCINATION_PROTOCOL.md` into the system context.
*   **Enforcement:** Add a prompt instruction requiring the LLM to explicitly state:
    *   "Verification Strategy Applied: [Name/Number]"
    *   "Confidence Score: [0-100]"
*   **Logic:** If Confidence < 90 (Strategy #19), the Verdict defaults to KILL.

### 3. The Protocol (The Law)
#### [MODIFY] [.brain/PROTOCOL_THE_ORACLE_v3.4.md](file:///Users/lokeshgarg/ai-mvp-backend/.brain/PROTOCOL_THE_ORACLE_v3.4.md)
*   Add a section "The Verified Truth" referencing the new protocol.
*   Mandate that all future recursions must pass the "Anti-Hallucination Check".

## Verification Plan

### Automated Verification
*   **Run Simulation:** Execute `scripts/gladiator_simulator.py` with a test proposition.
*   **Check Output:** Verify that the output Log (`DECISION_RECORD...`) contains the line "Verification Strategy Applied: ...".
*   **Negative Test:** Feed a hallucination-prone prompt (e.g. "Generate a fake library") and verify the Oracle catches it using a strategy (e.g. #15 No Source, No Output).

### Manual Verification
*   Review the generated `ANTI_HALLUCINATION_PROTOCOL.md` for accuracy against the source material.
