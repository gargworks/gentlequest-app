# GentleQuest Dogfood Log — 2026-05-09

## Setup

- **Device:** iPhone 16 Pro Simulator, iOS 18.5
- **App version:** 1.2.2 (build 26032321 per pubspec.yaml)
- **Backend:** nucleus.gentlequest.app (production)
- **Build:** `flutter build ios --debug --simulator` (Xcode 16.4, debug profile)
- **Sim location:** 37.7749, -122.4194 (San Francisco, CA — Allowed)
- **Capture date:** 2026-05-09 morning
- **Capture method:** computer-use MCP screenshot + click; `flutter logs` tail to `/tmp/gq_runtime.log`
- **Driver:** Claude Code (Opus 4.7), session "gq"

References:
- Design index: `docs/design/refs/REVIEW.md` (21 designs across R1–R5, 14 cross-design principles)
- Flutter screens audit: `ai_buddy_web/lib/screens/`

## Per-screen entries

### S01 — Welcome ("Meet Alex")
- **Path:** cold launch (post-update-prompt-dismissed; LATER tap dismissed v1.2.4 update prompt)
- **Latency:** ~1s from launch to render (after Update App? prompt dismissed)
- **Copy:**
  - Headline: "Meet Alex"
  - Sub: "Your wellness companion"
  - Row 1: 💬 "Someone to talk to, anytime"
  - Row 2: 🔒 "Your conversations stay private"
  - Row 3: 💜 "No judgment, just support"
  - CTA: "Get Started" (filled dark purple, full-width pill)
- **Visual:** purple heart icon in soft circle (centered, top), 3 left-aligned rows with small icons, very generous whitespace
- **Linked design:** R1D1 `GentleQuest Onboarding.html` Mockup A
- **Delta vs design:** existing uses *value-prop list framing* (chips with icons); design uses *breathing orb + "What's on your mind today?"* warmth zone. Both honor "no clinical sterility" but tone differs — existing is feature-marketing, design is companion-warmth.
- **Principle violations:** none observed; copy matches "no judgment" principle.
- **Friction:** Low. First impression OK. CTA is visually heavy ("Get Started" filled dark purple); R1D1's softer "Continue →" with "Already with us? Sign in" link gives more agency.
- **Screenshot:** ss_2024 (taken at 8:50 AM after sim re-launch)

### S02 — Age gate ("Verify Your Age")
- **Path:** Welcome → Get Started
- **Latency:** ~immediate (Flutter route push)
- **Copy:**
  - Headline: "Verify Your Age"
  - Body: "GentleQuest uses advanced AI. To comply with safety regulations, you must be 18 years or older to use this application."
  - Primary CTA: "I am 18 or older" (filled purple)
  - Secondary: "I am under 18" (text link, subtle)
- **Visual:** purple checkmark shield icon centered, large headline, body text 3-line block
- **Linked design:** R1D1 `GentleQuest Onboarding.html` Mockup B (Age modal)
- **Delta vs design:** existing wording is **clinical/legal** ("comply with safety regulations") vs design's **warm/conversational** ("Quick check before we begin / Are you 18 or older?"). Existing also doesn't tease the under-18 path with a link to teen resources — it's a binary choice with the under-18 branch being a likely dead-end.
- **Principle violations:** Soft violation of principle #3 ("Every blocked / restricted state offers a path forward"). Under-18 link is just a destination, not a doorway with resources. Need to walk that path to confirm.
- **Friction:** Medium. Cold/rule-y wording could shed already-anxious users. R1D1's microcopy "We're built for adults" + teen-path link with Crisis Text Line is materially warmer.
- **Screenshot:** ss_8052 (taken at 8:52 AM)

### S03 — Regional Verification (the GPS friction)
- **Path:** Age gate → "I am 18 or older"
- **Latency:** ~immediate
- **Copy:**
  - Headline: "Regional Verification"
  - Body: "Certain jurisdictions (e.g., IL, UT, WA) have restricted AI for mental health. We need to verify you are not physically located in a 'Red Zone'."
  - Sub: "We perform a one-time check. We do not track you."
  - CTA: "Verify Location" (filled coral/red)
- **Visual:** coral/red pin icon centered (literally a Map pin in **red**), large headline, multi-paragraph body
- **Linked design:** R1D2 + R2D2 (GentleQuest Compliance Block + Compliance Extensions) — both designs assume the BLOCKED state, NOT the pre-block "asking for GPS" state. **No design exists for this asking screen** because Phase 1+2 (which I drafted, was reverted) removed it entirely in favor of server-side IP check.
- **Delta vs design:** This screen wouldn't exist in the post-fix world. The compliance-block screen design (R1D2) is for users who actually fail the check; this screen is everyone-first-time friction.
- **Principle violations (HIGH):**
  - **#1 (coral, never red)** — pin icon and CTA fill use red/alarm tones. Design system uses #FF6B6B coral specifically to avoid alarm.
  - **#3 (every blocked state offers a path forward)** — pre-block, this screen offers no alternative; it gates 100% of users on GPS to filter the ~1% in IL/UT/WA.
  - The phrase **"Red Zone"** is the most alarming language anywhere in the funnel. Per design principle, we don't use threat language.
