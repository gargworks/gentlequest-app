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

## ☐ Step 4 — Android upload via Play Console (~10 min, but see Step 4-PRE first)

### ✅ Step 4-PRE — RESOLVED (Upload Key Reset approved, activates 2026-06-04 05:07 UTC)

**Status (2026-06-02 06:48 UTC):**
- Reset request submitted via cc_gq + Chrome MCP at 2026-06-02 05:00 UTC
- Google approved immediately, sent confirmation email
- **New upload key activates: 2026-06-04 at 05:07 UTC** (48h security cool-down)
- Until activation, Play Console rejects ALL new AAB/APK uploads
- After activation, gentlequest-upload-v2.jks-signed AABs accepted

**Once activated (Jun 4 05:07 UTC):** fire `Android Release (AAB)` workflow on amha — should upload AAB to Play Internal Track as draft.

```bash
gh workflow run "Android Release (AAB)" --repo eidetic-works/ai-mental-health-assistant --ref main \
  -f upload=true -f track=internal -f status=draft
```

Historical pre-reset context (kept below for posterity):

---

### Step 4-PRE (historical) — Resolve Play Console upload-key mismatch (BLOCKING)

**Empirical from GHA run [26797741207](https://github.com/eidetic-works/ai-mental-health-assistant/actions/runs/26797741207) (2026-06-02 04:20 UTC):**

```
The Android App Bundle was signed with the wrong key.
Found:    SHA1: 53:3E:6E:E8:51:10:D2:08:D0:25:AA:96:EC:0E:2E:CF:D3:B9:6C:FD  (new keystore, gentlequest-upload-v2.jks)
Expected: SHA1: BA:4A:0A:4F:9B:EA:D3:1A:8B:AC:FD:4D:F1:26:96:15:2F:51:5F:E9  (LOST original keystore)
```

Root cause: the original keystore (pre-rotation) was registered as the upload key for `app.gentlequest.www` in Play Console. The original keystore password was lost (forcing the rotation that produced gentlequest-upload-v2.jks). Play Console still expects the lost key. **This blocks BOTH GHA upload AND manual Play Console upload of the staged AAB.**

**Resolution — pick ONE of A, B, C based on whether app is published:**

#### A. If app `app.gentlequest.www` has NEVER been published on Play Console (DRAFT or empty listing)

This is fastest path (~5 min operator-side):

1. Play Console → All apps → click `GentleQuest` (or whatever the entry is named)
2. Settings → Advanced settings → "Delete app" (yes, fully delete the draft listing)
3. Re-create the app with the same name + package name `app.gentlequest.www`
4. When prompted for upload key, choose "Use Play App Signing" + upload `docs/release/v1.3.0/gentlequest-upload-v2.cer` as the upload certificate (the .cer in this repo is the public cert for the new keystore)
5. Continue to Step 4 (proceed with the AAB upload as documented)

#### B. If app HAS been published (TestFlight equivalent — internal track / closed testing released)

Must request upload key reset via Play Console support (24-48h Google turnaround):

1. Play Console → App integrity → "Request upload key reset"
2. Fill the form: reason = "Original upload key lost; new keystore generated 2026-06-01"
3. Upload `docs/release/v1.3.0/gentlequest-upload-v2.cer` as the new public certificate
4. Wait for Google email confirmation (typically 24-48h, can be up to 7 days)
5. After approval, continue to Step 4 with the staged AAB

#### C. Change the applicationId (last resort — public bundle ID changes)

If neither A nor B is viable. Updates `applicationId` from `app.gentlequest.www` to a fresh string (e.g., `app.gentlequest.gq`). Requires assetlinks.json rotation + Render redeploy + new Play Console listing. Loses any preconfigured store-listing metadata. Fire cc_gq to drive if needed.

---

### ☐ Step 4 — Actual Play Console upload (after Step 4-PRE resolves)

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

## ⚠ Known iOS GHA Limitation — Provisioning Profile Regeneration Required

**Symptom:** Firing `iOS Release (IPA)` workflow on amha fails with:

```
Error (Xcode): Provisioning profile "GentleQuest-AppStore-Prod" doesn't include
the com.apple.developer.associated-domains entitlement.
```

**Root cause:** The `IOS_MOBILEPROVISION_BASE64` secret on amha (dated 2025-12-30) was created before the Universal Links / AASA work added Associated Domains entitlement to `Runner.entitlements`. The Apple-issued profile is frozen at creation time — it does NOT auto-update when entitlements change in the project.

**Operator-only fix (~5 min):**

1. https://developer.apple.com/account/resources/profiles/list — log in with Apple ID
2. Find profile `GentleQuest-AppStore-Prod` → click → **Edit**
3. Enable capability: **Associated Domains** (toggle ON)
4. Save → **Download** the new `.mobileprovision` file
5. Convert to base64:
   ```bash
   base64 -i ~/Downloads/GentleQuest-AppStore-Prod.mobileprovision -o /tmp/mp.b64
   ```
6. Update GHA secret:
   ```bash
   gh secret set IOS_MOBILEPROVISION_BASE64 --repo eidetic-works/ai-mental-health-assistant < /tmp/mp.b64
   rm /tmp/mp.b64
   ```
7. Re-fire workflow:
   ```bash
   gh workflow run "iOS Release (IPA)" --repo eidetic-works/ai-mental-health-assistant --ref main \
     -f bundle_id=com.gentlequest.app -f upload=true -f environment=beta
   ```

**Alternative — bypass GHA entirely for v1.3.0:**

The locally-staged IPA at `~/.gemini/antigravity/scratch/gentlequest-v130-build/ios.ipa` (57.8 MB, SHA `7643a09b...`) was built via local automatic-signing which generates entitlement-current profiles on-the-fly. Upload via Transporter app (Step 4 above) takes ~5 min and bypasses the stale-profile issue. Use GHA fix above only if you want future iOS releases automated.

---

## See also

- `docs/release/v1.3.0/RELEASE_OPS.md` — comprehensive runbook with recovery procedures
- `app_store_assets/v1.3.0/APP_REVIEW_NOTES.md` — reviewer-facing content to copy into forms
- `app_store_assets/v1.3.0/metadata.md` — store listing copy
- `app_store_assets/v1.3.0/screenshots/` — 6 iPhone screenshots
- `docs/release/v1.3.0/gentlequest-upload-v2.cer` — public cert for fingerprint verification
