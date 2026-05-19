# GentleQuest — End-to-End Widget Use Cases
_Every screen · every widget · every sub-widget · every state variant_

Generated: 2026-05-19  
Source: live Flutter source across all 14 screens + widget library

---

## Reading guide

Each use case lists:
- **Screen / component** — the root widget under test
- **Precondition** — shared_preferences state, nav stack depth, provider state
- **Steps** — numbered taps/inputs with the **exact widget** in bold
- **Expected** — what renders, what fires, what state changes
- **Sub-widgets exercised** — every private class and nested widget touched

---

## Screen 1 — WelcomeScreen

### UC-W1 · Cold launch → hero render
**Precondition:** No SharedPreferences key `age_verified`; `_WelcomeState.hero`  
**Steps:**
1. App launches — `_WelcomeContent` renders inside `Stack`
2. Observe **`_AmbientBlob`** — two blurred `Container` circles (primary + accent) animate with slow scale pulse
3. Observe **`_BreathingIllustration`** — SVG-like `CustomPaint` with concentric rings, 5.6 s inhale/exhale loop
4. Observe three **`_TrustChip`** pills below illustration: 🔒 "Private by design", 🤝 "Not a diagnosis tool", ☁️ "Always here"
5. Observe headline `Text` ("A quiet place to check in") and sub-copy `Text`
6. Observe **`ElevatedButton`** with label **"Continue"** (full-width, GQColors.primary fill)

**Expected:** All widgets render; breathing animation running; no crash  
**Sub-widgets exercised:** `_WelcomeContent`, `_AmbientBlob`, `_BreathingIllustration`, `_TrustChip` ×3

---

### UC-W2 · Continue → age modal
**Precondition:** UC-W1 complete  
**Steps:**
1. Tap **`ElevatedButton("Continue")`**
2. **`_AgeModal`** slides up as `ModalBottomSheet` (drag handle at top, `isDismissible: false`)
3. Observe drag-handle `Container` (36×4 px, rounded)
4. Observe headline `Text` ("How old are you?") and sub-copy
5. Observe **`ElevatedButton("Yes, I am 18 or older")`** (primary fill, full-width)
6. Observe **`TextButton("Not yet")`** (no fill, accent text color)

**Expected:** Modal present; both buttons tappable  
**Sub-widgets exercised:** `_AgeModal`, drag-handle `Container`, two action buttons

---

### UC-W3 · Age modal → 18+ confirmed → ComplianceGuard
**Precondition:** `_AgeModal` open  
**Steps:**
1. Tap **`ElevatedButton("Yes, I am 18 or older")`**
2. SharedPreferences key `age_verified = true` written
3. `_WelcomeState` transitions → `Navigator.pushReplacement` to `ComplianceGuardScreen`

**Expected:** ComplianceGuardScreen renders; WelcomeScreen removed from stack

---

### UC-W4 · Age modal → Under-18 dignity path
**Precondition:** `_AgeModal` open  
**Steps:**
1. Tap **`TextButton("Not yet")`**
2. `_WelcomeState` transitions to `under18`; `_AgeModal` closes
3. **`_Under18Screen`** renders:
   - Back arrow `IconButton` (top-left)
   - Compassionate headline `Text` ("You matter — here are some resources")
   - **`_ResourceCard`** ×N — each card has title `Text`, subtitle `Text`, `Icons.open_in_new` `IconButton`
   - Footer `Text` ("Talk to a trusted adult or call 988")
4. Tap any **`_ResourceCard`** `IconButton` → `launchUrl()` fires (external browser)
5. Tap back **`IconButton`** → returns to `_WelcomeState.hero`

**Expected:** All resource cards render; external links launch; back returns to hero  
**Sub-widgets exercised:** `_Under18Screen`, `_ResourceCard` ×N, `IconButton(back)`, `IconButton(open_in_new)`

---

## Screen 2 — ComplianceGuardScreen

### UC-C1 · Available region — standard age gate
**Precondition:** `_ExtensionState.standard`; no MDM; region = available  
**Steps:**
1. `ComplianceGuardScreen` renders with GQ logo and region-aware copy
2. Observe **`ElevatedButton("I am 18 or older")`** (primary, full-width)
3. Observe **`TextButton("I am under 18")`** (below primary button)
4. Tap **`ElevatedButton("I am 18 or older")`** → HomeShell loads

**Expected:** Correct copy; both buttons tappable; 18+ routes to HomeShell  
**Sub-widgets exercised:** Logo widget, two action buttons

---

### UC-C2 · Blocked region — crisis path always reachable
**Precondition:** `_ExtensionState.blocked`; region = unavailable  
**Steps:**
1. Screen renders **`_BlockReasonDisclosure`** — expandable card explaining local-first framing
2. Observe **`_LifelineCard988`** — always-visible card with `Icons.phone` icon, "988 Suicide & Crisis Lifeline" `Text`, **`ElevatedButton("Call 988")`**
3. Tap **`ElevatedButton("Call 988")`** → `launchUrl(Uri.parse('tel:988'))` fires
4. Observe **`_TagPill`** ×N — regional alternative tags (e.g. "Text HOME to 741741")
5. Observe **`_RegionalResourceCard`** — state-specific resources with name, phone, hours
6. Observe **`_UniversalResourceCard`** ×N — national resources
7. Observe "Notify me when available" **`TextButton`** → opens email capture row:
   - **`TextField`** (email, keyboard type `emailAddress`)
   - **`ElevatedButton("Submit")`**
8. Type email → tap **`ElevatedButton("Submit")`** → confirmation `Text` appears; button disables

**Expected:** 988 always reachable; notify form submits; confirmation renders  
**Sub-widgets exercised:** `_LifelineCard988`, `_TagPill` ×N, `_RegionalResourceCard`, `_UniversalResourceCard` ×N, `_BlockReasonDisclosure`, `TextField(email)`, `ElevatedButton(Submit)`

---

### UC-C3 · MDM / managed-device state
**Precondition:** `_ExtensionState.mdm`  
**Steps:**
1. Screen shows managed-device copy ("This device is managed by your organisation")
2. **`_LifelineCard988`** still visible (P6 — crisis never blocks)
3. 200ms timer fires → crisis-keyword swap animation updates copy if crisis detected

**Expected:** MDM copy renders; 988 card always present  
**Sub-widgets exercised:** MDM copy `Text`, `_LifelineCard988`

---

## Screen 3 — InteractiveChatScreen (Talk tab)

### UC-I1 · First-turn render
**Precondition:** HomeShell loaded; Talk tab selected; no prior messages  
**Steps:**
1. Chat renders with Alex greeting bubble (R1D6 first-turn warmth copy, 3-second fade-in)
2. Observe **`_StreakBadge`** in app bar — shows current streak count with flame icon
3. Observe **`IconButton(Icons.account_circle_outlined)`** in app bar (profile nav)
4. Observe suggestion chips row — three **`_CrisisChip`**-styled chips ("I'm anxious", "I'm okay", "I had a bad day")
5. Observe **`_BreathingOrb`** — animated pulsing orb (if Alex is idle/waiting)
6. Bottom row: **`TextField`** (hint: "Message Alex…"), **`IconButton(Icons.send)`**, **`IconButton(Icons.mic_none)`** (voice toggle)

