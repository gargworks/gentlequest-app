# Google Play Console API Access: The Complete 2024-2025 Guide

> **TL;DR:** Google removed the "API Access" page from Play Console. You now set up API access through Google Cloud Console and invite the service account to Play Console via "Users and permissions."

---

## 📋 Table of Contents

1. [The Problem: Missing "API Access" Menu](#the-problem-missing-api-access-menu)
2. [Why This Happens](#why-this-happens)
3. [The New Process (Step-by-Step)](#the-new-process-step-by-step)
4. [Common Blockers & Solutions](#common-blockers--solutions)
5. [Troubleshooting](#troubleshooting)
6. [Fastlane & CI/CD Integration](#fastlane--cicd-integration)
7. [Security Best Practices](#security-best-practices)

---

## The Problem: Missing "API Access" Menu

If you're reading this, you've probably experienced one of these frustrating scenarios:

### What You Expected
Following every tutorial on the internet:
1. Go to **Play Console** → **Setup** → **API Access**
2. Link your Google Cloud Project
3. Create a service account
4. Done!

### What Actually Happens
- ❌ There is **no "Setup" menu** in the sidebar
- ❌ There is **no "API Access" option** anywhere
- ❌ Navigating directly to `/api-access` URL redirects to the Home page
- ❌ Every tutorial and documentation is completely outdated

### The Frustrating Part
- Google's own documentation still references the old UI
- Third-party tools (Fastlane, RevenueCat, Codemagic) still show outdated screenshots
- Searching for help returns results from 2020-2023 that no longer apply

---

## Why This Happens

### Google Changed the Process (Silently)

In 2024-2025, Google made significant changes to how API access is managed:

1. **The "API Access" page was removed** from Play Console for most accounts
2. **API management moved to Google Cloud Console** entirely
3. **The old "link project" workflow was deprecated** in favor of service account invitations
4. **Organization verification** may block some UI elements from appearing

### Key Insight

> 🎯 **The API access is NOT managed in Play Console anymore. It's managed entirely through Google Cloud Console + Play Console's "Users and permissions."**

---

## The New Process (Step-by-Step)

### Prerequisites

- A Google Play Developer account (enrolled)
- Access to Google Cloud Console (same Google account)
- An app published or in draft on Play Console

---

### Step 1: Create or Select a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click the project selector dropdown at the top
3. Either:
   - **Use an existing project** (recommended if you already have one for your app)
   - **Create a new project**: Click "New Project" and give it a name like `my-app-play-store`

> 💡 **Tip:** If your app uses Firebase, you likely already have a project with the same name.

---

### Step 2: Enable the Google Play Android Developer API

This step is **CRITICAL** - many people skip this and get 403 errors later.

1. In Google Cloud Console, go to **APIs & Services** → **Library**
   - Or navigate directly to: `https://console.cloud.google.com/apis/library`
2. Search for **"Google Play Android Developer API"**
3. Click on it
4. Click the **"Enable"** button

![Enable API](https://console.cloud.google.com/apis/library/androidpublisher.googleapis.com)

**Verification:** After enabling, you should see the API management dashboard with metrics graphs.

---

### Step 3: Create a Service Account

1. Go to **IAM & Admin** → **Service Accounts**
   - Or navigate directly to: `https://console.cloud.google.com/iam-admin/serviceaccounts`
2. Click **"+ Create Service Account"** at the top
3. Fill in the details:
   - **Service account name:** `play-store-upload` (or similar)
   - **Service account ID:** Auto-generated from the name
   - **Description:** Optional but helpful: "Used for automated Play Store publishing"
4. Click **"Create and Continue"**
5. **Skip the optional steps** (roles and user access) - just click "Done"

**Result:** You now have a service account with an email like:
```
play-store-upload@your-project-id.iam.gserviceaccount.com
```

> ⚠️ **IMPORTANT:** Copy this email address - you'll need it for Step 5!

---

### Step 4: Create a JSON Key for the Service Account

1. In the Service Accounts list, click on your newly created service account
2. Go to the **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Select **"JSON"** format (recommended)
5. Click **"Create"**

**Result:** A JSON file is automatically downloaded to your computer. This file looks like:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "play-store-upload@your-project-id.iam.gserviceaccount.com",
  "client_id": "123456789...",
  ...
}
```

> 🔐 **SECURITY:** This file is like a password. Store it securely and NEVER commit it to Git!

---

### Step 5: Add Service Account to Play Console

This is the step that replaces the old "API Access" linking process.

1. Go to [Google Play Console](https://play.google.com/console)
2. Click **"Users and permissions"** in the left sidebar
3. Click **"Invite new users"** button
4. In the **email address field**, paste your service account email:
   ```
   play-store-upload@your-project-id.iam.gserviceaccount.com
   ```
5. **Set permissions** (choose based on your needs):

#### For Automated Publishing (CI/CD):
| Permission | Required? |
|------------|-----------|
| View app information and download bulk reports | ✅ Yes |
| Release to production, exclude devices, and use Play App Signing | ✅ Yes |
| Release apps to testing tracks | ✅ Yes |
| Manage store presence | Optional |

#### For Read-Only Access (Analytics):
| Permission | Required? |
|------------|-----------|
| View app information and download bulk reports | ✅ Yes |
| View financial data | Optional |

6. Click **"Invite user"**
7. Confirm the invitation in the popup dialog

**Result:** The service account now appears in your Users list with "Active" status.

---

### Step 6: Wait for Permission Propagation

> ⏳ **Important:** Permissions can take **up to 24-48 hours** to fully propagate!

If you get authentication errors immediately after setup, wait and try again later. Google's systems need time to sync.

---

## Common Blockers & Solutions

### Blocker 1: "Setup" Menu is Missing

**Symptom:** You don't see any "Setup" menu item in Play Console sidebar.

**Cause:** Google hides this menu until organization verification is complete, or it may have been completely removed for your account type.

**Solution:** Skip the Play Console UI entirely. Use the Google Cloud Console method described above.

---

### Blocker 2: Organization Verification Banner

**Symptom:** You see "Upload documents to verify your organization" banner on the Home page.

**Cause:** Google requires identity verification for organization accounts.

**Impact:** This **does NOT block** the Google Cloud Console method! You can still:
- Enable the API
- Create service accounts
- Add them to Play Console via "Users and permissions"

**Recommendation:** Complete the verification when you have time, but don't let it block your API setup.

---

### Blocker 3: 403 Forbidden / Permission Denied Errors

**Symptom:** API calls fail with authentication errors.

**Checklist:**
1. ✅ Is the **Google Play Android Developer API enabled** in Cloud Console?
2. ✅ Did you **invite the service account** to Play Console?
3. ✅ Did the invitation reach **"Active" status**?
4. ✅ Did you wait at least **24 hours** for permission propagation?
5. ✅ Does the service account have **correct permissions** for the operation?

---

### Blocker 4: "API Access" URL Redirects to Home

**Symptom:** Navigating to `play.google.com/console/.../api-access` redirects to app list.

**Cause:** This page is deprecated/hidden for most accounts.

**Solution:** Don't use this URL. Follow the new process via Google Cloud Console.

---

### Blocker 5: Service Account Not Accepting Invitation

**Symptom:** You try to invite the service account email but get an error.

**Possible Causes:**
1. Typo in the email address
2. The service account doesn't exist
3. The project is in a different Google Workspace organization

**Solution:** Copy the email directly from Google Cloud Console → Service Accounts → Click on the account → Copy the email from the detail page.

---

## Troubleshooting

### Verifying Your Setup

Use this API test to verify everything is working:

```bash
# Set the path to your JSON key file
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-key.json"

# Test with the Google Cloud CLI
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS

# Or test with curl (requires access token generation)
```

### Checking API Access Programmatically (Python)

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Path to your JSON key file
KEY_FILE = 'path/to/your-service-account-key.json'
PACKAGE_NAME = 'com.your.app.package'

credentials = service_account.Credentials.from_service_account_file(
    KEY_FILE,
    scopes=['https://www.googleapis.com/auth/androidpublisher']
)

service = build('androidpublisher', 'v3', credentials=credentials)

# Test: Get app details
try:
    result = service.edits().insert(packageName=PACKAGE_NAME).execute()
    edit_id = result['id']
    print(f"✅ API access working! Edit ID: {edit_id}")
    
    # Clean up
    service.edits().delete(packageName=PACKAGE_NAME, editId=edit_id).execute()
except Exception as e:
    print(f"❌ Error: {e}")
```

---

## Fastlane & CI/CD Integration

### Fastlane Setup

1. Store your JSON key securely (never in Git)
2. Configure `fastlane/Appfile`:

```ruby
json_key_file("path/to/your-key.json")  # Path to the json secret file
package_name("com.your.app.package")
```

3. Or use environment variable:

```ruby
json_key_file(ENV["GOOGLE_PLAY_JSON_KEY"])
```

### GitHub Actions Example

```yaml
name: Deploy to Play Store

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Ruby
        uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.0'
          
      - name: Install Fastlane
        run: gem install fastlane
        
      - name: Decode Service Account Key
        run: |
          echo "${{ secrets.GOOGLE_PLAY_JSON_KEY_BASE64 }}" | base64 --decode > service-account.json
          
      - name: Deploy to Play Store
        run: fastlane deploy
        env:
          GOOGLE_PLAY_JSON_KEY: service-account.json
```

### Storing the JSON Key as a Secret

```bash
# Encode the JSON key as base64
cat your-key.json | base64

# Add the output as a secret in:
# - GitHub: Settings → Secrets → Actions → New secret
# - Bitrise: Secrets → Add new
# - GitLab: Settings → CI/CD → Variables
```

---

## Security Best Practices

### ✅ DO

1. **Store JSON keys in secret managers** (not in code repositories)
2. **Use least-privilege permissions** (only grant what's needed)
3. **Rotate keys periodically** (create new, update CI/CD, delete old)
4. **Monitor API usage** in Google Cloud Console
5. **Use separate service accounts** for different environments (staging, production)

### ❌ DON'T

1. **Never commit JSON keys to Git** (even in private repos)
2. **Don't share keys via email or chat** (use secret managers)
3. **Don't use the same key for all projects** (harder to audit/revoke)
4. **Don't ignore API usage alerts** (could indicate compromised keys)

---

## Summary

| Old Process (Deprecated) | New Process (2024-2025) |
|--------------------------|-------------------------|
| Play Console → Setup → API Access | Google Cloud Console → APIs |
| Link Google Cloud Project in Play Console | N/A (not needed) |
| Create service account in Play Console | Create in Google Cloud Console |
| Download key from Play Console | Download from Google Cloud Console |
| N/A | Invite service account email in Play Console → Users and permissions |

---

## Resources

- [Google Play Developer API Documentation](https://developers.google.com/android-publisher)
- [Google Cloud Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Fastlane Supply Plugin](https://docs.fastlane.tools/actions/supply/)

---

## Contributing

Found an issue with this guide? Have additional blockers to report?

This guide was created because **no existing documentation covered the 2024-2025 changes**. Help other developers by:
1. Reporting issues you encounter
2. Sharing solutions that worked for you
3. Keeping this guide updated as Google makes further changes

---

*Last updated: January 2026*
*Guide version: 1.0*
