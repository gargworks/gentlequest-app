# App Store Review Notes — GentleQuest v1.5.0 ("The ADHD Update")

**Audience:** App Store Connect + Google Play Console reviewers.
**Purpose:** Context for the new companionship/appearance features, the 18+ gate fix, and the safety-path changes in this release. Rejection history on this app makes these notes load-bearing — please read in full before flagging anything below as a defect.

---

## TL;DR for reviewers

GentleQuest is a peer-support / journaling app focused on mental wellness. It is **not** a medical device, does not diagnose or treat, and does not connect users to licensed clinicians. That has not changed in v1.5.0.

v1.5.0 adds two new features aimed at ADHD/overwhelm users who bounce off streak-based apps — **body doubling** and **quiet mode** — plus an optional onboarding step, a fix to a regression in the mandatory 18+ age gate, an enforced journal-privacy promise, and a crisis-detection scoring fix. None of these touch the app's medical/clinical posture.

---

## What's new in v1.5.0 (reviewer-relevant detail)

### 1. Body doubling — companionship feature, not medical

"Body doubling" is a peer-support / productivity technique (working alongside someone, even virtually, to stay on task) — it is **not** a therapeutic or clinical intervention, and the app never describes it as one. In-app: the user picks a task (free text) and a duration (5/10/15/25 min); the companion "Alex" sends a scripted, non-LLM check-in at session start, midpoint, and end, plus a warm no-guilt message if the user ends early. There is no video, no real co-presence infrastructure, and no clinical framing anywhere in the copy — this is a companionship/focus feature, positioned the same way a Pomodoro timer or a study-buddy app would be.

### 2. Quiet mode — appearance feature, not medical

"Quiet mode" (internally "low-stim") is a single Settings toggle (Settings → Appearance → "Low-stim quiet mode") that swaps the app's color saturation and disables non-essential animation app-wide. This is a **visual/appearance preference**, comparable to a dark-mode toggle — it makes no claims about symptom management, sensory processing disorder, or any diagnosis, and is not described as treating anything.

### 3. "Get to know your brain" — optional, skippable, non-diagnostic onboarding

A new onboarding step (shown once, skippable at every screen, never blocking) asks two self-discovery-toned questions about task initiation and sustained attention. **This is explicitly not a screening tool**: there is no scoring, no severity output, no clinical vocabulary (no "ASRS," no Likert scale, no diagnostic language) anywhere in the UI. Every path — both questions answered or skipped at any point — resolves to the same kind of result: a plain list of feature suggestions (body doubling, quiet mode, gentle quests). Both the intro and the suggestions screen carry "Not a diagnosis" microcopy, consistent with the disclaimer pattern already used on the PHQ-9/GAD-7 result screens.

### 4. 18+ age gate — regression fixed, now consistent everywhere

A June 2026 onboarding redesign shipped a single attestation button that briefly read "I'm 13 or older" and, because it routed straight past the age-modal state, silently dropped the under-18 decline path. **This was a UI regression, not a policy change** — the app's actual enforcement (`ComplianceService._kMinAgeUniversal = 18`, `ai_buddy_web/lib/services/compliance_service.dart`) was never anything but 18+, matching the store rating (17+/Mature) and the privacy policy's "built for adults aged 18 and older." v1.5.0 restores the correct attestation copy ("I'm 18 or older") and reinstates the low-key "Under 18? Find support made for you →" link, which routes to a dignity-first support screen (988 Suicide & Crisis Lifeline, Crisis Text Line, Teen Line, JED Foundation — no app access, no data collection). **The 18+ floor and the under-18 support path are now consistent across every entry point into the app**, closing the gap this regression opened.

### 5. Journal privacy promise — now enforced in code, not just copy

The journal screen has always displayed "Stays on your device. Never synced. Never shared." (`journal_empty_state.dart:165`). Until this release that was inaccurate: a live backend route (`routes/journal.py` → `/api/journal`) persisted journal entries server-side for signed-in users. v1.5.0 **deletes that route and its registration** — the on-screen promise is now true for all users. (The `JournalEntry` database model itself is retained, unused by any active route, solely so existing GDPR export/delete requests for entries written before this fix can still be honored — it accepts no new writes.)

### 6. Crisis-detection scoring fix — safety-only, no new data collection

A scoring bug in the (currently flag-gated, off-by-default) clinical crisis detector meant that even an unambiguous single high-severity signal (e.g., "I have a gun ready to kill myself tonight") could not clear the threshold that triggers immediate-action handling. This release fixes the scoring math. **The user-facing crisis flow is unchanged**: 988 Suicide & Crisis Lifeline and other crisis resources remain reachable from every screen, including blocked-region and offline states, exactly as in prior versions — this fix only improves internal risk-scoring accuracy behind the existing safety UI.