**Expected:** Greeting present; all widgets render; no crash  
**Sub-widgets exercised:** Greeting `ChatBubble`, `_StreakBadge`, `IconButton(account_circle)`, `_CrisisChip` ×3, `_BreathingOrb`, `TextField`, `IconButton(send)`, `IconButton(mic_none)`

---

### UC-I2 · Send a text message
**Precondition:** UC-I1 complete  
**Steps:**
1. Tap **`TextField`** → keyboard opens; cursor in field
2. Type "I'm feeling anxious today"
3. Observe **`IconButton(Icons.send)`** activates (accent color)
4. Tap **`IconButton(Icons.send)`**
5. User message bubble appears (right-aligned, primary background)
6. **`_TypingDots`** indicator appears (3 animated dots, 400ms stagger)
7. AI response bubble renders (left-aligned, surface background) after response

**Expected:** Message round-trip completes; typing indicator shows then hides  
**Sub-widgets exercised:** `TextField`, `IconButton(send)`, user `ChatBubble`, `_TypingDots`, AI `ChatBubble`

---

### UC-I3 · Suggestion chip → prefill → send
**Precondition:** First-turn state; chips visible  
**Steps:**
1. Tap any **`_CrisisChip`** (e.g. "I'm anxious")
2. Chip text fills **`TextField`** — does NOT auto-send (P7)
3. Observe cursor at end of prefilled text
4. Optionally edit text
5. Tap **`IconButton(Icons.send)`** → message fires

**Expected:** Prefill works; does not auto-send; chips hide after first message  
**Sub-widgets exercised:** `_CrisisChip`, `TextField` (auto-fill), `IconButton(send)`

---

### UC-I4 · Voice input toggle
**Precondition:** Chat screen visible  
**Steps:**
1. Tap **`IconButton(Icons.mic_none)`**
2. Mic icon toggles to `Icons.mic` (active state, accent color)
3. Voice waveform or recording indicator appears
4. Tap again → returns to text input mode

**Expected:** Toggle works; icon state reflects mode  
**Sub-widgets exercised:** `IconButton(mic_none / mic)`, voice indicator widget

---

### UC-I5 · Navigate to Profile via app bar icon
**Precondition:** Chat screen visible  
**Steps:**
1. Tap **`IconButton(Icons.account_circle_outlined)`** in app bar
2. `ProfileNavSheet` slides up (modal bottom sheet)
3. Sheet contains navigation options: "Profile", "Settings", "Journal"

**Expected:** Sheet opens; navigation options present  
**Sub-widgets exercised:** `IconButton(account_circle_outlined)`, `ProfileNavSheet`

---

### UC-I6 · Offline banner
**Precondition:** Device offline (`ConnectivityResult.none`)  
**Steps:**
1. Offline banner slides in at top of chat (amber `#C8923D` background)
2. Observe `Icons.wifi_off` icon and `Text("You're offline — Alex can't respond right now")`
3. Observe **`TextButton("Retry")`** at right of banner
4. Tap **`TextButton("Retry")`** → connectivity check fires
5. When back online → banner slides out (300ms fade)

**Expected:** Banner appears offline; retry button fires check; banner dismisses on reconnect  
**Sub-widgets exercised:** Offline `Container` banner, `Icons.wifi_off`, `TextButton(Retry)`

---

### UC-I7 · Crisis intervention sheet from chat
**Precondition:** Alex detects medium/high risk in message  
**Steps:**
1. **`CrisisInterventionSheet`** slides up (isDismissible: false, enableDrag: false)
2. Observe drag-handle `Container`
3. Observe **`_CrisisIconBubble`** (64×64, cupped-hands icon)
4. Observe headline `Text` ("You don't have to face this alone")
5. Observe **`ElevatedButton("Call 988")`** (primary, full-width) → `launchUrl(tel:988)`
6. Observe **`ElevatedButton("Text HOME to 741741")`** → `launchUrl(sms:741741)`
7. Observe **`TextButton("Keep chatting with Alex")`** → `CrisisSheetChoice.keepChatting`
8. Observe **`TextButton("I'm venting, not in crisis")`** → `CrisisSheetChoice.ventingOptOut`

**Expected:** Sheet non-dismissible; all 4 choices tappable; 988/741741 launch URLs  
**Sub-widgets exercised:** `CrisisInterventionSheet`, `_CrisisIconBubble`, 2× `ElevatedButton`, 2× `TextButton`

---

### UC-I8 · Acute crisis takeover (high risk)
**Precondition:** Risk = `RiskLevel.crisis`  
**Steps:**
1. **`AcuteCrisisTakeover`** renders full-screen (replaces chat view)
2. Observe large **`_CrisisIconBubble`** centered
3. Observe **`ElevatedButton("Call 988 now")`** (coral/accent, full-width, large)
4. Observe **`ElevatedButton("Text HOME to 741741")`**
5. Observe small **`TextButton("I'm safe — go back")`** at bottom
6. Tap **`TextButton("I'm safe — go back")`** → pops takeover; `CrisisFollowUpCard` queued for next dashboard load

**Expected:** Full-screen takeover; 988 prominent; safe-exit returns to chat  
**Sub-widgets exercised:** `AcuteCrisisTakeover`, `_CrisisIconBubble`, 2× `ElevatedButton`, `TextButton(I'm safe)`

---

## Screen 4 — MoodTrackerScreen + MoodEntry sheet

### UC-M1 · Mood tab render — no mood logged today
**Precondition:** Mood tab selected; no mood logged today  
**Steps:**
1. **`MoodTrackerScreen`** renders with "How are you right now?" `Text` header
2. Observe **`MoodTriggerCard`** — primary CTA card ("Check in")
3. Observe **`ClinicalCheckInCard`** — secondary card ("PHQ-9 / GAD-7 reflection")
4. Observe **`WeeklyReviewRow`** — row with `MoodShapeChart` stub and "Weekly review" `Text`
5. Tap **`MoodTriggerCard`** → mood bottom sheet opens

**Expected:** All cards render; trigger card opens sheet  
**Sub-widgets exercised:** `MoodTriggerCard`, `ClinicalCheckInCard`, `WeeklyReviewRow`, `MoodShapeChart` (stub)

---

