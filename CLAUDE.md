# Nucleus — Session Guardrails

**Direction:** "Does this make Nucleus a $5T outcome or just cleverness?"
Pick the hill. Opus is a force multiplier, not a crutch.

**Execution:** "Does .brain/ show evidence this code ran?"
Tests passing ≠ system alive. After building, check JSONLs — not just test output.

**Reality:** "Who asked for this? How many users does Nucleus have today?"
Zero users = ship and distribute first. Don't build Phase N+1 for an audience of one.

## Flywheel — the compounding loop (Frontier 4)

The flywheel turns every failure into curriculum and every success into a CSR
bump. It is **always on** unless you explicitly disable it via
`.brain/driver/config.json` `flywheel_accountability_enabled: false`.

- **CSR (Claim Survival Rate):** the scalar in `.brain/flywheel/csr.json`. Stays
  near 1.0 = system is trustworthy. Drops = something just broke. Read it before
  closing a session.
- **Failure capture:** never log a phase failure with a bare `print()`. Call
  `Flywheel(brain_path).file_ticket(step=..., error=..., phase=...)` so the
  6 actions fire (memory note, CSR bump, training pair, week report, GH issue,
  task queue). The `_fw_file_ticket` helper in `third_brother_driver.py` already
  wraps this for driver phase hooks.
- **Discovery:** future sessions can read `brain://flywheel/csr` and
  `brain://flywheel/dashboard` MCP resources, or invoke the `flywheel_check`
  prompt for a one-screen summary. Do that at the top of any session that
  touches driver work.
- **Compound loop:** `nucleus_flywheel(action="curriculum_refresh")` promotes
  pending DPO pairs whose step has since survived → ready, feeding the next TB
  training run. Run it weekly (or wire to cron).
- **Why it exists:** see `.brain/flywheel/thesis.md`. The short version: every
  loop has to make the next loop cheaper, faster, and more trustworthy than the
  last. The flywheel is the mechanism that proves it.
