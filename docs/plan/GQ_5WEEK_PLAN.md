> **CANONICAL COPY.** This plan was authored in plan mode at
> `~/.claude/plans/breezy-juggling-wozniak.md`, which is NOT under version control and
> does not survive this machine. Copied into the repo 2026-09-03 so it is versioned,
> greppable, and readable by the cross-vendor lanes. **Edit this copy, not the one in
> ~/.claude/plans.**
>
> Companion file: `docs/GQ_STATE_AND_REENTRY.md` — live status, ordered queue, credentials,
> and the re-entry prompt. THIS file is the reasoning (why each section exists, what was
> tried, what was retracted). That file is the current state. Read that one first on a cold
> start; read this one when you need to know *why*.

# GentleQuest — product & growth, next 5 weeks

## Context

The Stage-1 gate is **half won and half structurally broken**, and the broken half is
the whole job for the next five weeks.

- **Criterion (A), installs ≥250: PASSED** already, 2026-08-18 — 209 native + 144 web
  = 353 (`docs/gates/ADR-006-stage1-installs-pass.md:1,17-22`). Growth pressure on raw
  installs is *off*. Do not plan around it.
- **Criterion (B), D14 ≥15% with n≥40: cannot be scored as written.** The acquisition
  window is 2026-08-15→09-24 (`docs/gates/ADR-007-stage1-retention-instrument.md:30-33`),
  but no native telemetry existed until the GA4 property was created and 1.7.2+26082702
  shipped on **2026-08-27** — "no native data for its first 12 days and never will"
  (ADR-007:177-180). The roadmap's own rule is "**Unmeasurable = FAILED** … never
  'extend to find out'" (`docs/strategy/BILLION_DOLLAR_ROADMAP.md:52`), and the
  middle-band clause allows **ONE automatic 4-week extension to 2026-11-05**
  (ROADMAP:96). ADR-007:191-196 leaves the choice explicitly to the plan author.

So the real question is not "get more installs." It is: **make D14 measurable on a
legitimate window, then actually earn ≥15% on it** — with $0 spend, organic only.

Two live numbers frame the product work, both measured this session against GA4
property 551876340 (7-day window ending 2026-09-01):

- Funnel: 22 native installs → 16 compliance started (73%) → 12 completed (75%) →
  **3 first chat (25%)**. Nine of twelve people who cleared onboarding never sent a
  message. That 25% cliff is the activation wound.
- Native install rate ≈22/week, so **n≥40 is reachable in ~2 weeks of cohort** — n is
  not the binding constraint. **D14 quality is.**

And the one thing that moves D14 is re-engagement, which is currently dead: Android
scheduled notifications never fire (no `ScheduledNotificationReceiver`; the in-app test
button calls `.show()` directly so it looks healthy). There is no working retention
mechanism in the product today.

## The plan

### 1. Decide criterion (B)'s fate — governance, do first, costs nothing

Write a new ADR resolving ADR-007:191-196. Recommended ruling: **(b)
INSUFFICIENT-structural → restart the acquisition window at 2026-08-27** (first date
native telemetry actually existed), invoking the roadmap's single 4-week extension to
**2026-11-05**. Earliest complete D14 read lands ~2026-10-10, inside the extension.

This is not "extending to find out" — the original window is unmeasurable through no
behavioural fact about users, and scoring FAILED on missing instrumentation would
record a product verdict where only an instrumentation gap exists. Say that explicitly
in the ADR; it is the honest reading and it is also the one the roadmap's own
middle-band clause anticipates.

Amend ADR-007 (append-only) with the new window and name GA4 property **551876340** in
the ratified text, per the convention Amendment 2 already set.

### 2. Android notifications — receivers are FIXED; the permission gate is not

**Corrected 2026-09-02.** The premise here ("the entire re-engagement surface is dead")
came from a 2026-08-20 memory and is **stale**. Verified twice today — once by a
cross-vendor lane instructed to refute it, once by direct read:

- **Already fixed:** `ScheduledNotificationReceiver` + `ScheduledNotificationBootReceiver`
  (with `BOOT_COMPLETED`, `MY_PACKAGE_REPLACED`, 2× `QUICKBOOT_POWERON`) are declared at
  `android/app/src/main/AndroidManifest.xml:104-116`. Every `zonedSchedule` call uses
  `AndroidScheduleMode.inexactAllowWhileIdle` — deliberate, avoids exact-alarm Play review.
