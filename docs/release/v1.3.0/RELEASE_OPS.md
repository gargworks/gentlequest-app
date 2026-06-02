# v1.3.0 Release Ops — End-to-End Runbook + Keystore Rotation Audit Trail

**Status:** Both mobile artifacts staged + verified end-to-end. Operator-side App Store Connect + Play Console upload remains.

**Last updated:** 2026-06-02 by cc_gq lane execution

---

## TL;DR

- iOS IPA + Android AAB are built, staged, and independently SHA-verified.
- Android upload keystore was **rotated** on 2026-06-01 because the prior keystore password (set 2025-11-30) was lost. Live `assetlinks.json` updated to new fingerprint.
- New keystore lives at `/Users/lokeshgarg/Desktop/Keystores/gentlequest-upload-v2.jks` with password at `~/.gentlequest/keystore-password` (mode 600).
- Triple-redundant backup copies in 3 outside-repo locations + encrypted tarball.
- This doc + the public certificate (`.cer`) are the in-repo audit trail.

---

## 1. Mobile artifacts (staged, ready for upload)

### iOS IPA

| Field | Value |
|-------|-------|
| Path | `~/.gemini/antigravity/scratch/gentlequest-v130-build/ios.ipa` |
| Size | 57.8 MB (57,839,730 bytes) |
| SHA-256 | `7643a09b0464d759877b5c2df7a7a5a246a6c33db2f0529abe0ada97768abb14` |
| CFBundleIdentifier | `com.gentlequest.app` |
| DEVELOPMENT_TEAM | `828Q2S3G4Q` |
| Source ref | nucleus `feat/onboarding-10min-activation-walkthrough` @ `09bf2701` |

### Android AAB

| Field | Value |
|-------|-------|
| Path | `~/.gemini/antigravity/scratch/gentlequest-v130-build/android.aab` |
| Size | 87.1 MB (87,150,649 bytes) |
| SHA-256 | `6f82b56a326161296a7c87dd2567e85daf1170021181fc02d3bdab7d6803b764` |
| applicationId | `app.gentlequest.www` |
| Signing fingerprint (SHA-256) | `63:A5:FC:BD:15:A6:1B:30:AA:17:11:FF:36:A8:74:4E:93:75:EF:07:3E:20:FD:1F:EC:99:57:F3:C0:3E:B3:E4` |
| Signing fingerprint (SHA-1) | `53:3E:6E:E8:51:10:D2:08:D0:25:AA:96:EC:0E:2E:CF:D3:B9:6C:FD` |
| Source ref | nucleus `feat/onboarding-10min-activation-walkthrough` @ `09bf2701` (post local dup-removal fix) |

---

## 2. Keystore rotation incident — 2026-06-01

### Why

The prior upload keystore at `/Users/lokeshgarg/Desktop/Keystores/gentlequest-upload.jks` (generated Nov 30 2025) had its password lost. No recovery via 25+ common-password trials, Apple Keychain search, dotfile scan, or other local `.jks` files (4 candidates all failed unlock).

### Recovery taken

cc_gq generated a fresh upload keystore (RSA-4096, 25-year validity, pseudonymous DN) with a strong random 32-character base64url password. Updated `assetlinks.json` on `gentlequest.app` to the new fingerprint via PR #110 (squash `4c14b559`). Rebuilt AAB with new keystore via antigravity.

### New keystore details

```
Owner: CN=eidetic-works, OU=GentleQuest, O=Eidetic Works, L=Unknown, ST=Unknown, C=US
Issuer: (self-signed)
Valid from: Mon Jun 01 20:16:48 IST 2026 until: Fri May 26 20:16:48 IST 2051
Serial: ba7d72aeee46ed95
Algorithm: SHA384withRSA, 4096-bit RSA
SHA-256: 63:A5:FC:BD:15:A6:1B:30:AA:17:11:FF:36:A8:74:4E:93:75:EF:07:3E:20:FD:1F:EC:99:57:F3:C0:3E:B3:E4
SHA-1:   53:3E:6E:E8:51:10:D2:08:D0:25:AA:96:EC:0E:2E:CF:D3:B9:6C:FD
```

