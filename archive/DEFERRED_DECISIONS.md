# Deferred decisions — consolidation of 2026-08-27

Items inventoried during the consolidation but deliberately NOT acted on. Each
needs a decision by the operator (or the nucleus lane) before anything moves.
Nothing here is a recommendation to delete; it is a list of what was found and
why it was left alone.

## Nucleus / Eidetic–flagged (found in this repo, out of this consolidation's lane)

Ordered by how much they matter:

1. **`nucleus-launch-internal/` (47M, tracked)** — its own README says
   "NEVER COMMIT TO PUBLIC REPO", yet it is fully tracked here. Fine while both
   remotes are private; a real exposure if this repo is ever made public or
   synced to a public mirror. The single highest-priority item on this list.
2. **`demos/` (53M, tracked)** — reclassified DURING Phase 4: the plan called it
   "GentleQuest campaign assets", but `demos/CAMPAIGN_INDEX.md` identifies it as
   the **Nucleus Sovereign Demo Campaign** (v1.0.5 era), with internal links
   pointing at the ai-mvp-backend repo. Also referenced by ~10 scripts under
   `scripts/` (shorts/voiceover tooling). Left fully in place.
3. **`mcp-server-nucleus/` (20M, tracked)** — a full vendored copy of the
   Nucleus MCP server (not a submodule). Staleness vs. any canonical copy
   unknown. Multiple sibling copies exist across the machine.
4. **Root Nucleus docs kept in place although they look like GQ cruft by
   filename**: `sidecar_exploit.md`, `marketplace_poisoning.md`,
   `pricing_rebellion.md`, `DEMO_C_*`, `RECOVERY_*`, `NOP_V3_FINAL_HARDENING.md`,
   `ANTIGRAVITY_CONTEXT_RECOVERY.md`, `MEGA_MASTER_CONTEXT.md`,
   `V9_VULNERABILITY_REPORT.md`, `STATUS.md`, `DECISIONS.md`, `TODOS.md`,
   `task.md`, `ONBOARDING.md` — all read as substantially Nucleus/Eidetic
   content on inspection (Phase 2 skipped 19 such files).
5. **`docs/NUCLEUS_*`, `docs/v10_strategy/`, `docs/nucleus_v10/`** — the latter
   two are a near-duplicate directory pair; dedup belongs to the nucleus lane.
6. **`docs/MARKETING_MASTER_PLAYBOOK.md`** — a joint GentleQuest+Nucleus
   playbook; not archivable under a GQ-only bucket.
7. **`CLAUDE.md`** — carries Nucleus session guardrails in the GQ repo (scope
   mismatch). `.agent/workflows/release-protocol.md` is the Nucleus MCP
   release protocol — a wrong-repo trap sitting next to GQ workflows.
8. **`.brain/` (18M), `.brain.backup-20260103200606/`, `nucleus-landing/` (6.7M)**.

## GentleQuest items needing an operator decision

- **`release_artifacts/` (182M, tracked)** — NOT archived: Phase 4's pre-check
  found `scripts/one_click_release.sh` actively cleans/downloads/writes into it.
  The earlier "dead since Feb" verdict was wrong. Future option: teach the
  script a new output path, then decide between archiving the historical
  binaries or converting them to a git tag + removal from main (clone-size
  relief). Needs fresh consent either way.
- **History rewrite (filter-repo)** for the ~480M of cold blobs — the only way
  clone size actually shrinks. Destructive to SHAs; separate decision, separate
  window, both-remotes coordination.
- **`docs/design/refs/` visual walks** — infrastructure worth keeping, but the
  screenshots predate the 1.6 redesign; a refresh against 1.7.x UI would make
  the oracle useful again.
- **Quest-vocabulary rename** — `lib/quests/quests_engine.dart` is LIVE
  (mood streaks) while everything else named "quest" is retired; renaming would
  end the collision trap that nearly got it archived.
- **`docs/strategy/` gitignore rule** (`.gitignore:361`) — the roadmap is now
  force-committed, but the rest of the directory remains ignored; decide
  whether strategy docs should be tracked as a class.
