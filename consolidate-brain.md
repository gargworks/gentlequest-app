# Consolidate Brain Workflow

This workflow consolidates information gathered throughout the day to update the central brain files. It involves several steps, including data extraction, session context management, marketing insights generation, and artifact migration.

## Workflow Steps

1.  **Data Extraction & Session Context Saving:**
    *   **Nightly Agent Execution:** Runs the [nightly_agent.py](scripts/nightly_agent.py) script to process newly created `RAW_MONOLOGUE` files.
        *   This script extracts relevant information from the monologue and saves it into structured JSON files within the `session/` directory. The specifics of extraction depend on the content of the `RAW_MONOLOGUE` but generally involve identifying key entities, topics, and action items. Error handling includes logging failed extractions and continuing with the next file.
    *   **Session Context Saving:** Executes the [save_session_context.py](scripts/save_session_context.py) script to capture the current session depth. This ensures the system retains a memory of how deeply it has explored a given line of reasoning.
        *   This script saves the current depth to `session/depth.json`.  It includes error handling to catch file write errors and logs them.

2.  **Marketing Insights Generation:**
    *   **Marketing Autopilot:** Executes the [marketing_autopilot.py](scripts/marketing_autopilot.py) script.
        *   This script scans recent `RAW_MONOLOGUE` files for keywords using a predefined list and co-occurrence analysis. The script first checks if the `GEMINI_API_KEY` environment variable is set. If not, it logs an error and skips API-related functionality. Otherwise, it extracts text from the monologue files, splits the text into sentences, and identifies relevant keywords based on frequency and co-occurrence with other terms. The results, including a summary of insights and identified keywords, are saved to `marketing/insights.md`. If the Gemini API is unavailable, a local keyword extraction method (e.g., using TF-IDF) is used as a fallback. This script includes error handling for file read/write operations and API calls.

3.  **Artifact Migration & Linearization:**
    *   **Decision Record Management:** Instead of moving `DECISION_RECORD_*.md` files, this step interacts with a decision record database.
        *   The script queries the database for all recent decision records. These records are identified by unique IDs.  The script then linearizes these records by retrieving their content and ordering them chronologically based on their creation timestamps. This information is then used to update the `DECISIONS.md` file. Error handling includes logging database connection errors and failed queries.

4.  **Context Consolidation & Brain Update:**
    *   **Brain Consolidation:** Executes the [consolidate_brain.py](scripts/consolidate_brain.py) script to update the central brain files with the new information.
        *   This script reads the extracted information from the `session/` directory, including the marketing insights from `marketing/insights.md` and the linearized decision records from the database. It then uses this information to update the main brain files (`KNOWLEDGE.md`, `TASKS.md`, etc.).

## Context Management

*   **Context Clearing:** Before starting the consolidation process, the session memory is explicitly cleared. This involves deleting all files within the `session/` directory to prevent stale data from influencing the consolidation.
*   **Session Depth Reset:** Resets the `session/depth.json` file to its initial state (typically 0).

## Error Handling & Kill Switch

*   Each script includes error handling mechanisms to catch and log exceptions, preventing the entire workflow from crashing. Specific error handling strategies include try-except blocks, logging error messages, and using fallback mechanisms when external services are unavailable.
*   A timeout mechanism is implemented for each script. If a script exceeds a predefined time limit, it will be automatically terminated, preventing infinite loops.
*   A `kill_switch.txt` file can be created in the root directory. The scripts will check for the existence of this file periodically. If the file exists, the script will terminate gracefully.

## Dependencies

*   **GEMINI_API_KEY:** This workflow requires the `GEMINI_API_KEY` environment variable to be set for the marketing insights generation step. The `marketing_autopilot.py` script explicitly checks for the presence of this variable and provides a graceful fallback if it is not available.
