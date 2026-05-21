# Universal Links + App Links — Operator Setup

**Status:** framework-wired in v1.3.0 (release branch). Activation requires three operator steps below (Apple Dev, Android keystore, Render env vars). Until those land, the mobile magic-link still works via the `gentlequest://` custom scheme — Universal Links is an additive hardening, not a hard cutover.

## Why we're adding this

The magic-link flow 302s the verify URL to `gentlequest://auth/verify?token=...` on mobile UAs. Custom schemes are **first-come-first-served on iOS and Android** — if a malicious app on the same device also registers `gentlequest://`, the OS may route the magic-link tap into the attacker's app instead of GentleQuest, leaking the verify token.

Universal Links (iOS) and App Links (Android) close this window. Both rely on the same primitive:

1. The app declares **associated domains** in its build (entitlements / manifest).
2. The OS downloads a JSON document from `https://<domain>/.well-known/...` over HTTPS.
3. If the document cryptographically matches the installed app's identity (Apple Team ID + bundle ID on iOS; package name + SHA-256 signing-cert fingerprint on Android), tapping an `https://gentlequest.app/auth/...` link opens **our app directly** with no browser hop and no app-chooser. A malicious app can't claim our domain because it can't serve our `.well-known/` document.

The custom-scheme intent-filters stay in place as fallback for users on devices that haven't completed verification yet.

## What's wired now (in this PR)

| Surface | File | What changed |
|---|---|---|
| iOS | `ai_buddy_web/ios/Runner/Runner.entitlements` | `com.apple.developer.associated-domains` declares `applinks:gentlequest.app`, `applinks:www.gentlequest.app`, `applinks:app.gentlequest.app`, `webcredentials:gentlequest.app` |
| iOS | `ai_buddy_web/ios/Runner/Info.plist` | Existing `CFBundleURLTypes` (`gentlequest://`) kept as fallback |
| Android | `ai_buddy_web/android/app/src/main/AndroidManifest.xml` | New dedicated `<intent-filter android:autoVerify="true">` for `https://gentlequest.app/auth/*`; existing combined custom-scheme + https intent-filter kept as fallback |
| Backend | `routes/well_known.py` (NEW) | Serves `/.well-known/apple-app-site-association` and `/.well-known/assetlinks.json` with env-driven identity, 503s when unconfigured |
| Backend | `routes/__init__.py` | Registers `well_known_bp` |

## What Lokesh still needs to do himself

### iOS

1. **Apple Developer account** → Identifiers → select the `app.gentlequest.gentlequest` (or whatever the prod bundle ID is) app ID → **enable the "Associated Domains" capability**. This step is GUI-only; can't be automated from the repo.
2. Re-generate the provisioning profile (Xcode usually does this automatically once the capability is checked).
3. Set Render env vars:
   - `IOS_TEAM_ID` — the 10-character Team ID from the top-right of the Apple Developer portal (e.g. `ABCDE12345`).
   - `IOS_BUNDLE_ID` — defaults to `app.gentlequest.gentlequest`. Override only if the prod bundle differs.

### Android

1. **Get the SHA-256 fingerprint** of the signing key. For the debug keystore (dev/QA):
   ```bash
   keytool -list -v \
     -keystore ~/.android/debug.keystore \
     -alias androiddebugkey \
     -storepass android
   ```
   Grab the line that starts `SHA256:` (format `14:6D:E9:...:5F`).

   For the **release keystore** (production builds — this is the one that actually matters):
   ```bash
   keytool -list -v -keystore <release.keystore> -alias <release-alias>
   ```
   If GentleQuest is published via Play App Signing, the fingerprint to use is the one shown in **Play Console → Setup → App integrity → App signing key certificate (SHA-256)**, not the upload key. Using the wrong one silently breaks verification.

2. Set Render env vars:
   - `ANDROID_PACKAGE_NAME` — e.g. `com.gentlequest.app`
   - `ANDROID_SHA256_FINGERPRINT` — the colon-separated SHA-256 string from step 1

### Verify

1. **Backend documents reachable.** After setting env vars and redeploying:
   ```bash
   curl -sv https://nucleus.gentlequest.app/.well-known/apple-app-site-association
   curl -sv https://nucleus.gentlequest.app/.well-known/assetlinks.json
   ```
   Both should return 200 with `Content-Type: application/json` and the configured values. If either returns 503 with `{"error":"universal_links_not_configured"}`, the env vars aren't set on that environment.

   Whichever domain hosts the apex `gentlequest.app` traffic also needs to serve these paths. If the apex is fronted by a different worker/edge than `nucleus.*`, mirror or proxy the two `.well-known` paths to the Flask backend.

2. **Apple validator.** Paste the production `apple-app-site-association` URL into https://branch.io/resources/aasa-validator/ — it parses + flags missing components / wrong app-ID format / wrong content-type.

3. **Android live verification.** Install the app on a device, then:
   ```bash
   adb shell pm get-app-links com.gentlequest.app
   ```
   Look for `gentlequest.app: verified` against your `autoVerify` filters. If you see `legacy_failure` or `none`, Android didn't successfully fetch + parse `/.well-known/assetlinks.json` — re-check the fingerprint, the package name, and that the JSON is reachable without auth/redirect.

4. **End-to-end.** Send yourself a magic-link from the prod web UI, open the email on the same iOS / Android device with GentleQuest installed, tap the link. Expected: GentleQuest opens directly on the verify screen with no browser interstitial. Run twice — first tap teaches the OS the routing; second confirms it stuck.

## Failure modes worth knowing about

- **Wrong content-type on the iOS document.** Apple used to require `application/pkcs7-mime`; that requirement was dropped and `application/json` is now correct. `routes/well_known.py` sets it explicitly — don't proxy through anything that mangles the header.
- **Path-prefix typo.** The Android intent-filter scopes verification to `pathPrefix="/auth"`. If the magic-link 302 ever switches to a non-`/auth/...` URL, the App Link won't match and Chrome will open the URL in a browser tab instead of the app.
- **Play App Signing fingerprint vs upload key fingerprint.** This catches everyone once. The OS verifies against the **app-signing certificate** Google uses to re-sign your APK, not the upload key you submit. Use Play Console's value, not your local keystore, for Play Store builds.
- **JSON unreachable on apex.** If `gentlequest.app/.well-known/...` returns the marketing site's 404 instead of the Flask backend's JSON, verification never succeeds. Route `/.well-known/apple-app-site-association` and `/.well-known/assetlinks.json` from the apex to the Flask backend (nginx/Cloudflare rule, or a static mirror that you keep in lock-step with env vars).
