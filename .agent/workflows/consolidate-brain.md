# Brain Consolidation Workflow

## Objective
To consolidate and archive the rapidly growing `.brain/raw/` directory, preparing the data for long-term storage and extracting valuable insights for marketing and blog content.

## Workflow Steps

### 1. Session Context Preservation (The "Save")
This step preserves the current session depth to ensure continuity in future sessions.

1.  **Save Session Depth**
    *   Command: `python3 scripts/save_session_context.py`
    *   *Goal:* This script saves the current session's depth information to `session/depth.json`. This file is used to track the progress of the agent across multiple sessions. [Link to script](scripts/save_session_context.py)

### 2. Log Rotation and Archival (The "Clean")
This step manages the log files, archiving older logs to prevent excessive disk usage.

1.  **Rotate Logs**
    *   Command: `python3 scripts/nightly_agent.py rotate_logs`
    *   *Goal:* Rotates the agent's log files, archiving older logs based on a predefined schedule. This helps maintain a manageable log file size and prevents disk space exhaustion. [Link to script](scripts/nightly_agent.py)

2.  **Archive Raw Monologues**
    *   Archives `.brain/raw/` content based on size. Triggers deep archival if over 100MB.

### 3. Data Migration (The "Migrate")
This step migrates valuable artifacts (e.g., specific outputs) to a designated storage location.

1.  **Migrate Artifacts**
    *   Command: `python3 scripts/nightly_agent.py migrate_artifacts`
    *   *Goal:* Migrates essential artifacts, such as key outputs from the agent's operations, to a persistent storage location. This ensures that critical data is preserved even after a session ends. [Link to script](scripts/nightly_agent.py)

    *   Identifies and moves key files to a backup location.
    *   Deletes migrated files from the active `.brain/` directory.

### 4. Marketing Extraction (The "Value")
This step extracts key insights for marketing (blog posts, jargons).

1.  **Extract Marketing Gold** (requires GEMINI_API_KEY)
    *   Command: `python3 scripts/marketing_autopilot.py extract`
    *   *Goal:* Scans recent `RAW_MONOLOGUE` files for keywords like "Neural", "Agentic", "System", "Protocol" and saves them to `marketing/insights.md`.  This script leverages the GEMINI_API_KEY to identify and extract relevant marketing insights from the raw monologue data. [Link to script](scripts/marketing_autopilot.py)

### 5. Blog Export Phase (The "Publish") ⭐ NEW
This step prepares walkthroughs with embedded recordings for direct blog publication.

1.  **Identify Blog-Ready Walkthroughs**
    *   Search for: `BLOG_*.md`, `WALKTHROUGH_*.md` with embedded `.webp` or `.png`
    *   These contain `![caption](absolute_path)` media embeds

2.  **Export Blog Bundle**
    *   Command:
    ```bash
    ./scripts/export_blog.sh  # See BLOG_EXPORT_PROTOCOL.md
    ```
    *   *Goal:* Creates a self-contained blog export bundle in `./blog-export-YYYYMMDD/`. This bundle includes the Markdown file (with updated relative paths for assets) and an `assets/` folder containing all the necessary media files. [Link to script](scripts/export_blog.sh)
    *   Creates: `./blog-export-YYYYMMDD/` with:
        *   Markdown files (paths updated to relative)
        *   `assets/` folder with all media files

3.  **Available Recordings for Embedding:**
    | Recording | Size | Topic |
    |-----------|------|-------|
    | `cloud_run_e2e_test_*.webp` | 3.5MB | Cloud Run deployment |
    | `nucleus_hud_e2e_test_*.webp` | 8.5MB | HUD end-to-end test |
    | `nucleus_demo_*.webp` | 1-3MB | PyPI/Demo recordings |

4.  **For Astro/Starlight Blog:**
    *   Copy to `src/content/blog/` and `public/walkthrough-assets/`
    *   Update paths: `s|absolute_path|/walkthrough-assets/|g`

### 6. Assessment
*   Check the size of `.brain/raw/`. If > 100MB, trigger deep archival.
*   Verify `session/depth.json` is reset for the new session.
*   Generate `CONSOLIDATION_REPORT_YYYYMMDD.md` with:
    *   Captured logs count
    *   Migrated artifacts list
    *   Blog candidates identified