- **The real, live blocker:** `POST_NOTIFICATIONS` is requested at runtime **only** from
  Settings (`settings_screen.dart:211,260,297`), `notification_detail_screen.dart:49`, and
  `mood_tracker.dart:810`. **None is on the first-run path.** With `targetSdkVersion 35`,
  a fresh-install user who never opens Settings is never prompted, and the OS silently
  suppresses every scheduled notification. Working receivers behind an ungranted
  permission deliver exactly as many notifications as no receivers at all.

**Corrected again 2026-09-02 — my "live blocker" was mostly wrong too.** Dispatched a
lane specifically to refute it; verdict PARTIALLY-CONFIRMED, and my broad claim was the
wrong part:

- The three toggle categories are **correct by design.** Prefs default false, nothing is
  scheduled until an explicit opt-in, and each toggle awaits `requestPermissions()` and
  **reverts the pref on denial** (`settings_screen.dart:211-221,260-265,297-302`). No
  silent lie; the UI matches reality. "Every scheduled notification is suppressed" was
  simply false — most are never *scheduled*, which is the correct behaviour.
- `scheduleStreakNudge`, `scheduleMoodLowFollowup`, `scheduleWeeklyReviewIfEligible` have
  **no callers** — dead code, worth a separate cleanup decision.
- **The one real defect, now FIXED (`c9f48350`):** `scheduleCrisisFollowup` — the only
  category not behind a toggle — scheduled with no permission ask at all. A user picking
  "heavy" in the Q9 crisis bridge got a follow-up the OS silently discarded. It now asks
  first, at the service level, with an opposed-pair test and a verified positive control.

So notifications are **not** the D14 blocker I claimed. The honest remaining statement:
almost nobody opts in, because the toggles are buried in Settings and default off. That
is a discoverability question, not a permission bug — and it should be decided on data,
not another confident guess from me.

**Opposed-pair verification remains mandatory** — this bug class is precisely "a test
button that calls `.show()` and looks healthy." `sendTestNotification()` really does call
`_plugin.show()` (`notification_service_impl.dart:372`), which bypasses AlarmManager
entirely. So: prove a *scheduled* notification fires after app-kill and after reboot on a
fresh install that has never opened Settings, and prove it does **not** fire with the pref
off. A green test that only exercises `.show()` proves nothing.

### 3. The 25% activation cliff — CAUSE STILL UNKNOWN (earlier answer retracted)

**Retracted 2026-09-02.** This section previously said the cliff was caused by users
landing on Home instead of Talk. **That was wrong.** Users were already landing on Talk
on every mount: `HomeTabDeepLink` defaulted to `AppTab.talk` and
`HomeShell.initState` called `_onDeepLinkTab()` unconditionally, discarding `initialTab`
entirely. The deep-link bug is now fixed (`78d0d757`), but **landing on Talk was already
happening, so it cannot explain the cliff.**

How the wrong answer survived: a lane read `initialTab = AppTab.home` and stopped; I
"independently verified" by reading the *same two lines* and stopped in the same place.
Two checks, one blind spot — neither executed the code. A third lane, asked to write an
opposed-pair *test*, caught it in minutes. **Reading agreement is not verification;
running the opposed pair is.** I had also seen the app land on chat on a live emulator,
noted it contradicted the finding, and let it go — that observation was correct and I
should have chased it.

**So the cliff is open again.** What is now known: users reach the chat screen, and 9 of
12 still send nothing. Remaining candidates, none yet evidenced — a passive greeting that
doesn't invite input (the composer is never auto-focused), first-response latency, or
send failure.

The instrumentation shipped in `78d0d757` is what will name it: `chat_tab_viewed` →
`chat_composer_focused` → `chat_send_attempted` → `first_chat_message_sent`. **Do not
propose another fix before that data reads.** This section has already been wrong once
from exactly that impatience.

The instrumentation-artifact hypothesis was explicitly checked and **refuted**:
`first_chat_message_sent` is gated by a `first_chat_message_logged_v1` SharedPreferences
flag read at the top of `sendMessage` before any network work
(`providers/chat_provider.dart:333-359`), and fires on both send paths. The event is
honest; the funnel is real.

**The fix is a product decision, not a measurement one.** Options, cheapest first:
land post-compliance on the chat tab instead of home; or give WellnessHomeScreen a
primary "talk to Alex" CTA that switches tabs. Either is small. Which one is a judgment
call about what the first session should feel like — it should be made deliberately, not
defaulted.

Add the split-step GA4 events anyway (chat-tab-reached, composer-focused) so the fix can
be *proven* rather than assumed — extend `FUNNEL_STAGES` in
`metrics/onboarding_funnel_ga4.py` and the route/dashboard pick them up for free. But the
events are now the **proof**, not the diagnosis.

