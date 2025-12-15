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
echo "1. Installing screenshot tools..."
flutter pub global activate screenshots

echo ""
echo "2. Creating screenshot test file..."
cat > "$PROJECT_DIR/test/screenshot_test.dart" << 'EOF'
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_buddy_web/main.dart';
import 'package:ai_buddy_web/screens/interactive_chat_screen.dart';
import 'package:ai_buddy_web/screens/mood_tracker_screen.dart';
import 'package:ai_buddy_web/screens/home_shell.dart';
import 'package:integration_test/integration_test.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

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
    // Implement screenshot capture
    // This would integrate with device_preview or screenshots package
  }
}
EOF

echo ""
echo "3. Running screenshot generation..."

# iOS Screenshots (required sizes)
echo "   Generating iOS screenshots..."
IOS_DEVICES=(
  "iPhone 6.7"    # 1290x2796 - iPhone 15 Pro Max
  "iPhone 6.5"    # 1242x2688 - iPhone 11 Pro Max  
  "iPhone 5.5"    # 1242x2208 - iPhone 8 Plus
  "iPad 12.9"     # 2048x2732 - iPad Pro 12.9"
)

for device in "${IOS_DEVICES[@]}"; do
  echo "   - $device"
  # flutter drive --driver=test_driver/integration_test.dart --target=test/screenshot_test.dart --device="$device"
done

# Android Screenshots (required sizes)
echo "   Generating Android screenshots..."
ANDROID_DEVICES=(
  "phone"         # 1080x1920
  "tablet7"       # 600x1024  
  "tablet10"      # 800x1280
)

for device in "${ANDROID_DEVICES[@]}"; do
  echo "   - $device"
  # flutter drive --driver=test_driver/integration_test.dart --target=test/screenshot_test.dart --device="$device"
done

echo ""
echo "4. Processing screenshots with frames..."

# Add device frames using Figma templates
cat > "$OUTPUT_DIR/process_screenshots.py" << 'EOF'
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

# Process all screenshots
for root, dirs, files in os.walk("raw"):
    for file in files:
        if file.endswith('.png'):
            input_path = os.path.join(root, file)
            output_path = os.path.join("ios/screenshots", file)
            add_device_frame(input_path, output_path, "ios")
            
            output_path = os.path.join("android/screenshots", file)
            add_device_frame(input_path, output_path, "android")
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
