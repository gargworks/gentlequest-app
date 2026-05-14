# GentleQuest Design Review — 21 Designs (R1–R5)

Generated: 2026-05-10  
Source: https://claude.ai/design/p/019de5fe-e33f-795c-be8f-e9e40a743f0f  
Per-design HTML: docs/design/refs/htmls/

---

## Index

| ID    | Name                    | Round | File (htmls/)                               | Target screen(s)                                                                            | Tier | Status      |
|-------|-------------------------|-------|---------------------------------------------|---------------------------------------------------------------------------------------------|------|-------------|
| R1D1  | Onboarding              | R1    | GentleQuest_Onboarding.html                 | ai_buddy_web/lib/screens/welcome_screen.dart                                                | 0    | in-flight — https://github.com/eidetic-works/ai-mental-health-assistant/pull/17 |
| R1D2  | Wellness Dashboard      | R1    | GentleQuest_Wellness_Dashboard.html         | ai_buddy_web/lib/dhiwise/presentation/wellness_dashboard_screen/wellness_dashboard_screen.dart | 0 | Partial  |
| R1D3  | Dashboard States        | R2    | GentleQuest_Dashboard_States.html           | ai_buddy_web/lib/dhiwise/presentation/wellness_dashboard_screen/wellness_dashboard_screen.dart | 2  | Not started |
| R1D4  | Mood Entry              | R1    | GentleQuest_Mood_Entry.html                 | ai_buddy_web/lib/screens/mood_tracker_screen.dart                                           | 1    | in-flight — https://github.com/eidetic-works/ai-mental-health-assistant/pull/15 |
| R1D5  | Mood Reflection         | R1    | GentleQuest_Mood_Reflection.html            | ai_buddy_web/lib/screens/mood_tracker_screen.dart                                           | 1    | Partial     |
| R1D6  | Chat First Turn         | R1    | GentleQuest_Chat_First_Turn.html            | ai_buddy_web/lib/screens/chat_screen.dart                                                   | 1    | Partial     |
| R1D7  | Chat Active States      | R2    | GentleQuest_Chat_Active_States.html         | ai_buddy_web/lib/screens/chat_screen.dart                                                   | 2    | Not started |
| R1D8  | Clinical Assessment     | R2    | GentleQuest_Clinical_Assessment.html        | ai_buddy_web/lib/screens/clinical_assessment_screen.dart                                    | 2    | Not started |
| R1D9  | Crisis Intervention     | R1    | GentleQuest_Crisis_Intervention.html        | ai_buddy_web/lib/widgets/crisis_resources.dart                                              | 0    | in-flight https://github.com/eidetic-works/ai-mental-health-assistant/pull/21 |
| R1D10 | Compliance Block        | R1    | GentleQuest_Compliance_Block.html           | ai_buddy_web/lib/screens/compliance_guard_screen.dart                                       | 0    | Partial     |
| R1D11 | Compliance Extensions   | R2    | GentleQuest_Compliance_Extensions.html      | ai_buddy_web/lib/screens/compliance_guard_screen.dart                                       | 2    | Not started |
| R1D12 | Offline States          | R3    | GentleQuest_Offline_States.html             | ai_buddy_web/lib/screens/chat_screen.dart (inline banner)                                   | 3    | Not started |
| R1D13 | Quests                  | R1    | GentleQuest_Quests.html                     | ai_buddy_web/lib/screens/quest_screen.dart                                                  | 4    | Partial     |
| R1D14 | Journal                 | R2    | GentleQuest_Journal.html                    | ai_buddy_web/lib/screens/journal_screen.dart                                                | 2    | Not started |
| R1D15 | Weekly Review           | R3    | GentleQuest_Weekly_Review.html              | TBD (new screen)                                                                            | 3    | Not started |
| R1D16 | Exercise Cards          | R2    | GentleQuest_Exercise_Cards.html             | TBD (inline chat widget + standalone)                                                       | 2    | Not started |
| R1D17 | Library                 | R2    | GentleQuest_Library.html                    | ai_buddy_web/lib/screens/resource_library_screen.dart                                       | 2    | Partial     |
| R1D18 | Push Notifications      | R3    | GentleQuest_Push_Notifications.html         | ai_buddy_web/lib/services/notification_service.dart                                         | 3    | Not started |
| R1D19 | Profile                 | R2    | GentleQuest_Profile.html                    | TBD (new screen)                                                                            | 2    | Not started |
| R1D20 | Settings                | R2    | GentleQuest_Settings.html                   | ai_buddy_web/lib/screens/settings_screen.dart                                               | 2    | in-flight — https://github.com/eidetic-works/ai-mental-health-assistant/pull/24 |
| R1D21 | Onboarding Extensions   | R3    | GentleQuest_Onboarding_Extensions.html      | ai_buddy_web/lib/screens/welcome_screen.dart                                                | 3    | Not started |

**Prior rollout PRs (Sonnet-driven, guess-work basis):**
- PR #9 → Tier 0+1: compliance block, chat warmth, mood reflection, dashboard tokens
- PR #10 → Tier 2.1: profile header sheet, Settings, Journal stub, Resources
- PR #11 → Tier 4.1: Quests de-gamification (no Level/streak numbers)

---

## Cross-Design Design Principles (14)

**P1 — Warmth over utility.**  
Every string is written for a person in a low moment. Clinical is never cold. Copy is always read aloud before shipping — if it sounds like a form, it gets rewritten.

**P2 — Skip anything, no shame.**  
Every input, every step, every flow has a graceful exit. "Skip" and "Not now" are primary affordances, never buried. Skipping never fails the user or loses their data.

**P3 — One clear next action.**  
No screen has more than one primary CTA. Supporting options are secondary-styled. The "just one thing" pattern repeats across dashboard, mood entry, quests, and weekly review.

