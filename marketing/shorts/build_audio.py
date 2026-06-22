import os
import subprocess
import re
from pathlib import Path

# Paths (absolute — script may be run from any cwd)
BASE_DIR = Path(__file__).resolve().parent
VIDEOS_DIR = BASE_DIR / "out"
TRANSCRIPTS_DIR = BASE_DIR / "transcripts"
FINAL_DIR = VIDEOS_DIR / "final"
TEMP_DIR = BASE_DIR / "temp"
FINAL_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# 1. Download a royalty-free ambient track
bg_music_path = TEMP_DIR / "bg_music.mp3"
if not bg_music_path.exists():
    print("Downloading royalty-free ambient music...")
    subprocess.run([
        "curl", "-L", "-o", str(bg_music_path),
        "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"
    ], check=True)
    print(f"  Saved: {bg_music_path}")

def process_video(name):
    video_path = VIDEOS_DIR / f"gq_short_{name}.mp4"
    transcript_path = TRANSCRIPTS_DIR / f"{name}_transcript.txt"
    final_path = FINAL_DIR / f"gq_short_{name}_final.mp4"

    if not video_path.exists():
        print(f"  SKIP {name} — no video")
        return
    if not transcript_path.exists():
        print(f"  SKIP {name} — no transcript")
        return

    with open(transcript_path, "r") as f:
        lines = f.readlines()

    vo_text = " ".join([l.replace("VOICEOVER:", "").strip()
                        for l in lines if l.strip().startswith("VOICEOVER:")])
    subtitles = [l.replace("SUBTITLE:", "").strip()
                 for l in lines if l.strip().startswith("SUBTITLE:")]

    if not vo_text or not subtitles:
        print(f"  SKIP {name} — no VO or subtitles found")
        return

    print(f"  VO: {vo_text[:80]}...")
    print(f"  Subs: {len(subtitles)} lines")

    # 2. Voiceover — Mac Samantha, rate 135 for calm tone
    vo_path = TEMP_DIR / f"vo_{name}.wav"
    subprocess.run(["say", "-v", "Samantha", "-r", "135", "-o", str(vo_path),
                    "--data-format=LEF32@44100", vo_text], check=True)

    # 3. SRT with real scene timings
    srt_path = TEMP_DIR / f"{name}.srt"
    time_re = re.compile(r'\[(\d+):(\d+)–(\d+):(\d+)\]')
    sub_timings = []
    for l in lines:
        m = time_re.search(l)
        if m:
            start_s = int(m.group(1)) * 60 + int(m.group(2))
            end_s = int(m.group(3)) * 60 + int(m.group(4))
            sub_timings.append((start_s, end_s))

    with open(srt_path, "w") as f:
        for i, sub in enumerate(subtitles):
            if i < len(sub_timings):
                start, end = sub_timings[i]
            else:
                dur = 28.0 / max(1, len(subtitles))
                start, end = i * dur, (i + 1) * dur
            start_str = f"00:00:{int(start):02d},{int((start % 1) * 1000):03d}"
            end_str = f"00:00:{int(end):02d},{int((end % 1) * 1000):03d}"
            f.write(f"{i+1}\n{start_str} --> {end_str}\n{sub}\n\n")

    # 4. FFmpeg: video + VO + bg music (-20dB)
    # Note: captions already baked into frames by bake_caption.py — no SRT burn needed
    print(f"  Rendering {name}...")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(vo_path),
        "-stream_loop", "-1", "-i", str(bg_music_path),
        "-filter_complex",
        "[2:a]volume=-20dB[bg];[1:a][bg]amix=inputs=2:duration=longest:dropout_transition=0[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-t", "30",
        str(final_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg ERROR: {result.stderr[-800:]}")
    else:
        size_mb = final_path.stat().st_size / (1024 * 1024)
        print(f"  Done: {final_path.name} ({size_mb:.1f} MB)")

# Process v7-v12 only (skip v1-v6 — already shipped)
for video_file in sorted(VIDEOS_DIR.glob("gq_short_v*.mp4")):
    name_part = video_file.stem.replace("gq_short_", "")
    if name_part[0:3] in ("v10", "v11", "v12"):
        pass  # don't skip — these are new
    elif name_part[0:2] in ("v1", "v2", "v3", "v4", "v5", "v6"):
        continue
    print(f"\n=== {name_part} ===")
    process_video(name_part)

print("\nAll processing complete!")
