#!/bin/bash
# Install Production Dependencies for GentleQuest Launch

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "📦 Installing Production Dependencies"
echo "====================================="

cd ai_buddy_web

echo ""
echo "Installing Firebase and production packages..."
flutter pub add \
  firebase_core:^3.8.1 \
  firebase_analytics:^11.3.6 \
  firebase_crashlytics:^4.2.1 \
  in_app_review:^2.0.9 \
  upgrader:^11.3.0 \
  app_links:^6.3.2

echo ""
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo "Running flutter pub get to resolve dependencies..."
flutter pub get

echo ""
echo "Checking for dependency conflicts..."
flutter pub deps

echo ""
echo -e "${YELLOW}Next Steps for Firebase Setup:${NC}"
echo ""
echo "1. Create Firebase Project:"
echo "   - Go to https://console.firebase.google.com"
echo "   - Create project: 'gentlequest-app'"
echo "   - Enable Google Analytics"
echo ""
echo "2. Add Android App:"
echo "   - Package name: app.gentlequest.www"
echo "   - Download google-services.json"
echo "   - Place in: ai_buddy_web/android/app/"
echo ""
echo "3. Add iOS App:"
echo "   - Bundle ID: com.gentlequest.app"
echo "   - Download GoogleService-Info.plist"
echo "   - Place in: ai_buddy_web/ios/Runner/"
echo ""
echo "4. Initialize FlutterFire:"
echo "   dart pub global activate flutterfire_cli"
echo "   flutterfire configure --project=gentlequest-app"
echo ""
echo -e "${GREEN}✓ Production dependencies ready!${NC}"
echo ""
echo "Run './scripts/complete_launch_checklist.sh' to verify everything is ready."
