---
description: Run the Brain Consolidation Protocol (Periodic Saving & Marketing Capture)
---

# Brain Consolidation Protocol

**Trigger:** Run this via `/consolidate-brain`
**Frequency:**
*   **Routine:** Once per day (Nightly)
*   **On-Demand:** After any significant "Monologue" or creative session where marketing gold/jargons were generated.

## Objective
To capture, preserve, and consolidate the "Neural Pathways" (thought processes, raw logs, blog drafts) into the Brain, ensuring nothing is lost to context window limits.

## 1. Capture Phase (The "Save")
This step ensures that recent interactions, especially creative/marketing outputs, are saved to persistent storage.

1.  **Run Session Saver**
    *   Command: `python3 scripts/save_session_context.py`
    *   *Goal:* Dumps the current active session memory and generic "Raw Monologue" into `.brain/raw/`.

## 2. Consolidation Phase (The "Prune")
This step cleans up the artifacts, merges redundancies, and prepares the brain for the next session.

1.  **Run Nightly Agent**
    *   Command: `python3 scripts/nightly_agent.py`
    *   *Goal:* Wakes up the `Librarian` agent to scan for:
        *   Stale commitments
        *   Unprocessed `RAW_MONOLOGUE` files
        *   Duplicate artifacts

## 3. Marketing Extraction (The "Value")
This step extracts key insights for marketing (blog posts, jargons).

1.  **Extract Marketing Gold**
    *   Command: `python3 scripts/marketing_autopilot.py extract`
    *   *Goal:* Scans recent `RAW_MONOLOGUE` files for keywords like "Neural", "Agentic", "System", "Protocol" and saves them to `marketing/insights.md`.

## 4. Assessment
*   Check the size of `.brain/raw/`. If > 100MB, trigger deep archival.
*   Verify `session/depth.json` is reset for the new session.
