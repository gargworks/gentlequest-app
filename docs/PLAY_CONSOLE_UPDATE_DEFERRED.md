# Play Console Listing Update — DEFERRED to next Android release

**Status:** Deferred | **Date:** 2026-06-22 | **Owner:** operator (manual login)

## Why deferred

Chrome MCP browser session could not complete Google OAuth sign-in to Play Console
on 2026-06-22. The login page loaded but Google's anti-bot protections blocked
automated form submission. Play Console has no API for listing edits without a
service account + OAuth 2.0 setup (separate manual step).

## What needs to happen (next Android release)

1. **Operator logs into Play Console manually** (https://play.google.com/console)
2. Update the main store listing using the content in
   [`docs/APP_STORE_LISTING.md`](./APP_STORE_LISTING.md):
   - App title, short desc, full description
   - Store graphics (icon 512x512, feature graphic 1024x500, screenshots)
   - Content rating questionnaire
   - Privacy policy URL + data safety form
3. Upload the signed AAB from `release_artifacts/android.aab` to the internal
   testing track
4. Configure pricing & distribution (free, global, 16+)

## Alternative: API-based update (future)

If we want to automate this in future releases:
1. Create a Google Cloud service account
2. Enable Google Play Android Developer API
3. Link the service account in Play Console → Setup → API access
4. Use `googleapis` npm package or `google-api-python-client` to push listing
   edits programmatically

Reference: `docs/GOOGLE_PLAY_API_ACCESS_GUIDE.md`

## Source content

All listing copy, keywords, graphics checklist, and release notes template are
already staged in [`docs/APP_STORE_LISTING.md`](./APP_STORE_LISTING.md). No
content authoring needed — just the manual upload step.
