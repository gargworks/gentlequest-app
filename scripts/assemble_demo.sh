#!/bin/bash
# Nucleus Demo Video Assembly Script
#
# Merges screen recording + voiceover audio using ffmpeg
#
# Usage:
#   ./scripts/assemble_demo.sh demo_a_screen.mov demo_a_voiceover.mp3 demo_a_final.mp4

set -e

if [ "$#" -ne 3 ]; then
    echo "❌ Usage: $0 <screen_recording.mov> <voiceover.mp3> <output.mp4>"
    echo "Example: $0 demo_a_screen.mov demo_a_voiceover.mp3 demo_a_final.mp4"
    exit 1
fi

SCREEN_VIDEO="$1"
VOICEOVER_AUDIO="$2"
OUTPUT_VIDEO="$3"

# Check if input files exist
if [ ! -f "$SCREEN_VIDEO" ]; then
    echo "❌ Error: Screen recording not found: $SCREEN_VIDEO"
    exit 1
fi

if [ ! -f "$VOICEOVER_AUDIO" ]; then
    echo "❌ Error: Voiceover audio not found: $VOICEOVER_AUDIO"
    exit 1
fi

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ Error: ffmpeg is not installed"
    echo "Install with: brew install ffmpeg"
    exit 1
fi

echo "🎬 Assembling Nucleus Demo Video"
echo "Screen: $SCREEN_VIDEO"
echo "Audio: $VOICEOVER_AUDIO"
echo "Output: $OUTPUT_VIDEO"
echo ""

# Merge video + audio
# -c:v copy: Copy video codec (no re-encoding for speed)
# -c:a aac: Encode audio as AAC
# -map 0:v:0: Use video from first input
# -map 1:a:0: Use audio from second input
# -shortest: Match duration to shortest stream (audio or video)
ffmpeg -i "$SCREEN_VIDEO" -i "$VOICEOVER_AUDIO" \
    -c:v copy -c:a aac -b:a 192k \
    -map 0:v:0 -map 1:a:0 \
    -shortest \
    -y "$OUTPUT_VIDEO"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Success! Demo video created: $OUTPUT_VIDEO"
    echo ""
    echo "📊 Video Info:"
    ffprobe -v quiet -show_format -show_streams "$OUTPUT_VIDEO" | grep -E "(duration|codec_name|width|height)" || true
else
    echo "❌ Error: ffmpeg failed"
    exit 1
fi