### 4. Growth, $0 organic — landing-page measurement: DONE 2026-09-02

All three fixes shipped by a cross-vendor lane (devin/swe-1-7), verified by diff and a
clean build:

- gtag repointed `G-Z4Z92EJ3DV` → **`G-MBBHN4PT39`** (`landing-page/index.html:23,28`) —
  the correct web stream for property 551876340 (`ADR-007:155`).
- `sendBlogEvent` added (`App.jsx:19`), posting to **both** gtag and the backend
  `/api/analytics/log`. `cta_impression` fires via `IntersectionObserver`; `cta_click`
  on all three CTAs (iOS / Android / web).
- Version chip → **v1.7.2**.

**A caution worth more than the fix.** I twice recorded a wrong belief about this file:
first the scout's report, then my own "it was already fixed" correction — which was wrong
because I read the file *after* the lane had silently written to it. `nucleus_delegate`
had reported `timed_out / effect: no_files_touched / changed_paths: []` because it
compared git HEAD before/after, and the lane (correctly, per instruction) did not commit.
Real work was indistinguishable from no work. **Verify a lane's effect with
`git status`/`git diff` on the worktree, never from the tool's HEAD-based verdict.**

So growth work goes straight to channels. `docs/ASO_STORE_OPTIMIZATION.md:11-19` already
has a keyword table — a store-listing refresh is the highest-yield $0 lever and it
compounds. Reddit is **not** a candidate: `docs/marketing/marketing_log.md:77` records the
Anti-Streak launch at 0 upvotes / 31% ratio with a recommendation to stop direct promo.

### 4b. Channel attribution — MEASURED 2026-09-02, and the answer is stark

Built `metrics/channel_installs_ga4.py` (`f08894c8`) and **ran it live** against property
551876340. 30-day window:

```
(direct) / (none)   native 30   (iOS 16, Android 14)   web 0
total               native 30
```

**Every single install is unattributed.** Not one of the last 30 days' installs is
credited to the landing page, the blog, Reddit, or any campaign. One channel row, and it
is the "we don't know" row.

Two readings, **not yet distinguished**:
- (a) direct store search/browse genuinely is the only thing producing installs — which
  would make **ASO the sole working lever**, or
- (b) GA4 simply cannot see store referrals, because store links are not UTM-tagged and
  Play/App Store campaign linking is not configured.

The actionable conclusion is the same either way: **no acquisition channel is provably
producing installs.** Distinguishing (a) from (b) is cheap — tag the store links — and
should happen *before* any effort goes into a channel whose contribution cannot be
measured. Doing ASO work is defensible right now precisely because it is the one lever
consistent with both readings.

Also fixed en route (`1a91b985`): `cta_impression` was not sending UTMs while
`cta_click` was, so per-channel CTR had a missing denominator.

Method note worth keeping: the lane built the module but could not run it (no creds in
its environment). **The tests passing proved it parsed; only the live call proved
`firstUserSourceMedium` + `first_open` is a combination GA4 accepts.** Always land the
live smoke before believing a new instrument.

## Explicitly out of scope

Paid acquisition (operator chose $0/organic). Dark mode — 4 rulings still pending
(`docs/design/DARK_MODE_RULINGS_PENDING.md:7-34`) and it does not move D14. Any 1.7.3
scope list — none exists yet (`docs/KNOWN_ISSUES_NEXT_RELEASE.md:18`, "awaiting detail"),
and inventing one now would be fiction. Server-side notification pref sync.

## Verification

```bash
# gates, per train
export PATH="/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin:$PATH"
cd ~/gq-wo/ai_buddy_web && flutter analyze          # baseline 8
flutter test                                        # baseline 381 pass / 5 fail
#   (5 known: interactive_chat x1, j03_compliance x4)

# funnel, after instrumenting the activation gap
python3 metrics/onboarding_funnel_ga4.py --days 7
curl -s "https://app.gentlequest.app/api/metrics/onboarding_funnel?days=7"

# notifications — opposed pair, on device, both directions
#   pref ON  + app killed + reboot -> scheduled notification MUST fire
#   pref OFF                       -> MUST NOT fire
```

**Machine note:** Render auto-deploy is OFF — backend changes need a manual
`POST /v1/services/srv-d2r3i1fdiees73dqtov0/deploys`. iOS Simulator `flutter run` is
currently broken on this Mac (mDNS/Bonjour resolver down, breaks VM-service discovery);
Android emulator works and is the verification path until that's fixed.

## Decision reserved for the operator

The criterion-(B) ruling in §1 is a governance call with kill-clause implications.
The recommendation is stated; it should be ratified as an ADR, not applied silently.
