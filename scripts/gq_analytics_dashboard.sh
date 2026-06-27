#!/bin/bash
# GentleQuest Analytics Dashboard
# Pulls key metrics from Google Analytics 4 and displays them
# Run: bash scripts/gq_analytics_dashboard.sh

# GA4 Property ID (find at https://analytics.google.com → Admin → Property Settings)
GA4_PROPERTY_ID="${GA4_PROPERTY_ID:-345678901}"

# Check if gcloud/ga4 CLI is available
if ! command -v curl &> /dev/null; then
    echo "Error: curl not found"
    exit 1
fi

echo "================================================"
echo "  GentleQuest Analytics Dashboard"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"
echo ""

# Google Analytics 4 Data API requires OAuth — this is a reference implementation
# For automated daily reports, set up a service account and use the GA4 Data API
# See: https://developers.google.com/analytics/devguides/reporting/data/v1

echo "📊 METRICS TO TRACK (set up in GA4 dashboard):"
echo ""
echo "  Conversions (mark these as key events in GA4):"
echo "    - newsletter_signup        → email captures from blog + landing page"
echo "    - ios_download_click       → App Store button clicks"
echo "    - android_download_click   → Play Store button clicks"
echo "    - app_link                 → general app link clicks"
echo ""
echo "  Engagement:"
echo "    - page_view                → blog post views"
echo "    - scroll                   → deep reads (scroll >50%)"
echo "    - session_duration         → time on page"
echo ""
echo "  Traffic sources:"
echo "    - organic search           → SEO traffic"
echo "    - social                   → Twitter/LinkedIn/Reddit/Medium"
echo "    - direct                   → typed URL"
echo "    - referral                 → Medium → blog"
echo ""
echo "📋 GA4 DASHBOARD URL:"
echo "    https://analytics.google.com/analytics/web/#/p${GA4_PROPERTY_ID}/reports"
echo ""
echo "🔧 SETUP INSTRUCTIONS:"
echo "    1. Go to GA4 → Admin → Events"
echo "    2. Mark these as conversions: newsletter_signup, ios_download_click, android_download_click"
echo "    3. Go to GA4 → Reports → Engagement → Conversions to see the funnel"
echo ""
echo "📈 KEY FUNNEL TO TRACK:"
echo "    Blog visitor → Newsletter signup → App download"
echo "    Social click → Blog visitor → Newsletter signup"
echo "    Medium reader → Canonical click → Blog visitor → App download"
echo ""

# If we have the GA4 access token, pull real data
if [ -n "${GA4_ACCESS_TOKEN:-}" ]; then
    echo "🔄 Pulling real-time data from GA4..."
    YESTERDAY=$(date -u -v-1d '+%Y-%m-%d' 2>/dev/null || date -u -d 'yesterday' '+%Y-%m-%d')
    TODAY=$(date -u '+%Y-%m-%d')

    curl -s "https://analyticsdata.googleapis.com/v1beta/properties/${GA4_PROPERTY_ID}:runReport" \
        -H "Authorization: Bearer ${GA4_ACCESS_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{
            \"dateRanges\": [{\"startDate\": \"${YESTERDAY}\", \"endDate\": \"${TODAY}\"}],
            \"metrics\": [
                {\"name\": \"totalUsers\"},
                {\"name\": \"newUsers\"},
                {\"name\": \"screenPageViews\"},
                {\"name\": \"conversions\"}
            ],
            \"dimensions\": [
                {\"name\": \"date\"}
            ]
        }" 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "    (Failed to pull data — check token)"
else
    echo "ℹ️  Set GA4_ACCESS_TOKEN env var to pull real data"
    echo "    Or just check the dashboard: https://analytics.google.com"
fi

echo ""
echo "================================================"
