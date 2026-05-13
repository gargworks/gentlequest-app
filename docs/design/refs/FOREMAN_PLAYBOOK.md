# GentleQuest Foreman Playbook
## One-PR-per-Tier Design Rollout

> **Operational status:** this playbook becomes fully operational once PRs
> **#9, #12, #13** are merged into `main`.  Until then the referenced files
> (`lib/theme/gq_tokens.dart`, `docs/design/refs/REVIEW.md`,
> `docs/design/refs/htmls/`, `scripts/gq_screenshot_diff.sh`) do not exist on
> `main`.  A foreman agent MAY be invoked against a branch that already has
> these files checked out (e.g. a worktree built on `feat/gq-design-extract`
> for read-only reference), but MUST NOT open a tier PR until all prerequisite
> PRs are merged.

---

## 1. Purpose

The foreman replaces ad-hoc, Opus-heavy tier dispatch with a deterministic,
design-driven pipeline.  Every tier ships as a single PR, driven by the spec in
`REVIEW.md`, verified by the screenshot rig, and closed by Lokesh before the
next tier begins.  The foreman never picks two tiers at once and never opens a
PR against an unmerged dependency.

---

## 2. Inputs the foreman needs

| Input | Path | Role |
|---|---|---|
| Design source of truth | `docs/design/refs/REVIEW.md` | Per-tier layout, copy verbatim, principle alignment, target Flutter file, dependency list, **status** |
| Authoritative HTML designs | `docs/design/refs/htmls/` | Fallback for verbatim copy when REVIEW.md entry is partial; read `htmls/{DESIGN_ID}*.html` |
| Screenshot rig | `scripts/gq_screenshot_diff.sh` | Captures launch screenshot from the tier branch |
| Design tokens | `lib/theme/gq_tokens.dart` | Every colour, spacing, and typography value.  No new hardcoded hex anywhere. |
| Cross-design principles | REVIEW.md §Cross-Design Principles | 14 principles; every tier PR must quote the ones it satisfies |

**Reading order:** playbook → REVIEW.md (full file, not just the tier row) →
`htmls/{DESIGN_ID}*.html` (only the designs named in the tier spec) →
`gq_tokens.dart` (skim token names before touching any widget).

---

## 3. State machine

### 3.1 Status column values

REVIEW.md maintains an index table with a `Status` column.  Valid values:

| Value | Meaning |
|---|---|
| `pending` | Not yet implemented |
| `in-flight` | Foreman agent is currently working on it; PR open (include PR URL inline) |
| `merged` | PR merged; design lives in `main` |
| `blocked` | Has a dependency tier whose status is not yet `merged` |

### 3.2 Tier-selection algorithm

```
1. Read REVIEW.md index table.
2. Collect candidate rows: status == `pending`
   AND every row listed in that tier's "Depends on" column has status == `merged`.
3. From candidates, pick the row with the lowest tier number (e.g. 1.0 < 1.1 < 2.0).
4. If no candidates exist:
   - Count tiers where status == `in-flight` or `blocked`.
   - Exit with message:
     "Queue blocked — {N} tiers waiting on {M} unmerged upstream tiers.
      Merge open PRs first, then re-invoke the foreman."
5. Proceed with the selected tier.
```

### 3.3 State transitions

```
pending  ──[foreman picks tier]──► in-flight  (foreman writes PR URL into REVIEW.md)
in-flight ──[Lokesh merges PR]───► merged     (Lokesh updates status after merge)
pending  ──[dep not merged yet]──► blocked    (foreman writes "blocked on tier X")
blocked  ──[dep merges]──────────► pending    (foreman re-evaluates on next invocation)
```

The foreman only drives `pending → in-flight`.  Lokesh drives `in-flight →
merged`.  Transitions into `blocked` are written by the foreman during
pre-flight when a tier's listed dependency is unmerged.

---

## 4. Pre-flight checks

Run these **before touching any code**.  If any check fails, surface the
failure reason and exit without creating a branch.

### 4.1 Branch hygiene

