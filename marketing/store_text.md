# Store listing copy — GentleQuest v1.3.0

Drafts for Apple App Store Connect + Google Play Console. Tone aligned to
the public landing pages (hobby-side-project voice per moonlighting period).

## Both stores

**App name (30-char limit):**
```
GentleQuest
```

**Privacy policy URL:**
```
https://gentlequest.app/privacy
```

**Support URL / contact email:**
```
https://gentlequest.app/about
hi@gentlequest.app
```
(Will move to `support@gentlequest.app` post-quit-job; see project memory `project_gq_public_pseudonym_pre_quit`.)

---

## Apple App Store

**Subtitle (30-char limit):**
```
Quiet check-ins. Stays yours.
```

**Promotional text (170-char limit, can update without resubmit):**
```
Six moods. One tap. No streaks, no shame, no nudge spam. Journal stays on your phone. 988 always reachable — even offline.
```

**Description (4000-char limit):**
```
GentleQuest is a small, low-pressure mental-health companion for the days
that don't need fixing — just noticing.

Six moods. Tap to log. Skip anything, no shame.
Most check-ins take 2 seconds. The app remembers nothing you'd rather it forget.

— Mood —
Log how you are right now in two seconds. Six moods, plus optional "what's
touching it" tags (work, sleep, people, body, money). No streaks. No daily
guilt if you skip.

— Chat —
A warm first turn from someone who's noticed you're here. Not a therapist.
Not a coach. Just a presence that asks better questions when you want them.

— Journal —
What worked, what didn't. Stays on your phone — never synced, never
uploaded. Three taps and it's there for Future You.

— Weekly Review —
Looks at the week without grading you. Patterns, not scores. Insights you
can share with a real therapist if you want.

— Crisis support, always reachable —
988 lifeline one tap away. Crisis Text HOME to 741741. International
options. Works even offline — the numbers live in the app, not the cloud.

— What GentleQuest is NOT —
Not medical care. Not a diagnosis tool. Not a streak-shaming gamified
wellness app. Not a quiet way to harvest your data.

— Privacy —
Journal entries stay on-device. Mood logs sync only if you opt in. No ads.
No third-party trackers. Account is optional.

GentleQuest is a small, self-funded side project — built quietly, shipped
slowly, no investor timeline rushing the design.
```

**Keywords (100-char limit, comma-separated):**
```
mood,journal,mental health,anxiety,depression,calm,crisis,self care,wellness,therapy,reflection
```

**Primary category:** Health & Fitness
**Secondary category:** Lifestyle

**What's New (release notes, 4000-char limit):**
```
v1.3.0 — First public release.

What's in this build:
• Six-mood check-in with optional context tags
• Warm chat first turns with low-pressure pacing
• On-device journal with three-tap entry
• Weekly review that shows patterns without grading you
• 988 + Crisis Text + international crisis lines, reachable offline
• Profile preferences: nickname, pronouns, tone, greeting style
• Safety Plan you can recall in one tap from the Profile screen
• Voice playback option for chat replies (off by default)
• Notifications you can fully turn off (and they stay off)

Built quietly. Reply to support@gentlequest.app if anything feels wrong —
the maintainer reads everything.
```

---

## Google Play Console

**Short description (80-char limit):**
```
Quiet mood check-ins, on-device journal, crisis support always reachable.
```

**Full description (4000-char limit):**

(Same as Apple description above.)

**What's new (500-char limit):**
```
First public release of GentleQuest. Six-mood check-in. On-device journal.
Weekly review. 988 + crisis text reachable offline. Profile preferences
(nickname, pronouns, tone, greeting style). Safety Plan one-tap recall.
Voice playback option for chat (off by default).
```

**App category:** Health & Fitness
**Content rating:** Teen (13+) — matches in-app age gate

**Tags:**
```
Mood tracker, Journal, Mental health, Mindfulness, Crisis support
```

---

## Notes for operator at submission time

- **Screenshots upload order (both stores):** 1, 3, 5, 2, 4, 6
  (mood → privacy → crisis → chat → review → settings)
- **App icon:** use existing 1024×1024 from `ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png` for App Store; use `marketing/play_store/play_high_res_icon_512.png` for Play.
- **Feature graphic (Play only):** `marketing/play_store/feature_graphic.png` (1024×500).
- **iPad screenshots:** not required (iPad target dropped — `TARGETED_DEVICE_FAMILY = "1"` in pbxproj).
- **Tax / banking / agreements:** operator-side fill at ASC + Play Console.
