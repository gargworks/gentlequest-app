# Operator steps: Add YouTube API tester (1 min)

## Goal
Add `admin@gentlequest.app` as a test user on the Nucleus OAuth consent screen so the YouTube upload script can authenticate.

## Steps

1. Open: https://console.cloud.google.com/apis/credentials/consent
   - Make sure project = `nucleus-training-mailforlkgarg` (top dropdown)

2. Scroll to **"Test users"** section

3. Click **"+ ADD USERS"**

4. Enter: `admin@gentlequest.app`

5. Click **SAVE**

6. Tell me "done" — I'll retry the upload script immediately.

## Why
The OAuth app is in "testing" mode. Only listed test users can grant consent.
Once added, the upload script (`marketing/shorts/upload_youtube.py`) will open
a browser, you log in with admin@gentlequest.app, click Allow, and all 6
shorts upload automatically as unlisted. The token saves for future runs.
