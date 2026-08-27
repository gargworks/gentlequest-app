# One-Button Release (Beta) – Inputs, Secrets, and Notes

## Inputs (workflow_dispatch)
- `release_notes` (string): Stored as artifact; not auto-published to stores.
- `build_number` (string, optional): Defaults to run number when empty.
- `android_params` (JSON): `{ "app_id", "package_name", "track", "upload", "preflight", "crashlytics_upload" }`
- `ios_params` (JSON): `{ "bundle_id", "scheme", "export_method", "upload", "preflight" }`
- `sentry_params` (JSON): `{ "upload", "org", "project_android", "project_ios", "release", "environment" }`
- `release_params` (JSON): `{ "create_gh_release", "notify_slack", "tag_prefix" }`

## Required secrets for store uploads
### Google Play (Android)
- Service account JSON with upload rights (store as secret). Referenced by the Android workflow to upload when `android_params.upload` is `true`.
- Track & package set via `android_params`.

### App Store Connect / TestFlight (iOS)
- ASC API key, key ID, issuer ID (secrets).
- Signing cert (.p12) + password (secrets).
- Provisioning profile (.mobileprovision) (secret).
- Used when `ios_params.upload` is `true`. Without secrets, the workflow builds an unsigned IPA artifact only.

## What the workflow does today
- Builds Android AAB (signed) and iOS IPA (unsigned if no signing secrets; signed if provided).
- Always emits IPA (even without signing) for artifact download.
- Pins Firebase iOS SDK to 11.10.0.
- Upload to stores is **off by default** (upload flags false). Set `upload:true` to enable.
- Release notes are stored as an artifact; not pushed to stores.

## Optional enhancements
- Auto-publish release notes to Play/App Store when upload is enabled.
- Enable preflight (format/analyze/tests) by setting `preflight:true`.
- Add notifications (Slack) via `release_params.notify_slack`.

## Quick start
1) Set secrets (Play JSON; ASC key/ID/Issuer; iOS cert+profile).
2) Dispatch: set `upload:true` in `android_params`/`ios_params` when ready to publish.
3) Download artifacts (`android-aab`, `ios-ipa`) for manual store upload if keeping upload off.