```bash
git branch --show-current          # HARD RULE: must match expected branch name
                                   # (see feedback_verify_branch_before_commit)
git fetch upstream main            # ensure base is current before branching
```

### 4.2 PR queue depth

```bash
gh pr list \
  --repo eidetic-works/ai-mental-health-assistant \
  --state open \
  --limit 20
```

Count the open PRs.  **If the count is already ≥ 4 (Lokesh-tunable), refuse:**

```
PR queue too deep ({N} open).  Merge some PRs first before shipping another tier.
```

The threshold of 4 is intentionally conservative: one or two legacy PRs (#8,
#5) may be long-lived.  The foreman should exclude draft PRs from the count if
they are clearly stale, but must call this out explicitly in its output.

### 4.3 Prerequisite PRs merged

Verify that the three foundational PRs are merged:

- **PR #9** — `lib/theme/gq_tokens.dart` (design tokens)
- **PR #12** — `docs/design/refs/REVIEW.md` + `docs/design/refs/htmls/`
- **PR #13** — `scripts/gq_screenshot_diff.sh`

Check by confirming the files exist on the current base (`upstream/main` after
fetch):

```bash
test -f lib/theme/gq_tokens.dart     || echo "MISSING: PR #9 not merged"
test -f docs/design/refs/REVIEW.md   || echo "MISSING: PR #12 not merged"
test -f scripts/gq_screenshot_diff.sh || echo "MISSING: PR #13 not merged"
```

If any file is missing, exit with:

```
Cannot proceed: prerequisite PR(s) not yet merged.
Missing: {list}
Re-invoke after Lokesh merges the listed PRs.
```

### 4.4 Target Flutter file

Read the tier spec's "Target Flutter File" field from REVIEW.md.

- If the spec says "existing file" → verify it exists: `test -f {path}`.
- If the spec says "new file" or "needs creation" → this is expected; proceed.
- If the file is supposed to exist but doesn't → surface as a pre-flight
  failure with path.

### 4.5 Dependency tier status

Re-read REVIEW.md's status column for every tier listed in the selected tier's
"Depends on" field.  Even if the algorithm in §3.2 already checked this,
re-verify after fetch in case another concurrent session updated the file.

---

## 5. Implementation rules

These apply once pre-flight passes.

1. **One tier, one PR.**  The branch name must be
   `feat/gq-rollout-tier{TIER_ID}-{slug}` (e.g.
   `feat/gq-rollout-tier1.0-onboarding-warmth`).  Do not accumulate changes
   from other tiers.

2. **Design-driven, not guess-driven.**  Every widget, copy string, colour, and
   spacing value must be traceable to either REVIEW.md or the named HTML file.
   If a design detail is absent from both sources, mark it as `[assumed]` in
   the PR body and flag it for Lokesh review; do not invent values.

3. **Token-only colours and typography.**  Import from `lib/theme/gq_tokens.dart`.
   No raw hex (`#RRGGBB`), no `Colors.blue`, no hardcoded `FontSize` literals
   that duplicate a token.  If a design value has no matching token, add the
   token in the same PR with a clear name and comment.

4. **flutter analyze must pass.**  Run on every Dart file you touch:

   ```bash
   flutter analyze lib/path/to/changed_file.dart
   ```

   Do not open a PR with analyzer warnings.  Fix them or, if a suppression is
   genuinely required, add `// ignore: rule_name` with a comment explaining why.

5. **`flutter build ios --debug --simulator --no-codesign` must succeed.**  `flutter analyze` scoped to touched files misses cross-file syntax errors AND analyzer-clean code that fails at compile time (typos in imports, missing required params from edits to call sites in untouched files, etc.).  Build is the cheapest gate that catches these.  Run from `ai_buddy_web/`:

   ```bash
   cd ai_buddy_web
   export PATH="/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin:$PATH"
   flutter build ios --debug --simulator --no-codesign 2>&1 | tail -10
   ```

   - Exit code MUST be 0
   - Last line should contain `✓ Built build/ios/iphonesimulator/Runner.app`
   - If build fails: fix the build, do NOT push the PR
   - Build time: typically 30–90 s incremental, 3–5 min cold.  Plan for it.

6. **No drive-by refactors.**  Touch only the files named in the tier spec plus
   `gq_tokens.dart` if new tokens are needed.  Incidental cleanups go in a
   separate PR (or a TODO comment in the code, not in this PR).

7. **Copy verbatim.**  If REVIEW.md records a "Copy Verbatim" paragraph for
   this tier, that exact string must appear in the widget — not a paraphrase.

---

## 6. Post-flight

### 6.a — Build verification (hard gate)

Run `flutter build ios --debug --simulator --no-codesign` from `ai_buddy_web/`:

```bash
cd ai_buddy_web
export PATH="/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin:$PATH"
flutter build ios --debug --simulator --no-codesign 2>&1 | tail -10
```

If it fails:
- Diagnose + fix the build error in your branch
- Re-run build to confirm green
- Only then proceed to §6.b

This is the gate that catches typos analyze missed.  Do NOT proceed to screenshot, commit, or PR while build is red.

### 6.b — Update REVIEW.md

Before committing, update the tier's status row in REVIEW.md:

```markdown
| 2.0 | Home Dashboard Warmth | in-flight | https://github.com/eidetic-works/ai-mental-health-assistant/pull/NN |
```

Include this REVIEW.md change in the same commit as the implementation.

### 6.c — Screenshot rig

Run the screenshot rig from the tier branch:

```bash
bash scripts/gq_screenshot_diff.sh tier-{TIER_ID}
```

The rig captures a launch screenshot.  Walk-mode (interaction sequences) is
**idb-blocked** and not currently functional; the rig captures only the launch
frame until idb_companion is available (see §10, Future Extension Hooks).

- If the rig succeeds: attach the screenshot path in the PR body under
  "## Visual diff".
- If the rig fails: ship the PR anyway but add a "## Screenshot status" section
  that says exactly what failed.  Do NOT hold the PR for screenshot issues.
  Document it as a review item for Lokesh.

### 6.d — PR body shape

The PR description must contain these sections in order:

```markdown
## Design reference
- Design ID(s): {DESIGN_IDS}
- REVIEW.md tier: {TIER_ID}
- HTML source(s): docs/design/refs/htmls/{DESIGN_ID}*.html

## Copy verbatim landed
{paste the exact copy string(s) from the spec, or "N/A"}

## Principle alignment
{list each of the 14 cross-design principles this tier satisfies, with
 one-sentence justification per principle cited}

## Files changed
{bulleted list of every changed file with one-line description of what changed}

## Visual diff
{screenshot path or "screenshot rig failed — see Screenshot status section"}

## Pre-flight checklist
- [ ] `git fetch upstream main` run before branching
- [ ] Open PR count was N (≤ 4 threshold)
- [ ] Prerequisite PRs #9, #12, #13 confirmed merged
- [ ] Target Flutter file existence verified
- [ ] Dependency tier statuses confirmed `merged`
- [ ] `flutter analyze` passed on all touched files
- [ ] `flutter build ios --debug --simulator --no-codesign` succeeded (exit 0, ✓ Built line present)
- [ ] `gq_tokens.dart` used for all colours/typography (no hardcoded hex)
- [ ] REVIEW.md status updated to `in-flight` with PR URL

## Reviewer notes
{anything the foreman is uncertain about, assumed values, design gaps, or
 items requiring Lokesh's explicit sign-off before merge}
```

### 6.e — Open PR

```bash
git add docs/design/refs/REVIEW.md {all changed files}
git branch --show-current   # verify branch before commit (HARD RULE)
git commit -m "feat(gq-rollout): Tier {TIER_ID} — {one-line description} (#N)"
git push -u upstream feat/gq-rollout-tier{TIER_ID}-{slug}
gh pr create \
  --repo eidetic-works/ai-mental-health-assistant \
  --base main \
  --head feat/gq-rollout-tier{TIER_ID}-{slug} \
  --title "feat(gq-rollout): Tier {TIER_ID} — {slug}" \
  --body "$(cat <<'PREOF'
  {PR body from §6.d}
  PREOF
  )"
```

### 6.f — Exit

After pushing and opening the PR, the foreman **exits**.  It does NOT poll for
merge.  It does NOT open the next tier.  Lokesh reviews, merges if satisfied,
then re-invokes the foreman (or issues a direct `/to-cowork` relay) to ship
the next tier.

Report back to the caller in **under 200 words**:
- Files changed + line delta
- Branch name
- Commit SHA
- PR URL
- Screenshot path (or failure note)
- Any blocking items or assumed values

---

## 7. Brief template

Paste the block below into a new Agent invocation to fire a foreman run.
Substitute all `{PLACEHOLDER}` tokens before firing.  Do not leave any
placeholder un-filled — the agent will not detect un-substituted tokens.

```
You are a foreman agent executing one GentleQuest design-rollout tier.

STEP 0 — Read the playbook first
  Read docs/design/refs/FOREMAN_PLAYBOOK.md in full.
  Do not skip any section.

STEP 1 — Identify your tier
  Tier ID:          {TIER_ID}           (e.g. "2.0")
  Design ID(s):     {DESIGN_IDS}        (e.g. "design_07, design_08")
  Target file:      {TARGET_FLUTTER_FILE}  (e.g. "flutter_app/lib/screens/dashboard_screen.dart")
  Copy verbatim:    {COPY_VERBATIM_PARAGRAPH}
    (paste the exact copy string from REVIEW.md; omit if REVIEW.md says "N/A")

STEP 2 — Pre-flight (§4 of playbook)
  Run every check in §4 in order.
  If any check fails, stop and report the failure; do not touch code.

STEP 3 — Read design sources
  Read docs/design/refs/REVIEW.md — full file.
  Read docs/design/refs/htmls/{DESIGN_IDS}*.html for verbatim copy and layout detail.
  Read lib/theme/gq_tokens.dart for available token names.

STEP 4 — Implement
  Scope: only the changes described in REVIEW.md for tier {TIER_ID}.
  Rules (§5 of playbook):
  - All colours/typography from gq_tokens.dart only. No hardcoded hex.
  - Copy verbatim string(s) must appear word-for-word in the widget.
  - flutter analyze must pass on every touched file.
  - Also: `flutter build ios --debug --simulator --no-codesign` must succeed (exit 0, ✓ Built line). Build catches what analyze misses. If build fails, fix and re-build before continuing.
  - No drive-by refactors.
  - If a design detail is missing from both REVIEW.md and the HTML, mark it [assumed] and flag it.

STEP 5 — Post-flight (§6 of playbook)
  a. Build gate (§6.a): run `flutter build ios --debug --simulator --no-codesign` from `ai_buddy_web/`. Must be green before any further step.
  b. Update REVIEW.md: set tier {TIER_ID} status to `in-flight`.
  c. Run: bash scripts/gq_screenshot_diff.sh tier-{TIER_ID}
     — if rig fails, note failure; still proceed to PR.
  d. Commit (verify branch first with `git branch --show-current`).
  e. Push and open PR using the body shape in §6.d of the playbook.
  f. Report back in <200 words: files changed, branch, commit SHA, PR URL,
     screenshot path or failure note, any assumed values or blockers.
```

---

## 8. Failure modes and recoveries

| Failure | Recovery |
|---|---|
| Pre-commit hook flags "bulk file" or rejects commit | DO NOT use `--no-verify`. Surface the hook output to Lokesh verbatim and await explicit ack before proceeding. |
| `flutter analyze` reports errors | Fix the analyzer errors first. Do not push a broken PR. Surface what failed and the file/line. |
| `flutter analyze` passed but `flutter build` failed | Common cause: typo in a modified file outside analyze's narrow scope (e.g. `;;`, missing import, stale super-call). Open the build error, fix the file, re-build. Never push without green build. |
| Concurrent CC session activity detected | Run `git branch --show-current` immediately before every `git commit`. If branch doesn't match, stop — do not commit to the wrong branch. Cherry-pick to the correct branch after diagnosis. |
| Screenshot rig (`gq_screenshot_diff.sh`) fails | Still ship the PR. Add a "Screenshot status" section to the PR body explaining the failure. Note it as a review item. Do not hold the PR for screenshot issues. |
| REVIEW.md tier spec is ambiguous or contradicts the HTML | Do not invent values. Document the ambiguity in the PR body under "Reviewer notes". Implement the conservative interpretation and flag it `[assumed]`. |
| Target Flutter file missing (expected to exist per spec) | Pre-flight failure — surface the missing path to Lokesh. Do not create a substitute file. Wait for clarification. |
| Prerequisite PRs (#9, #12, #13) not yet merged | Pre-flight failure — exit immediately with message listing missing files. Re-invoke after Lokesh merges them. |
| PR queue ≥ 4 open | Pre-flight failure — refuse to open another PR. Output the list of current open PRs and ask Lokesh to merge some first. |
| `gq_tokens.dart` has no matching token for a design value | Add the token in the same PR. Name it following the existing naming convention in `gq_tokens.dart`. Add a comment explaining which design it came from. Flag the addition in the PR body. |
| `git push` rejected (non-fast-forward) | Run `git fetch upstream main`. If the base has moved, rebase: `git rebase upstream/main`. Re-run `flutter analyze` after rebase. Do not force-push without Lokesh ack. |

---

## 9. Lessons / known footguns

**2026-05-13 — PR #18 build-gate retrofit.** Foreman initially only required `flutter analyze`. A Sonnet agent's run reported "analyze 0 errors" while a `;;` syntax error sat in `wellness_dashboard_screen.dart:29`. Build caught it immediately. Lesson: analyze is necessary but not sufficient. Build is the gate.

---

## 10. Future extension hooks

These are **not live today**.  Do not implement or reference them as if they
are.  Each item has a one-line activation trigger once the prerequisite
exists.

1. **Walk-mode screenshot capture** — once `idb_companion` is available on the
   CI runner, add the interaction sequence to `gq_screenshot_diff.sh`'s
   `WALK_STEPS` array.  No other change needed; the rig already has a
   `WALK_STEPS` hook point.

2. **Multi-screen capture per tier** — extend `gq_screenshot_diff.sh` to loop
   over a list of screen names passed as arguments:
   `bash gq_screenshot_diff.sh tier-{TIER_ID} screen1 screen2 ...`.

3. **A11y verification** — once accessibility testing is prioritized, add a
   `flutter test --tags a11y` step between the screenshot rig call and the
   commit in post-flight.

4. **Playwright web variant** — if a web variant of GentleQuest ships, replace
   the `idb_companion` screenshot step with a Playwright headless run.  The PR
   body shape and post-flight steps remain identical.

5. **Automated REVIEW.md merge-status sync** — a GitHub Actions workflow that
   writes `merged` into the status column when a PR is merged.  Until that
   exists, Lokesh updates the status manually after merging.

---

## 11. Glossary

| Term | Definition |
|---|---|
| Foreman | A Sonnet (or Haiku) sub-agent invoked with the brief template in §7 to ship one tier |
| Tier | A named unit of design work, identified by a numeric ID (e.g. 2.0), scoped in REVIEW.md |
| REVIEW.md | The canonical source of truth for all tier specs, statuses, and cross-design principles |
| Design token | A named constant in `gq_tokens.dart` for a colour, spacing, or typography value |
| Verbatim copy | The exact UI text string recorded in REVIEW.md; must appear word-for-word in the widget |
| Pre-flight | Checks run before touching code; any failure aborts the run |
| Post-flight | Steps run after implementation; includes screenshot, REVIEW.md update, and PR open |
| idb-blocked | idb_companion walk-mode is not yet available; only launch screenshots work today |
