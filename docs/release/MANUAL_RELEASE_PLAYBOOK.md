# Manual Release Playbook — GHA-Down Fallback + Edge-Case Nuances

> **Sibling of:** `docs/ONE_BUTTON_RELEASE_GUIDE.md` (happy-path)
> **Use this when:** GitHub Actions billing is exhausted, Apple has closed an in-review train, screenshots need surgical replacement, or the self-hosted Mac runner is the only working CI surface.
> **Source events:** 2026-06-02 → 2026-06-03 v1.3.0 → v1.3.1 ship cycle. Every section below was traversed empirically; quirks are noted with the failure mode that exposed them.

---

## Table of Contents

1. [Decision tree — which lane to use](#1-decision-tree)
2. [iOS — direct App Store Connect API lane](#2-ios-direct-asc-api-lane)
3. [Android — upload-key cron-fire lane](#3-android-cron-fire-lane)
4. [Screenshots — auto-clone, replacement, dedup](#4-screenshots-auto-clone-replacement-dedup)
5. [Self-hosted Mac runner — GHA fallback](#5-self-hosted-mac-runner-fallback)
6. [Chrome MCP — when API hits UI-only fields](#6-chrome-mcp-fallback)
7. [Known gotchas](#7-known-gotchas)
8. [Outstanding gaps to close before next ship](#8-outstanding-gaps)

---

## 1. Decision tree

Before reaching for anything below, try `./scripts/release_mobile.sh public` (the one-button path). Reach for this playbook only when:

| Failure signal | Lane to take |
|---|---|
| `gh workflow run ios-release.yml` returns 402 / "billing" / spending-limit | §2 + §5 (direct API build + self-hosted runner) |
| `xcrun altool --upload-app` returns `90186` train-closed or `90062` shortVersion-too-low | §2.4 (bump version + reupload) |
| ASC version submitted, but screenshots show legacy UI on App Store | §4 (replace iPhone set, retain iPad if no new asset) |
| App is approved but operator wants new metadata before release | Apple released `AFTER_APPROVAL`? Then it's already public; only fixable forward via §2.6 |
| flutterfire CLI missing on the build host | §7 (dSYM upload retroactively + install for next ship) |
| Need a UI-only ASC field (copyright cosmetic, declarations) | §6 (Chrome MCP) |

---

## 2. iOS — direct App Store Connect API lane

### 2.1 Pre-reqs (one-time)

| File | Purpose | Mode |
|---|---|---|
| `~/.appstoreconnect/private_keys/AuthKey_<KEY_ID>.p8` | ASC API key | 600 |
| `~/.appstoreconnect/issuer_id.txt` | Issuer UUID | 600 |

Issuer ID lives at https://appstoreconnect.apple.com/access/api (top of Keys section). Persist once; never recreate.

JWT generation: **use Python `pyjwt`, not Ruby `jwt`**.
`scripts/asc_status_local.sh` defaults to ruby-jwt, which triggers `sudo gem install` and dies in non-interactive shells. The local-fix is a 10-line python script:

```python
import jwt, time
now = int(time.time())
token = jwt.encode(
    {"iss": ISSUER_ID, "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"},
    open(KEY_FILE).read(),
    algorithm="ES256",
    headers={"kid": KEY_ID, "typ": "JWT"},
)
```
PyJWT 2.10+ is already in `/opt/homebrew/bin/python3` — no install needed.

### 2.2 Build the IPA locally

```bash
cd $HOME/gentlequest/ai_buddy_web
./scripts/bump_version.sh patch       # bumps pubspec + creates app_store_assets/<ver>/RELEASE_NOTES.md stub
vi app_store_assets/v1.3.1/RELEASE_NOTES.md
flutter build ipa --release
```

Output IPA: `build/ios/ipa/ai_buddy_web.ipa`. Verify before upload:

```bash
unzip -p build/ios/ipa/ai_buddy_web.ipa Payload/Runner.app/Info.plist | \
  plutil -p - | grep -E "(CFBundleShortVersionString|CFBundleVersion|DTSDKName|DTXcode)"
```

Confirm shortVersion strictly > Apple's last-approved.

### 2.3 Upload via altool

```bash
xcrun altool --upload-app --type ios \
  --file build/ios/ipa/ai_buddy_web.ipa \
  --apiKey <KEY_ID> \
  --apiIssuer $(cat ~/.appstoreconnect/issuer_id.txt) \
  --verbose
```

**Run in background** (`run_in_background: true`). 55MB takes 5-10 min on residential connections; retries handled by altool itself. Watch for `UPLOAD SUCCEEDED with no errors` and the `Delivery UUID` (it doubles as the build resource ID in ASC API).

Network blips are normal — altool retries multipart chunks (`WILL RETRY PART N` lines are noise unless terminal error follows).

### 2.4 Train-closed gotcha (90186 / 90062)

Once a train is approved and waiting for release (state `PENDING_DEVELOPER_RELEASE` or already `READY_FOR_SALE`), Apple **closes the train for new builds**:

```
ERROR ITMS-90186: "The train version '1.3.0' is closed for new build submissions"
ERROR ITMS-90062: "CFBundleShortVersionString must contain a higher version than previously approved [1.3.0]"
```

Fix: bump the patch version (`bump_version.sh patch` → 1.3.0 → 1.3.1), rebuild, re-altool. The previous train's metadata is mirrored on submit (§2.6).

### 2.5 Wait for build processing

After altool, the build sits in TestFlight processing for 5-30 minutes. Don't try to attach it before `processingState=VALID`. Poll:

```python
build_id = "<Delivery UUID from altool>"  # also the ASC build resource ID
GET /v1/builds/{build_id}
# attributes.processingState: VALID = ready; PROCESSING = wait
```

### 2.6 Create App Store Version + attach build + mirror localization

```python
# 1. Create version (Apple auto-mirrors previous version's review detail + screenshots)
POST /v1/appStoreVersions
{
  "data": {
    "type": "appStoreVersions",
    "attributes": {
      "platform": "IOS",
      "versionString": "1.3.1",
      "copyright": " N/A",            # carry forward from prior version
      "releaseType": "AFTER_APPROVAL" # = auto-release on approval; no manual click required
    },
    "relationships": {
      "app": {"data": {"type": "apps", "id": APP_ID}},
      "build": {"data": {"type": "builds", "id": BUILD_ID}}
    }
  }
}
# Returns new version ID. State = PREPARE_FOR_SUBMISSION.
```

```python
# 2. Apple AUTO-CREATES en-US localization. You MUST PATCH it (POST returns 409 DUPLICATE).
loc_id = (GET /v1/appStoreVersions/{V_ID}/appStoreVersionLocalizations).data[0].id
PATCH /v1/appStoreVersionLocalizations/{loc_id}
{
  "data": {
    "type": "appStoreVersionLocalizations",
    "id": loc_id,
    "attributes": {
      "description": "...",          # carry from prior version
      "keywords": "...",             # carry from prior version
      "supportUrl": "https://www.gentlequest.app/",
      "whatsNew": open("app_store_assets/<ver>/RELEASE_NOTES.md").read()
    }
  }
}
```

### 2.7 Screenshots — see §4

### 2.8 Submit for review

```python
# 1. Create review submission
POST /v1/reviewSubmissions
{
  "data": {
    "type": "reviewSubmissions",
    "attributes": {"platform": "IOS"},
    "relationships": {"app": {"data": {"type": "apps", "id": APP_ID}}}
  }
}
# Returns RS_ID

# 2. Add version as item
POST /v1/reviewSubmissionItems
{
  "data": {
    "type": "reviewSubmissionItems",
    "relationships": {
      "reviewSubmission": {"data": {"type": "reviewSubmissions", "id": RS_ID}},
      "appStoreVersion": {"data": {"type": "appStoreVersions", "id": V_ID}}
    }
  }
}

# 3. Fire (IRREVERSIBLE — starts Apple review timer)
PATCH /v1/reviewSubmissions/{RS_ID}
{
  "data": {
    "type": "reviewSubmissions",
    "id": RS_ID,
    "attributes": {"submitted": true}
  }
}
# Verify: GET version → appStoreState should be WAITING_FOR_REVIEW
```

### 2.9 AFTER_APPROVAL auto-release semantics

`releaseType=AFTER_APPROVAL` means **Apple ships the version to the public the moment they approve**. There is no "Release" click. If you want manual gating, set `releaseType=MANUAL` on creation.

On 2026-06-02, v1.3.0 was created with `AFTER_APPROVAL`; Apple approved it overnight and silently shipped it to the App Store before the operator was aware. **Always confirm `releaseType` matches the intended ship cadence.**

---

## 3. Android — cron-fire lane

The Android upload key for `com.gentlequest.app` was reset 2026-06-02 (Google approved 2026-06-02; new key activates **2026-06-04 05:07 UTC**). Until activation, AAB uploads fail.

To ship the moment activation occurs, `scripts/release_android_at_activation.sh` is wired via system cron + CronCreate:

```cron
# Crontab fires the AAB upload at the activation moment.
38 10 4 6 * $HOME/ai-mvp-backend/scripts/release_android_at_activation.sh
```
(10:38 IST 2026-06-04 = 05:08 UTC, 1 min after key activates.)

Script behaviour (from memory `project_v130_android_upload_key_activates.md`):
- Polls Play Console internal API until upload key is accepted.
- Triggers the `android-release.yml` GHA workflow OR falls through to local `bundle release` + `fastlane supply` if GHA still down.
- Posts result to Telegram via brain_telegram.

**Verification (after activation):** check Play Console → Internal Track for the new AAB; the build number is bumped via `bump_version.sh` parity with iOS.

---

## 4. Screenshots — auto-clone, replacement, dedup

### 4.1 Apple auto-clones from previous version

When you POST `/v1/appStoreVersions`, Apple **automatically copies all screenshot sets + screenshots** from the immediately-prior version. The new version's screenshot sets are pre-populated:

| Display type | Internal name | Dimensions (px) |
|---|---|---|
| iPhone 6.7" | `APP_IPHONE_67` | 1290 × 2796 |
| iPad Pro 12.9" (3rd gen+) | `APP_IPAD_PRO_3GEN_129` | 2048 × 2732 |

The auto-clone race condition: if you list `appScreenshots` immediately after creating the version, you may see partial population. **Wait ~30s then re-query** before deciding the sets are empty.

### 4.2 Replacing a set (e.g., redesigned iPhone screenshots)

```python
# 1. List current screenshots in the set
GET /v1/appScreenshotSets/{SET_ID}/appScreenshots
# Note each id

# 2. DELETE each
for sid in existing_ids:
    DELETE /v1/appScreenshots/{sid}

# 3. Upload new files
for fname in sorted(local_pngs):
    content = open(path, "rb").read()
    md5 = hashlib.md5(content).hexdigest()

    # 3a. Reserve slot — Apple returns uploadOperations[] with presigned URLs
    res = POST /v1/appScreenshots {
        "data": {
            "type": "appScreenshots",
            "attributes": {"fileName": fname, "fileSize": len(content)},
            "relationships": {"appScreenshotSet": {"data": {"type": "appScreenshotSets", "id": SET_ID}}}
        }
    }

    # 3b. PUT each chunk (small PNGs = 1 chunk, large ones may be multi-part)
    for op in res.data.attributes.uploadOperations:
        PUT op.url with body=content[op.offset:op.offset+op.length], headers=op.requestHeaders

    # 3c. Finalize
    PATCH /v1/appScreenshots/{res.data.id} {
        "data": {
            "type": "appScreenshots",
            "id": <id>,
            "attributes": {"uploaded": True, "sourceFileChecksum": md5}
        }
    }
```

### 4.3 Dedup after race

Apple's auto-clone occasionally re-fires *after* your DELETE+upload, leading to duplicate fileNames in the set. After uploading, list the set and dedup:

```python
GET /v1/appScreenshotSets/{SET_ID}/appScreenshots
groups = defaultdict(list)
for s in result:
    groups[s.attributes.fileName].append(s)
for name, group in groups.items():
    if len(group) > 1:
        group.sort(key=lambda x: x.attributes.createdDate, reverse=True)
        for dup in group[1:]:
            DELETE /v1/appScreenshots/{dup.id}
```

### 4.4 Verify checksums post-upload

```python
expected_md5 = {fname: hashlib.md5(open(path, "rb").read()).hexdigest() for fname, path in local_files}
shots = GET /v1/appScreenshotSets/{SET_ID}/appScreenshots
for s in shots:
    assert s.attributes.sourceFileChecksum == expected_md5[s.attributes.fileName], \
        f"checksum drift on {s.attributes.fileName}"
```

If checksums match expected, the visible App Store screenshots are exactly the local PNGs.

### 4.5 Asset format notes

- Local iPhone 6.7" screenshots in `app_store_assets/v1.3.0/screenshots/*.png` are correctly sized 1290×2796.
- No iPad-sized renders exist locally as of 2026-06-03 — iPad set falls back to whatever Apple auto-clones from the prior version. To refresh, render 2048×2732 PNGs in `app_store_assets/<ver>/screenshots_ipad/` first.
- iPad screenshots are second-order; most users see iPhone. Don't block ship on iPad refresh.

---

## 5. Self-hosted Mac runner fallback

When GHA org billing is exhausted, the Mac at `$HOME/actions-runner-new` can act as a personal CI surface.

### 5.1 Re-registration to a different repo

The runner was originally bound to `eidetic-works/mcp-server-nucleus`. To swap to `eidetic-works/ai-mental-health-assistant` (or similar):

```bash
cd $HOME/actions-runner-new
./config.sh remove --token <removal-token-from-prev-repo-settings>
# Then register against new repo:
./config.sh \
  --url https://github.com/eidetic-works/ai-mental-health-assistant \
  --token <registration-token-from-new-repo-settings> \
  --name mac-self-hosted-arm64-xcode26 \
  --labels self-hosted,macOS,ARM64,xcode-26 \
  --work _work \
  --unattended
./run.sh &  # leave running; survives via launchd if configured
```

Registration tokens are at: GitHub repo → Settings → Actions → Runners → New self-hosted → copy token.

### 5.2 Gotchas the runner ran into 2026-06-03

| Gotcha | Symptom | Fix |
|---|---|---|
| Keychain locked | xcodebuild signing fails | `security unlock-keychain login.keychain` before run |
| Bash profile stripped | `pod` not found in PATH | Ensure `/opt/homebrew/bin` is in `$PATH` in `.actions-runner.env` |
| Wrong Xcode active | Build fails at SDK resolve | `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer` |
| Stale Pods | `pod install` fails on new dependency | `pod repo update` once after disk cleanup |
| GHA workflow timeout while runner alive | `TaskOrchestrationJobNotFoundException` after ~90 min | Workflow timeout < runner active time; raise `timeout-minutes` in workflow OR pivot to local build |

### 5.3 When the runner itself isn't enough

If self-hosted runner is alive but the workflow times out (as happened 2026-06-03), abort GHA entirely and do the build locally with `flutter build ipa --release` then §2.3 altool. This bypasses GHA orchestration completely.

### 5.4 Runner is a free-tier escape hatch — don't depend on it daily

The runner adds Mac-up-time + power-cost. Use it for emergency ships. Restore GHA billing as the primary path.

---

## 6. Chrome MCP fallback

For UI-only ASC fields not exposed by API:
- **Copyright field**: ASC web UI under App Information. Can be triple-clicked + edited via Chrome MCP.
- **Screenshot Media Manager**: opaque CSS-in-JS classes (`Box-sc-18eybku-0...`); Chrome MCP cannot drive the drag-drop. **Operator must manually drag-drop from Finder** if API upload is failing.
- **Apple "Newer Build Available" dialog**: appears if Apple indexes a build after submission started. Harmless — click Submit anyway or wait for indexing.

Chrome MCP is the second-line tool when (a) the field isn't in ASC API, or (b) the field exists but isn't editable for the current version state.

---

## 7. Known gotchas

### 7.1 Spaces in SSD path break CocoaPods Ruby

If `Podfile` resolves under `/Volumes/Samsung SSD 990 PRO 2TB Media/...`, `pod install` warns:
```
ruby: No such file or directory -- /path/with spaces/ruby
```
The warning is *non-fatal*; pods still install and build proceeds. To eliminate, move the working tree off the spaces-bearing volume (use the internal SSD).

### 7.2 `flutterfire` CLI not installed → dSYM upload silently skipped

iOS build phase `[firebase_crashlytics] Upload Crashlytics symbols` shells out to:
```
flutterfire upload-crashlytics-symbols --upload-symbols-script-path=$PATH_TO_CRASHLYTICS_UPLOAD_SCRIPT ...
```
If `flutterfire` is missing OR `firebase login` is empty, the script exits non-zero and the build phase logs a warning but **build succeeds without uploading symbols**. Crashlytics will then show obfuscated frames for any v1.3.1 crashes.

Two fixes:
1. **Retroactive (no new build):** invoke the Pod's `upload-symbols` binary directly:
   ```bash
   $HOME/gentlequest/ai_buddy_web/ios/Pods/FirebaseCrashlytics/run \
     -gsp $HOME/gentlequest/ai_buddy_web/ios/Runner/GoogleService-Info.plist \
     -p ios \
     $HOME/gentlequest/ai_buddy_web/build/ios/archive/Runner.xcarchive/dSYMs
   ```
2. **Forward-prevent:** `dart pub global activate flutterfire_cli` + `firebase login` once.

### 7.3 `gh pr merge` leaks real identity

Per `feedback_gh_pr_merge_squash_for_pseudonymity.md` HARD RULE: always `gh pr merge --squash` (never `--merge`) on eidetic-works repos. `--merge` leaks `mailforlkgarg@gmail.com` in AUTHOR field even with GitHub email-privacy on.

### 7.4 `git gc` without disk headroom

Per `feedback_git_gc_needs_repo_size_headroom.md`: never run `git gc`/`git repack` when free disk < pack-size × 1.5. Repack writes `tmp_pack_*` proportional to full pack; failure orphans 700MB+ temp files in `.git/objects/pack/`.

### 7.5 `du -sh` lies about cross-volume symlinks

Per `feedback_du_through_symlinks_over_reports.md`: use `du -sxh` (with `-x`) for footprint surveys. Bare `du -sh` walks symlinks and over-counts.

---

## 8. Outstanding gaps to close before next ship

| Gap | Owner | Track |
|---|---|---|
| dSYM upload for v1.3.1 build 26060318 (currently in Apple review) | cc-main | §7.2 retroactive path; verify in Firebase Console → Crashlytics → dSYMs tab |
| Install `flutterfire` + `firebase login` on this Mac | cc-main / agy | One-time; durable across all future builds |
| Event taxonomy documentation (~30 callsites, no central registry) | agy (primary — authored recent commits) | Author `docs/analytics/EVENT_TAXONOMY.md` |
| Backend `/api/analytics/log` verification (does it exist on Render? where does data persist?) | agy + cc-main | Inspect Render service routing + persistence layer |
| Privacy disclosure alignment (ASC App Privacy form + Privacy Policy + v1.3.1 release-notes claim) | operator-strategic + agy support | Schedule pre-v1.4.0 |
| iPad redesigned screenshots (2048×2732) | render rig owner | Defer; iPad set falls back to legacy auto-clone |
| Texas SB 2420 + Play Age Signals API v0.0.3 integration | cc-main / agy | v1.4.0 candidate; enforcement window mid-Jun → mid-Jul 2026 |

---

## Appendix A — Durable Python helpers

Canonical implementations of §2-§4 patterns. Run from repo root.

- `scripts/asc_screenshot_swap.py` — replace a screenshot set + dedup race + checksum verify (§4)
  ```bash
  python3 scripts/asc_screenshot_swap.py \
      --version-id <APP_STORE_VERSION_UUID> \
      --set iphone67 \
      --src app_store_assets/v1.3.0/screenshots
  ```
- `scripts/asc_dedupe.py` — dedupe screenshots by fileName, keep newest (§4.3)
  ```bash
  python3 scripts/asc_dedupe.py --version-id <VERSION_UUID> --set iphone67 [--dry-run]
  ```
- `scripts/asc_submit_for_review.py` — 3-step submit-for-review, irreversible (§2.8)
  ```bash
  python3 scripts/asc_submit_for_review.py --app-id 6756537464 --version-id <VERSION_UUID>
  ```

Each script:
- Reads `~/.appstoreconnect/issuer_id.txt` + `~/.appstoreconnect/private_keys/AuthKey_<KEY_ID>.p8`
- Defaults `ASC_KEY_ID=L6BQY5DFKM`; override via env var if rotated
- Uses PyJWT (no sudo install required); no Ruby dependency

## Appendix B — Glossary

- **ASC** — App Store Connect (Apple's developer portal + API).
- **altool** — Apple's IPA upload utility (`xcrun altool`).
- **PREPARE_FOR_SUBMISSION → WAITING_FOR_REVIEW → IN_REVIEW → PENDING_DEVELOPER_RELEASE → READY_FOR_SALE** — ASC version state machine. With `AFTER_APPROVAL`, the machine jumps directly to `READY_FOR_SALE` post-approval.
- **Train** — Apple's term for a versionString family. A train "closes" once approved; new builds need a higher versionString.
- **dSYM** — Debug Symbols. Required for Crashlytics to symbolicate stack traces.
- **GHA** — GitHub Actions (the CI surface this playbook substitutes when down).

---

**Last refresh:** 2026-06-03. Edit dates here whenever you traverse a section and find drift.