### UC-M2 · Mood entry bottom sheet — select and save
**Precondition:** Mood sheet open (from UC-M1)  
**Steps:**
1. Sheet renders with 5 emoji mood buttons in a row
2. Observe each mood option with emoji + label:
   - 😊 **"Great"** (GQColors.moodGreat `#9CC487`)
   - 🙂 **"Good"** (GQColors.moodGood `#FFB59B`)
   - 😐 **"Okay"** (GQColors.moodOkay `#C9B7F0`)
   - 😔 **"Meh"** (GQColors.ink3)
   - 😰 **"Rough"** (GQColors.accentSoft)
3. Tap **"Great"** → emoji button highlights (scaled + colored border)
4. Observe **`TextField`** ("Add a note… (optional)") below mood row
5. Tap **`TextField`** → type "Feeling good after a walk"
6. Observe **`ElevatedButton("Save check-in")`** (primary, full-width)
7. Tap **`ElevatedButton("Save check-in")`** → sheet dismisses; mood written via `MoodProvider`

**Expected:** Selection highlights; note saves; sheet dismisses; provider updated  
**Sub-widgets exercised:** 5× mood `ElevatedButton` (emoji + label), `TextField(note)`, `ElevatedButton(Save check-in)`

---

### UC-M3 · Low-mood post-submit reflection sheet
**Precondition:** Saved mood = "Rough" or "Meh"  
**Steps:**
1. After save, `MoodReflectionSheet` slides up automatically
2. Observe empathetic copy `Text` (P1 — warmth)
3. Observe **`_FaceOption`** row: 😔 "Heavy" / 😐 "Flat" / 🙂 "Hanging in" / 🌱 "Turning around"
4. Tap any **`_FaceOption`** → face highlights
5. Observe **`TextButton("Skip for now")`** — exits without selecting
6. Observe **`ElevatedButton("Talk to Alex about it")`** → navigates to chat with pre-seeded context
7. Tap **`TextButton("Skip for now")`** → sheet closes

**Expected:** Reflection sheet appears for low mood only; all 4 faces tappable  
**Sub-widgets exercised:** Reflection copy `Text`, `_FaceOption` ×4, `TextButton(Skip)`, `ElevatedButton(Talk to Alex)`

---

### UC-M4 · Clinical check-in card tap
**Precondition:** Mood tab  
**Steps:**
1. Tap **`ClinicalCheckInCard`**
2. `ClinicalAssessmentScreen` pushes onto nav stack

**Expected:** Navigation fires; assessment entry screen loads  
**Sub-widgets exercised:** `ClinicalCheckInCard`, `Navigator.push`

---

### UC-M5 · Weekly review row tap
**Precondition:** Mood tab; week data available  
**Steps:**
1. Observe **`WeeklyReviewRow`** — contains `MoodShapeChart` (mini) + "Weekly review" label + `Icons.chevron_right`
2. Tap row → `WeeklyReviewScreen` pushes

**Expected:** Navigation fires; weekly review screen loads  
**Sub-widgets exercised:** `WeeklyReviewRow`, `MoodShapeChart` (mini), `Icons.chevron_right`

---

## Screen 5 — WellnessDashboardScreen (Dashboard tab)

### UC-D1 · Not-logged state render
**Precondition:** `DashboardState.notLogged`; no mood logged today  
**Steps:**
1. Dashboard renders with "Good morning, [name]" greeting `Text`
2. Hero zone shows **"How are you today?"** check-in `Card` (primary CTA, full-width)
3. Observe **`_RingPainter`** progress ring (CustomPaint, 46px radius, 4px stroke) — 0% or last-week progress
4. Observe quest cards row via **`QuestCardWidget`** ×N (from `QuestProvider`)
5. Observe **`RecommendationCardWidget`** — suggestion from Alex
6. Observe `AssessmentSplash` if PHQ-9 due
7. Observe **`AppBottomNav`** at bottom (if `showBottomNav = true`)
8. Tap check-in `Card` → `MoodTrackerScreen` pushes

**Expected:** All sections render; check-in card navigates to mood screen  
**Sub-widgets exercised:** Greeting `Text`, check-in `Card`, `_RingPainter`, `QuestCardWidget` ×N, `RecommendationCardWidget`, `AppBottomNav`

---

### UC-D2 · Feeling-great state
**Precondition:** `DashboardState.feelingGreat`; high mood logged  
**Steps:**
1. Hero zone changes to "You're doing great today 🌟" copy
2. **Confetti** (`ConfettiController`) fires briefly (celebration microinteraction)
3. Progress ring animates to current value (`kRingDuration` 520ms, `kRingCurve` easeOutCubic)
4. Ripple animation fires (`kRippleDuration` 380ms, `kRippleEndRadius` 84px, `kRippleCurve` easeOutCubic)

**Expected:** Confetti fires; ring animates; copy variant correct  
**Sub-widgets exercised:** `ConfettiWidget`, `_RingPainter`, ripple `Container`

---

### UC-D3 · Long-absence state (highest priority)
**Precondition:** `DashboardState.longAbsence`; >7 days no login  
**Steps:**
1. Hero zone shows absence-acknowledgment copy ("We noticed you've been away — welcome back")
2. No confetti; gentle gradient background
3. Check-in CTA prominent

**Expected:** Absence copy renders; check-in still present  
**Sub-widgets exercised:** Absence `Text`, check-in `Card`

---

### UC-D4 · Weekend state
**Precondition:** `DashboardState.weekend`; Saturday or Sunday  
**Steps:**
1. Hero copy shifts to weekend tone ("Hope you're resting today")
2. Quest cards still present but "rest is progress" framing

**Expected:** Weekend copy variant renders  
**Sub-widgets exercised:** Weekend `Text` hero

---

### UC-D5 · Crisis follow-up card (post-flag)
**Precondition:** `CrisisFollowUpCard` queued (≤24h after crisis flag)  
**Steps:**
1. **`CrisisFollowUpCard`** renders at top of dashboard (above check-in card)
2. Observe gentle copy ("Checking in — how are you feeling since we last spoke?")
3. Observe **`ElevatedButton("I'm okay now")`** → dismisses card; clears flag
4. Observe **`ElevatedButton("I still need support")`** → opens `CrisisInterventionSheet`

**Expected:** Card persists ≤24h; both buttons functional  
**Sub-widgets exercised:** `CrisisFollowUpCard`, 2× `ElevatedButton`

---

## Screen 6 — QuestScreen

### UC-Q1 · Quest list view render
**Precondition:** Quest tab selected; `_QuestView.list`  
**Steps:**
1. **`_QuestListView`** renders with quest cards
2. Observe **`_ProgressRing`** (custom `_RingPainter` arc, week completion %)
3. Each **`QuestCardWidget`**:
   - Icon in circular container (10% black opacity bg)
   - Title `Text` (18px bold) + description `Text` (14px grey)
   - **`LinearProgressIndicator`** (8px height, 4px border-radius) if in-progress
   - Progress label `Text` ("{n}% complete") if in-progress
4. Observe "3 Good Things" quest card always first

