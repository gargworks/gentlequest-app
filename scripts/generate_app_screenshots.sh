#!/bin/bash
# Automated Screenshot Generation for App Stores
# Generates all required screenshots for iOS App Store and Google Play Store

set -e

echo "📸 App Store Screenshot Generator for GentleQuest"
echo "================================================"

# Configuration
PROJECT_DIR="$(pwd)/ai_buddy_web"
OUTPUT_DIR="$(pwd)/app_store_assets"

# Create output directories
mkdir -p "$OUTPUT_DIR/ios/screenshots/raw"
mkdir -p "$OUTPUT_DIR/ios/screenshots/framed"
mkdir -p "$OUTPUT_DIR/android/screenshots/raw"
mkdir -p "$OUTPUT_DIR/android/screenshots/framed"
mkdir -p "$OUTPUT_DIR/raw"

echo ""
echo "1. Checking dependencies..."
if ! python3 -c "from PIL import Image" &>/dev/null; then
  echo "⚠️ Python Pillow not found. Installing..."
  pip3 install Pillow
fi

if ! command -v pngquant &> /dev/null; then
  echo "⚠️ pngquant not found. Screenshots won't be optimized, but will still be generated."
fi

echo ""
echo "2. Creating screenshot test file..."
cat > "$PROJECT_DIR/test/screenshot_test.dart" << 'EOF'
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/main.dart';
import 'package:integration_test/integration_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    SharedPreferences.setMockInitialValues({
      'compliance_age_verified_18_plus': true,
      'compliance_location_verified': true,
      'compliance_verified_region': 'CA',
      'compliance_verification_timestamp': DateTime.now().millisecondsSinceEpoch,
    });
  });

  group('App Store Screenshots', () {
    testWidgets('1. Chat Interface', (WidgetTester tester) async {
      await tester.pumpWidget(const MyApp());
      await tester.pumpAndSettle(const Duration(seconds: 5));
      
      if (find.text('Talk').evaluate().isNotEmpty) {
        await tester.tap(find.text('Talk'));
        await tester.pumpAndSettle();
      }
      
      await binding.takeScreenshot('chat_interface');
    });

    testWidgets('2. Mood Tracker', (WidgetTester tester) async {
      await tester.pumpWidget(const MyApp());
      await tester.pumpAndSettle(const Duration(seconds: 5));
      
      await tester.tap(find.text('Mood'));
      await tester.pumpAndSettle(const Duration(seconds: 2));
      
      await binding.takeScreenshot('mood_tracker');
    });

    testWidgets('3. Community', (WidgetTester tester) async {
      await tester.pumpWidget(const MyApp());
      await tester.pumpAndSettle(const Duration(seconds: 5));
      
      await tester.tap(find.text('Community'));
      await tester.pumpAndSettle(const Duration(seconds: 2));
      
      await binding.takeScreenshot('community_support');
    });
  });
}
EOF

echo ""
echo "3. Running integration tests..."
cd "$PROJECT_DIR"

# Find an available simulator and boot it
SIM_ID=$(xcrun simctl list devices | grep -m 1 "iPhone" | grep -v "unavailable" | sed -E 's/.*\(([-0-9A-F]+)\).*/\1/' | head -n 1)
SIM_NAME=$(xcrun simctl list devices | grep "$SIM_ID" | sed -E 's/([^(]+).*/\1/' | sed 's/ $//' | head -n 1)

if [ -n "$SIM_ID" ]; then
  echo "   Targeting simulator: $SIM_NAME ($SIM_ID)"
  xcrun simctl boot "$SIM_ID" || true
  TARGET_DEVICE="$SIM_ID"
else
  echo "⚠️ No iPhone simulators found. Attempting 'iphonesimulator' literal..."
  TARGET_DEVICE="iphonesimulator"
fi

flutter drive \
  --driver=test_driver/integration_test.dart \
  --target=test/screenshot_test.dart \
  -d "$TARGET_DEVICE" \
  --no-pub \
  -v

echo "   Moving screenshots to raw..."
cd ..
if [ -d "ai_buddy_web/build/integration_test_screenshots" ]; then
    cp ai_buddy_web/build/integration_test_screenshots/*.png "$OUTPUT_DIR/raw/"
fi

echo ""
echo "4. Processing screenshots with frames..."
cd "$OUTPUT_DIR"
cat > "process_screenshots.py" << 'EOF'
import os
from PIL import Image, ImageDraw, ImageFont

def process_raw():
    raw_dir = "raw"
    ios_dir = "ios/screenshots/framed"
    android_dir = "android/screenshots/framed"
    
    os.makedirs(ios_dir, exist_ok=True)
    os.makedirs(android_dir, exist_ok=True)
    
    if not os.path.exists(raw_dir):
        return
    
    for f in os.listdir(raw_dir):
        if f.endswith(".png"):
            # For now, just copy to framed as a placeholder for the framing logic
            # In a real scenario, we'd add frames here.
            img = Image.open(os.path.join(raw_dir, f))
            img.save(os.path.join(ios_dir, f))
            img.save(os.path.join(android_dir, f))
            print(f"Processed {f}")

if __name__ == "__main__":
    process_raw()
EOF

python3 process_screenshots.py

echo ""
echo "5. Optimizing screenshots..."
if command -v pngquant &> /dev/null; then
  find . -name "*.png" -exec pngquant --quality=85-95 --ext=.png --force {} \;
fi

echo ""
echo "✅ Screenshot generation complete!"
echo ""
echo "Generated screenshots in:"
echo "  iOS: $OUTPUT_DIR/ios/screenshots/framed/"
echo "  Android: $OUTPUT_DIR/android/screenshots/framed/"
echo ""
