#!/bin/bash
set -e

echo "Starting Flutter Web Build on Render..."

# Cache directory for Flutter SDK to speed up subsequent builds
FLUTTER_DIR="/opt/render/project/flutter"

if [ ! -d "$FLUTTER_DIR" ]; then
  echo "Downloading Flutter SDK (stable branch)..."
  git clone https://github.com/flutter/flutter.git -b stable "$FLUTTER_DIR"
else
  echo "Flutter SDK found in cache, pulling latest stable..."
  cd "$FLUTTER_DIR"
  git pull origin stable
  cd -
fi

export PATH="$FLUTTER_DIR/bin:$PATH"

echo "Fetching dependencies..."
# Render executes the command from the root of the repository.
# But render.yaml specified: buildCommand: ./ai_buddy_web/build_render_web.sh
# Let's make sure we are in the ai_buddy_web directory.
cd "$(dirname "$0")"

flutter config --enable-web
flutter pub get

echo "Building web app..."
# Use CanvasKit renderer for best performance and accuracy on desktop browsers
flutter build web --release --web-renderer canvaskit

echo "Build complete."