**Expected:** All quest cards render with correct progress state  
**Sub-widgets exercised:** `_QuestListView`, `_ProgressRing`, `_RingPainter`, `QuestCardWidget` ×N, `LinearProgressIndicator`

---

### UC-Q2 · Quest card tap → preview
**Precondition:** Quest list visible  
**Steps:**
1. Tap any **`QuestCardWidget`**
2. **`_QuestPreviewView`** slides in (or `QuestPreviewScreen` pushes)
3. Preview shows: quest icon, title, full description, duration `Text`, difficulty `Text`
4. Observe **`ElevatedButton(key: ValueKey('quest_start_button'))`**:
   - Label = **"Start"** if `progress == 0`
   - Label = **"Continue"** if `progress > 0`
5. Button color = quest's theme color (blue / green / orange)
6. Tap **`ElevatedButton("Start")`** → quest begins; view transitions to `_QuestInProgressView`

**Expected:** Preview renders correctly; Start/Continue label correct; quest launches  
**Sub-widgets exercised:** `_QuestPreviewView`, `ElevatedButton(ValueKey quest_start_button)`

---

### UC-Q3 · Quest in-progress view
**Precondition:** Quest started; `_QuestView.inProgress`  
**Steps:**
1. **`_QuestInProgressView`** renders with active quest fields
2. "3 Good Things" quest: 3× `TextField` (one per gratitude item)
3. **`_PrimaryButton("Complete today")`** at bottom
4. Tap **`_PrimaryButton("Complete today")`** → completion animation; XP chip flies to progress ring; quest marked done for today

**Expected:** In-progress fields visible; completion fires; XP microinteraction plays  
**Sub-widgets exercised:** `_QuestInProgressView`, `TextField` ×N (quest-specific), `_PrimaryButton(Complete today)`, XP `AnimatedWidget`

---

## Screen 7 — ProfileScreen

### UC-P1 · About You section
**Precondition:** ProfileScreen open (via profile avatar or Settings →)  
**Steps:**
1. **`AboutYouCard`** renders with "ABOUT YOU" section header `Text`
2. **`TextField(nickname)`** — editable; hint "What should Alex call you?"
3. Pronoun row: 6× **`_GQToggle`**-styled pronoun chips — "she/her", "he/him", "they/them", "ze/zir", "xe/xem", "any/all"
4. Tap any pronoun chip → chip highlights (primary border + fill); others deselect
5. Avatar row: 6× **`AvatarDot`** — gradient circles (6 different gradient pairs from `GQColors`)
6. Tap any **`AvatarDot`** → dot highlights (scale 1.15, white border ring)
7. Edits auto-save via debounced `SharedPreferences` write

**Expected:** Nickname editable; pronoun selection exclusive; avatar selection visual  
**Sub-widgets exercised:** `AboutYouCard`, `TextField(nickname)`, `_GQToggle` ×6, `AvatarDot` ×6

---

### UC-P2 · Voice / Tone section
**Precondition:** ProfileScreen open  
**Steps:**
1. **`VoiceCard`** renders with "HOW ALEX TALKS TO YOU" section header
2. Three tone buttons (each a `GestureDetector` + `Container`):
   - 🌿 **"Warm"** — gentle, nurturing
   - ⚡ **"Direct"** — clear, no fluff
   - ✨ **"Playful"** — light, fun
3. Tap any tone button → button gets primary border + background; others clear
4. **`_GQToggle`** labeled "Voice notes" — tap → toggles on/off; writes to prefs
5. Active tone saved via `SharedPreferences`

**Expected:** Tone selection exclusive; voice toggle fires; prefs written  
**Sub-widgets exercised:** `VoiceCard`, 3× tone `GestureDetector` + `Container`, `_GQToggle(voice notes)`

---

### UC-P3 · Safety Plan — empty state → build
**Precondition:** `SafetyPlanState.empty`; no plan saved  
**Steps:**
1. **`SafetyPlanCard`** renders with "SAFETY PLAN" header
2. Observe **`_SafetyPill`** count badge (shows "0 / 3 steps")
3. **`_IconCircleButton("Build my safety plan")`** — primary CTA
4. **`TextButton("Maybe later")`** — secondary; calls `Navigator.of(context).maybePop()`
5. Tap **`_IconCircleButton("Build my safety plan")`** → `SafetyPlanBuilderStep` opens (step 1 of 3)
6. **Step 1 — Warning signs:**
   - `Text("What are your warning signs?")` header
   - `TextField` (multiline, hint "Racing thoughts, isolation…")
   - **`StepDots`** — 3 dots, dot 1 active (primary), dots 2-3 grey
   - **`ElevatedButton("Save & continue")`** → advances to step 2; calls `widget.onClose ?? maybePop`
   - **`GestureDetector("Save & exit")`** → closes builder; calls `widget.onClose ?? maybePop`
   - **`GestureDetector("Skip — use 988 only")`** → `Navigator.of(context).maybePop()`
7. **Step 2 — Coping strategies:**
   - `TextField` (multiline, hint "Deep breathing, calling a friend…")
   - **`StepDots`** — dot 2 active
   - Same Save & continue / Save & exit / Skip controls
8. **Step 3 — People to contact:**
   - `TextField` for contact name
   - `TextField` for phone
   - **`StepDots`** — dot 3 active
   - **`ElevatedButton("Finish plan")`** → saves plan; `SafetyPlanState` → `filled`

**Expected:** 3-step builder completes; plan saved; state transitions to filled  
**Sub-widgets exercised:** `SafetyPlanCard`, `_SafetyPill`, `_IconCircleButton`, `TextButton(Maybe later)`, `SafetyPlanBuilderStep` ×3, `StepDots`, `TextField` ×5, `ElevatedButton(Save & continue)`, `GestureDetector(Save & exit)`, `GestureDetector(Skip)`

---

### UC-P4 · Safety Plan — filled state → use
**Precondition:** `SafetyPlanState.filled`  
**Steps:**
1. **`SafetyPlanCard`** shows plan summary; **`_SafetyPill`** shows "3 / 3 steps"
2. **`_SafetyButton("Use now")`** — primary, triggers `showCrisisInterventionSheet()`
3. **`_SafetyButton("Edit plan")`** — secondary, opens builder in edit mode
4. Tap **`_SafetyButton("Use now")`** → `CrisisInterventionSheet` opens

**Expected:** Use now opens crisis sheet; Edit plan opens builder  
**Sub-widgets exercised:** `SafetyPlanCard`, `_SafetyPill`, `_SafetyButton(Use now)`, `_SafetyButton(Edit plan)`

---

### UC-P5 · Safety Contacts section
**Precondition:** ProfileScreen open; contacts section visible  
**Steps:**
1. **`SafetyContactsPreview`** renders with up to 3 contact rows via **`_ContactRow`**
2. Each **`_ContactRow`**:
   - **`TextField(name)`** — editable
   - **`TextField(relationship)`** — editable  
   - **`TextField(phone)`** — editable, keyboard type `phone`
   - **`IconButton(Icons.star_border)`** → toggles to `Icons.star` (favorite)
   - **`IconButton(Icons.phone)`** ("Call") → `ScaffoldMessenger.showSnackBar` ("Calling [name]…")
