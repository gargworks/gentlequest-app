---
description: Run the local One-Click Release script (Interactive)
---

# Local One-Click Release Protocol

This workflow runs the local interactive release script for GentleQuest. 
Unlike the GitHub Actions version, this script executes on your local machine and requires local dependencies (Flutter, Java, etc.).

**Prerequisites:**
- Flutter SDK installed and on PATH
- Java (JDK) installed (for Android)
- `gh` CLI installed and authenticated
- **Signing Keys:** You must have `upload-keystore.jks` and a valid `key.properties` (or environment variables) for production-ready builds.

## Usage

Run the local interactive script:

```bash
./scripts/one_click_release.sh
```

### Flow:
1. **Selection:** You will be prompted to choose 1 (Beta), 2 (Production), or 3 (Hotfix).
2. **Analysis:** The script runs `flutter analyze` and `flutter test`.
3. **Trigger:** It attempts to trigger the GitHub workflow first. 
4. **Fallback:** If triggering fails (or if requested), it falls back to a **local build**:
   - `flutter build appbundle` (Android)
   - `flutter build ios --no-codesign` (iOS)

## Troubleshooting
- **Missing Keys:** If you see "No signing credentials found", the build will use debug signing.
- **iOS Signing:** Local builds for iOS are `--no-codesign`. You must sign them manually using Xcode or Transporter to upload to TestFlight.
- **Interactivity:** This script requires human input. Agents should clarify this to the user.
