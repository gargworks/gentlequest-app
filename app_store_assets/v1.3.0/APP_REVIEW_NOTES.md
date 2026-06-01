# App Store Review Notes — GentleQuest v1.3.0

**Audience:** App Store Connect + Google Play Console reviewers.
**Purpose:** Context for the location prompt and state-gating behavior, plus a short reviewer-walkthrough to demonstrate the app's intended use.

---

## TL;DR for reviewers

GentleQuest is a peer-support / journaling app focused on mental wellness. It is **not** a medical device, does not diagnose or treat, and does not connect users to licensed clinicians.

The app requests **approximate location once at first launch** strictly to confirm regulatory eligibility — i.e., to determine which US state (or country) the user is in, so that we can:
1. Hard-block users in states where unlicensed AI peer-support is illegal (Illinois — WOPR Act / HB1806).
2. Temp-block users in states where compliance work is still in progress (Utah HB452, Washington MHMDA).
3. Surface the correct crisis line for the user's region.

We **never** track the user's continuous location, store GPS coordinates, or share location with third parties. We store only the derived region label (e.g., "California") locally. The location permission is `WhenInUse` only on iOS and `COARSE_LOCATION` only on Android.

---

## Why a reviewer might see a location prompt

If the reviewer's IP-region check returns one of our hard-ban or temp-block states (IL / UT / WA), they will be unable to proceed past the ComplianceGuard screen. This is **by design** — we cannot legally serve users in those jurisdictions until each state's compliance regime is met.

**For review purposes:** Apple/Google reviewers are typically in California (Cupertino) or other unblocked states. The location flow should pass on first launch and reach the main chat experience within ~10 seconds.

If review is conducted from a hard-ban state network, the app will display the regional-block screen, which is the intended user experience for that jurisdiction. Please contact us before flagging this as a defect.

---

## Reviewer walkthrough (recommended path)

1. **Launch app cold.** Splash screen → ~1.5s → Welcome screen.
2. **Tap Continue** on Welcome.
3. **Age gate prompt:** confirm you are 18+ (the app enforces 18+ globally for v1.3.0 to avoid minor-data regulatory complexity).
4. **Location permission prompt:** tap "Allow While Using App" (iOS) or "Allow only while using the app" (Android, coarse).
5. **Compliance check completes** in <5s. You land on the Talk (chat) tab.
6. **Send a test message** like "I'm feeling overwhelmed today." The AI responds with a warm, non-clinical message.
7. **Explore tabs:** Mood (track), Quest (gentle activities), Library (resources), Profile.
8. **Crisis surface:** In the chat, type a self-harm phrase like "I want to hurt myself" — the app immediately surfaces the 988 Suicide & Crisis Lifeline screen with one-tap call/text. This is the most safety-critical path and is the reason the app exists.

---

## Age rating defensibility

- iOS: declared **17+** (Frequent/Intense Medical/Treatment Information + Infrequent/Mild Mature/Suggestive Themes).
- Google Play: declared **Mature 17+**.
- Code enforces **18+** universally (see `ai_buddy_web/lib/services/compliance_service.dart` line 72: `_kMinAgeUniversal = 18`).
- Privacy policy at `https://gentlequest.app/privacy` states "built for adults aged 18 and older."

The 18+ floor (above the 17+ rating) is operator-deliberate: it gives extra legal buffer against minor-data regulatory regimes (COPPA, GDPR-K, India DPDP 2023 children's-data provisions) without forfeiting the 17+ App Store category.

---

## Data handling (matches Privacy Nutrition Label / Data Safety)

**Collected:**
- Account identifiers (email, anonymized user ID) — only if user opts to create an account; default is anonymous.
- Chat messages — to provide the AI conversational response; processed via Gemini API; not used to train models.
- Mood entries, journal entries, quest progress — stored encrypted at rest in our database; never sold or shared.
- Approximate location (one-time, coarse) — for regulatory eligibility only; we store the derived region label, not GPS coordinates.
- Crash + diagnostic data (Sentry) — anonymized; no chat/mood/journal content.

**Not collected:**
- Real name, contact info beyond email
- Precise location, location history
- Browsing/search history outside the app
- Health/fitness data, biometrics
- Photos, files, contacts

**Third parties:**
- Apple (App Store, APNs, crash reporting)
- Google Firebase (anonymized analytics, crash reporting)
- Sentry (anonymized error diagnostics)
- Email provider (support correspondence only)

We do **not** sell data, use it to train AI models, or share with advertisers.

---

## Crisis resources (US-only for v1.3.0)

When the app detects crisis keywords or the user taps the crisis button:
- 988 Suicide & Crisis Lifeline (call / text)
- Crisis Text Line (text HOME to 741741)
- Teen Line (310-855-4673)
- JED Foundation (jedfoundation.org)

International crisis localization (UK, India, EU, Canada, Australia) is planned for v1.4.0. Until then, the app is configured for US release only.

---

## Universal Links (deep linking)

- iOS Universal Links: AASA served at `https://gentlequest.app/.well-known/apple-app-site-association` (verified HTTP 200 with `828Q2S3G4Q.com.gentlequest.app` and exclusions for `/privacy`, `/terms`).
- Android App Links: assetlinks.json served at `https://gentlequest.app/.well-known/assetlinks.json` (verified HTTP 200 with `app.gentlequest.www` package and Play App Signing SHA-256 fingerprint).

`/privacy` and `/terms` are intentionally excluded from the app intercept so reviewers (and users) see the marketing legal pages in their browser, not in-app.

---

## Account / test credentials

The app supports **anonymous mode by default** — no account creation required to reach any feature. Reviewers can complete the entire walkthrough without entering an email.

If account testing is needed: tap Profile → Sign in → use any email; magic-link sent. (Backend is on Render free tier — magic-link may take up to 1 minute to arrive.)

---

## Backend / infrastructure context

- Web/API host: Render (web_service `GentleQuest`, custom domain `app.gentlequest.app`).
- Database: Neon Postgres (permanent free tier, Singapore region).
- LLM: Google Gemini (gemini-2.5-flash for tool/function calls).
- AI safety: keyword-trigger crisis surface; no model is allowed to refuse safety responses.

The backend may have a ~5-15 second cold-start on the first request after idle (Render free tier behavior).

---

## Source-of-truth references

- Mobile build: nucleus `feat/onboarding-10min-activation-walkthrough` (post-PR #428 merge).
- Web build: amha main HEAD `e4815a46` (post PR #105 + #106 + universal-links commit).
- Privacy policy: `https://gentlequest.app/privacy` (last updated 2026-05-31).
- Terms: `https://gentlequest.app/terms`.

For any questions during review, please contact the developer via App Store Connect / Play Console messaging.