3. **`IconButton(Icons.add)`** at section bottom → adds new contact row
4. **`IconButton(Icons.delete_outline)`** per row → removes row with confirmation

**Expected:** All 3 fields editable; favorite toggle works; call shows snackbar; add/remove rows  
**Sub-widgets exercised:** `SafetyContactsPreview`, `_ContactRow`, 3× `TextField`, `IconButton(star)`, `IconButton(phone)`, `IconButton(add)`, `IconButton(delete)`

---

### UC-P6 · Settings navigation from Profile
**Precondition:** ProfileScreen open; "Settings →" link visible  
**Steps:**
1. Observe **`GestureDetector`** with `Text("Settings →")` at bottom of profile sheet
2. Tap → `Navigator.push(MaterialPageRoute(builder: (_) => const SettingsScreen()))`
3. `SettingsScreen` renders on top of stack

**Expected:** Settings pushes; back arrow returns to profile  
**Sub-widgets exercised:** `GestureDetector(Settings →)`, `SettingsScreen`

---

## Screen 8 — SettingsScreen

### UC-S1 · Default view — all sections render
**Precondition:** SettingsScreen open (view state A)  
**Steps:**
1. **`_SettingsCard`** — "YOUR DATA" section:
   - **`_SettingsRow("Export my data", Icons.download_outlined)`**
   - **`_SettingsRow("Delete my account", Icons.delete_outline)`** (coral text)
   - **`_SettingsRow("Anonymity mode", Icons.visibility_off_outlined)`** + **`_GQToggle`**
2. **`_SettingsCard`** — "NOTIFICATIONS" section:
   - **`_SettingsRow("Daily check-in reminder", Icons.notifications_outlined)`** + `Icons.chevron_right`
   - **`_SettingsRow("Streak gentle nudge", Icons.local_fire_department_outlined)`** + **`_GQToggle`**
3. Scroll down → **`_SettingsCard`** — "ABOUT" section:
   - **`_SettingsRow("Privacy policy", Icons.policy_outlined)`**
   - **`_SettingsRow("Terms of service", Icons.description_outlined)`**
   - **`_SettingsRow("Crisis resources", Icons.favorite_border)`**
4. Bottom: **`_EraseLocalDataBtn`** — "Erase local data" (destructive, coral, `Icons.warning_amber_outlined`)

**Expected:** All rows present; sections divided by `_SettingsCard` containers  
**Sub-widgets exercised:** 3× `_SettingsCard`, `_SettingsRow` ×8, `_GQToggle` ×2, `_EraseLocalDataBtn`

---

### UC-S2 · Export my data
**Precondition:** SettingsScreen open  
**Steps:**
1. Tap **`_SettingsRow("Export my data")`**
2. `ScaffoldMessenger.showSnackBar` fires: "Export started — you'll receive an email shortly"
3. Snackbar auto-dismisses after 4s

**Expected:** Snackbar fires with correct copy  
**Sub-widgets exercised:** `_SettingsRow(Export)`, `SnackBar`

---

### UC-S3 · Delete account flow
**Precondition:** SettingsScreen open  
**Steps:**
1. Tap **`_SettingsRow("Delete my account")`**
2. Confirmation `ModalBottomSheet` opens (view state C):
   - Coral `Icons.warning_rounded` icon
   - `Text("This can't be undone")` headline
   - `Text` explaining data loss
   - **`TextField`** with hint "Type DELETE to confirm"
   - **`ElevatedButton("Delete my account")`** — disabled until text == "DELETE"
   - **`TextButton("Cancel")`** → pops sheet
3. Type "DELETE" → `ElevatedButton` enables (coral fill)
4. Type anything else → button stays disabled
5. Tap **`TextButton("Cancel")`** → sheet pops

**Expected:** Button gated behind typed confirmation; cancel pops; button enables exactly on "DELETE"  
**Sub-widgets exercised:** `ModalBottomSheet`, `Icons.warning_rounded`, `TextField(confirm)`, `ElevatedButton(Delete)` (state gate), `TextButton(Cancel)`

---

### UC-S4 · Anonymity mode toggle
**Precondition:** SettingsScreen open  
**Steps:**
1. **`_SettingsRow("Anonymity mode")`** has **`_GQToggle`** at right
2. Tap **`_GQToggle`** → toggles on; **`_AnonymityBanner`** slides in below row:
   - `Icons.visibility_off` icon
   - `Text("Your name is hidden from exports and reports")`
3. Tap again → toggles off; banner slides out

**Expected:** Toggle fires; banner appears/hides; pref written  
**Sub-widgets exercised:** `_GQToggle(anonymity)`, `_AnonymityBanner`, `Icons.visibility_off`

---

### UC-S5 · Daily check-in reminder → notification detail
**Precondition:** SettingsScreen open  
**Steps:**
1. Tap **`_SettingsRow("Daily check-in reminder", chevron_right)`**
2. Notification detail screen opens (view state B):
   - "ON DAYS" `Text` label
   - 7× day chips (Mon Tue Wed Thu Fri Sat Sun) — each a `FilterChip` or `GestureDetector`
   - Tap any day chip → toggles on (primary fill) / off (grey)
   - "TIME" `Text` label + time display `Text` (e.g. "8:00 AM")
   - **`TextButton("Change")`** → `showTimePicker()` opens native time picker
   - **`_GQToggle("Enable")`** — master on/off for this notification
   - **`ElevatedButton("Send a test notification")`** (full-width)
3. Tap **`ElevatedButton("Send a test notification")`** → `NotificationService.sendTest()` → snackbar confirms
4. Tap any day chip → toggles
5. Tap **`TextButton("Change")`** → `TimePickerDialog` opens; select time → saves

**Expected:** Day chips toggle; time picker works; test notification fires snackbar  
**Sub-widgets exercised:** Day `FilterChip` ×7, `TextButton(Change)`, `TimePickerDialog`, `_GQToggle(Enable)`, `ElevatedButton(Send a test notification)`, `SnackBar`

---

### UC-S6 · Streak gentle nudge toggle
**Precondition:** SettingsScreen open  
**Steps:**
1. **`_SettingsRow("Streak gentle nudge")`** has **`_GQToggle`** at right
2. Tap **`_GQToggle`** → toggles; pref written
3. No detail screen (toggle-only row)

**Expected:** Toggle fires; pref persists across app restarts  
**Sub-widgets exercised:** `_GQToggle(streak nudge)`

---

### UC-S7 · Privacy policy navigation
**Precondition:** SettingsScreen open; scrolled to ABOUT section  
**Steps:**
1. **`scrollUntilVisible`** finds **`_SettingsRow("Privacy policy")`**
2. Tap → `LegalScreen` pushes (or `launchUrl` for external link)
3. Back arrow returns to Settings

