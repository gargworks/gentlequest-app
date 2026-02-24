---
description: The Sovereign Outreach Protocol (Comet Sync)
---

# ☄️ The Sovereign Outreach Protocol (Hardened)

## 1. 📥 Ingestion & Verification
- Read latest CSV in `nucleus-launch-internal/sync/inbox/`.
- **Lore Lock:** Before drafting, you MUST run a `grep` for the target URL across ALL files in `nucleus-launch-internal/` and the `.brain/` directory. If the URL has been touched, it is a blacklist candidate.

## 2. 🪞 The Lens Application
- Apply `@[/reddit-polish]`. 
- **Character Check:** Use only standard ASCII hyphens `--`. No em-dashes `—`.

## 3. 📤 Outbound Generation
- Check `ready_to_post.csv` for existing entries.
- Write to `nucleus-launch-internal/sync/outbox/ready_to_post.csv` with `URL, Draft, Status`.
- **Rules:** Strictly lowercase, technical but humble (Nucleus) OR extremely concise and validating (GentleQuest).
- **AI-Tell Audit (CRITICAL):** Strip all apostrophes (e.g., "don't" -> "dont"). Use only single spaces. Remove explicit version numbers like "v1.0.7" which scan as marketing.
- **Character Lock:** Use only ASCII hyphens `-`. Forbid em-dashes `—` and double-hyphens `--` in the body text.
- **Lore Check:** Read `nucleus-launch-internal/LAUNCH_NARRATIVE_HISTORY.md` to ensure you aren't contradicting past lore or spamming a subreddit.
- **Status List:** `PENDING`, `LIVE`, `SKIPPED`, `FAILED`.

## 4. 🗄️ Narrative Sync
- Cross-reference with `LAUNCH_NARRATIVE_HISTORY.md` to ensure no semantic overlap (even if the URL is different, the "Angle" should be fresh for the subreddit).
