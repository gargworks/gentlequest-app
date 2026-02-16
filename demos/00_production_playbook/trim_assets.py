#!/usr/bin/env python3
import subprocess
from pathlib import Path

# Configuration
ROOT_DIR = Path(__file__).parent.parent
FFMPEG = "ffmpeg"

def trim_video(input_path, output_path, start_time, duration, speed_factor=1.0):
    print(f"✂️  Trimming {input_path.name}...")
    
    # Base filter: trim video and audio
    # setpts=PTS/SPEED for video speed
    # atempo=SPEED for audio speed (limit 0.5 to 2.0, so need cascading for 4x)
    
    filter_complex = f"[0:v]trim=start={start_time}:duration={duration},setpts=PTS/{speed_factor}[v];[0:a]atrim=start={start_time}:duration={duration},asetpts=PTS[a]"
    
    # Note: For simple trimming without speed changes on audio (since we replace audio anyway), 
    # we can just ignore audio processing or silence it if speed is high.
    # For this specific task, we are replacing audio with VO, so video speed is the priority.
    
    cmd = [
        FFMPEG, "-y",
        "-i", str(input_path),
        "-ss", str(start_time), # Fast seek
        "-t", str(duration),
        "-filter:v", f"setpts=PTS/{speed_factor}",
        "-an", # Remove audio (we have VO)
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        str(output_path)
    ]
    
    subprocess.run(cmd, check=True)
    print(f"✅ Generated: {output_path.name}")

def main():
    # Demo A: Startup - Part 1
    # Source: 2m 17s. Target: ~16s.
    trim_video(
        ROOT_DIR / "01_demo_a_startup" / "part_1.mov",
        ROOT_DIR / "01_demo_a_startup" / "part_1_trimmed.mp4",
        start_time="00:00:00",
        duration="00:01:05", 
        speed_factor=4.0
    )

    # Demo A: Startup - Part 2
    # Source: ~4m. Target: ~20s.
    # Strategy: Take first 40s. Speed up 2x.
    trim_video(
        ROOT_DIR / "01_demo_a_startup" / "part_2.mov",
        ROOT_DIR / "01_demo_a_startup" / "part_2_trimmed.mp4",
        start_time="00:00:00",
        duration="00:00:40",
        speed_factor=2.0
    )

    # Demo B: Context - Part 1
    # Source: 47s. Target: ~15s.
    # Strategy: Take 00:00-00:45. Speed up 3x.
    trim_video(
        ROOT_DIR / "02_demo_b_context" / "part_1.mov",
        ROOT_DIR / "02_demo_b_context" / "part_1_trimmed.mp4",
        start_time="00:00:00",
        duration="00:00:45",
        speed_factor=3.0
    )

    # Demo B: Context - Part 2
    # Source: 41s. Target: ~20s.
    # Strategy: Take full clip. Speed up 2x.
    trim_video(
        ROOT_DIR / "02_demo_b_context" / "part_2.mov",
        ROOT_DIR / "02_demo_b_context" / "part_2_trimmed.mp4",
        start_time="00:00:00",
        duration="00:00:41",
        speed_factor=2.0
    )

    # Demo C: Sovereign - Part 1
    # Source: 6m 40s. Target: 30s.
    # Strategy: Take first 90s. Speed 3x.
    trim_video(
        ROOT_DIR / "03_demo_c_sovereign" / "part_1.mov",
        ROOT_DIR / "03_demo_c_sovereign" / "part_1_trimmed.mp4",
        start_time="00:00:00",
        duration="00:01:30",
        speed_factor=3.0
    )

    # Demo C: Sovereign - Part 2
    # Source: 1m 30s. Target: 25s.
    # Strategy: Take 00:05 to 00:55 (50s). Speed 2x.
    trim_video(
        ROOT_DIR / "03_demo_c_sovereign" / "part_2.mov",
        ROOT_DIR / "03_demo_c_sovereign" / "part_2_trimmed.mp4",
        start_time="00:00:05",
        duration="00:00:50",
        speed_factor=2.0
    )



if __name__ == "__main__":
    main()