**Expected:** Navigation or URL launch fires  
**Sub-widgets exercised:** `_SettingsRow(Privacy policy)`, `LegalScreen` or `launchUrl`

---

### UC-S8 · Crisis resources from Settings
**Precondition:** SettingsScreen open; scrolled to ABOUT  
**Steps:**
1. Tap **`_SettingsRow("Crisis resources")`**
2. `CrisisInterventionSheet` opens (risk = medium by default)
3. All 4 choice buttons present (same as UC-I7)

**Expected:** Crisis sheet opens from Settings  
**Sub-widgets exercised:** `_SettingsRow(Crisis resources)`, `CrisisInterventionSheet`

---

### UC-S9 · Erase local data
**Precondition:** SettingsScreen open; scrolled to bottom  
**Steps:**
1. **`_EraseLocalDataBtn`** renders (coral, `Icons.warning_amber_outlined`, "Erase local data")
2. Tap → `AlertDialog` opens:
   - `Text("Erase all local data?")` title
   - `Text` body explaining what is erased
   - **`TextButton("Cancel")`** → dismisses dialog
   - **`ElevatedButton("Erase", style: coral)`** → clears SharedPreferences + local DB; pops back to Welcome
3. Tap **`TextButton("Cancel")`** → dialog dismisses; no data erased

**Expected:** Confirmation dialog guards erase; cancel is safe; erase clears data  
**Sub-widgets exercised:** `_EraseLocalDataBtn`, `AlertDialog`, `TextButton(Cancel)`, `ElevatedButton(Erase)`

---

## Screen 9 — ClinicalAssessmentScreen

### UC-CA1 · Entry screen
**Precondition:** Navigated from mood check-in card or UC-M4  
**Steps:**
1. Entry screen renders two assessment cards:
   - **`AssessmentEntryCard("PHQ-9")`** — "Depression reflection", 9 questions
   - **`AssessmentEntryCard("GAD-7")`** — "Anxiety reflection", 7 questions
2. Each card shows: scale name `Text`, item count `Text`, `Icons.psychology_outlined`, "Why we ask" expandable `ExpansionTile`
3. Expand **`ExpansionTile`** → rationale `Text` reveals (animated expand)
4. Tap **`AssessmentEntryCard("PHQ-9")`** → `AssessmentScale.phq9` flow begins

**Expected:** Both cards render; expansion works; PHQ-9 tapped launches flow  
**Sub-widgets exercised:** `AssessmentEntryCard` ×2, `ExpansionTile` ×2, `Icons.psychology_outlined`

---

### UC-CA2 · PHQ-9 question flow — full pass
**Precondition:** PHQ-9 selected; `_AssessmentFlowScreen` open  
**Steps:**
1. **Q1 renders:** `Text("Little interest or pleasure in doing things?")`
2. 4× **`_LikertPill`** in a row:
   - **"Not at all"** (score 0)
   - **"Several days"** (score 1)
   - **"More than half the days"** (score 2)
   - **"Nearly every day"** (score 3)
3. Tap **`_LikertPill("Several days")`** → pill fills primary; **`ElevatedButton("Next")`** enables
4. Tap **`ElevatedButton("Next")`** → Q2 loads (same structure)
5. Tap **`TextButton("Back")`** → Q1 returns; prior answer preserved
6. Repeat for Q3–Q8
7. **Q9 — "Thoughts of self-harm":** select **`_LikertPill("Nearly every day")`** (score 3)
8. **`_Q9CrisisBridgeSheet`** appears automatically (`_BridgeCardStyle.highAlert`):
   - `Icons.favorite` icon (coral)
   - Compassionate `Text` header
   - **`ElevatedButton("Call 988")`** → `launchUrl(tel:988)`
   - **`ElevatedButton("Text HOME to 741741")`** → `launchUrl(sms:741741)`
   - **`TextButton("I'm safe, continue assessment")`** → bridge dismisses; Q9 answer kept
9. Tap **`TextButton("I'm safe, continue assessment")`** → bridge closes; Q9 done
10. **`ElevatedButton("Next")`** on Q9 → result screen loads

**Expected:** Q-by-Q flow; back preserves answers; Q9 bridge fires for score 3; bridge dismissible  
**Sub-widgets exercised:** `_AssessmentFlowScreen`, `Text(question)` ×9, `_LikertSelector`, `_LikertPill` ×4, `ElevatedButton(Next)`, `TextButton(Back)`, `_Q9CrisisBridgeSheet`, `ElevatedButton(Call 988)`, `ElevatedButton(Text 741741)`, `TextButton(I'm safe)`

---

### UC-CA3 · Save & exit mid-assessment
**Precondition:** Mid-assessment (any question)  
**Steps:**
1. **`TextButton("Save & exit")`** visible at top-right of every question screen
2. Tap → assessment state persists (partial answers saved); `Navigator.of(context).pop()` fires
3. Re-entering from UC-M4 resumes at saved question

**Expected:** Partial save works; navigation pops; resume on re-entry  
**Sub-widgets exercised:** `TextButton(Save & exit)`

---

### UC-CA4 · Result reveal screen
**Precondition:** All 9 PHQ-9 questions answered  
**Steps:**
1. **`_ResultRevealScreen`** loads with animated reveal (300ms fade)
2. Observe **`_SeverityBandViz`** — gradient bar showing score position (0–27 range)
3. Score `Text` + severity label `Text` (Minimal / Mild / Moderate / Moderately severe / Severe)
4. 4× **`ResultActionCard`**:
   - **"Talk it through with Alex"** (`Icons.chat_bubble_outline`) → navigates to chat
   - **"Try a 1-min breathing exercise"** (`Icons.air`) → `Navigator.pushNamed('/interactive-chat')`
   - **"Crisis resources"** (`Icons.favorite_border`) → `CrisisInterventionSheet`
   - **"Save this result for therapist"** (`Icons.share_outlined`) → `ScaffoldMessenger.showSnackBar`
5. **`_GQToggle("2-week reminder")`** — schedules follow-up notification when toggled on
6. Tap each action card → correct action fires

**Expected:** All 4 action cards fire; severity band renders; toggle schedules notification  
**Sub-widgets exercised:** `_ResultRevealScreen`, `_SeverityBandViz`, score `Text`, severity `Text`, `ResultActionCard` ×4, `_GQToggle(2-week reminder)`

---

## Screen 10 — WeeklyReviewScreen

### UC-WR1 · Heavy week render
**Precondition:** `WeekState.heavy`; `WeeklyReviewData.stubHeavy()`  
**Steps:**
1. Sky background `Container` color = `#2D3561` (heavy/night tone)
2. **`MoodShapeChart`** renders:
   - 7× **`_BarSlot`** — one per day (Mon–Sun)
   - Each `_BarSlot`: animated bar height = `0.2 + moodIdx * 0.2` of `maxH` (60px max)
   - Missing days: dashed `Container` (`CustomPaint` dashes, 2px wide, 4px spacing)
   - Day label `Text` below each bar (Mon, Tue…)
