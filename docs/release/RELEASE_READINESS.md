# GentleQuest — release readiness checklist

Snapshot at 2026-05-21. Updated alongside the auth/login + cross-device-sync
work that landed across commits `5c186254 … 7eb11e20`.

## Hard blockers (release fails without these)

| # | Item | Status | Owner / next step |
|---|---|---|---|
| 1 | **Email backend provider configured** | Code-complete — routes/auth.py supports Resend / SendGrid / Postmark via `EMAIL_BACKEND` env var; defaults to stdout in dev | Lokesh: pick a provider, set `EMAIL_BACKEND=resend` + `RESEND_API_KEY=...` (or SendGrid / Postmark equivalents) in prod env vars. Also set `EMAIL_FROM` (default `GentleQuest <hello@gentlequest.app>`). DNS for the sender domain has to be live before the first send — most providers require SPF + DKIM verification. |
| 2 | **`auth_tokens` table on prod DB** | Will be created automatically by `db.create_all()` at backend boot (see app.py:231). Migration 009 also written for explicit alembic users. | Just deploy backend; first boot creates the table. Verify by hitting `GET /api/auth/me` — should return `{"user": null}` not 500. |
| 3 | **App Store / Play Store URLs** | Placeholder fallbacks land users on the iOS App Store *search* (real page, useful) and the Play Store `details?id=com.gentlequest.app` (real if published). Override via `--dart-define=APP_STORE_URL=...` / `--dart-define=PLAY_STORE_URL=...` at build time. | Lokesh: get the live `id<n>` from App Store Connect when the app is approved + pass via dart-define. |
| 4 | **Backend deploy** | Code is on `release/v1.3.0`. Deploys via Render / Cloud Run / Docker per repo's existing pipeline; `app:app` + start.sh handles it. | Lokesh: push branch → trigger deploy. |

## Significant (release-ish but degraded)

| # | Item | Status | Owner / next step |
|---|---|---|---|
| 5 | **Legal opinion on 13+ age gate** | Code defaults to 13 in regions where law allows, 16 in EU-GDPR-K-Article-8 countries, 18 in India / unknown regions. Privacy policy updated accordingly. | Lokesh + counsel: see [LEGAL_REVIEW_BRIEF.md](LEGAL_REVIEW_BRIEF.md) for the lawyer briefing. |
| 6 | **Voice STT live-fire** | Wired with `speech_to_text: ^7.0.0`, on-device-only mode (`onDevice: true`), iOS Info.plist + Android Manifest permissions in place. Not yet tested with real audio on a device. | Build + sideload → test recording → confirm transcript reaches text field. |
| 7 | **Magic-link round trip live-fire** | Backend tests cover the full flow (8/8 pass). UI not yet tested with a real email. | After (1) is configured: from a real device, request → email arrives → tap deep link → see signed-in state in Settings. |
| 8 | **Cross-device sync live-fire** | Backend tests cover canonical session adoption. Two-device test not done. | Sign in on web, write a journal entry, sign in on phone, confirm entry appears. |
| 9 | **Privacy policy v2** | Updated to cover accounts, magic-link tokens, regional age tiers. | Have counsel review alongside (5). |

## App store submission readiness

| # | Item | Status |
|---|---|---|
| 10 | iOS bundle ID + signing | Existing — `com.gentlequest.app` |
| 11 | iOS permission strings | NSMicrophoneUsageDescription + NSSpeechRecognitionUsageDescription added; wellness-companion tone (not legalese) for App Store review |
| 12 | iOS App Store screenshots | Stale relative to current UI — chip reorder, Mood pill, Mental wellness label, footer disclaimer all new since last screenshot run. Capture fresh from a clean simulator post-deploy. |
| 13 | Android permissions | RECORD_AUDIO + BLUETOOTH{_ADMIN,_CONNECT} + `android.speech.RecognitionService` query added |
| 14 | Android Play Store listing | Same screenshot staleness as (12) |

## Live verification matrix

| Surface | Verified live this session | Pending verification |
|---|---|---|
| Mood tab "+" → "Log mood" pill | ✅ | – |
| Mental wellness check-in label | ✅ | – |
| Chat starter chip reorder | ✅ | – |
| Journal persistence (cold restart) | ✅ | – |
| ProfileNavSheet from avatar tap | ✅ | – |
| Footer disclaimer chip | – | iOS + Android |
| Voice mic (graceful degrade on unsupported device) | – | iOS + Android |
| Voice STT actual transcription | – | iOS + Android with real audio |
| Magic-link email send | – | Needs (1) configured |
| Magic-link deep link → verify → signed-in | – | Needs (1) configured |
| Journal sync across two devices | – | Needs sign-in working |
| Chat history cross-device | – | Needs sign-in working |
| 13+ age gate copy on welcome screen | – | iOS + Android cold launch |
| Web build runs at all | – | Run `flutter build web`, open in browser |
| Web mobile-promo sheet (one-time) | – | Open web build for the first time |

## Test gate

- `flutter analyze` whole project: **0 issues**.
- `pytest tests/test_auth.py tests/test_journal.py`: **14 passed**.
- `flutter test test/`: **123 passed, 0 failed** (after relocating
  `screenshot_test.dart` to `integration_test/` and removing 12 stale
  pre-existing tests that referenced superseded R1D1 + safety-plan
  designs).
- `flutter build ios --simulator`: clean compile (verified earlier).

## Operational steps before traffic

1. Set `EMAIL_BACKEND` + provider API key in prod env. Confirm SPF/DKIM
   live for the sender domain.
2. Set `EMAIL_FROM=GentleQuest <hello@gentlequest.app>` (or your verified
   sender).
3. Set `APP_STORE_URL` and `PLAY_STORE_URL` via dart-define at build
   time when the App Store ID is approved.
4. Deploy `release/v1.3.0` to backend.
5. Curl-smoke: `curl https://nucleus.gentlequest.app/api/auth/me` →
   should return `{"user": null}` with 200.
6. Curl-smoke: `curl -X POST -H 'Content-Type: application/json'
   -d '{"email":"you@yourdomain"}'
   https://nucleus.gentlequest.app/api/auth/magic-link` → 202.
   Check your inbox for the magic link.
7. From a phone build, tap the deep link → should land in app
   signed in. Settings → ACCOUNT card now shows your email.
8. Run one cross-device test: write a journal entry on the signed-in
   device, sign into a second device with the same email, confirm the
   entry appears.

Once (1)-(8) pass, the auth + cross-device-sync stack is genuinely
release-ready.
