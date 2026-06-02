# v1.3.0 Ship Checklist — Operator 30-min Runbook

**Scannable companion to `RELEASE_OPS.md`. Tick boxes as you go.**

---

## ☐ Step 1 — Back up the keystore password (1 min, CRITICAL)

```bash
pbcopy < ~/.gentlequest/keystore-password
```

Then in 1Password:
- New item → Secure Note → "GentleQuest Android upload keystore v2"
- Paste the password into the value field
- Attach `/Users/lokeshgarg/Desktop/Keystores/gentlequest-upload-v2.jks` as a file
- Save + log out + log back in to verify retrievability

`pbcopy < /dev/null` after to clear clipboard.

---

## ☐ Step 2 — Verify artifact SHAs (30 sec)

```bash
shasum -a 256 ~/.gemini/antigravity/scratch/gentlequest-v130-build/ios.ipa
shasum -a 256 ~/.gemini/antigravity/scratch/gentlequest-v130-build/android.aab
```

Expected:

- iOS IPA: `7643a09b0464d759877b5c2df7a7a5a246a6c33db2f0529abe0ada97768abb14`
- Android AAB: `6f82b56a326161296a7c87dd2567e85daf1170021181fc02d3bdab7d6803b764`

If either doesn't match, **stop** — artifact corrupted. Re-fire antigravity to rebuild.

---

## ☐ Step 3 — iOS upload via Transporter (~5 min + 10-30 min Apple processing)

1. Open Transporter.app
2. Drag `~/.gemini/antigravity/scratch/gentlequest-v130-build/ios.ipa` into the app
3. Sign in with operator Apple ID (handle 2FA)
4. Click DELIVER
5. Wait for "Successfully delivered" — IPA is uploaded
6. Open https://appstoreconnect.apple.com/apps → GentleQuest → TestFlight tab
7. Wait ~10-30 min for Apple processing (status changes from "Processing" to "Ready to Submit")
8. (Optional) Submit for external TestFlight beta first OR proceed to step 5 (App Store submission)

---

## ☐ Step 4 — Android upload via Play Console (~10 min)

1. Open https://play.google.com/console (sign in with Google account)
2. GentleQuest → Production → Create new release
3. **If first time:** enroll Play App Signing (recommended; Google generates app signing key)
4. Upload `~/.gemini/antigravity/scratch/gentlequest-v130-build/android.aab` (drag-drop or file picker)
5. If you enrolled Play App Signing, Google will show the **app signing key fingerprint**. Copy it.
6. Release notes: copy from `app_store_assets/v1.3.0/metadata.md` (release notes section)
7. Click Next → Review and roll out

### ☐ Step 4b — If Play App Signing fingerprint differs from current assetlinks

If Play Console shows a fingerprint different from `63:A5:FC:BD:15:A6:1B:30:AA:17:11:FF:36:A8:74:4E:93:75:EF:07:3E:20:FD:1F:EC:99:57:F3:C0:3E:B3:E4`, fire cc_gq a relay with the new fingerprint. cc_gq will open a PR rotating assetlinks.json + Render auto-deploys.

---

## ☐ Step 5 — Fill review forms (use APP_REVIEW_NOTES.md)

### iOS — App Store Connect

App Store Connect → GentleQuest → 1.3.0 prepare → 
- **App Review Information → Notes:** copy TL;DR + reviewer walkthrough from `app_store_assets/v1.3.0/APP_REVIEW_NOTES.md`
- **Demo Account:** leave blank (app supports anonymous mode)
- **Contact Information:** operator email
- **App Privacy:** matches the Data Handling section of APP_REVIEW_NOTES.md
- Click "Submit for Review"

### Android — Play Console

Play Console → GentleQuest → 
- **Store listing:** copy from `app_store_assets/v1.3.0/metadata.md`
- **Data Safety:** copy from APP_REVIEW_NOTES.md Data Handling section
- **Content Rating:** answer questionnaire — likely Teen (13+) or Mature 17+. App enforces 18+ so either rating is defensible.
- **App content → Government apps:** select "No"
- **App content → Target Audience and content:** **18+ (since code enforces 18+ everywhere)**
- **Reviewer Notes:** copy reviewer walkthrough from APP_REVIEW_NOTES.md
- Click "Send for review"

---

## ☐ Step 6 — Post-submit smoke

### iOS

```bash
# Verify build is in TestFlight (replace YOUR_APP_ID)
xcrun altool --list-apps -u <APPLE_ID> -p <APP_SPECIFIC_PASSWORD>
```

OR check via https://appstoreconnect.apple.com/apps → builds tab.

### Android

Play Console → GentleQuest → Production → check "Latest release" status. Should show "In review" within minutes.

---

## ☐ Step 7 — Backup verification (1 min)

After both submissions are in:

```bash
# Confirm all backups intact
ls -la ~/.gentlequest/
ls -la ~/Documents/Keystores-Backup/
ls -la "/Users/lokeshgarg/Library/Application Support/GentleQuest/"
```

All 3 paths should show the keystore + password files at mode 600. 1Password entry created in Step 1 should also be retrievable.

---

## Total time: ~30 min operator-side + 1-7 days Apple/Google review

## What cc_gq can drive AFTER submission

- If Apple/Google reject for a fixable reason → cc_gq + antigravity reproduce + ship a fix PR
- If they accept → operator releases to public, cc_gq starts v1.4.0 implementation per PRD

---

## See also

- `docs/release/v1.3.0/RELEASE_OPS.md` — comprehensive runbook with recovery procedures
- `app_store_assets/v1.3.0/APP_REVIEW_NOTES.md` — reviewer-facing content to copy into forms
- `app_store_assets/v1.3.0/metadata.md` — store listing copy
- `app_store_assets/v1.3.0/screenshots/` — 6 iPhone screenshots
- `docs/release/v1.3.0/gentlequest-upload-v2.cer` — public cert for fingerprint verification