3. "This was a heavy week" heading `Text`
4. Sub-copy `Text` (empathetic, P1)
5. **`NextWeekPromptCard`** below chart — "What would help next week?"
6. Observe 4× **`_FaceOption`**: 😔 / 😐 / 🙂 / 🌱 row
7. **`ElevatedButton("Just rest")`** → `Navigator.of(context).pop()`
8. **`GestureDetector`** with `Text("Skip this — I'll figure it out")` → `Navigator.of(context).pop()`

**Expected:** Heavy sky color; dashed slots for missing days; Just rest pops; Skip pops  
**Sub-widgets exercised:** `MoodShapeChart`, `_BarSlot` ×7, `NextWeekPromptCard`, `_FaceOption` ×4, `ElevatedButton(Just rest)`, `GestureDetector(Skip this)`

---

### UC-WR2 · Light week render
**Precondition:** `WeekState.light`; `WeeklyReviewData.stubLight()`  
**Steps:**
1. Sky color = `#87CEEB` (light/day tone)
2. Bars animate taller (higher mood values)
3. **`_CalmCheckInRow`** visible — "You had a calm week" + checkmark icon
4. Same Just rest / Skip controls; **`ElevatedButton("Just rest")`** text variant: "Keep the rhythm →"
5. Optional: **`TextButton("Share with therapist")`** at bottom → `mailto:` launch (deferred/stub)

**Expected:** Light sky; calm row visible; button labels adapt to state  
**Sub-widgets exercised:** `_CalmCheckInRow`, `ElevatedButton(Keep the rhythm)`, `TextButton(Share with therapist)`

---

### UC-WR3 · Full week render
**Precondition:** `WeekState.full`  
**Steps:**
1. All 7 bars present (no dashes)
2. `MoodShapeChart` shows complete week arc
3. Summary stats: "7 / 7 days logged" `Text`

**Expected:** All bars solid; no dashed slots  
**Sub-widgets exercised:** `MoodShapeChart` (full), stats `Text`

---

## Screen 11 — ResourceLibraryScreen

### UC-RL1 · Initial render — "All" filter active
**Precondition:** Resource library opened  
**Steps:**
1. **`_LibraryNavBar`** at top with 6× filter chips:
   - **"All"** (active, primary fill)
   - **"Breathing"**
   - **"Grounding"**
   - **"Body"**
   - **"Quick wins"**
   - **"Sleep"**
2. **`_FeaturedExerciseCard`** below nav:
   - "TRY THIS WHEN YOU'RE HEAVY" label `Text`
   - Featured exercise title + description
   - **`ElevatedButton("Start")`** → opens exercise
3. **`_ExerciseGrid`** — 2-column grid of **`_ExerciseGridItem`** cards:
   - Each item: icon `Container`, title `Text`, duration `Text`, `Icons.bookmark_border` favorites
   - `SizedBox(height: 12)` spacer (not `Spacer()`)

**Expected:** All filter chips, featured card, and grid render without overflow  
**Sub-widgets exercised:** `_LibraryNavBar`, 6× filter `FilterChip`, `_FeaturedExerciseCard`, `ElevatedButton(Start)`, `_ExerciseGrid`, `_ExerciseGridItem` ×N, `Icons.bookmark_border`

---

### UC-RL2 · Filter by category
**Precondition:** UC-RL1 complete  
**Steps:**
1. Tap **"Breathing"** chip → grid filters; only breathing items remain; "Breathing" chip fills primary
2. Tap **"Grounding"** chip → grid re-filters; "Grounding" active
3. Tap **"Sleep"** chip → grid re-filters
4. Tap **"All"** → full grid restores

**Expected:** Each filter shows correct subset; active chip highlighted; no layout errors  
**Sub-widgets exercised:** 6× `FilterChip` (each individually)

---

### UC-RL3 · Favorite an exercise
**Precondition:** Grid visible  
**Steps:**
1. Tap **`Icons.bookmark_border`** on any grid item → icon fills to `Icons.bookmark` (primary color)
2. Favorited items sort to top of grid
3. Tap again → unfavorites; item returns to position

**Expected:** Favorite toggle works; sort-to-top fires  
**Sub-widgets exercised:** `IconButton(bookmark_border / bookmark)`, grid re-sort

---

### UC-RL4 · Open an exercise
**Precondition:** Any category active  
**Steps:**
1. Tap any **`_ExerciseGridItem`**
2. `ExerciseCardScaffold` opens (full-screen or inline in chat)
3. Exercise phases render; "Skip phase" button visible per phase
4. "Complete" button on last phase

**Expected:** Exercise opens; phases accessible; complete button present  
**Sub-widgets exercised:** `_ExerciseGridItem`, `ExerciseCardScaffold`

---

## Screen 12 — JournalScreen

### UC-J1 · Empty state render
**Precondition:** No journal entries in memory  
**Steps:**
1. **`_JournalEmptyState`** renders:
   - AppBar: "Journal" `Text` title + **`_NavIconButton(Icons.add)`** (circular, 32×32, white bg)
   - **`_JournalEmptyIllustration`** — `CustomPaint` notebook with `_SpinePainter`, `_LinedPagePainter`, `_NotebookScribble`, `_LeafIcon`, `_LeafPainter`
   - `Text("Your journal lives here")` heading
   - `Text` sub-copy ("A quiet space just for you")
   - **`_StarterChips`** — 3 chips: "Today, what worked was…", "I noticed myself…", "I want to remember…"
   - **`ElevatedButton("Start an entry")`** (GQColors.primary, full-width)
   - Footer: `Icons.lock_outline` + `Text("Stays on your device. Never synced. Never shared.")`

**Expected:** All illustration elements and chips render  
**Sub-widgets exercised:** `_JournalEmptyState`, `_NavIconButton(add)`, `_JournalEmptyIllustration` (5 CustomPainter layers), `_StarterChips` ×3, `ElevatedButton(Start an entry)`, footer `Row`

---

### UC-J2 · Starter chip → editor prefill
**Precondition:** UC-J1 visible  
**Steps:**
1. Tap **`_StarterChip("Today, what worked was…")`** → **`_JournalEditorSheet`** opens with text prefilled in `TextField`
2. Continue typing after prefill
3. Tap **back `IconButton`** → `_save()` fires; entry persisted in memory

**Expected:** Chip prefills editor; save fires on back  
**Sub-widgets exercised:** `_StarterChip`, `_JournalEditorSheet`, `TextField(body)`, `IconButton(back → _save)`

---

