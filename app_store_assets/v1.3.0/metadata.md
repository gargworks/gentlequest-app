# GentleQuest v1.3.0 — App Store metadata

## Title (30 chars max)
GentleQuest

## Subtitle (30 chars max)
A quiet place, when you need it

## Promotional text (170 chars max — updatable without review)
The R1 redesign is here. Warmer onboarding, gentler mood tracking, journal that respects your privacy. No streaks. No shame.

## Description (4000 chars max)
GentleQuest is a wellness companion for people navigating heavy moments. It's not therapy. It's not medical care. It's a space where you can log how you're feeling, talk things through, and find resources that match where you are.

What's in v1.3.0:
• **Warmer onboarding.** Three trust chips up front: Private. No judgment. No pressure. Age gate as a quiet check, not a wall.
• **Mood entry, redone.** Six emoji moods. Optional context chips (Work, Sleep, People, Body, Money, Other). Auto-advance with explicit cancel — never trapped.
• **Crisis paths that never block.** 988 always reachable. Inline crisis card surfaces if your message suggests you need more than chat right now.
• **Journal that stays on your phone.** Local-first. Three views: today, an entry, the timeline.
• **Weekly review without scores.** Sundays show mood shapes — not a diagnosis. "One thing worth remembering" from the week.
• **Settings with privacy at the top.** Anonymity mode, data export, account delete — all visible, all under your control.
• **Library + Exercises.** 4-7-8 breathing, 5-4-3-2-1 grounding, body scan. Take what helps, skip the rest.
• **Push that reads like a check-in.** No streak shame nudges (off by default). Crisis follow-up persistent. Weekly review Sunday 8pm if you've logged ≥3 times that week.
• **Profile + Safety plan.** Build a plan on a calm day. The card is there when you need it.

What we don't do: streaks, levels, scores, diagnoses, judgment. Skip anything. No shame.

Not medical advice. If you're in crisis, call 988 (US) or your local emergency line.

## Keywords (100 chars, comma-separated)
mental health, mood tracker, anxiety, journal, mindfulness, wellness, breathing, crisis, gentle, calm

## What's New (4000 chars max — required per submission)
v1.3.0 — The R1 redesign release.

Every screen has been redesigned around three rules: warmth over utility, skip anything no shame, one clear next action.

New & redesigned:
• Onboarding · Mood entry with context chips · Mood reflection after submit · Wellness dashboard with state-aware greeting · Chat with breathing orb & gentle starter chips · Clinical assessments framed as reflection not diagnosis · Crisis intervention (3 states) · Compliance + crisis-keyword override · Offline state with 988 always reachable · Quests reframed (no streaks, no levels) · Journal with timeline view · Weekly review on Sundays · 3 exercise types (4-7-8, grounding, body scan) · Resource library · Push notifications (gentle, opt-in) · Profile + safety plan · Settings with anonymity + data export

## Universal links — operator action required

1. **Replace `TEAM_ID_PLACEHOLDER` in `.well-known/apple-app-site-association`** with your Apple Developer Team ID (10-char alphanumeric, e.g. `ABCDE12345`). Look up via App Store Connect → Membership → Team ID.
2. **Verify bundle ID** matches Xcode project (`com.gentlequest.app` assumed; correct in AASA + entitlements + xcodeproj if different).
3. **Host the AASA file** at `https://gentlequest.app/.well-known/apple-app-site-association` (no `.json` extension, `Content-Type: application/json`). Cloudflare Pages serves the `.well-known/` dir if present in `landing-page/public/.well-known/`. May need to copy or symlink.
4. **Verify**: `curl -I https://gentlequest.app/.well-known/apple-app-site-association` → 200 + `application/json` content-type.
5. **Test universal link**: long-press `https://gentlequest.app/journal/abc` in Notes; should offer to open in app.