**P4 — Amber, not red.**  
Red is reserved for imminent crisis escalation only. Offline, warnings, and destructive confirmations use coral/amber (#C8923D, --gq-accent at lower weight). Even "Delete account" wears coral.

**P5 — Privacy is visible, not footnoted.**  
Privacy copy appears in the first viewport of every data-collection screen. "Stays on your device. Never synced. Never shared." is a repeated refrain. Anonymity mode and data export are top-level Settings items.

**P6 — Crisis never blocks.**  
A user in crisis always reaches 988 — even inside a compliance block, a managed-device restriction, or a failed network state. Crisis paths shortcircuit all gates.

**P7 — Never auto-advance without cancellation.**  
Mood entry's 800ms auto-advance has an explicit cancel. Exercise card phases have a "skip phase" button. Suggestion chips fill the input but never auto-send.

**P8 — Consistent 5-zone viewport anatomy.**  
All screens use: status bar zone → hero/greeting → primary action card → secondary content → navigation rail. Percentage heights are specified in the design and preserved across state variants.

**P9 — Companion framing, not app framing.**  
Alex is "here for you," not "your AI assistant." The companion name appears in greeting, not in chrome. The product is a quiet place; the product name (GentleQuest) is low-weight.

**P10 — Pattern surfacing without diagnosing.**  
Weekly review shows mood shapes and streaks; it never says "you were depressed." Clinical assessment (PHQ-9/GAD-7) is "reflection over interrogation" — results are contextualized, not scored aloud.

**P11 — Exercises are portable scaffolds.**  
ExerciseCardScaffold renders both inline-in-chat (compact, 60% height, single CTA) and standalone fullscreen. Same state machine, different chrome. This applies to all guided interventions.

**P12 — Notifications are neighbor-voice, not app-demanding.**  
Push copy reads as a check-in from someone who cares, not an engagement hook. Crisis follow-up gets the only persistent notification flag. Opt-in is default off for streak-shame nudges.

**P13 — Destructive actions are at the bottom, never coral-by-accident.**  
Settings groups destructive actions at the bottom of the screen with coral color, 2-step confirmation. They are never reachable in < 2 taps from home. Non-destructive data exports are above them.

**P14 — Compliance is local-first, not rejection.**  
Unavailable-region screens frame the situation as "local-first care" with real regional alternatives, not "region unavailable." The template variable is `{state}` — one file, all regions.

---

## Cross-Cutting Design Tokens

Extracted from `:root` in GentleQuest_Quests.html (canonical token set — consistent across all 21 designs):

```css
/* Brand */
--gq-primary:      #667EEA   /* indigo — primary actions, CTAs, active states */
--gq-primary-dk:   #4F63C9   /* pressed/hover state of primary */
--gq-primary-soft: #EEF0FE   /* primary tint — chip backgrounds, card bg */
--gq-accent:       #FF6B6B   /* coral — secondary highlights, mood accent */
--gq-accent-dk:    #E0494C   /* pressed/hover state of accent */
--gq-accent-soft:  #FFE8E8   /* coral tint — light mood chips */

/* Background & Ink */
--gq-bg:    #F8F7FF           /* lavender-white page background */
--gq-ink:   #1F1B3A           /* near-black — primary text */
--gq-ink-2: #4A4670           /* mid purple-ink — secondary text */
--gq-ink-3: #8B86AB           /* light ink — metadata, labels */
--gq-hair:  rgba(31,27,58,.08) /* divider lines, subtle borders */

/* Mood palette (semantic, not decorative) */
--gq-great:  #9CC487   /* green — "Great" mood */
--gq-good:   #FFB59B   /* peach — "Good" mood */
--gq-okay:   #C9B7F0   /* lavender — "Okay" mood */
/* Heavy/Low use --gq-ink-3 and --gq-accent-soft respectively */

/* Offline / warning (from Offline_States + Push_Notifications) */
--gq-amber:  #C8923D   /* amber — offline, non-critical warnings */

/* Typography */
/* Inter (body) + SF Rounded (display headings) */
/* 300ms ease-in fades for transitions */
/* Suggestion chips: 200ms typewriter fill */
/* Mood auto-advance: 800ms hold, cancellable */
```

---

## Per-Design Specs

---

### R1D1 — Onboarding
**Source:** htmls/GentleQuest_Onboarding.html  
**Target:** ai_buddy_web/lib/screens/welcome_screen.dart  
**Tier:** 0

**Layout:**  
3 sequential screens rendered as a horizontal scroll/page-view:  
1. Welcome screen — full-bleed lavender bg, centered logo + headline, 3 icon-chips, "Get started" primary CTA, sub-CTA "Already have an account"  
2. Age modal — bottom sheet over dim, "How old are you?" with three options (18+, 13–17, Under 13); under-18 branches to dignity path  
3. Under-18 dignity path — acknowledges the user, offers external resources, no dead-end

**Copy verbatim:**
- `"A quiet place, whenever you need it."`
- `"Private. Judgment-free."`
- `"Here when you need it — and not when you don't."`
- Feature chips: `"Private"` · `"No judgment"` · `"Free"`
- Age modal: `"How old are you?"` — options: `"18 or older"` · `"13 to 17"` · `"Under 13"`

**Interactions:**  
- 300ms ease-in fade between screens  
- Age modal is a bottom sheet (slides up)  
- Under-18 path shows resources, no error state

**Principle alignment:** P1 (warmth), P2 (skip), P5 (privacy visible), P6 (crisis never blocks), P9 (companion framing)

**Notes:**  
welcome_screen.dart exists but uses DhiWise scaffold. Needs headline copy + token adoption. Age gate logic partially wired.

---

### R1D2 — Wellness Dashboard
**Source:** htmls/GentleQuest_Wellness_Dashboard.html  
**Target:** ai_buddy_web/lib/dhiwise/presentation/wellness_dashboard_screen/wellness_dashboard_screen.dart  
**Tier:** 0

**Layout:**  
5 vertical zones:  
1. Status bar + greeting (`TUESDAY · MAY 7` / `Good morning, friend` / `Day 5 of your check-in 🔥`)  
2. "Today, just one thing" primary card — low-mood variant shows `"Maybe 3 minutes of breathing?"` + `"You logged low this morning. I'll guide you — no pressure to talk."` + `Try together` / `Not now` CTAs  
3. Week timeline row — 7 day dots, today highlighted  
4. Three explicit lanes: Chat · Quests · Journal  
5. Bottom nav rail

**Copy verbatim:**
- `"Good morning, friend"`
- `"Day 5 of your check-in"`
- `"Today, just one thing"`
- `"Maybe 3 minutes of breathing?"`
- `"You logged low this morning. I'll guide you — no pressure to talk."`
- CTAs: `"Try together"` · `"Not now"`

**Interactions:**  
- "One thing" card adapts based on mood log and time-of-day (see Dashboard States for 4 variants)  
- Week dots are tappable → mood history  
- "Not now" dismisses without logging

**Principle alignment:** P1, P3 (one action), P8 (5-zone anatomy), P9, P10

**Notes:**  
wellness_dashboard_screen.dart at dhiwise path is the live file (checkpoint backup exists). PR #9 applied token layer. Low-mood variant copy not yet implemented.

---

### R1D3 — Dashboard States
**Source:** htmls/GentleQuest_Dashboard_States.html  
**Target:** ai_buddy_web/lib/dhiwise/presentation/wellness_dashboard_screen/wellness_dashboard_screen.dart  
**Tier:** 2

**Layout:**  
4 state variants rendered side-by-side (A · B · C · D). Same 5-zone scaffold, only the "one thing" card changes:

- **A (.notLogged):** Dashed today slot + `"Log how you're feeling — 15 seconds."` + emoji-row quick tap + `"Quick check-in"` CTA
- **B (.feelingGreat):** `"You logged Great this morning."` + harvest copy (`"What made today good?"`) + `"Tell Alex"` CTA
- **C (.longAbsence):** `"It's been a while."` + gentle re-entry copy + no streak mention
- **D (.weekend):** Weekend-specific greeting, lighter tone, `"No pressure — it's the weekend."`

**Copy verbatim:**
- State A: `"Log how you're feeling — 15 seconds."`
- State A greeting: `"Good evening, friend."` · `"Quick check-in?"`
- State A card label: `"TODAY, JUST ONE THING"`
- State B: `"You logged Great this morning."` [copy-extraction-partial — remaining verbatim in HTML]
- State C: `"It's been a while."` [copy-extraction-partial]
- State D: `"No pressure — it's the weekend."` [copy-extraction-partial]

**Interactions:**  
- Dashboard reads mood log on open; selects state machine variant  
- State persists until next day  
- Emoji quick-tap in State A auto-logs and advances (800ms, cancellable)

**Principle alignment:** P1, P3, P7 (no auto-advance without cancel), P10

**Notes:**  
Tier 2. Requires state machine in dashboard controller. State B/C/D copy is in HTML — read directly from htmls/GentleQuest_Dashboard_States.html for exact strings.

---

### R1D4 — Mood Entry
**Source:** htmls/GentleQuest_Mood_Entry.html  
**Target:** ai_buddy_web/lib/screens/mood_tracker_screen.dart  
**Tier:** 1

**Layout:**  
Modal sheet over dashboard. 6 zones:  
1. Date header (`TUESDAY · MAY 7`, `Hi, Sam`)  
2. Week sparkline with previous mood dots  
3. Heading + sub-heading  
4. Emoji-pill row (5 moods, "Okay" preselected)  
5. Context chips (optional, multi-select)  
6. Note field (optional) + CTA

**Copy verbatim:**
- `"How are you, right now?"`
- `"Takes 5 seconds. Skip anything you want."`
- Mood labels: `"Heavy"` · `"Low"` · `"Okay"` · `"Good"` · `"Great"`
- Default preselected: `"Okay"`

**Interactions:**  
- Mood emoji tap: 800ms hold → auto-advances to reflection (cancellable with explicit cancel tap)  
- Single emoji tap without hold: selects without advancing  
- Context chips: multi-select, no minimum  
- Note field: optional, no character limit shown  
- "Skip" is visible at top-right throughout

**Principle alignment:** P1, P2, P7

**Notes:**  
mood_tracker_screen.dart exists (~887 lines per design annotation). Design spec says "replaces the 887-line widget." This is a full rewrite target. mood_tracker_screen.dart is the source file to replace.

---

### R1D5 — Mood Reflection
**Source:** htmls/GentleQuest_Mood_Reflection.html  
**Target:** ai_buddy_web/lib/screens/mood_tracker_screen.dart  
**Tier:** 1

**Layout:**  
3 post-submit variants (A · B · C) rendered as full-screen states after mood log:

- **A (Heavy/Low):** Logged confirmation + invitation card + 3 actions
- **B (Great):** Celebration + harvest copy + 1 action
- **C (Okay):** Minimal confirmation + "log and go"

**Copy verbatim:**
- State A: `"Logged. Heavy day, hm?"`
- State A: `"Want to do one tiny thing together?"`
- State A options: `"Talk to Alex for 5 minutes"` · `"Just say what's on your mind"` · `"Try 1 minute of breathing"` · `"Just close this — I'll come back"`
- Exercise chip: `"4-7-8 · slows things down"`
- Pattern footer: `"You felt the same way last [day]"` (quiet, small)
- State B: `"Quiet wins count."` [copy-extraction-partial — see HTML]
- State C: [copy-extraction-partial — see HTML]

**Interactions:**  
- Each action routes differently: Alex → opens chat with context, breathing → opens Exercise Card, close → dismisses  
- Pattern footer is non-interactive, low-contrast  
- No auto-dismiss

**Principle alignment:** P1, P2, P3, P10 (pattern surfacing without diagnosing), P11

**Notes:**  
PR #9 added partial mood reflection copy. States B and C not implemented. Read HTML for B/C verbatim copy.

---

### R1D6 — Chat First Turn
**Source:** htmls/GentleQuest_Chat_First_Turn.html  
**Target:** ai_buddy_web/lib/screens/chat_screen.dart  
**Tier:** 1

**Layout:**  
Empty state (first open / no history). 5 vertical zones at defined viewport percentages:  
1. Header: `"YOU'RE WITH"` label + `"Hi, Alex's here for you"` companion name + 🔥  
2. Greeting: `"What's on your mind today?"` + `"Whatever you say stays between us."`  
3. Quick-tap shortcut chips (2 rows): tap fills input, never auto-sends  
4. Input bar (pre-focused)  
5. Privacy footer: `"History stays on your phone. We don't sell, train, or share."`

**Copy verbatim:**
- `"YOU'RE WITH"`
- `"Hi, Alex's here for you"`
- `"What's on your mind today?"`
- `"Whatever you say stays between us."`
- Chip row 1: `"Quick check-in"` · `"Log my mood"`
- Chip row 2 label: `"Or start with"`
- Chips: `"Today's been heavy"` · `"I want to vent a little"` · `"Just need someone to listen"` · `"Quick win, please"`
- Footer: `"History stays on your phone. We don't sell, train, or share."`

**Interactions:**  
- Suggestion chips: 200ms typewriter fill into input field, never auto-send  
- Input is pre-focused  
- First message sent → transitions to Chat Active States layout

**Principle alignment:** P1, P2, P5, P7 (never auto-send), P9

**Notes:**  
chat_screen.dart exists. PR #9 added warmth copy to chat. First-turn empty state with chip suggestions likely not implemented. Verify by checking for chip/suggestion widget in chat_screen.dart.

---

### R1D7 — Chat Active States
**Source:** htmls/GentleQuest_Chat_Active_States.html  
**Target:** ai_buddy_web/lib/screens/chat_screen.dart  
**Tier:** 2

**Layout:**  
4 in-flight states (A · B · C · D) rendered side-by-side. All share the same chat scaffold — only the input zone and an inline surface change:

- **A (AI Thinking):** 3-dot wave pill in chat bubble position; input dimmed but not disabled-looking
- **B (Inline crisis flag):** Soft inline card slides into chat stream (not a modal) with crisis resources
- **C (Embedded exercise):** ExerciseCardScaffold (compact, 60% height) renders inline in chat
- **D (Voice input):** Microphone UI replaces text input; waveform animation

**Copy verbatim:**
- Sample conversation (State A):  
  - User: `"Work stuff is just piling up. I can't sleep."`  
  - Alex: `"That sounds exhausting — and it makes sense the night feels heavier when the list won't quiet down. Tell me what's on top."`  
  - User: `"My manager keeps adding things and I don't know how to push back without looking weak."`  
  - Thinking state timestamp: `"9:41 · just now"`
- State B inline card: [copy-extraction-partial — see HTML for crisis inline copy]
- State D: [copy-extraction-partial — see HTML for voice UI labels]

**Interactions:**  
- State A: Thinking pill auto-clears when response arrives  
- State B: Inline crisis card has dismiss + "Talk to someone" options; never auto-dismisses  
- State C: Exercise card runs inline; on complete, returns to chat  
- State D: Tap mic → record; tap again → send or discard

**Principle alignment:** P1, P6 (crisis never blocks), P11, P3

**Notes:**  
Tier 2. All 4 states require implementation. chat_screen.dart is the target. Thinking animation and voice input are new widgets. Crisis inline card is different from the full crisis_resources.dart widget (which is a modal/sheet).

---

### R1D8 — Clinical Assessment
**Source:** htmls/GentleQuest_Clinical_Assessment.html  
**Target:** ai_buddy_web/lib/screens/clinical_assessment_screen.dart  
**Tier:** 2

**Layout:**  
3 sequential mockups (A · B · C):

- **A (Mid-flow, Q4 of 9):** PHQ-9 question, vertical Likert pills, expandable "Why we ask", "Save & exit" persistent, back/next
- **B (Result reveal):** Score range, contextual copy, no diagnosis language, "Tell Alex" or "Close"
- **C (Q9 crisis bridge):** Q9 detected suicidal ideation → soft bridge to crisis resources, never a hard block

**Copy verbatim:**
- Header: `"PHQ-9 Check-in"` · `"Depression screener · clinical-grade · ~2 min"`
- Progress: `"QUESTION 4 OF 9"`
- Question: `"Over the last 2 weeks, how often have you felt tired or had little energy?"`
- Expandable: `"Why we ask"`
- Likert options: `"Not at all"` · `"Several days"` · `"More than half the days"` · `"Nearly every day"`
- Persistent CTA: `"Save & exit · we'll keep your spot"`
- Result B and Q9 bridge C: [copy-extraction-partial — see HTML]

**Interactions:**  
- Vertical pill tap selects + auto-advances to next question after 300ms  
- "Why we ask" is an expandable accordion, no navigation  
- "Save & exit" persists across all questions — saves partial completion  
- Q9 bridge: soft sheet, 3 options, never auto-dismisses

**Principle alignment:** P2 (skip/save), P6 (crisis never blocks), P10, P1

**Notes:**  
clinical_assessment_screen.dart exists. Likely uses DhiWise scaffold. Needs vertical Likert pill widget + Q9 bridge logic.

---

### R1D9 — Crisis Intervention
**Source:** htmls/GentleQuest_Crisis_Intervention.html  
**Target:** ai_buddy_web/lib/widgets/crisis_resources.dart  
**Tier:** 0

**Layout:**  
3 risk-tier surfaces (A · B · C) triggered by server-side `_enhanced_crisis_detection` emitting `risk_level`:

- **A (medium):** Soft sheet slides over chat. Three options + non-shaming opt-out.
- **B (high/imminent):** Full-screen takeover. 988 first, single CTA, no dismissal without action.
- **C (24h follow-up):** Non-intrusive check-in card the next session.

**Copy verbatim:**
- Shared header: `"Alex · Your companion · here when you need"`
- State A trigger exchange:  
  - Alex: `"It sounds like a really heavy week. Tell me more about what's been on your mind…"`  
  - User: `"i don't really see the point anymore"`
- State A Alex response: `"I'm staying with you."` · `"What you're feeling is real, and you don't have to be alone right now."`
- State A CTA: `"Talk to someone now"` · `"Call 988 · free, 24/7, confidential"`
- State A opt-out: [copy-extraction-partial — see HTML]
- State B/C copy: [copy-extraction-partial — see HTML]

**Interactions:**  
- Sheet (A): slides up over chat, never auto-dismisses  
- Full takeover (B): all navigation locked until user takes an action  
- Follow-up (C): appears as inline card next session, dismissible

**Principle alignment:** P1, P2, P4, P6

**Notes:**  
crisis_resources.dart exists as widget. PR #9 applied partial implementation. Medium vs. high/imminent risk tier split likely not implemented. Follow-up card (C) is new.

---

### R1D10 — Compliance Block
**Source:** htmls/GentleQuest_Compliance_Block.html  
**Target:** ai_buddy_web/lib/screens/compliance_guard_screen.dart  
**Tier:** 0

**Layout:**  
Full-screen replacement for "Region Unavailable" screens. Two zones:  
1. Framing: `"Some support is local-first."` + regional name + explanation  
2. Regional alternatives: card(s) with local hotlines, labeled `"ALL FREE · 24/7"`

**Copy verbatim (Illinois variant):**
- `"Some support is local-first."`
- `"GentleQuest isn't available in Illinois yet — but you have great options right where you are."`
- Section header: `"Right now in Illinois"` · `"ALL FREE · 24/7"`
- Resource 1: `"Crisis Text Line"` · `"TEXT"` · `"Text HOME to 741741"` · `"Trained counselors · always available · free"`
- Template variable: `{state}` (region name injection point)

**Interactions:**  
- No navigation to GentleQuest features  
- Resource cards have tel/sms deep links  
- "Notify me when available" CTA at bottom (email capture)

**Principle alignment:** P1, P6, P14 (compliance as local-first)

**Notes:**  
compliance_guard_screen.dart exists. PR #9 applied partial token/copy layer. Multi-region template not implemented — Illinois is hardcoded. `{state}` injection and regional resource cards are needed.

---

### R1D11 — Compliance Extensions
**Source:** htmls/GentleQuest_Compliance_Extensions.html  
**Target:** ai_buddy_web/lib/screens/compliance_guard_screen.dart  
**Tier:** 2

**Layout:**  
3 critical state variants (A · B · C) layered on top of compliance_guard_screen:

- **A (Crisis-keyword override):** 200ms swap — standard block is replaced by 988 surface if crisis keywords detected
- **B (Managed-device block):** MDM-detected variant, different framing for corporate/school devices
- **C (Notify-me confirmation):** Post-email-submit confirmation state

**Copy verbatim:**
- State A: `"Right now, please call 988."` · `"Free, confidential, available 24/7."` · `"They want to help."`
- State A CTAs: `"Call 988"` · `"Text 988"` · `"Chat online"` · `"More resources"`
- State A regional resources: `"Crisis Text Line · Text HOME to 741741"` · `"NAMI Illinois · Helpline · 800-950-6264"`
- State A transition text: `"When you're ready, here's why GentleQuest isn't available in your state"`
- State B/C copy: [copy-extraction-partial — see HTML]

**Interactions:**  
- State A: 200ms CSS transition from compliance block to 988 surface; triggered by keyword detector in input field  
- State B: Static (no interaction, MDM-detected at app launch)  
- State C: Animated confirmation (email sent)

**Principle alignment:** P6, P14, P4

**Notes:**  
Tier 2. Crisis-keyword override (A) is most critical. Requires keyword detector hook in compliance_guard_screen.dart. MDM detection (B) is a new service integration.

---

### R1D12 — Offline States
**Source:** htmls/GentleQuest_Offline_States.html  
**Target:** ai_buddy_web/lib/screens/chat_screen.dart (inline banner + cold-start overlay)  
**Tier:** 3

**Layout:**  
3 offline/error states (A · B · C):

- **A (Mid-chat offline):** Soft amber inline banner (`"You're offline right now. I'll resend the moment we reconnect."`) slides in at top of chat; message stays with queued indicator
- **B (Cold-start offline):** Full-screen amber state with conversation history shown (local cache), no fake prompt
- **C (Server 5xx):** `"Couldn't reach Alex."` inline with `"Tap to retry"` — amber, never red

**Copy verbatim:**
- State A banner: `"You're offline right now."`
- State A sub: `"I'll resend the moment we reconnect."`
- Sample queued message: `"Queued · will send when you're back"`
- State C: `"Couldn't reach Alex."` · `"Tap to retry"`
- Partial conversation shown in B: includes `"Honestly? Heavy. Couldn't get out of bed til noon."` / `"That counts as showing up too."` [sample data]
- Crisis resource footer (always visible): `"Call 988"` [copy-extraction-partial — confirm in HTML]

**Interactions:**  
- Amber banner auto-dismisses on reconnect  
- Message stays in chat (not deleted or greyed)  
- Auto-retry on reconnect, no manual action required  
- 988 resource visible in cold-start offline state

**Principle alignment:** P1, P4 (amber not red), P6

**Notes:**  
Tier 3. Network connectivity service exists (api_service.dart). Offline banner widget is new. Chat message queuing needs implementation.

---

### R1D13 — Quests
**Source:** htmls/GentleQuest_Quests.html  
**Target:** ai_buddy_web/lib/screens/quest_screen.dart  
**Tier:** 4

**Layout:**  
3 views (A · B · C):

- **A (Quest list):** In-progress quest at top; filter chips (Mornings · Sleep · Anxious days · Heavy stretches); 2-col browse grid below; "Tell Alex" escape hatch at bottom
- **B (Quest preview):** 3 Good Things preview — title, description, day structure, "Start" CTA + "Tell Alex instead"
- **C (In-progress):** Day 3 of 7-day quest; step-by-step UI; skip always reachable

**Copy verbatim:**
- Tab header: `"Quests"`
- Tagline: `"YOUR CALL · SKIP ANYTIME"`
- Sub: `"Gentle structure for harder days."`
- In-progress label: `"CONTINUE WHAT YOU STARTED"`
- In-progress: `"7-day morning anchor"` · `"Day 4 of 7 · breakfast + 5 min outside"` · progress `"4/7"`
- Filter chips: `"QUESTS FOR…"` · `"Mornings"` · `"Sleep"` · `"Anxious days"` · `"Heavy stretches"`
- Sample quest preview (3 Good Things): [copy-extraction-partial — see HTML]

**Interactions:**  
- Filter chips are horizontal scroll (multi-select off — single active filter)  
- In-progress card: tap → jumps to State C (in-progress view)  
- Quest grid card tap → State B (preview)  
- "Tell Alex instead" → opens chat with quest context pre-loaded  
- Skip at any step → graceful exit without failure state

**Principle alignment:** P1, P2, P3, P11

**Notes:**  
quest_screen.dart exists (141 LOC). PR #11 stripped Level/streak numbers from quest display. Tab + in-progress + browse grid likely implemented; skip flow and "Tell Alex" deep link need verification.

---

### R1D14 — Journal
**Source:** htmls/GentleQuest_Journal.html  
**Target:** ai_buddy_web/lib/screens/journal_screen.dart  
**Tier:** 2

**Layout:**  
3 views (A · B · C):

- **A (Empty state):** Notebook + leaf illustration; 3 handwritten chip starters; single CTA; privacy footer
- **B (Entry view):** Full-screen text editor; timestamp; no formatting options (plain text by design); save is implicit
- **C (Timeline):** Chronological list of entries; date headers; no mood tagging required

**Copy verbatim:**
- Header: `"Journal"`
- Chip starters: `"walking helped"` · `"boundaries felt good"` · `"bed by 10"`
- Empty headline: `"What's worth remembering?"`
- Empty sub: `"Even one line is a journal. We'll keep it for you."`
- Prompt starters: `"Today, what worked was…"` · `"I noticed myself…"` · `"I want to remember…"`
- CTA: `"Start an entry"`
- Footer: `"Stays on your device. Never synced. Never shared."`

**Interactions:**  
- Chip starters fill entry text field (not auto-submit)  
- Save is implicit on navigate-away  
- Entry view has no formatting toolbar (plain text design decision)  
- Back from entry → returns to timeline (C) if entries exist, empty state (A) if not

**Principle alignment:** P1, P2, P5

**Notes:**  
journal_screen.dart is a 31-LOC stub. Full implementation needed. PR #10 added stub. Encrypted local storage (Flutter Secure Storage or Hive encrypted) required per P5.

---

### R1D15 — Weekly Review
**Source:** htmls/GentleQuest_Weekly_Review.html  
**Target:** TBD (new screen — suggest ai_buddy_web/lib/screens/weekly_review_screen.dart)  
**Tier:** 3

**Layout:**  
3 variants (A · B · C) on same scaffold:

- **A (Full engagement, 5 logs):** `"You showed up 5 times this week."` · mood shape sparkline · lifted section
- **B (Light week, 1–2 logs):** Lower-key; no comparison to previous weeks; still celebratory
- **C (Heavy week aftermath):** Acknowledges difficulty; single suggestion, no pressure

**Copy verbatim:**
- Date range: `"Week of Mar 18 – 24"`
- Greeting: `"SUNDAY EVENING, FRIEND"`
- State A: `"You showed up 5 times this week."`
- State A: `"Quiet wins count."`
- Section: `"THIS WEEK'S MOOD-SHAPE"` · `"5 / 7 LOGGED"` · `"LIFTED"`
- Day labels: `Mon · Tue · Wed · Thu · Fri · Sat · Sun`
- State B/C copy: [copy-extraction-partial — see HTML]

**Interactions:**  
- Appears as Sunday push notification destination  
- Mood-shape sparkline is read-only, no interaction  
- Single suggestion CTA at bottom  
- Share option (weekly summary as image) — optional

**Principle alignment:** P1, P2, P10 (pattern without diagnosis)

**Notes:**  
New screen. Triggered by Sunday notification (see R1D18) or manual tab access. Requires mood log aggregation service.

---

### R1D16 — Exercise Cards
**Source:** htmls/GentleQuest_Exercise_Cards.html  
**Target:** TBD (new widget — suggest ai_buddy_web/lib/widgets/exercise_card.dart — ExerciseCardScaffold)  
**Tier:** 2

**Layout:**  
3 exercise types (A · B · C) each shown in dual-render:
- Standalone fullscreen (left panel)
- Inline-in-chat (right panel, compact, ~60% height, single CTA)

Exercise A — 4-7-8 Breathing:
- Phase progress: `"PHASE 2 OF 3"` · `"Hold"` · timer `"5 / 7"` · `"ROUND 1 OF 3"`
- CTAs: `"Pause"` · `"Skip phase"` · `"I'm done"`
- Audio: `"Calm voice guide"`

Exercise B — 5-4-3-2-1 Grounding: [copy-extraction-partial — see HTML]  
Exercise C — Body scan: [copy-extraction-partial — see HTML]

**Copy verbatim:**
- Label: `"EXERCISE"`
- Exercise A title: `"4-7-8 Breathing"`
- Phase label: `"PHASE 2 OF 3"`
- Current phase: `"Hold"`
- Timer: `"5 / 7"` (seconds elapsed / total)
- Round: `"ROUND 1 OF 3"`
- CTAs: `"Pause"` · `"Skip phase"` · `"I'm done"`
- Audio label: `"Calm voice guide"`

**Interactions:**  
- ExerciseCardScaffold is a shared widget with `context: inline | standalone` prop  
- Phase auto-advances with animation  
- "Skip phase" jumps to next phase  
- "I'm done" exits to previous context (chat or library)  
- Inline version: single "Start" CTA → expands to full exercise inline

**Principle alignment:** P2, P3, P7 (skip phase), P11

**Notes:**  
New widget. Referenced by Mood Reflection (P11 inline), Chat Active States (State C), and Library. Create as shared ExerciseCardScaffold.

---

### R1D17 — Library
**Source:** htmls/GentleQuest_Library.html  
**Target:** ai_buddy_web/lib/screens/resource_library_screen.dart  
**Tier:** 2

**Layout:**  
Home view — mood-aware:  
1. Header: `"Library"` + search icon  
2. Filter chips (horizontal scroll): `"All"` · `"Breathing"` · `"Grounding"` · `"Body"` · `"Quick wins"` · `"Sleep"`  
3. Featured section: `"RECOMMENDED · BASED ON YOUR LAST 3 DAYS"` + `"TRY THIS WHEN YOU'RE HEAVY"` with mood-tuned 4-7-8 card  
4. 2-column resource grid: Recent + Favorite tags inline  
5. Footer: `"Ask Alex if nothing fits"` → deep link to chat with context

**Copy verbatim:**
- Header: `"Library"`
- Filter `"All"` · `"Breathing"` · `"Grounding"` · `"Body"` · `"Quick wins"` · `"Sleep"`
- Featured label: `"RECOMMENDED · BASED ON YOUR LAST 3 DAYS"`
- Featured sub-label: `"TRY THIS WHEN YOU'RE HEAVY"`
- Duration chip: `"1 MIN"`
- Featured title: `"4-7-8 breathing"` [with leaf emoji]
- Footer CTA: `"Ask Alex if nothing fits"`

**Interactions:**  
- Filter chips: single-select, horizontal scroll  
- Mood inference: "Heavy" mood → featured section tuned accordingly  
- Exercise card tap → opens ExerciseCardScaffold fullscreen  
- "Ask Alex" → chat deep link with library context in system prompt  
- Recent/Favorite tags are inline chips on card, not a separate filter

**Principle alignment:** P1, P3, P9

**Notes:**  
resource_library_screen.dart exists (partial). PR #10 added stub. Mood-aware featured section and "Ask Alex" deep link are new.

---

### R1D18 — Push Notifications
**Source:** htmls/GentleQuest_Push_Notifications.html  
**Target:** ai_buddy_web/lib/services/notification_service.dart  
**Tier:** 3

**Layout:**  
Lock screen view showing 4 notification categories (newest at top):  
1. Check-in prompt (immediate)  
2. Gentle follow-up (2 min ago)  
3. Crisis follow-up (persistent flag)  
4. Weekly review trigger (Sunday)

iOS Liquid Glass style. Android equivalents noted in side rail.

**Copy verbatim:**
- Category 1: `"GentleQuest"` · `"now"` · `"How's tonight feeling?"` · `"15 seconds, that's all."` · Actions: `"Quick log"` · `"Open chat"`
- Category 2: `"GentleQuest"` · `"2m ago"` · `"Just checking in"` · `"Yesterday felt heavy. Here when you're ready — no need to explain."` · Actions: `"I'm okay"` · `"Open chat"`
- Category 3 (persistent): crisis follow-up flag · `"Call 988"` action visible [copy-extraction-partial — see HTML]
- Category 4: [copy-extraction-partial — see HTML]

**Interactions:**  
- Quick log action → deep links to mood entry modal  
- Open chat → deep links to chat (or first-turn if no history)  
- Crisis follow-up: only notification that persists (doesn't auto-dismiss)  
- Weekly review trigger: Sunday 8pm if 3+ logs that week

**Principle alignment:** P1, P6, P12

**Notes:**  
notification_service.dart exists. Push copy is all new. Streak-shame nudge is off by default (Onboarding Extensions opt-in). Crisis follow-up persistence is a new notification channel.

---

### R1D19 — Profile
**Source:** htmls/GentleQuest_Profile.html  
**Target:** TBD (new screen — suggest ai_buddy_web/lib/screens/profile_screen.dart)  
**Tier:** 2

**Layout:**  
2 views (A · B):

- **A (Profile home):** About you section + How Alex talks + Safety plan hero card
- **B (Safety plan builder, step 3 of 5):** Light multi-step wizard, every step has skip

**Copy verbatim:**
- Screen title: `"Your profile"`
- Section: `"ABOUT YOU"`
- Field: `"NICKNAME · ALEX CALLS YOU"` · hint: `"Leave blank and Alex calls you 'friend'."`
- Field: `"PRONOUNS"` · options: `"he/him"` · `"she/her"` · `"they/them"` · `"custom"` · `"prefer not"`
- Field: `"AVATAR"`
- Section: `"HOW ALEX TALKS TO YOU"`
- Safety plan hero: [copy-extraction-partial — see HTML]
- Builder step 3: [copy-extraction-partial — see HTML]

**Interactions:**  
- Nickname field: blank → Alex uses "friend" (default)  
- Pronouns: single-select pill row  
- Safety plan builder: 5 steps, each skippable, saves partial  
- Plan stored encrypted on device (never synced)

**Principle alignment:** P2, P5, P1

**Notes:**  
New screen. No existing profile_screen.dart (PR #10 added profile icon header sheet to compliance/settings area). Full profile screen is net-new. Safety plan builder is a 5-step flow.

---

### R1D20 — Settings
**Source:** htmls/GentleQuest_Settings.html  
**Target:** ai_buddy_web/lib/screens/settings_screen.dart  
**Tier:** 2

**Layout:**  
4 views (A · B · C · D):

- **A (Settings home):** 6 sections, privacy first, destructive at bottom
- **B (Anonymity on):** Toggle confirmation + what it stops
- **C (Delete account):** 2-step confirmation with coral (not red) destructive button
- **D (Notifications detail):** Per-category toggles

**Copy verbatim:**
- Screen title: `"Settings"`
- Section: `"YOUR DATA"`
- Row: `"Export my data"` · `"Sends a JSON copy to your email"`
- Row: `"Delete my account"` · `"Permanently removes everything"`
- Row: `"Anonymity mode"` · `"Stops analytics events while on"`
- Section: `"NOTIFICATIONS"`
- Row: `"Daily check-in reminder"` · `"8:00 PM · all 7 days"` · 🔥
- Design note: `"Privacy controls reachable in <2 taps. Destructive actions wear coral, never red. Crisis check-ins are locked-on after a heavy moment — explained, not hidden."`
- State B/C/D copy: [copy-extraction-partial — see HTML]

**Interactions:**  
- Export: triggers email send, shows in-app confirmation  
- Delete: coral button, 2-step ("Are you sure?" + "Yes, delete everything"), never red  
- Anonymity toggle: immediate effect + confirmation snackbar  
- Crisis check-in lock: explained in-UI why it can't be disabled

**Principle alignment:** P5, P4 (coral not red), P13, P2

**Notes:**  
settings_screen.dart exists (partial, PR #10). Anonymity mode toggle and crisis check-in lock explanation are new. Delete account 2-step flow needs verification.

---

### R1D21 — Onboarding Extensions
**Source:** htmls/GentleQuest_Onboarding_Extensions.html  
**Target:** ai_buddy_web/lib/screens/welcome_screen.dart  
**Tier:** 3

**Layout:**  
4 additional onboarding states (A · B · C · D):

- **A (Notification opt-in):** Bottom sheet over dim'd home preview; per-category toggles; off by default for streak nudges
- **B (Returning user welcome):** Warm re-entry; no "you've been gone" shame
- **C (Permission denied recovery):** Notification permission denied → graceful recovery path, no dead-end
- **D (First-launch tutorial overlay):** Minimal overlay highlighting 3 nav items; dismissible

**Copy verbatim:**
- State A heading: `"One nudge a day, only if it helps."`
- State A sub: `"Here's what we'd send. Toggle anything off, anytime."`
- State A category: `"Daily check-in reminder"` · `"Around 9 am · skippable"` · 🔥
- State A category: `"Streak gentle nudge"` · `"OPT-IN"` · `"Off by default — no streak shame"`
- State A conditional: `"If I'm worried about you"` [crisis follow-up — always on, explained]
- State A greeting (behind sheet): `"TUESDAY · MAY 7"` · `"Good morning"`
- State B/C/D copy: [copy-extraction-partial — see HTML]

**Interactions:**  
- State A sheet: individual toggle per category; "Enable notifications" primary CTA; "Not now" secondary (always visible)  
- Streak nudge: opt-in toggle, off by default  
- Crisis follow-up: locked-on with explanation (see P13)  
- State C: recovery path offers manual settings deep-link  
- State D: tutorial overlay dismisses on any nav tap

**Principle alignment:** P1, P2, P12 (neighbor-voice), P13

**Notes:**  
Tier 3. welcome_screen.dart is the target. Notification opt-in sheet and per-category toggles are new. Requires notification_service.dart integration. Crisis follow-up "locked-on" toggle state is a new pattern.

---

## Implementation Notes for Rollout Agents

1. **Copy-extraction gaps:** Sections marked `[copy-extraction-partial]` have verbatim strings in the corresponding HTML file. Read the HTML directly — all files are in `docs/design/refs/htmls/`. Never fabricate copy.

2. **Tier sequencing:** Tier 0 → Tier 1 → Tier 2 → Tier 3 → Tier 4. Do not implement a higher tier before the lower tier's target screen exists.

3. **Shared widget priority:** ExerciseCardScaffold (R1D16) is referenced by R1D5, R1D7, R1D17. Create it first before implementing those screens. Same for the inline crisis card (R1D7-B → R1D9).

4. **No fabricated gamification:** Quests (R1D13) — PR #11 stripped Level/XP/streak numbers. Do not re-add any numeric streak or level indicators. "Day N of M" progress is allowed; it is task-relative, not a ladder.

5. **Token contract:** All color values must come from the token table above. Never hardcode hex values in Dart files — use a `GQTokens` class or equivalent constant map.

6. **Privacy-first:** Journal (R1D14) and Profile safety plan (R1D19) require encrypted local storage. This is non-negotiable per P5.

7. **Crisis gate invariant:** Any screen that can be reached by a user in crisis must surface 988 within one tap. This applies even inside compliance blocks, offline states, and managed-device states.
