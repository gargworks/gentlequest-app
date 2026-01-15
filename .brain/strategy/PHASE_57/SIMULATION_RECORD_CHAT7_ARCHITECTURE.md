# SIMULATION_RECORD_CHAT7_ARCHITECTURE: The Blueprints

**Session:** Chat 7 (Architecture Deep Dive)
**Date:** 2026-01-13
**Status:** ✅ COMPLETED

---

## 1. The Core Principle: Manifest-over-Git

We are **NOT** building a binary repository (like NPM/PyPI).
We are building a **Verification Layer** over Git.

*   **The Code:** Lives in a standard Git Repo (GitHub/GitLab).
*   **The Artifact:** The `.nuke` file is a small, signed JSON object that points to a specific **Commit Hash** in that repo.
*   **The Trust:** The System verifies the Signature of the `.nuke` file, then clones the Repo, and verifies the Commit Hash matches.

---

## 2. Component A: `manifest.yaml` (The Intent)
Lives in the root of the Agent's repo. Defines *what* the agent is and *what* it wants.

```yaml
id: "antigravity.researcher"
version: "1.0.0"
name: "Deep Research Agent"
description: "Crawls the web and summarizes complex topics."
publisher_key: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA..."

capabilities:
  - name: "web_search"
    description: "Search Google and DuckDuckGo"
    risk: "medium"
  
  - name: "memory_read"
    description: "Read context from User Obsidian Notes"
    risk: "high"

lifecycle: "persistent" # Requires Heartbeat
```

---

## 3. Component B: `release.nuke` (The Stamp)
The actual file distributed in the Marketplace Registry. It locks the code to a moment in time.

```json
{
  "manifest_hash": "sha256:a1b2c3d4...",
  "repo_url": "https://github.com/antigravity/researcher.git",
  "commit_hash": "e5f6g7h8...",
  "signature": "sig-ed25519:9z8y7x6w...",
  "timestamp": "2026-01-13T12:00:00Z"
}
```

---

## 4. Component C: `registry.json` (The Web of Trust)
Locally stored in `.brain/registry/`. Maps Agent IDs to trusted Public Keys.

```json
{
  "trusted_publishers": {
    "antigravity": {
      "public_key": "ssh-ed25519 AAAAC3...",
      "trust_level": "verified"
    }
  },
  "installed_agents": {
    "antigravity.researcher": {
      "version": "1.0.0",
      "status": "active",
      "granted_scopes": ["web_search"]
    }
  }
}
```

---

## 5. The Installation Flow

1.  **User:** `brain install antigravity.researcher`
2.  **Nucleus:** Fetches `release.nuke` from Registry.
3.  **Nucleus:** Verifies `signature` against `trusted_publishers`.
4.  **Nucleus:** Clones `repo_url` @ `commit_hash` into `~/.nucleus/agents/antigravity.researcher/`.
5.  **Nucleus:** Verifies `manifest.yaml` hash matches.
6.  **Nucleus:** Reads `capabilities` from manifest.
7.  **Nucleus:** **INTERACTIVE PROMPT:** "Agent wants to 'access web'. Allow? [y/N]"
8.  **Nucleus:** Generates `Grant` with Budget $0.

**Next Step (Chat 8): The GTM Simulation.**
The Tech works. The Ethics work. The Security works.
How do we get the first 100 agents?
**The "Zero to One" Go-To-Market Strategy.**