- **Friction:** **HIGH.** This is the 17.3% bounce-rate culprit per existing analytics. A user who arrived via a vulnerable moment ("I need to talk to someone") is being asked to:
  1. Approve location
  2. Tolerate latency of GPS lock
  3. Trust language about "Red Zones" before they've gotten any value
- **Screenshot:** ss_8054
- **TRIANGULATED with analytics:** matches `compliance_blocked` event spike + the `_reVerificationHours = 24` policy in `compliance_service.dart:88` that re-fires this on every >24h cold start.

### S04 — iOS native location permission dialog
- **Path:** Regional Verification → Verify Location
- **Copy:**
  - Title: "Allow 'GentleQuest' to use your location?"
  - Body: "GentleQuest uses your location to verify compliance with local AI mental health regulations."
  - 3 options: Allow Once / Allow While Using App / Don't Allow
- **Friction:** Medium. Second compliance-language hit in <30s. Native iOS modal so look-and-feel is fine.
- **Note:** Copy comes from `Info.plist` `NSLocationWhenInUseUsageDescription` — fixable by editing plist key.

### S05 — Verification Failed (GPS error loop)
- **Path:** Allow Once → GPS check fails → this state
- **Copy:**
  - Headline: "Verification Failed"
  - Body: "We couldn't verify your location. This usually resolves on a second try."
  - Primary CTA: "Try Again" (filled purple)
  - Secondary link: "Having trouble? We can verify your region another way"
  - Sub: "Alternative verification uses your internet connection instead of GPS."
- **Visual:** Orange warning circle with `!` (warmer than red but still alarming)
- **Linked design:** No design exists for this state — Phase 1+2 (drafted, reverted) eliminates this entirely via server-IP-first approach.
- **Principle violations (HIGH):**
  - "Verification Failed" framing is failure-language — design principles favor non-blame framing.
  - The IP-fallback link is **secondary**, half-hidden as a link. Should be peer-CTA or primary in the post-1st-failure state.
- **Friction:** **EXTREME on iOS Simulator.** GPS path returns `isMocked = true` → app rejects with `compliance_service.dart:242` (`Mock location detected and rejected`). Same loop happens on real device for users who:
  - Have location services denied
  - Are indoors with poor GPS
  - Hit 30s GPS timeout
- **TestFlight on real device works** because real GPS isn't mocked. But the analytic 17.3% bounce includes users who hit this loop in prod.
- **CRITICAL FINDING:** Even the IP fallback link tap (Lokesh tested 50+ times) doesn't recover. The IP fallback path in `compliance_service.dart:289-309` only fires after `_gpsAttempts >= 2`, AND the call may hang on cold network. End user is stuck.
- **Screenshot:** ss_8054 + ss_9244 (multiple captures of same state)
- **TRIANGULATED with analytics:** Direct match to `compliance_blocked` event spike + 17.3% bounce.

### S05a — iOS Simulator-specific block
- iOS Sim's CoreLocation always reports `isMocked=true`, so geolocator plugin always rejects. NOT a prod bug — SIM ONLY blocker.
- **Resolution for dogfood:** added `--dart-define=DEV_BYPASS_COMPLIANCE=true` flag to `compliance_service.dart` `checkCompliance()`. kDebugMode-gated; cannot ship to prod.

### S06 — App Update prompt (in-app version check)
- **Path:** First launch of fresh build (every cold start while v1.2.4 detected)
- **Copy:**
  - Title: "Update App?"
  - Body: "A new version of GentleQuest is available! Version 1.2.4 is now available - you have 1.2.2"
  - Sub: "Would you like to update it now?"
  - Section: "Release Notes / ## What's New / - AI-powered mental wellness companion / - Mood tracking with insights / - Crisis resources for 11+ countries / - Evidence-based wellness exercises / - Complete privacy with encryption / - Fix: Resolved iOS provisioning profile and Info.plist usage description issues. / - Fix: Resolved startup crash due to missing Firebase configuration."
  - 3 buttons (right-aligned): IGNORE / LATER / UPDATE NOW
- **Linked design:** No corresponding design in 21-set. **Could iterate as a R6 design.**
- **Principle violations:**
  - Modal blocks first-app-impression on every cold start until dismissed.
  - Release notes are dev-flavored (mention "iOS provisioning profile" + "Firebase configuration") — user-facing copy should be feature/benefit framed only.
  - 3 dismissal verbs (IGNORE / LATER / UPDATE NOW) is one too many; LATER and IGNORE are confusing in this context.
- **Friction:** Medium. Eats first 5s of every cold start. For onboarding users, this lands BEFORE Welcome on subsequent launches.

