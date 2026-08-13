# GentleQuest v1.6.0 — Release Notes

> **Stage 1 submission prep.** Version 1.6.0. App Store + Play Store.
> Generated 2026-08-13 for the v1.6 submission cycle.

---

## Version

**1.6.0**

---

## Feature list (v1.6)

1. **Companion creature that grows with check-ins** — a gentle companion that
   evolves as you log check-ins. It never punishes absence: missing a day
   doesn't reset progress or shrink the creature. Growth is purely additive,
   so the companion is always a soft invitation back, never a guilt trip.
2. **Shareable mood cards** — turn your week into a shareable mood card you can
   send to a friend, partner, or therapist. Exports a clean visual summary;
   no raw data leaves your device unless you choose to share.
3. **Streamlined onboarding** — removed the popup chain. New users land in the
   app without interrupting modals; setup prompts are inline and skippable.
4. **Sean-Ellis survey** — a single Sean-Ellis question ("How disappointed
   would you be if you could no longer use GentleQuest?") surfaces
   periodically to measure product-market fit signal. Opt-in, dismissible.
5. **Mobile navigation improvements** — flatter tab structure, faster reach to
   check-in and mood log, reduced taps to core actions.
6. **Bug fixes and performance improvements** — stability and latency fixes
   across check-in sync, mood logging, and the companion render path.

---

## App Store — What's New (release notes)

```
A companion that grows with you — gently.

• Companion creature that grows with check-ins (never punishes absence)
• Shareable mood cards — share your week with a friend or therapist
• Streamlined onboarding — no more popups
• Sean-Ellis survey to help us improve
• Mobile navigation improvements
• Bug fixes and performance improvements
```

---

## Play Store — What's New (release notes, < 500 chars)

```
A companion that grows with you — gently.

• Companion that grows with check-ins (never punishes absence)
• Shareable mood cards
• Streamlined onboarding (no popups)
• Sean-Ellis survey
• Navigation improvements
• Bug fixes & performance improvements
```

**Character count:** ~230 chars (well under the 500-char Play Store truncation
limit; full text visible without "more" expansion).

---

## ASO — Title and subtitle suggestions

### App Store (30-char title / 30-char subtitle)

| Slot | Suggestion | Chars | Rationale |
|---|---|---|---|
| Title (30) | `GentleQuest: Mood & Companion` | 29 | Brand + two highest-value ASO keywords (mood, companion). Stays under 30. |
| Subtitle (30) | `Gentle check-ins, growing pal` | 29 | Emotional benefit + the v1.6 hero feature (companion). Differentiates from clinical trackers. |

**Alternate titles (A/B candidates):**
- `GentleQuest: Mood Tracker` (25) — leans on the higher-search-volume "mood tracker" keyword.
- `GentleQuest: Mental Health` (26) — broader category keyword; risk of competing with clinical apps.

**Alternate subtitles:**
- `Check in. Grow your companion.` (30) — action-led.
- `Mood, check-ins, a gentle pal` (30) — keyword-stuffed but readable.

### Play Store (50-char app name / 80-char short description)

| Slot | Suggestion | Chars | Rationale |
|---|---|---|---|
| App name (50) | `GentleQuest: Mood Tracker & Companion` | 38 | Brand + "mood tracker" (high volume) + "companion" (v1.6 hero). |
| Short description (80) | `Gentle mood check-ins with a companion that grows with you.` | 60 | Benefit-led, keyword-rich (mood, check-ins, companion), under 80. |

**Targeted ASO keywords (use in long description naturally):**
mood tracker, mental health, check-in, journal, companion, self-care,
anxiety relief, mood log, wellness, mindfulness, gentle, habits, mood cards,
therapy companion, daily check-in.

---

## Privacy nutrition labels — update notes

v1.6 introduces two data-touching features that affect App Store privacy
nutrition labels. Update the App Store Connect "App Privacy" section before
submission:

### Data collected by v1.6

| Data type | Used | Linked to user | Collected by | New in v1.6? |
|---|---|---|---|---|
| **Health & fitness — Mood** (user mood entries) | App functionality, analytics | Not linked to identity | App only | Existing; clarify "mood" category. |
| **Photos or videos** (mood card export image) | App functionality (share) | Not linked to identity | App only | **NEW** — only when the user explicitly generates and shares a mood card; image is composed on-device. |
| **Diagnostics — usage data** (Sean-Ellis survey response) | Analytics | Not linked to identity | App only | **NEW** — single survey response, no PII. |
| **Other user content** (companion state) | App functionality | Not linked to identity | App only | Existing; companion growth state is derived from check-in frequency. |

### What to declare

- **Linked to you / used to track:** NONE. GentleQuest does not link mood data
  to identity and does not track users across apps/sites.
- **Purposes:** App functionality (mood, companion, mood card), Analytics
  (Sean-Ellis survey, aggregate usage).
- **On-device only:** mood card composition and companion state derivation
  happen on-device; nothing new leaves the device unless the user explicitly
  shares a mood card.

### Action items for submission

1. In App Store Connect → App Privacy, add **Photos or videos** (App
   functionality, not linked, collected by app) for the mood-card export.
2. Add **Diagnostics → usage data** (Analytics, not linked, collected by app)
   for the Sean-Ellis survey response.
3. Confirm **Health & fitness → Mood** is already declared (existing); no
   change to its linkage status.
4. No third-party SDKs added in v1.6, so no new third-party data collection to
   declare.

---

## Submission checklist (for the operator)

- [ ] Bump version to 1.6.0 in `pubspec.yaml` (and store-facing metadata).
- [ ] Update App Store release notes (What's New section above).
- [ ] Update Play Store release notes (What's New section above).
- [ ] Update App Store title/subtitle if adopting the ASO suggestions.
- [ ] Update Play Store app name / short description if adopting ASO suggestions.
- [ ] Update App Privacy nutrition labels per the table above.
- [ ] Build AAB + IPA per `docs/STORE_DEPLOYMENT.md`.
- [ ] Upload via `fastlane supply` (Play) and `xcrun altool` (App Store).
- [ ] Submit for review on both stores.