Public certificate committed alongside this doc as `gentlequest-upload-v2.cer` (DER format). View with:

```
keytool -printcert -file docs/release/v1.3.0/gentlequest-upload-v2.cer
```

### Old (now-orphaned) keystore

Old keystore file remains on disk at `/Users/lokeshgarg/Desktop/Keystores/gentlequest-upload.jks` (2760 bytes, Nov 30 2025). Password unknown. Old fingerprint:

```
32:4E:83:98:B3:AC:85:C8:FF:FE:EB:91:2F:D2:1F:A2:65:99:32:18:51:AE:0C:C2:34:80:CD:74:33:A5:77:59
```

If operator ever recovers the password, the old keystore can be used again — but `assetlinks.json` would need to be rotated back. Recommend leaving the old keystore in place for forensic continuity (don't delete).

---

## 3. Keystore + password backup locations

**🔐 CRITICAL: If the password file is lost, the keystore is unrecoverable. Back this up to 1Password / encrypted-disk-image / iCloud Keychain immediately.**

### Outside-repo (3 redundant copies + encrypted tarball)

| Location | Contents | Mode |
|----------|----------|------|
| `~/.gentlequest/gentlequest-upload-v2.jks` | keystore | 600 |
| `~/.gentlequest/keystore-password` | password | 600 |
| `~/Documents/Keystores-Backup/gentlequest-upload-v2.jks` | keystore copy | 600 |
| `~/Documents/Keystores-Backup/gentlequest-upload-v2.password` | password copy | 600 |
| `~/Library/Application Support/GentleQuest/gentlequest-upload-v2.jks` | keystore copy | 600 |
| `~/Library/Application Support/GentleQuest/keystore-password` | password copy | 600 |
| `~/Documents/Keystores-Backup/gentlequest-keystore-backup-20260602.tar.gz` | encrypted tarball of both | 600 |
| `/Users/lokeshgarg/Desktop/Keystores/gentlequest-upload-v2.jks` | primary (referenced by `key.properties`) | 600 |

### In-repo (this PR)

- This document — operational audit trail
- `docs/release/v1.3.0/gentlequest-upload-v2.cer` — public certificate (no secret material; safe to commit)

### Operator's responsibility

1. Open `~/.gentlequest/keystore-password` in Terminal: `cat ~/.gentlequest/keystore-password` (do not screenshot)
2. Paste into 1Password under "GentleQuest Android upload keystore v2" entry, with the keystore file as an attachment
3. Verify retrievability — log out + log back into 1Password, confirm both visible

---

## 4. Upload runbook

### iOS — App Store Connect

**Option A — Transporter app (recommended, GUI):**
1. Open Transporter.app
2. Drag `~/.gemini/antigravity/scratch/gentlequest-v130-build/ios.ipa` into the app
3. Sign in with operator Apple ID (2FA prompt)
4. Click DELIVER
5. Wait for Apple processing (~10-30 min)

**Option B — `xcrun altool` (CLI):**

```bash
APPLE_ID="<operator-email>"
APP_PASSWORD="<app-specific-password-from-appleid.apple.com>"
xcrun altool --upload-app \
  -f ~/.gemini/antigravity/scratch/gentlequest-v130-build/ios.ipa \
  -t ios \
  -u "$APPLE_ID" -p "$APP_PASSWORD"
```

### Android — Play Console (web only)

1. Open https://play.google.com/console
2. Select GentleQuest → Production track → Create new release
3. Upload `~/.gemini/antigravity/scratch/gentlequest-v130-build/android.aab`
4. **If prompted to enroll in Play App Signing**: enroll (Google recommends; we keep our upload key for AAB signing, Google generates a separate app-signing key for end users). **Note:** If you enroll, the assetlinks fingerprint may need a follow-up rotation to match Google's app-signing key — Play Console will show you that fingerprint after enrollment.
5. Fill Release Notes (copy from `app_store_assets/v1.3.0/metadata.md`)
6. Fill Data Safety + Content Rating + Pricing forms (copy from `app_store_assets/v1.3.0/APP_REVIEW_NOTES.md`)
7. Save + Review + Submit

### Both stores — review notes

Source of truth: `app_store_assets/v1.3.0/APP_REVIEW_NOTES.md` (PR #109, on amha main). Copy the "TL;DR for reviewers" + "Reviewer walkthrough" sections into:

- App Store Connect → App Information → Review Notes
- Play Console → App content → Target Audience and content / Government apps → Notes for reviewers

---

## 5. Recovery procedures

### If the keystore password file is lost AGAIN

1. cc_gq cannot recover from cryptographic randomness; requires another rotation
2. Run the rotation procedure: `scripts/release/rotate-android-keystore.sh` (TODO: codify the procedure from the 2026-06-01 cascade into a script for next time)
3. Update `assetlinks.json` with new fingerprint, push to amha, deploy
4. Rebuild AAB with new keystore
5. After Play Console release: contact Google Support to update upload key (Google has a 1-time upload key rotation process if locked out)

### If the AAB is rejected for fingerprint mismatch

1. Check what fingerprint Play Console expects (Settings → App integrity → Upload key certificate fingerprint)
2. Compare to live `assetlinks.json` on `gentlequest.app/.well-known/assetlinks.json`
3. Update `assetlinks.json` to whichever fingerprint Play Console reports as expected
4. PR → cc_gq self-merge on amha → Render auto-deploys gentlequest-landing
5. Retry submission

### If iOS bundle ID / Team ID mismatch

1. Verify on Apple Developer portal: https://developer.apple.com/account/resources/identifiers/list
2. Compare to `ai_buddy_web/ios/Runner/Info.plist` CFBundleIdentifier
3. Compare to live `gentlequest.app/.well-known/apple-app-site-association`
4. All three must match: `828Q2S3G4Q.com.gentlequest.app`

---

## 6. Source-of-truth references

- **Pre-submission audit:** nucleus `feat/onboarding-10min-activation-walkthrough` @ `app_store_assets/v1.3.0/PRESUBMISSION_AUDIT.md`
- **Review notes for store forms:** amha main @ `app_store_assets/v1.3.0/APP_REVIEW_NOTES.md`
- **v1.4.0 PRD:** amha main @ `docs/v1.4.0/PRD_DRAFT.md`
- **v1.4.0 compliance matrix:** amha main @ `docs/v1.4.0/COMPLIANCE_MATRIX.md`
- **Live AASA:** https://gentlequest.app/.well-known/apple-app-site-association
- **Live assetlinks:** https://gentlequest.app/.well-known/assetlinks.json
- **App on Render (web):** https://app.gentlequest.app (web_service GentleQuest, srv-d2r3i1fdiees73dqtov0)
- **Landing on Render (marketing):** https://gentlequest.app (static_site gentlequest-landing, srv-d5fjme7gi27c73dse3qg)

---

## 7. Audit trail of v1.3.0 cascade (cc_gq + antigravity + windsurf)

Chronological summary of the work that landed v1.3.0:

| Date | Action |
|------|--------|
| Various pre-2026-05 | Initial v1.3.0 audit by windsurf — produced PRESUBMISSION_AUDIT.md |
| 2026-05-31 | Honesty audit BLOCKER + MEDIUM clearance: PRs #92-#97 (audit §1-§10) + PR #98 (post-rename sweep) + PR #99 (docs hygiene) + PR #100 (web bundle rebuild) + PR #105/#106 (web compliance port) on amha + PR #428 on nucleus + PR #107/#108/#109 (v1.4.0 PRD + Compliance Matrix + App Review Notes) on amha |
| 2026-06-01 | Universal Links (assetlinks + AASA) initial setup by antigravity + verified live by cc_gq |
| 2026-06-01 | Path B keystore rotation: PR #110 (new fingerprint) — old keystore lost, new one generated, assetlinks rotated, AAB rebuilt |
| 2026-06-02 | This release-ops document (PR forthcoming) |