### UC-J3 · Start an entry → open editor
**Precondition:** UC-J1  
**Steps:**
1. Tap **`ElevatedButton("Start an entry")`** → **`_JournalEditorSheet`** opens (empty `TextField`)
2. `TextField` hint: "What's on your mind…"
3. Select mood via **`_MoodPill`** row: great / good / okay / meh / rough (each tappable pill)
4. Tap **`_MoodPill("great")`** → mood dot shows `GQColors.moodGreat`; mood halo gradient applies
5. Type entry body
6. Tap **`IconButton(back)`** → `_save()` → entry added to list; `_JournalTimelineView` appears (if first entry)

**Expected:** Editor opens; mood selection applies halo; save adds entry; transitions to timeline  
**Sub-widgets exercised:** `_JournalEditorSheet`, `TextField(hint: "What's on your mind…")`, `_MoodPill` ×5, `IconButton(back)`

---

### UC-J4 · Timeline view — filter and read
**Precondition:** ≥1 entry saved; `_JournalTimelineView` showing  
**Steps:**
1. AppBar: `Text("Journal")` + **`_NavIconButton(Icons.add)`**
2. **`_TimelineStatStrip`** — entry count `Text`, word count `Text`
3. **`_TimelineFilterControl`** with 3 **`_FilterBtn`**: "All", "Week", "Tag"
4. Tap **"Week"** → `_TimelineFilter.thisWeek`; only current-week entries show
5. Tap **"Tag"** → `_TimelineFilter.byTag`; tag picker appears; select a tag → filters
6. **`_WeekHeader`** separates entries by week ("This week", "Last week", "3 weeks ago"…)
7. Each **`_JournalEntryCard`**:
   - Mood dot `Container` (4px, mood color)
   - Time `Text` (relative: "2h ago", "Yesterday")
   - Preview `Text` (first 80 chars of body)
   - Word count `Text`
   - Tag `Text` ×N (prefixed "#")
8. Tap any **`_JournalEntryCard`** → **`_JournalEntryView`** opens

**Expected:** Filter controls work; week grouping correct; entry cards navigate to detail  
**Sub-widgets exercised:** `_TimelineStatStrip`, `_TimelineFilterControl`, `_FilterBtn` ×3, `_WeekHeader`, `_JournalEntryCard` ×N

---

### UC-J5 · Entry view — read and delete
**Precondition:** `_JournalEntryView` open  
**Steps:**
1. AppBar: date `Text` + **`IconButton(Icons.more_horiz)`**
2. Mood halo gradient strip (18% opacity, entry's mood color)
3. **`_MoodPill`** at top ("Mood · Great")
4. Entry body `Text` (full, scrollable)
5. Detected tags with "#" prefix `Text` ×N
6. Tap **`IconButton(Icons.more_horiz)`** → bottom sheet with **`ListTile("Delete entry")`**
7. Tap **`ListTile("Delete entry")`** → `AlertDialog("Delete this entry?")` opens:
   - **`TextButton("Cancel")`** → dismisses
   - **`ElevatedButton("Delete")`** → removes entry; pops to timeline

**Expected:** Full entry readable; delete flow has confirmation  
**Sub-widgets exercised:** `_JournalEntryView`, mood halo `Container`, `_MoodPill`, body `Text`, tag `Text` ×N, `IconButton(more_horiz)`, `ListTile(Delete)`, `AlertDialog`, `TextButton(Cancel)`, `ElevatedButton(Delete)`

---

## Screen 13 — QuestPreviewScreen (standalone)

### UC-QP1 · Quest preview cards render
**Precondition:** Navigated to `QuestPreviewScreen`  
**Steps:**
1. AppBar: "Quest Screen Preview" `Text` + **`AppBackButton`**
2. Three **`_buildQuestCard()`** widgets render:
   - **Daily Check-in** — `Icons.check_circle` (blue), 30% progress, "Continue" button
   - **Meditation Challenge** — `Icons.self_improvement` (green), 70% progress, "Continue" button
   - **Gratitude Journal** — `Icons.book` (orange), 0% progress, "Start" button
3. Each card: icon `Container` (10% black bg) + title `Text` (18px bold) + description `Text` (14px grey)
4. `LinearProgressIndicator` (8px, 4px radius) if progress > 0 + "{n}% complete" `Text`
5. **`ElevatedButton("Start" / "Continue")`** — color = quest theme color
6. Tap button → `Navigator.popUntil('/home')` or `pushNamedAndRemoveUntil`

**Expected:** All 3 cards render; progress bars show; correct button label per state  
**Sub-widgets exercised:** `AppBackButton`, 3× `_buildQuestCard`, `Icons.check_circle/self_improvement/book`, `LinearProgressIndicator` ×2, `ElevatedButton(Start / Continue)` ×3

---

## Cross-Screen Widgets

### UC-X1 · AppBottomNav — tab switching
**Precondition:** HomeShell loaded  
**Steps:**
1. **`AppBottomNav`** visible at bottom with 4 tabs: Talk (`Icons.chat_bubble_outline`), Mood (`Icons.favorite_border`), Quests (`Icons.emoji_events_outlined`), Dashboard (`Icons.grid_view_outlined`)
2. Tap each tab icon → corresponding screen loads; active tab highlights primary color

**Expected:** All 4 tabs switch screens; active state highlights  
**Sub-widgets exercised:** `AppBottomNav`, 4× tab `BottomNavigationBarItem`

---

### UC-X2 · AppBackButton behavior
**Precondition:** Any pushed screen  
**Steps:**
1. **`AppBackButton`** in AppBar — circular white button with `Icons.arrow_back_ios_new`
2. Tap → `Navigator.maybePop()` if stack depth > 1, else no-op
3. In modal context → checks `ModalRoute.of(context)?.isFirst` before popping

**Expected:** Back pops correctly; no crash when at root  
**Sub-widgets exercised:** `AppBackButton`, `Icons.arrow_back_ios_new`

---

### UC-X3 · ProfileNavSheet
**Precondition:** Opened from chat header icon (UC-I5)  
**Steps:**
1. `ModalBottomSheet` with `ProfileNavSheet` content
2. Navigation options render as `ListTile` items: "Profile", "Settings", "Journal"
3. Tap any → correct screen pushes; sheet closes

**Expected:** Sheet opens; 3 nav options present; each navigates correctly  
**Sub-widgets exercised:** `ProfileNavSheet`, `ListTile` ×3

---

### UC-X4 · KeyboardDismissibleScaffold
**Precondition:** Any screen with text input  
**Steps:**
1. Tap into any `TextField` → keyboard opens
2. Tap anywhere outside `TextField` (on scaffold body) → keyboard dismisses
3. Interaction with other widgets works immediately after dismiss

**Expected:** Keyboard dismisses on outside tap; no lingering focus  
**Sub-widgets exercised:** `KeyboardDismissibleScaffold` wrapper

---

_Total use cases: 46 across 13 screens and 4 cross-screen widgets._  
_Every widget, sub-widget, private class, enum variant, and callback covered._
