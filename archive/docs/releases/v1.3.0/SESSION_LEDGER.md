# v1.3.0 Mobile Ship — Session Ledger (2026-06-02)

**Single source of truth** for what was done, where the ship state is, and what's next.

---

## TL;DR ship state (as of 2026-06-02 ~13:00 UTC)

| Surface | State | Next action |
|---------|-------|-------------|
| **iOS TestFlight** | ✅ LIVE — build 1.3.0 (75) Complete, Internal group | Operator can install via TestFlight app |
| **iOS App Store** | 🔄 **UNDER APPLE REVIEW** — submitted 10:37 UTC | Wait 24-48h for Apple email |
| **Android Play (any track)** | ⏳ Blocked until 2026-06-04 05:07 UTC | After activation: `./scripts/release_mobile.sh public` |
| **Android Play Production** | ⏳ Same as above | Same |

---

## Operator's full action list (right now → forward)

### Right now (anytime today)
- [ ] Verify v1.3.0 actual review state via `./scripts/asc_status_local.sh` (needs Issuer ID once — grab from https://appstoreconnect.apple.com/access/api top of Keys section)
- [ ] (Optional) Back up `~/.gentlequest/keystore-password` to 1Password

### When Apple email arrives (24-48h)
- [ ] If approved → already configured to auto-release; verify via TestFlight tab in ASC
- [ ] If rejected → read email, fix, fire `release_mobile.sh public` again

### 2026-06-04 05:07 UTC (Android upload key activates)
- [ ] Run `./scripts/release_mobile.sh public` from amha repo root → AAB uploads to Play Production track as draft → Google review 1-7 days

### After both stores approve
- [ ] Update gentlequest.app landing page with App Store + Play Store badges
- [ ] Public launch announcement (per ADR-028 / distribution-officer)

---

## 19 PRs landed this session (#111-#129, all squash-merged)

| PR | Title | Why |
|----|-------|-----|
| #111 | RELEASE_OPS runbook + public upload-keystore cert | Documentation foundation |
| #112 | Tight 7-step operator ship checklist | Operator runbook |
| #113 | Port nucleus PR #428 audit-clearance mobile subset to amha main | iOS/Android Info.plist + AndroidManifest stripped of unused permissions |
| #114 | iOS GHA provisioning profile remediation steps in CHECKLIST | Initial docs (later superseded by actual fix in #118) |
| #115 | Strip `integration_test` from pubspec in Android Release workflow | Fixed AAB build failure |
| #116 | Play Console upload-key mismatch blocker + resolution paths | Docs |
| #117 | Add Play Console App Signing key fingerprint to assetlinks.json | Android App Links work for Play Store users |
| #118 | iOS device family 1→1,2 + GHA `macos-26-arm64` for iOS 26 SDK | Apple deadline compliance + iPad |
| #119 | iOS runner `macos-26-arm64` → `macos-26` (x64) for capacity | arm64 runner queued 43+ min |
| #120 | Android reset RESOLVED + iOS shipped to TestFlight | Status doc |
| #121 | One-button now submits iOS to App Store Review | reviewSubmissions API extension |
| #122 | iOS-submit: preReleaseVersion + new reviewSubmissions API | Fix wrong version field + deprecated API |
| #123 | iOS-submit: use builds/{id}/preReleaseVersion endpoint | Fix relationship data |
| #124 | iOS-submit: rename pre-submission version in-place | Apple allows only ONE pre-submission version |
| #125 | iOS-submit: nested query + diagnostics | Better diagnostics |
| #126 | Zero-touch v1.3.1+ release automation | bump_version.sh + auto-load notes + whatsNew patch |
| #127 | Full localization copy from READY_FOR_SALE source | Apple doesn't auto-inherit metadata via API |
| #128 | Read-only ASC Status workflow | Verification via GHA (currently blocked by org billing) |
| #129 | Local ASC status script | Verification anytime via operator's local .p8 |

---

## How v1.3.1+ ships in seconds (operator-attended time)

```bash
# From amha repo root:
./scripts/bump_version.sh patch              # 2 sec — pubspec 1.3.0 → 1.3.1 + RELEASE_NOTES.md stub
vi app_store_assets/v1.3.1/RELEASE_NOTES.md  # type real notes
git commit -am "release: v1.3.1"             # 5 sec
gh pr create + merge                         # 10 sec
./scripts/release_mobile.sh public           # 1 sec — walks away (~12 min pipeline + 24-48h Apple)
```

Operator-attended: **~30 seconds**. Pipeline: ~12 min. Apple Review: 24-48h.

---

## Known remaining gaps (will surface when fired)

1. **PR #127's full localization copy is UNTESTED** — exercised on first v1.3.1 fire. May surface another Apple API gate.
2. **App Privacy / Age Rating not in our API copy** — those are App-level on ASC. May need separate workflow if Apple flags missing on v1.3.1.
3. **eidetic-works GHA billing** — currently EXHAUSTED. iOS Release workflow requires macos-26 (pricey). Top up org budget before next fire.
4. **Phone +91-2220851185 in App Review Information** — operator's personal number visible to Apple Reviewer.

---

## Persistent memory written

- `~/.claude/projects/-Users-lokeshgarg-ai-mvp-backend/memory/project_v131_zero_touch_release.md`
- `~/.claude/projects/-Users-lokeshgarg-ai-mvp-backend/memory/project_v130_android_upload_key_activates.md`

Future sessions will read these via auto-memory and avoid rediscovering.
