#!/usr/bin/env python3
"""Generate a Google Drive refresh token for mailforlkgarg@gmail.com.

One-time setup. The token persists in Colab Secrets forever.

Prerequisites:
    pip3 install google-auth-oauthlib

Step 1 — Create OAuth credentials (one-time):
    1. Go to https://console.cloud.google.com/apis/credentials
       (sign in as mailforlkgarg@gmail.com or any account with a GCP project)
    2. Create a project if needed (name: "Nucleus Training")
    3. Enable the Google Drive API:
       https://console.cloud.google.com/apis/library/drive.googleapis.com
    4. Configure OAuth consent screen:
       - User type: External (or Internal if Workspace)
       - App name: "Nucleus Training"
       - Scopes: add ../auth/drive
       - Test users: add mailforlkgarg@gmail.com
    5. Create credentials > OAuth 2.0 Client ID:
       - Application type: Desktop app
       - Name: "Nucleus Training CLI"
    6. Download the JSON file

Step 2 — Generate the token:
    python3 scripts/get_drive_token.py --client-json ~/Downloads/client_secret_*.json

Step 3 — Add to Colab Secrets (key icon in left sidebar):
    MAILFORLKGARG_TOKEN         = <refresh_token from output>
    MAILFORLKGARG_CLIENT_ID     = <client_id from output>
    MAILFORLKGARG_CLIENT_SECRET = <client_secret from output>

    Toggle "Notebook access" ON for each secret.

Done. Every Colab session (any account) will use mailforlkgarg's quota.
"""

import sys


def main():
    if "--client-json" not in sys.argv:
        print(__doc__)
        return

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Install dependency first:")
        print("  pip3 install google-auth-oauthlib")
        sys.exit(1)

    client_json_path = sys.argv[sys.argv.index("--client-json") + 1]

    print(f"\nUsing client config: {client_json_path}")
    print("A browser window will open — sign in as mailforlkgarg@gmail.com\n")

    flow = InstalledAppFlow.from_client_secrets_file(
        client_json_path,
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    creds = flow.run_local_server(port=0, open_browser=True)

    print("\n" + "=" * 60)
    print("SUCCESS — Add these 3 Colab Secrets:")
    print("=" * 60)
    print(f"\nMAILFORLKGARG_TOKEN         = {creds.refresh_token}")
    print(f"MAILFORLKGARG_CLIENT_ID     = {creds.client_id}")
    print(f"MAILFORLKGARG_CLIENT_SECRET = {creds.client_secret}")
    print(f"\nColab > Left sidebar > Key icon > Add each secret")
    print(f"Toggle 'Notebook access' ON for each one.")
    print("=" * 60)


if __name__ == "__main__":
    main()
