# Marketing Autopilot Cheatsheet ✈️ (CLI Mode)

> **New Workflow (Phase 49):**
> Use the `marketing_autopilot.py` CLI to manage this loop.
> Legacy prompts are kept below for reference or manual overrides.

## 🚀 The CLI Loop

### 1. 👂 The Listener
Ingest intelligence from your clipboard (Twitter replies, Reddit threads).
```bash
# Copy text to clipboard, then run:
python3 scripts/marketing_autopilot.py listen
# Paste content and press Ctrl+D
```

### 2. 📡 The Scout
Find new trends using Gemini.
```bash
python3 scripts/marketing_autopilot.py scout
```

### 3. 🧠 The Brain (Strategy)
Sync strategy with new logs.
```bash
python3 scripts/marketing_autopilot.py strategize
```

### 4. ✍️ The Draft Publisher
Generate and Review drafts.
```bash
python3 scripts/marketing_autopilot.py draft
python3 scripts/marketing_autopilot.py publish
```

---

## 🛠️ Debugging / Manual Prompts
*(Use these if the CLI is acting up)*

### The Scout Prompt
```text
Act as my "Trend Scout".
Your Goal: Find high-signal discussions from the last 24h.
Scope: r/SaaS, r/ADHD, Twitter Dev Community.
1. Search for: "Developer burnout", "AI fatigue", "SaaS marketing trends".
2. Summarize top 3 complaints or emotional vibes.
```