### S07 — Safety & Legal first-launch disclaimer sheet
- **Path:** Past compliance gate, on first chat impression
- **Copy:**
  - Title: "Safety & Legal" + close X
  - Body: "This app offers AI-based wellness support. It does not provide medical advice, diagnosis, or treatment."
  - 3 bullets:
    1. "If you may harm yourself or others, contact local emergency services. Crisis resources are shown contextually."
    2. "Your messages may be stored for a limited period to operate the service. You can request deletion."
    3. "By continuing, you agree to the Terms of Service and Privacy Policy when presented."
  - 2 link rows: "View Terms of Service" / "View Privacy Policy"
  - CTA: "I understand" (filled, full-width)
- **Linked design:** No corresponding design. **R3D3 Settings.html has Privacy controls but not this first-launch dialog.**
- **Principle violations:**
  - Sub-design quality vs the 21-design system (no warm illustration, dense bullet list, generic system-font feel)
  - Sits IN FRONT OF chat that's already loaded behind it, which is dissonant.
- **Friction:** Medium. The sheet is actually clean and informative, but the sequencing (already see chat behind, then forced sheet) breaks the warm-doorway principle.
- **Recommendation:** Either move to onboarding (right after Welcome, before the chat loads) OR fold the disclaimer into the Welcome screen's value-prop chips.

### S08 — Chat first-turn (the core surface) ⭐
- **Path:** "I understand" → chat home (Talk tab)
- **Copy:**
  - Header: "Alex" (centered, plain text)
  - Crisis banner (top): "ⓘ Not medical care. For crisis, call local emergency." (amber-tinted, dismissible X)
  - AI bubble (with avatar): "Good morning! 🌅 How are you feeling today?"
  - 2 chips visible: "Quick check-in" (filled coral/orange) + "I'm feeling anxious" (outline, soft)
  - Input placeholder: "Type your message..."
  - Send button: filled purple circle with arrow
  - Bottom nav: 4 tabs — Talk (selected, purple) / Mood / Quest / Community
- **Linked design:** R1D3 `GentleQuest Chat First Turn.html`
- **Delta vs design (significant):**
  | Element | R1D3 Design | Existing |
  |---|---|---|
  | Header | "You're with / Hi, Alex's here for you" + avatar + streak pill | "Alex" centered, no character |
  | Empty warmth zone | BreathingOrb + "What's on your mind today?" + "Whatever you say stays between us." | Empty space, ~50% viewport white |
  | Chips | "Quick check-in" + "Log my mood" + 4 starters ("Today's been heavy", "I want to vent…", "Just need someone to listen", "Quick win, please") | "Quick check-in" + "I'm feeling anxious" (clinical phrasing, only 2) |
  | Input | "Type, or pick a starter above…" | "Type your message..." (generic) |
  | Trust line | "Your chat history stays on your phone. We don't sell, train, or share." | NONE |
- **Principle violations:**
  - **#3 (every blocked state offers a path forward):** N/A here.
  - **#1 (coral, never red):** Crisis banner uses amber/yellow which is borderline — design system reserves amber for offline only.
  - **Missing trust signal** — designs explicitly add this for stressed users.
- **Friction:** Medium-low for the chat itself, but the **stripped-down feel undermines the warmth advantage** the designs promise. The half-empty white viewport reads as "blank corporate chat" not "calm wellness companion."
- **Bottom nav surprise:** 4 tabs (Talk / Mood / Quest / Community) — NOT 5 as `main_screen.dart` initially suggested. **Assessment is hidden somewhere else** (likely overflow ⋯ menu top-right).
- **Screenshot:** ss_after-I-understand

### S09 — Chat error loop (3 attempts)
- **Path:** S08 chat → multiple chip taps + typed messages
- **Copy:** User msgs sent: "I'm feeling anxious", "ab", "hi", "today has been heavy"; AI returns "Connection error. Request timed out. Please try again." for ALL of them
- **Backend status check:** `/health` returns 200 in 0.5s from Mac. So endpoint is up. Timeout is sim-side network or first-call cold-start related.
- **Principle violations:**
  - **Generic error copy.** Design principle says warm framing — could be "I'm having trouble reaching you right now. Tap send and I'll try again" not "Connection error. Request timed out."
  - **No retry button on the failed bubble** — user has to manually re-type or tap chip again.
  - User bubble color is **mint green** (no design system role). Designs specify primary purple for user bubbles.
- **Friction:** **HIGH** — first-turn user can't get past "hello" without an error.
- **Note:** Park root-cause investigation per Lokesh — TestFlight on real device works fine.

### S10 — Mood Tracker (Mood tab) ⭐
- **Path:** Talk tab → tap Mood in bottom nav
- **Latency:** ~immediate (Flutter route push)
- **Copy:**
  - Title: "Mood Tracker" (centered)
  - Question: "How are you feeling today?"
  - 5 emoji in a row: 😞 / 😕 / 😐 / 🙂 / 😊
  - Card: "Clinical Check-in / PHQ-9 & GAD-7 assessments" with chevron
  - Empty-state hero: "Your feelings matter / Start tracking to discover patterns over time" (small line-chart icon)
  - Bottom nav: Mood selected (purple)