---

## Prior Apple rejection — status

GentleQuest was previously rejected under **App Store Review Guideline 1.4.1 (Physical Harm)**. That rejection was resolved with a **metadata-only fix** (App Store Connect listing/disclaimer copy, no code change) in the v1.4.x resubmission cycle. The disclaimer language that satisfied that review is maintained at `docs/legal/app_store_review_notes.md` (the canonical, cross-version source for guideline-1.4.1 disclaimer content) and remains **unchanged** in v1.5.0 — none of this release's new features (body doubling, quiet mode, ADHD onboarding) introduce new medical claims that would reopen that finding. If this build is flagged again under 1.4.1, please check first whether App Store Connect's current listing copy still matches `docs/legal/app_store_review_notes.md` — metadata drift, not app behavior, was the root cause last time.

---

## Age rating defensibility (unchanged from v1.3.0)

- iOS: declared **17+** (Frequent/Intense Medical/Treatment Information + Infrequent/Mild Mature/Suggestive Themes).
- Google Play: declared **Mature 17+**.
- Code enforces **18+** universally (`ai_buddy_web/lib/services/compliance_service.dart:96`, `_kMinAgeUniversal = 18`) — see item 4 above for the v1.5.0 fix that restored consistent enforcement across every entry point.
- Privacy policy at `https://gentlequest.app/privacy` states "built for adults aged 18 and older."

The 18+ floor (above the 17+ rating) remains operator-deliberate: legal buffer against minor-data regulatory regimes (COPPA, GDPR-K, India DPDP 2023) without forfeiting the 17+ App Store category.

---

## Crisis resources (unchanged — always reachable, "P6")

Crisis resources are never blocked — not by the age gate, the IL/UT/WA regional restrictions, offline state, or any feature added in this release. When crisis keywords are detected or the user taps the crisis button:
- 988 Suicide & Crisis Lifeline (call / text)
- Crisis Text Line (text HOME to 741741)
- Teen Line (310-855-4673)
- JED Foundation (jedfoundation.org)

The under-18 support screen (item 4 above) surfaces the same resource set for users who decline the 18+ attestation.

---

## Reviewer walkthrough (recommended path)

1. **Launch app cold.** Splash screen → Welcome screen (single-tap redesign).
2. **Age attestation:** tap "I'm 18 or older" to proceed. To verify the under-18 path, instead tap "Under 18? Find support made for you →" — confirm it shows crisis resources and does **not** grant app access.
3. Re-launch and confirm with 18+: you land on the Mood tab.
4. **ADHD onboarding (optional):** if shown (first run only), answer or skip the two questions — confirm no score/diagnosis is ever displayed, and that skipping at any point still reaches the app.
5. **Body doubling:** open the Talk (chat) tab → tap the timer icon in the header → start a short session → confirm a companion check-in appears in chat at session start, and that ending early produces a warm, non-shaming message.
6. **Quiet mode:** Settings → Appearance → toggle "Low-stim quiet mode" → confirm the app-wide color/motion change, and that toggling it off restores the normal look.
7. **Crisis path test:** in the Talk tab, send "I want to hurt myself" — the app immediately surfaces the 988 Suicide & Crisis Lifeline with one-tap call/text, unchanged from prior versions.
8. **Journal:** Profile → Journal → write an entry → confirm the "Stays on your device. Never synced. Never shared." copy, now accurate.

---

## Data handling (unchanged from v1.3.0 — see `app_store_assets/v1.3.0/APP_REVIEW_NOTES.md` for the full matrix)

No new data categories are collected in v1.5.0. Journal entries for new writes are local-only (see item 5). Feedback submissions (new in this release — in-app feedback form now reaches the team instead of only local storage) are anonymous, rate-limited, and contain only the rating, optional free-text feedback, app version, and platform — no account or device identifier beyond an ephemeral session ID already used elsewhere in the app.

---

## Account / test credentials

Unchanged: anonymous mode by default, no account required to reach any feature described above.

---

## Source-of-truth references

- Mobile build: `ai-mental-health-assistant` main HEAD post-PR #172 (`6e1c3d63` + this release's version bump).
- Feature PRs: #166 (body doubling), #167 (journal route deletion + clinical-detector verification), #168 (quiet mode), #169 (ADHD onboarding), #170 (crisis-detection scoring fix), #171 (onboarding/quiet-mode wiring), #172 (18+ attestation fix).
- Canonical Apple guideline 1.4.1 disclaimer content: `docs/legal/app_store_review_notes.md`.
- Privacy policy: `https://gentlequest.app/privacy`. Terms: `https://gentlequest.app/terms`.

For any questions during review, please contact the developer via App Store Connect / Play Console messaging.
