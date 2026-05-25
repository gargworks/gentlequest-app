# App Store screenshots — GentleQuest v1.3.0

Generated via Claude Design → headless Chrome render. Apple-compliant
iPhone 6.7" display size (1290 × 2796 px). Six frames cover the core
value-prop flow.

## Frames

| # | File                           | Tagline                                              |
| - | ------------------------------ | ---------------------------------------------------- |
| 1 | `frame_1_mood_entry.png`       | Six moods. Tap to log. Skip anything, no shame.      |
| 2 | `frame_2_chat_first_turn.png`  | (chat first turn warmth)                             |
| 3 | `frame_3_journal.png`          | Journal stays on your phone. Always.                 |
| 4 | `frame_4_weekly_review.png`    | (weekly review insight)                              |
| 5 | `frame_5_crisis.png`           | 988 always reachable. Even offline.                  |
| 6 | `frame_6_settings.png`         | (settings / data control)                            |

## Upload order (App Store Connect)

Apple shows screenshots left-to-right in the order uploaded. Recommended
upload order is **1, 3, 5, 2, 4, 6** — leads with mood (core daily flow),
then journal (privacy), then crisis (trust), then chat / review / settings
(depth proof).

## Regeneration

```bash
cd marketing/app_store
python3 render_frames.py
```

`screenshots_source.html` is the canonical source from Claude Design's
GentleQuest project. Edits to copy/visuals should happen there first,
then re-paste the HTML here and re-render.

## Constraints

- iPhone 6.7" display (1290 × 2796 px) is the **mandatory** size; Apple
  derives 6.5" / 5.5" screenshots automatically from this on submission.
- PNG format, sRGB color space, 8-bit per channel — all confirmed.
- Apple max 10 screenshots per locale; we have 6.
- No transparency in final PNGs (Apple rejects translucent app-store
  screenshots).
