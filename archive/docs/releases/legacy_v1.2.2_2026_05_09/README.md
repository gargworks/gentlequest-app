# GentleQuest v1.2.2 Legacy Snapshot — 2026-05-09

This directory captures the **pre-redesign-rollout** state of GentleQuest at the moment Lokesh + Claude completed a systematic dogfood audit and synthesized a 21-design rollout plan. Preserved for rollback safety and 5-year nostalgia.

## What is preserved

### Code
- **Git tag:** `legacy-pre-redesign-rollout-2026-05-09` (annotated, on commit `5d7da643`)
- **Same commit as:** `v1.2.2` (the prod App Store release at this moment)
- **Branch state was:** `feat/tb-phase3-archives` working tree clean of GentleQuest changes (all my Phase 1+2 compliance edits had been reverted)
- **App version:** 1.2.2+26032321 (build date Mar 23, 2026)
- **Backend:** `nucleus.gentlequest.app` (production)
- **iOS:** Xcode 16.4, Flutter 3.32.8, Dart 3.8.1

### Visual record
- `screens/01_chat_home.png` — captured fresh via `xcrun simctl io screenshot` after a clean re-boot of the bypass build. Shows: Header "Alex" / Crisis disclaimer banner / AI greeting "Good morning! 🌅 How are you feeling today?" / "Quick check-in" + "I'm feeling anxious" chips / 4-tab bottom nav (Talk/Mood/Quest/Community).
- **Other 15 dogfood screenshots from the audit walk are NOT in this dir** — they were saved to ephemeral session-state caches that got cleaned by Claude Code state rotation between turns. The textual record of every state is in `docs/design/refs/DOGFOOD_LOG.md` (S01-S16) including verbatim copy, layout descriptions, and visual deltas. Future-you can recreate them at any time by:

  ```bash
  # Re-build the bypass-flag legacy version
  git checkout legacy-pre-redesign-rollout-2026-05-09
  cd ai_buddy_web
  export PATH="/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin:$PATH"  # or wherever Flutter SDK lives
  flutter pub get
  cd ios && pod install && cd ..
  flutter build ios --debug --simulator --dart-define=DEV_BYPASS_COMPLIANCE=true
  # Boot any iPhone Sim and install build/ios/iphonesimulator/Runner.app
  # Walk the app capturing screens via:
  #   xcrun simctl io <udid> screenshot path/to/file.png
  ```

  *(The `DEV_BYPASS_COMPLIANCE` flag was added in this session to skip the GPS gate for dogfood — it was part of the changes being preserved alongside the dogfood; on legacy reproduction the flag may need to be re-introduced if the working tree was reset.)*

### Designs (the "future" reference)
- **Claude Design project:** `https://claude.ai/design/p/019de5fe-e33f-795c-be8f-e9e40a743f0f`
- **21 HTML files in that project** (R1–R5 design rounds). Index + cross-design principles in `docs/design/refs/REVIEW.md`.
- These are the designs the redesign rollout will translate into Flutter widget edits.

### Audit narrative
- **`docs/design/refs/DOGFOOD_LOG.md`** — 16 per-screen entries (S01–S16) + Synthesis section (top-8 friction ranked, Tier 0/1/2/3/4 actions, R6 design candidates).
- **Headline findings preserved verbatim there:**
  - F1: Compliance gate = entire 17.3% bounce
  - F2: Mood-low silent dismiss = highest D7 lever
  - F3: Chat error UX = silent abandonment
  - F4: Navigation gap = 5 designs unreachable in current UI
  - F5–F8: chat first-turn sparse, Quest gamification, onboarding tone, Update prompt friction
- **Design system contract preserved:**
  - 14 cross-design principles (REVIEW.md §"Cross-design design principles")
  - Color tokens: Primary #667EEA, Accent #FF6B6B, Soft bg #F8F7FF
  - Mood palette: #C9CCEB / #B6A3D9 / #A9B5F4 / #FFB59B / #FF8E7A
  - Typography: Inter / SF Rounded
  - Radii: cards 16px, sheets 24px top, buttons rounded-full
  - Motion: 300ms fades, 800ms auto-advance, 200ms typewriter, 1s confetti

### Deferred tooling (reactivation triggers)
- **`docs/design/refs/DEFERRED_TOOLING.md`** — install `idb_companion` + `joshuayoes/ios-simulator-mcp` once Xcode 26 + Wi-Fi available. ROI: ~500× token reduction on iOS automation.

## How to roll back to this state

```bash
git checkout legacy-pre-redesign-rollout-2026-05-09
# OR equivalent
git checkout v1.2.2
```

These both point to commit `5d7da643`.

## How to use this for nostalgia (5 years from now)

1. Read `DOGFOOD_LOG.md` for the textual time-capsule
2. Open the Claude Design project URL above (if still hosted) for the visual designs
3. Compare against then-current GentleQuest to see how far the redesign rollout drifted
4. Re-create visuals using the build steps above

## Notes for the redesign rollout team

The synthesis at the bottom of `DOGFOOD_LOG.md` proposes a re-ordering of the rollout in REVIEW.md based on observed evidence. Key shifts:
- **Insert Tier 0** (compliance, chat error UX, update prompt) — code surgery, no design dependency
- **Promote R2D4 Mood Reflection** to Tier 1 (biggest D7 lever)
- **Promote R3D3 Settings** to Tier 2 (App Store requirement)
- **Insert Tier 2.1 Navigation Decision** as explicit blocker before Tier 3
- **Demote R5D3 Quest** to "policy-pending" (gamification call needed first)

When work begins translating designs into Flutter widget edits, this directory should be left untouched — it's the canonical "before" reference.
