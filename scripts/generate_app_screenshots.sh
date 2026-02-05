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
mkdir -p "$OUTPUT_DIR/ios/screenshots"
mkdir -p "$OUTPUT_DIR/android/screenshots"
mkdir -p "$OUTPUT_DIR/raw"

echo ""
echo "1. Checking dependencies..."
# Check for python3 and Pillow
if ! python3 -c "from PIL import Image" &>/dev/null; then
  echo "⚠️ Python Pillow not found. Installing..."
  pip3 install Pillow
fi

# Check for pngquant (optional but recommended)
if ! command -v pngquant &> /dev/null; then
  echo "⚠️ pngquant not found. Screenshots won't be optimized, but will still be generated."
fi

echo ""
echo "2. Creating screenshot test file..."
cat > "$PROJECT_DIR/test/screenshot_test.dart" << 'EOF'
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/main.dart';
import 'package:integration_test/integration_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  // Set up mock SharedPreferences for all tests
  setUpAll(() async {
    SharedPreferences.setMockInitialValues({
      'age_verified': true,
      'compliance_accepted': true,
    });
  });

  group('App Store Screenshots', () {
    testWidgets('1. Chat Interface', (WidgetTester tester) async {
      await tester.pumpWidget(MyApp());
      await tester.pumpAndSettle();
      
      // Navigate to chat
      await tester.tap(find.text('Talk'));
      await tester.pumpAndSettle();
      
      // Take screenshot
      await tester.takeScreenshot('chat_interface');
    });

    testWidgets('2. Mood Tracker', (WidgetTester tester) async {
      await tester.pumpWidget(MyApp());
      await tester.pumpAndSettle();
      
      // Navigate to mood tracker
      await tester.tap(find.text('Track'));
      await tester.pumpAndSettle();
      
      await tester.takeScreenshot('mood_tracker');
    });

    testWidgets('3. Crisis Resources', (WidgetTester tester) async {
      await tester.pumpWidget(MyApp());
      await tester.pumpAndSettle();
      
      // Open crisis resources
      await tester.tap(find.byIcon(Icons.emergency));
      await tester.pumpAndSettle();
      
      await tester.takeScreenshot('crisis_resources');
    });

    testWidgets('4. Quest/Exercises', (WidgetTester tester) async {
      await tester.pumpWidget(MyApp());
      await tester.pumpAndSettle();
      
      // Navigate to quests
      await tester.tap(find.text('Quest'));
      await tester.pumpAndSettle();
      
      await tester.takeScreenshot('wellness_exercises');
    });

    testWidgets('5. Community', (WidgetTester tester) async {
      await tester.pumpWidget(MyApp());
      await tester.pumpAndSettle();
      
      // Navigate to community
      await tester.tap(find.text('Community'));
      await tester.pumpAndSettle();
      
      await tester.takeScreenshot('community_support');
    });
  });
}

extension on WidgetTester {
  Future<void> takeScreenshot(String name) async {
    final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized() as IntegrationTestWidgetsFlutterBinding;
    // We Settlement between actions to ensure UI is stable
    await pumpAndSettle();
    await binding.takeScreenshot(name);
  }
}
EOF

echo "   Checking for available devices..."
if ! flutter devices | grep -q "available device" && ! flutter devices | grep -q "simulator"; then
  echo "⚠️ No devices or simulators found."
  echo "   Attempting to start iOS Simulator..."
  open -a Simulator || true
  # Give it some time to boot or show up
  for i in {1..30}; do
    if flutter devices | grep -q "simulator"; then
      echo "   Simulator started!"
      break
    fi
    echo "   Waiting for simulator... $i/30"
    sleep 2
  done
fi

# Run the actual screenshot generation
echo "   Running integration test locally..."
# Create the screenshots directory if it doesn't exist (IntegrationTest driver expects it)
mkdir -p "$OUTPUT_DIR/raw"

# Move to the flutter project directory
cd ai_buddy_web

# Execute the test and capture screenshots
# --screenshot-path is where the driver will save the images
# Run build first to ensure app bundle exists (especially on clean runs)
# Using --debug as it's faster and sufficient for screenshots
# Explicitly targeting simulator to avoid failures with connected physical devices
  # Using --timeout 20m because builds take time
  flutter drive \
    --driver=test_driver/integration_test.dart \
    --target=test/screenshot_test.dart \
    -d iphonesimulator \
    --no-pub \
    -v || { echo "❌ flutter drive failed"; exit 1; }

