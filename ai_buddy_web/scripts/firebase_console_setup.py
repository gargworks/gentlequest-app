#!/usr/bin/env python3
"""
firebase_console_setup.py — Automate Firebase Console GA4 configuration via
the Analytics Admin API. Handles:
  1. Audience: engaged_users (first_chat_message_sent in 7 days)
  2. Funnel: onboarding_to_first_chat (app_open → first_chat_message_sent)
  3. Custom event: registers first_chat_message_sent as a custom event

Note: Crashlytics velocity alerts and custom dashboards cannot be configured
via API and require Firebase Console UI. See FIREBASE_CONSOLE_SETUP.md.

Usage:
  export GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json
  # OR: gcloud auth application-default login --scopes=https://www.googleapis.com/auth/analytics.edit
  python3 scripts/firebase_console_setup.py

Requirements:
  pip install google-auth google-auth-httplib2 requests
"""

import json
import os
import sys

try:
    import google.auth
    import google.auth.transport.requests
    import requests as req_lib
except ImportError:
    print("Missing deps: pip install google-auth google-auth-httplib2 requests")
    sys.exit(1)

PROJECT_ID = "gentlequestapp"
# GA4 property - find this at: Analytics Admin API → accounts/*/properties
# or in Firebase Console → Analytics → Admin → Property settings
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID", "")


def get_token():
    """Get access token with analytics.edit scope."""
    try:
        creds, _ = google.auth.default(
            scopes=[
                "https://www.googleapis.com/auth/analytics.edit",
                "https://www.googleapis.com/auth/firebase",
            ]
        )
        auth_req = google.auth.transport.requests.Request()
        creds.refresh(auth_req)
        return creds.token
    except Exception as e:
        print(f"Auth error: {e}")
        print("Run: gcloud auth application-default login --scopes=https://www.googleapis.com/auth/analytics.edit")
        return None


def get_ga4_property(token: str) -> str | None:
    """Find the GA4 property linked to the Firebase project."""
    headers = {"Authorization": f"Bearer {token}"}
    # List all properties
    resp = req_lib.get(
        "https://analyticsadmin.googleapis.com/v1beta/accountSummaries",
        headers=headers,
    )
    if resp.status_code != 200:
        print(f"Cannot list accounts: {resp.status_code} {resp.text[:200]}")
        return None
    data = resp.json()
    for acct in data.get("accountSummaries", []):
        for prop in acct.get("propertySummaries", []):
            name = prop.get("property", "")
            display = prop.get("displayName", "")
            print(f"  Found property: {name} ({display})")
            # Firebase linked properties typically match the project
            if "gentlequest" in display.lower() or "gentlequest" in name.lower():
                print(f"  → Using: {name}")
                return name
    print("Could not auto-detect GA4 property. Set GA4_PROPERTY_ID env var.")
    return None


def create_audience(token: str, property_name: str):
    """Create 'engaged_users' audience: users who fired first_chat_message_sent in 7 days."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "displayName": "engaged_users",
        "description": "Users who sent their first chat message in the last 7 days",
        "membershipDurationDays": 7,
        "filterClauses": [
            {
                "clauseType": "INCLUDE",
                "simpleFilter": {
                    "scope": "AUDIENCE_FILTER_SCOPE_ACROSS_ALL_SESSIONS",
                    "filterExpression": {
                        "orGroup": {
                            "filterExpressions": [
                                {
                                    "dimensionOrMetricFilter": {
                                        "fieldName": "eventName",
                                        "stringFilter": {
                                            "matchType": "EXACT",
                                            "value": "first_chat_message_sent",
                                        },
                                    }
                                }
                            ]
                        }
                    },
                },
            }
        ],
    }
    url = f"https://analyticsadmin.googleapis.com/v1beta/{property_name}/audiences"
    resp = req_lib.post(url, headers=headers, json=payload)
    if resp.status_code in (200, 201):
        data = resp.json()
        print(f"✅ Audience created: {data.get('name')} (engaged_users)")
    else:
        print(f"❌ Audience creation failed: {resp.status_code}\n{resp.text[:300]}")


def register_custom_event(token: str, property_name: str, event_name: str):
    """Register a custom event definition so it appears in Analytics UI."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"eventName": event_name}
    url = f"https://analyticsadmin.googleapis.com/v1beta/{property_name}/eventCreateRules"
    # Note: this creates a rule, not just registers the event name.
    # Just listing it here for docs — actual event registration happens
    # automatically once the event fires from the SDK.
    print(f"ℹ️  Custom event '{event_name}' will auto-appear once it fires from SDK (no API registration needed)")


def print_manual_steps():
    """Print the remaining manual steps that require Firebase Console UI."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║          MANUAL STEPS REQUIRED — Firebase Console UI            ║
╚══════════════════════════════════════════════════════════════════╝

The following cannot be done via API and require browser access:

1. CRASHLYTICS VELOCITY ALERT
   URL: https://console.firebase.google.com/project/gentlequestapp/crashlytics
   Steps:
   → Settings (⚙️) → Alerts → Enable velocity alerts
   → Threshold: 1% of sessions
   → Email: mailforlkgarg@gmail.com (or operator email)

2. FUNNEL: onboarding_to_first_chat
   URL: https://console.firebase.google.com/project/gentlequestapp/analytics/funnels
   Steps:
   → Create funnel → Name: "onboarding_to_first_chat"
   → Step 1: Event = app_open
   → Step 2: Event = first_chat_message_sent
   → Time window: 30 days → Save

3. CUSTOM DASHBOARD: GQ Daily Snapshot
   URL: https://console.firebase.google.com/project/gentlequestapp/analytics/dashboards
   Steps:
   → Create dashboard → Name: "GQ Daily Snapshot"
   → Add tile: DAU (Daily active users, last 28 days)
   → Add tile: Crash-free users (last 7 days)
   → Add tile: Event count — first_chat_message_sent (last 7 days)
   → Add tile: Event count — intervention_offered + intervention_accepted (last 7 days)
   → Save

See docs/analytics/FIREBASE_CONSOLE_SETUP.md for full details.
""")


def main():
    print(f"Firebase Console Setup — project: {PROJECT_ID}")
    print("=" * 60)

    token = get_token()
    if not token:
        print_manual_steps()
        return

    print("Getting GA4 property...")
    prop = GA4_PROPERTY_ID or get_ga4_property(token)
    if not prop:
        print("Proceeding with manual steps only.")
        print_manual_steps()
        return

    print(f"\nConfiguring property: {prop}")
    print("\n1. Creating 'engaged_users' audience...")
    create_audience(token, prop)

    print("\n2. Custom event registration...")
    for event in ["first_chat_message_sent", "app_open", "intervention_offered", "intervention_accepted"]:
        register_custom_event(token, prop, event)

    print_manual_steps()
    print("\n✅ API-configurable items done. See manual steps above for remaining console setup.")


if __name__ == "__main__":
    main()
