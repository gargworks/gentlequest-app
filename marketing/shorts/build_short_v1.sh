#!/usr/bin/env bash
# build_short_v1.sh — GQ YouTube Short v1
#
# Builds a 30s 1080×1920 vertical Short from existing oracle screenshots.
# Pillow bakes captions into source frames; ffmpeg adds Ken-Burns zoompan + concat.
#
# Output: marketing/shorts/out/gq_short_v1.mp4  (H.264, 30fps)

set -euo pipefail

ROOT=/Users/lokeshgarg/gentlequest/marketing/shorts
REPO=/Users/lokeshgarg/ai-mvp-backend
SCR="$REPO/docs/design/refs/screenshots/oracle-run-2026-06-10"

OUT_DIR="$ROOT/out"
TMP="$OUT_DIR/_tmp"
mkdir -p "$TMP"

W=1080; H=1920; FPS=30

# Sources
SRC_A="$SCR/I1_chat_home.png"
SRC_B="$SCR/M2c_mood_submitted.png"
SRC_C="$SCR/P3_safety_plan_card.png"
SRC_D="$SCR/Q2_quest_preview.png"

# Durations (sum=30s)
T0=4; T1=7; T2=6; T3=6; T4=5; T5=2

# Captions
CAP0="a small mental-health app"
CAP1="say what is on your mind"
CAP2="check in with your mood"
CAP3="safety plan, not buried"
CAP4="tiny quests, no streaks"
CAP5="iOS + Android · free"

BAKE="$ROOT/bake_caption.py"

bake_phone() {  python3 "$BAKE" --src "$1" --out "$2" --caption "$3" --bg phone --size 58; }
bake_card()  {  python3 "$BAKE"            --out "$1" --caption "$2" --bg black --size "$3"; }

echo "[1/6] bake title..."
bake_card  "$TMP/f0.png" "$CAP0" 78
echo "[2/6] bake scene A — Talk..."
bake_phone "$SRC_A" "$TMP/f1.png" "$CAP1"
echo "[3/6] bake scene B — Mood..."
bake_phone "$SRC_B" "$TMP/f2.png" "$CAP2"
echo "[4/6] bake scene C — Safety..."
bake_phone "$SRC_C" "$TMP/f3.png" "$CAP3"
echo "[5/6] bake scene D — Quest..."
bake_phone "$SRC_D" "$TMP/f4.png" "$CAP4"
echo "[6/6] bake end card..."
bake_card  "$TMP/f5.png" "$CAP5" 72

# Render each clip — Ken-Burns zoompan only on phone scenes; cards are static
mkclip_kenburns() {
  local img="$1" out="$2" dur="$3"
  local frames=$((dur * FPS))
  ffmpeg -y -loglevel error -loop 1 -i "$img" \
    -filter_complex "[0:v]scale=${W}*2:${H}*2,zoompan=z='min(zoom+0.0008,1.08)':d=${frames}:s=${W}x${H}:fps=${FPS}[v]" \
    -map "[v]" -t "$dur" -r ${FPS} -c:v libx264 -pix_fmt yuv420p -preset medium -crf 20 \
    "$out"
}

mkclip_static() {
  local img="$1" out="$2" dur="$3"
  ffmpeg -y -loglevel error -loop 1 -i "$img" \
    -t "$dur" -r ${FPS} -vf "scale=${W}:${H}" \
    -c:v libx264 -pix_fmt yuv420p -preset medium -crf 20 \
    "$out"
}

echo "[clip 0/5] title card..."
mkclip_static    "$TMP/f0.png" "$TMP/s0.mp4" "$T0"
echo "[clip 1/5] Talk..."
mkclip_kenburns  "$TMP/f1.png" "$TMP/s1.mp4" "$T1"
echo "[clip 2/5] Mood..."
mkclip_kenburns  "$TMP/f2.png" "$TMP/s2.mp4" "$T2"
echo "[clip 3/5] Safety..."
mkclip_kenburns  "$TMP/f3.png" "$TMP/s3.mp4" "$T3"
echo "[clip 4/5] Quest..."
mkclip_kenburns  "$TMP/f4.png" "$TMP/s4.mp4" "$T4"
echo "[clip 5/5] end card..."
mkclip_static    "$TMP/f5.png" "$TMP/s5.mp4" "$T5"

# Concat (re-encode for safety — covers any param drift between clips)
LIST="$TMP/concat.txt"
: > "$LIST"
for f in s0 s1 s2 s3 s4 s5; do echo "file '$TMP/$f.mp4'" >> "$LIST"; done

FINAL="$OUT_DIR/gq_short_v1.mp4"
echo "[concat] joining..."
ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST" \
  -c:v libx264 -pix_fmt yuv420p -preset medium -crf 20 \
  "$FINAL"

DUR=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$FINAL" 2>/dev/null)
ls -lh "$FINAL"
echo ""
echo "Done: $FINAL"
echo "Duration: ${DUR}s  (target 30s)"