# Move back to root
cd ..

# Move captured screenshots from project directory to raw directory
if [ -d "ai_buddy_web/build/integration_test_screenshots" ]; then
    echo "   Moving screenshots to raw..."
    cp ai_buddy_web/build/integration_test_screenshots/*.png "$OUTPUT_DIR/raw/"
fi

# Placeholder device loops for future expansion
# IOS_DEVICES=("iPhone 15 Pro Max")
# for device in "${IOS_DEVICES[@]}"; do
#   echo "   - $device"
#   # flutter drive --driver=test_driver/integration_test.dart --target=test/screenshot_test.dart --device="$device"
# done

echo ""
echo "4. Processing screenshots with frames..."

# Add device frames using Figma templates
cd "$OUTPUT_DIR"
cat > "process_screenshots.py" << 'EOF'
import os
from PIL import Image, ImageDraw, ImageFont

def add_device_frame(input_path, output_path, device_type):
    """Add device frame and marketing text to screenshots"""
    
    # Load screenshot
    screenshot = Image.open(input_path)
    
    # Add rounded corners
    mask = Image.new('L', screenshot.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), screenshot.size], radius=40, fill=255)
    screenshot.putalpha(mask)
    
    # Add shadow and frame (simplified - use Figma for production)
    framed = Image.new('RGBA', 
                       (screenshot.width + 100, screenshot.height + 200), 
                       (248, 250, 252))
    framed.paste(screenshot, (50, 100), screenshot)
    
    # Add marketing text
    draw = ImageDraw.Draw(framed)
    try:
        font = ImageFont.truetype("Arial.ttf", 48)
        small_font = ImageFont.truetype("Arial.ttf", 32)
    except:
        font = ImageFont.load_default()
        small_font = font
    
    # Headlines for each screenshot
    headlines = {
        "chat_interface": "AI That Truly Understands",
        "mood_tracker": "Track Your Emotional Journey",
        "crisis_resources": "Help When You Need It Most",
        "wellness_exercises": "Evidence-Based Exercises",
        "community_support": "You're Never Alone"
    }
    
    filename = os.path.basename(input_path).replace('.png', '')
    headline = headlines.get(filename, "Mental Wellness Support")
    
    # Draw headline
    text_width = draw.textlength(headline, font=font)
    x = (framed.width - text_width) // 2
    draw.text((x, 30), headline, fill=(102, 126, 234), font=font)
    
    framed.save(output_path, "PNG")
    print(f"   ✓ Processed: {output_path}")

# Process all screenshots
raw_dir = os.path.join(os.getcwd(), "raw")
if not os.path.exists(raw_dir):
    os.makedirs(raw_dir)
    print(f"⚠️ Raw directory {raw_dir} was missing. Creating...")

processed_count = 0
for root, dirs, files in os.walk(raw_dir):
    for file in files:
        if file.endswith('.png'):
            input_path = os.path.join(root, file)
            
            # Save to iOS
            ios_out = os.path.join("ios/screenshots", file)
            add_device_frame(input_path, ios_out, "ios")
            
            # Save to Android
            android_out = os.path.join("android/screenshots", file)
            add_device_frame(input_path, android_out, "android")
            processed_count += 1

if processed_count == 0:
    print("❌ No raw screenshots found to process!")
else:
    print(f"✅ Processed {processed_count} screenshots.")
EOF

python3 "$OUTPUT_DIR/process_screenshots.py"

echo ""
echo "5. Optimizing screenshots..."
# Optimize file sizes
find "$OUTPUT_DIR" -name "*.png" -exec pngquant --quality=85-95 --ext=.png --force {} \;

echo ""
echo "✅ Screenshot generation complete!"
echo ""
echo "Generated screenshots in:"
echo "  iOS: $OUTPUT_DIR/ios/screenshots/"
echo "  Android: $OUTPUT_DIR/android/screenshots/"
echo ""
echo "Next steps:"
echo "1. Review and adjust screenshots in Figma/Photoshop"
echo "2. Add actual device frames using templates"
echo "3. Ensure text is localized if needed"
echo "4. Upload to App Store Connect and Play Console"