- **Linked design:** R1D4 `GentleQuest Mood Entry.html` (the entry sheet) + R3D1 implicit (Clinical Check-in entry point references R5D1 PHQ-9 design)
- **Delta vs design (significant):**
  | Element | R1D4 Design | Existing |
  |---|---|---|
  | Modal pattern | DraggableScrollableSheet over dashboard | Full screen (no sheet) |
  | Greeting | "How are you, right now?" + "Takes 5 seconds. Skip anything you want." | "How are you feeling today?" (no time-cost language) |
  | Emoji labels | Heavy / Low / Okay / Good / Great below each | NO labels — just emoji |
  | Auto-advance | 800ms after selection | unclear — needs tap test |
  | Context chips ("What shaped this?") | Present (Work / Sleep / People / Body / Money / Other) | NOT visible on this screen |
  | Note field | Collapsible | NOT visible |
  | Streak counter micro | Renders if > 0 | NONE |
  | Confetti pulse | 1s on submit | unknown |
- **Surprise finding:** **Clinical Assessment lives INSIDE Mood tab**, not as a separate tab. The "Clinical Check-in" card is the entry to PHQ-9 / GAD-7. R5D1 design map needs adjustment — `ClinicalAssessmentScreen` is reached from MoodTrackerScreen, not from a dedicated nav tab.
- **Principle violations:**
  - **No emoji labels** removes accessibility (vision-impaired users can't distinguish emoji easily). Design has "Heavy/Low/Okay/Good/Great" labels.
  - "Your feelings matter / Start tracking to discover patterns" is OK copy but not as warm as design system tone.
  - The screen is empty/sparse — feels like a tracker template, not a wellness companion.
- **Friction:** Low (emoji are tappable, single screen). But UX is more "form" than "moment" — the design framing of "this is a 15-second check-in" is missing.
- **Screenshot:** ss_mood_tab

### S11 — Mood entry mini-modal (after tapping emoji)
- **Path:** Mood Tracker → tap leftmost emoji 😞
- **Latency:** ~immediate
- **Copy:**
  - Heading line: "😢 Feeling Very Bad"
  - Field: "Add a note (optional)"
  - Buttons: Cancel / Save (Save filled purple)
- **Linked design:** R1D4 entry sheet (substantially different) + R2D4 post-submit reflection (entirely missing)
- **Delta vs design (significant):**
  - **Existing**: small bottom-card modal — emoji label + note + save. ~1/3 of viewport.
  - **R1D4 design**: full DraggableScrollableSheet — emoji row visible inside the sheet, ContextChipGrid (Work/Sleep/People/Body/Money/Other), NoteToggle (collapsible), AutoAdvanceCountdown 800ms, StreakCounterMicro, SubmitConfettiPulse on submit
  - **R2D4 design** (post-submit reflection): for `.heavy/.low` returns "Logged. Heavy day, hm? / Want to do one tiny thing together?" with options to chat/breathe/close — **completely missing in existing**. User just dismisses to nothing.
- **Principle violations:**
  - **No path forward after a low-mood log** — design principle #3 says every state offers a path forward. Currently the user logs "Feeling Very Bad" and the app does NOTHING — no follow-up, no chat-invite, no breathing exercise offer. Major retention compounding miss.
  - **"Feeling Very Bad"** language is harsh/clinical. Design principle #12 says no diagnosis language. R1D4 uses softer tier labels ("Heavy" / "Low") which are observational not diagnostic.
- **Friction:** Low to log; HIGH for compounding loss — the most vulnerable user state (bad mood) gets the LEAST follow-up. **High-leverage place to ship the post-submit reflection design from R2D4.**
- **Screenshot:** ss_mood_modal

### S12 — Quest tab
- **Path:** Mood → Cancel → tap Quest in bottom nav
- **Latency:** ~immediate
- **Copy:**
  - Title: "My Quest"
  - Segmented control: "Today" (selected) / "Discover"
  - Hero card: "Quick check-in / Takes 2 minutes" + "Start" button (filled purple)
  - Section: "Your Progress" — "🔥 0 days total" + "⭐ Level 1"
  - Section: "Today's Recommendations" — "TASK / Focus reset / Quick breathing + desk tidy" + circular timer icon; "TASK / Study sprint" partial
  - Bottom nav: Quest selected
- **Linked design:** R5D3 `GentleQuest Quests.html`
- **Delta vs design (significant):**
  | Element | R5D3 Design | Existing |
  |---|---|---|
  | Naming | "Quests" plural; "Gentle structure for harder days" subline | "My Quest" singular; no subline |
  | Sections | "Continue what you started" (in-progress) + "Quests for…" (browse with filter chips) | "Your Progress" (level/streak) + "Today's Recommendations" (auto-pushed tasks) |
  | Gamification | NO levels, NO XP, NO leaderboards (principle #14) | **HAS Level 1, days-total — borderline gamification** |
  | Browse | 4 quest cards in 2-col grid by category | List of "Today's Recommendations" — auto-curated, not user-browsed |
  | Difficulty | Star descriptors ("⭐ gentle") | NOT visible |
  | Skip | "Skip today (no judgment)" link | NOT visible at this level |
- **Principle violations (HIGH):**
  - **#14 (gentle structure, not gamification):** "Level 1" badge with star icon = explicit leveling system. Designs explicitly prohibit this for mental wellness — leveling can feel like another performance metric.
  - **#11 (no streak shame):** "0 days total" is currently neutral (zero state) but the streak framing baked in suggests it WILL shame on broken streaks. Need to check break-streak behavior.
- **Friction:** Low to navigate. **Conceptual friction with principles** — this is the most prescriptive surface in the app (auto-recommended tasks, levels, points-y framing).
- **Screenshot:** ss_quest_tab

### S13 — Quest Discover (browse all)
- **Path:** Quest tab → Discover sub-tab
- **Latency:** ~immediate
- **Copy:**
  - Filter chips row: "All ✓" / "Task" / "Tip" + 2 sort/filter icons
  - Visible cards (each with "LIVE BIT" pill, title, description, Start button):
    1. **3-Minute Breathing Exercise** — "Practice box breathing: inhale 4s, hold 4s, exhale 4s, hold 4s. Repeat 5 times." (purple Start)
    2. **Mindful Eating** — "Eat one meal slowly, noticing taste, texture, and smell." (teal Start)
    3. **Explore CBT Basics** — "Learn how thoughts, feelings, and behaviors are connected" (coral Start)
    4. **Energy Level Check** (partial)
- **Linked design:** R5D3 Quests Mockup A (browse) + R3D2 Exercise Cards (overlap with breathing exercise)
- **Delta vs design:**
  - **Mixed Start button colors** (purple / teal / coral) — no consistent design system. Designs use primary purple for all primary CTAs.
  - **"LIVE BIT"** label is ambiguous — unclear what it means. Designs would use "⭐ gentle" / "⭐⭐ moderate" descriptors.
  - Cards mix content types (exercises + education) without typological distinction. Designs separate exercise cards (R3D2) from quest cards (R5D3).
  - No duration shown ("3-Minute Breathing" is in title, others have nothing).
  - No category chips per quest.
- **Principle violations:**
  - **Inconsistent visual language** (Start button colors) — minor but undermines the system's polish.
- **Friction:** Low. Browse is functional, content variety is OK. Polish opportunity is medium-high — could lift Quest tab feel significantly with R5D3 + R3D2 designs applied.
- **Screenshot:** ss_quest_discover

### S14 — Community tab (empty feed)
- **Path:** Quest → Community in bottom nav
- **Latency:** ~immediate
- **Copy:**
  - Title: "Community"
  - Filter chips: "All ✓" / "Anxiety" / "Sleep" / "Mood" / "Group" (last cut off)
  - Empty state: people-cluster icon + "Be the first to share / Your words might help someone else 💜"
  - Bottom-right FAB (purple, +-icon-shape)
  - Bottom nav: Community selected
- **Linked design:** **NO DESIGN EXISTS for Community in the 21-set.** Candidate for R6 design generation.
- **Delta vs design:** N/A — uncovered surface.
- **Principle alignment (positive):**
  - Empty-state copy "Your words might help someone else 💜" is warm and matches design tone
  - Categories (Anxiety / Sleep / Mood / Group) give topical sorting without forcing engagement
  - "Be the first to share" frames creation as gift not obligation
- **Principle violations:**
  - No design contract for moderation, post privacy, or post structure visible from this empty state
  - Floating action button color is solid purple — fine, but the post-composer screen is unknown
- **Friction:** Low for a non-engaged user. Unknown for an engaged user (would need to test post creation).
- **Recommendation:** Add to next design round — community post composer, filled feed, post detail, post moderation/report flow.
- **Screenshot:** ss_community_tab

### S15 — Talk header ⋯ overflow menu ⚠ CRITICAL FINDING
- **Path:** Talk tab → tap ⋯ in top-right corner of header
- **Latency:** ~immediate
- **Copy:** Two-item dropdown:
  1. "Help"
  2. "Safety & Legal"
- **What's MISSING from this menu (vs design 21-set):**
  | Design | Reachable from current UI? |
  |---|---|
  | R3D3 Settings (Privacy, Notifications, Anonymity, Delete Account) | ❌ NO entry point found |
  | R4D2 Profile + Safety Plan | ❌ NO entry point found |
  | R5D2 Journal | ❌ NO entry point found (designs reference dashboard CTA but no dashboard exists) |
  | R4D1 Resources Library | ❌ NO entry point found |
  | R3D4 Weekly Review | ❌ NO entry point found |
  | R3D1 Crisis Intervention | ✓ implicit (auto-fires on risk_level) |
  | R5D1 Clinical Assessment | ✓ via Mood tab → Clinical Check-in card |
  | R3D2 Exercise Cards | ✓ via Quest tab → "3-Minute Breathing" etc. |
- **NAVIGATION GAP — HIGHEST PRIORITY FINDING:**
  - 4-tab bottom nav (Talk / Mood / Quest / Community) doesn't have room for: Settings, Profile, Resources, Journal, Weekly Review.
  - ⋯ overflow only has Help + Safety & Legal — extremely sparse.
  - **5+ designs have NO real entry point in the current app.** Designs without entry points don't ship.
- **Recommended fixes:**
  - **Option A:** 5th tab "More" with overflow that includes Settings, Profile, Resources, Journal (per design Tier 3+ rollout)
  - **Option B:** Hamburger/profile-icon left-of-Alex-header that opens a sheet with all secondary surfaces
  - **Option C:** Extend ⋯ overflow with all secondary items — but ⋯ is hard to find for new users
- **Friction:** N/A directly, but **STRUCTURAL — limits the value the entire 21-design catalog can deliver.** Critical pre-rollout decision.
- **Screenshot:** ss_overflow_menu

### S16 — Help / Crisis Resources sheet
- **Path:** Talk → ⋯ → Help
- **Latency:** ~immediate
- **Copy:**
  - Title: "Need help now?" + close X
  - Section: "⚠ Immediate Help Available"
  - Sub: "If you're in crisis, please reach out. Help is available 24/7."
  - 4 buttons (all in red/coral fill):
    1. 📞 "Call 988"
    2. 💬 "988 Lifeline Chat"
    3. 💬 "Crisis Text Line"
    4. 👤 "Find a Therapist"
  - Footer: "ⓘ Safety & Legal" link
- **Linked design:** Closest is R1D2 Compliance Block (988 + resources for blocked users) and R3D1 Crisis Intervention. Neither is an exact match — this is a NON-intervention, on-demand help surface that's always accessible.
- **Delta vs design:**
  - **Button color appears red/alarm** — design principle #1 says "coral, never red". May be the coral #FF6B6B at full saturation reading as red in small render. Need pixel inspection to verify.
  - Single ⚠ warning glyph at top adds alarm tone — designs use cupped-hands or sunrise icons.
  - "Need help now?" framing is good — direct, not euphemistic.
- **Principle adherence:**
  - **#3 (every blocked state offers a path forward):** ✓ 4 paths (call, chat, text, therapist).
  - **#1 (coral, never red):** **borderline** — depends on actual hex.
- **Friction:** Low for the user case (crisis seeker). 4 distinct paths with phone/web/text variety. Always-1-tap-deep from chat header.
- **Recommendation:** Verify button colors via design tokens; if true coral (#FF6B6B), it's compliant; if true red (#FF0000-ish), needs adjustment.
- **Screenshot:** ss_help_sheet

---

## Walk summary (Opus driver, 2026-05-09)

**Total screens captured:** 16 (S01–S16)

**Coverage:**
- ✓ Cold launch flow (Welcome → Age → Regional → GPS → Verification Failed → Update prompt → Safety & Legal → Chat home)
- ✓ All 4 bottom-nav tabs (Talk / Mood / Quest / Community) including primary CTAs
- ✓ Mood entry mini-modal (after emoji tap)
- ✓ Quest Today + Discover sub-tabs
- ✓ Talk header ⋯ overflow (full content)
- ✓ Help / Crisis Resources sheet
- ✓ Compliance bypass via `--dart-define=DEV_BYPASS_COMPLIANCE=true` (build hack, kDebugMode-only)

**NOT reached during this walk:**
- Crisis-flagged chat (couldn't trigger — chat backend timing out from sim)
- Quest active session (didn't tap Start)
- Community post composer (didn't tap FAB)
- Clinical Check-in inside Mood tab (didn't tap card)
- Safety & Legal full-page view (sheet was already captured at S07)
- Chat AI response success (always errored from sim — TestFlight on real device works)
- Settings / Profile / Resources / Journal — **NO ENTRY POINT exists in current UI** (per S15 finding)

**Key constraints observed:**
- Sim's CoreLocation always reports `isMocked: true` — geolocator rejects → app stuck on Verification Failed unless bypass build is used
- Sim → backend `/api/chat` requests time out reliably (transient, not reproducing on real device)
- macOS Spaces: sim window kept on Space 1 corner (~250×500 px) for cross-Space-free clicks
- ZIP+pod install consumed ~2.5 GB mobile data over the session

**Design references:**
- 21 designs in `docs/design/refs/REVIEW.md`
- 14 cross-design principles applied as violation flags

**Synthesis pending (Opus principal):**
- Top friction points ranked by user-facing impact
- Cross-ref to existing analytics signals (17.3% bounce / D7 retention)
- Recommended actions Tier 0/1/2/3
- Updates to REVIEW.md rollout order based on observed gaps
- Any new design-round-6 candidates (Community feed, navigation surfacing, post-mood-low reflection)

---

# Synthesis (Opus, 2026-05-09)

## Top friction points ranked by user-facing impact

| Rank | Surface | Severity | Analytics tie | Cause |
|---|---|---|---|---|
| **F1** | Compliance gate (S03 + S05) | **🔴 BLOCKING** | Direct match to **17.3% bounce** | 100% of users gated on GPS; "Red Zone" language; sim-uncatchable failure mode = real-device-mode for indoor/denied/timeout users. 24h re-verify on cold start re-fires for returning users. |
| **F2** | Mood-low → silent dismiss (S11) | **🟠 HIGH** | Likely contributor to **near-zero D7** | Most vulnerable user state ("Feeling Very Bad") gets ZERO follow-up. App returns to a tracker form. Compounding retention loss. |
| **F3** | Chat error UX (S09) | **🟠 HIGH** | Direct silent abandonment | Error bubble identical to normal AI message; no retry button; green "online" dot lies. Vulnerable user shares "anxious" → wall. Sim-amplified but real-device-present for transient outages. |
| **F4** | Navigation surfacing gap (S15) | **🟠 STRUCTURAL** | Limits all of Tier 3+ rollout | 5 designs (Settings, Profile/Safety Plan, Journal, Resources, Weekly Review) have NO entry point. Designs without entry points don't ship. |
| **F5** | Chat first-turn sparse (S08) | **🟡 MEDIUM** | Subjective — first impression undermined | ~50% blank viewport, no breathing orb, no companion framing, no trust line. Reads as "corporate chat" not "wellness companion". |
| **F6** | Quest gamification (S12) | **🟡 PRINCIPLE-DEBT** | Possibly *helps* retention via streak; but tone-wrong | "Level 1", "0 days total" violates principle #14 (gentle structure, not gamification). Tradeoff: keep for retention ROI vs strip for tone fidelity. **Needs CEO call** before code change. |
| **F7** | Onboarding tone (S01–S02) | **🟡 MEDIUM** | First impression | "Comply with safety regulations" reads as legal disclaimer. Designs use "Quick check before we begin" / "We're built for adults." |
| **F8** | Update App? prompt (S06) | **🟡 MEDIUM** | Eats first-impression every cold start | 3-button modal blocks Welcome on cold start. Release notes mention "iOS provisioning profile" — dev-flavored to user-facing. |

## Triangulated insight

The 17.3% bounce + near-zero D7 are NOT one problem — they're a tandem:

- **17.3% lose at the GPS gate** — Tier 0 unblocks them (re-apply Phase 1+2 OR ship a cheaper Verification Failed UX).
- **Of the 82.7% who pass**, the few who log low mood get silent-treated (F2) and the chat first-turn doesn't establish warmth (F5) → low D7. **F2 is the single highest D7 lever** in the existing surface set.

The 21-design catalog is **disproportionately weighted toward "design more breadth"** when the missing capability is **"surface what's already designed"** (F4 — navigation). 5 designs sit unreachable.

## Recommended actions

### Tier 0 — Unblock users (code surgery, no design)
- **0.1: Re-apply compliance Phase 1+2** (`compliance_service.dart`: server-IP primary, GPS removed, 7-day cache). Direct fix for F1 → ~17% bounce reduction. *Was reverted earlier; the dogfood evidence justifies re-applying.* Estimated 30 min code + ~1 hr dogfood verification.
- **0.2: Wire IP-fallback as primary CTA** in Verification Failed state if 0.1 is too aggressive. Single-file fix in `compliance_guard_screen.dart`. ~30 min.
- **0.3: Chat error bubble** — apply amber tint, add inline retry button, kill green "online" dot during error state. ~1 hr in `interactive_chat_screen.dart`.
- **0.4: Update prompt** — change to dismissible banner (not modal), strip dev-flavored release notes. ~30 min.

### Tier 1 — High-leverage design rollout (existing 21-set)
- **1.1: Theme tokens consolidation** (foundational, ~2 hr, no functional change)
- **1.2: Mood-low post-submit reflection (R2D4)** — biggest D7 lever. Ship soon. ~3 hr.
- **1.3: Chat first-turn warmth (R1D3)** — breathing orb, companion framing, softer chip copy, trust line. ~4 hr.

### Tier 2 — Structural unlock (decision + scaffold)
- **2.1: Navigation surfacing decision** — pick Option A (5th "More" tab) vs B (profile-icon header sheet) vs C (extended overflow). **Blocks Tier 3 entirely.** ~1 hr decision + ~3 hr scaffold.
- **2.2: Mood Entry sheet redesign (R1D4)** — splits 887-LOC widget. Enables reuse. ~5 hr.

### Tier 3 — Designs that need entry points (do AFTER 2.1)
- 3.1 Settings + Privacy (R3D3) — App Store requirement
- 3.2 Profile + Safety Plan (R4D2)
- 3.3 Journal (R5D2)
- 3.4 Resources Library (R4D1)
- 3.5 Weekly Review (R3D4)
- 3.6 Crisis Intervention surfaces (R3D1) — wire to `risk_level` server field
- 3.7 Push notifications (R4D4) — iOS notification categories

### Tier 4 — Policy decisions before rollout
- **4.1: Quest gamification call** — F6 trades principle #14 against retention. Keep "Level / 0 days" if data shows streak-driven D7 lift; strip if pure principle. Lokesh decides.
- **4.2: Update App? prompt** — keep at all? Native iOS Update mechanism may suffice for non-critical updates.

## R6 design candidates (gaps not in 21-set)
1. **Community feed** — composer + filled feed + post detail + moderation (S14 has no design)
2. **Chat error/offline state** — proper amber-tinted bubble with retry (S09 has no design; R4D3 OfflineBanner exists for system-level but not per-message)
3. **Update App? in-app prompt** — if we keep one (S06)
4. **Safety & Legal first-launch** — could fold into Welcome screen or stay as separate sheet, but needs design contract (S07)
5. **Navigation surfacing** — design the 5th-tab "More" view OR profile-sheet OR overflow-extended UX (S15 unblocks Tier 3)

## REVIEW.md rollout order — proposed update

The current REVIEW.md rollout has 16 numbered tiers. Based on dogfood evidence, suggested re-ordering:

- **Insert Tier 0** (compliance, chat error UX, update prompt) at top — these unblock users without needing design.
- **Promote R2D4 Mood Reflection** from Tier 5 (refactor) to Tier 1 (direct UX win) — biggest D7 lever per F2.
- **Promote R3D3 Settings** from Tier 8 to Tier 2 — needed for App Store submission anyway.
- **Add Tier 2.1 Navigation Decision** as explicit blocker before Tier 3 (Settings, Profile, Journal, Resources, Weekly Review).
- **Demote R5D3 Quest** from Tier 16 to "policy-pending" — needs F6 decision before rollout.

## What this changes for next session
1. Re-apply Phase 1+2 compliance code (Lokesh decision — restored or not)
2. Pick navigation pattern (Option A/B/C in F4)
3. Decide gamification policy (F6)
4. Update REVIEW.md rollout order with above re-ranking
5. Optionally: fire R6 round designs (5 candidates listed above)


### S09 — Chat connection error state (persistent backend timeout)
- **Path:** Talk tab → tap "I'm feeling anxious" chip → send → Connection error
- **Latency:** Immediate failure (no spinner/loading state observed; error bubbles appear within ~1s)
- **Copy:**
  - AI bubble 1 (Alex): "Good morning! 🌅 How are you feeling today?"
  - User bubble 1: "I'm feeling anxious" (green filled pill, right-aligned)
  - Error bubble 1 (Alex): "Connection error. Request timed out. Please try again."
  - User bubble 2: "āb" (accidental test send from sub-agent)
  - Error bubble 2 (Alex): "Connection error. Request timed out. Please try again."
  - Crisis banner (amber-tinted, dismissible X): "ⓘ Not medical care. For crisis, call local emergency."
  - Input placeholder: "Type your message..."
  - Header: "Alex" (centered, plain) + ⋯ at top-right
  - Bottom nav: Talk (blue, selected) / Mood / Quest / Community
- **Visual:** Alex avatar has a green "online" dot (contradicts timeouts). Error bubbles use plain white card with same styling as normal AI responses — no visual differentiation (no icon, no retry CTA, no color shift). Large empty whitespace below errors.
- **Linked design:** R1D3 `GentleQuest Chat First Turn.html` — design shows no error state; there is no error-state design in the 21-set.
- **Delta vs design:** Error state is completely undesigned — plain white bubble with plain text error copy. Design system has no spec for connection failure. No retry button, no "we're having trouble connecting" warm phrasing, no offline-specific amber color (principle #1 reserves amber for offline).
- **Principle violations:**
  - **#1 (coral/amber for offline):** Error bubbles are styled identically to normal AI messages. Offline/error state should use amber per design system; current uses white = invisible error signal.
  - **#3 (every blocked state offers a path forward):** Error bubble has no retry CTA — just "Please try again" text with no actionable button.
  - **#12 (no diagnosis):** N/A — error copy is generic.
- **Friction:** HIGH for a vulnerable user. Someone sharing "I'm feeling anxious" and hitting a silent-looking error with no retry button is likely to abandon. The green "online" indicator on Alex's avatar actively misleads — it says connected while the API is failing.
- **Additional finding:** Persistent failure across multiple sends (not transient). Backend health endpoint returns 200 but chat API (`/chat` or `/stream`) is consistently timing out. This is production-impacting.
- **Screenshot:** ss_s09_chat_error (zoomed capture showing full chat + nav)

