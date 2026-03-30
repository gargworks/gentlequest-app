import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# CONFIGURATION
BASE_DIR = Path("/Users/lokeshgarg/ai-mvp-backend")
ASSETS_DIR = BASE_DIR / "demos/sovereign-control-campaign/assets"
TEMP_DIR = ASSETS_DIR / "temp_shorts"
END_CARD = TEMP_DIR / "logo_static.mp4"
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf" # Bold font preferred if available

shorts_config = [
    {
        "name": "short_2_atomic_V2",
        "shot": "/Users/lokeshgarg/.gemini/antigravity/brain/6c3f8018-b6eb-4dae-9476-ed32eb313b95/windows_atomic_setup_live_v2_1772022722848.webp",
        "audio": TEMP_DIR / "short_2_atomic_vo.mp3",
        "subs": [
            {"text": "THE WINDOWS GAP", "start": 0, "end": 4},
            {"text": "NON-DETERMINISTIC", "start": 4, "end": 7},
            {"text": "ATOMIC SETUP", "start": 7, "end": 10},
            {"text": "ONE COMMAND", "start": 10, "end": 13},
            {"text": "ZERO ROT", "start": 13, "end": 18},
            {"text": "FIRST CLASS", "start": 18, "end": 22},
            {"text": "LOCAL CONTROL", "start": 22, "end": 26},
            {"text": "NUCLEUS-OS.DEV", "start": 26, "end": 30}
        ]
    },
    {
        "name": "short_3_shield_V2",
        "shot": "/Users/lokeshgarg/.gemini/antigravity/brain/6c3f8018-b6eb-4dae-9476-ed32eb313b95/windows_git_shield_live_v2_1772022760038.webp",
        "audio": TEMP_DIR / "short_3_shield_vo.mp3",
        "subs": [
            {"text": "SILENT KILLER", "start": 0, "end": 4},
            {"text": "CRLF", "start": 4, "end": 7},
            {"text": "BUILD DIES", "start": 7, "end": 10},
            {"text": "GIT SHIELD", "start": 10, "end": 13},
            {"text": "ATOMIC ENFORCEMENT", "start": 13, "end": 18},
            {"text": "UNIVERSAL HEALTH", "start": 18, "end": 22},
            {"text": "MAINTAIN THE MONOLITH", "start": 22, "end": 26},
            {"text": "NUCLEUS-OS.DEV", "start": 26, "end": 30}
        ]
    }
]

def create_sub_overlay(text, output_path):
    img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, 100) # Large bold text
    except:
        font = ImageFont.load_default()
    
    # Simple centering
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    w, h = right - left, bottom - top
    x = (1080 - w) // 2
    y = 1600 # Bottom area
    
    # Black outlined box for visibility
    draw.rectangle([x-20, y-20, x+w+20, y+h+20], fill=(0, 0, 0, 200))
    draw.text((x, y), text, font=font, fill=(255, 255, 0, 255)) # Yellow
    img.save(output_path)

def assemble_short(config):
    name = config['name']
    shot_path = config['shot']
    audio_path = config['audio']
    subs = config['subs']
    
    print(f"[ASSEMBLY] Processing {name} (WebP to Frames)...")
    frames_dir = TEMP_DIR / f"{name}_frames"
    frames_dir.mkdir(exist_ok=True)
    
    # 1. Convert WebP to PNG sequence
    cmd_magick = [
        "magick", str(shot_path), str(frames_dir / "frame.png")
    ]
    subprocess.run(cmd_magick, check=True)
    
    temp_body = TEMP_DIR / f"{name}_body.mp4"
    final_output = ASSETS_DIR / f"{name}_FINAL.mp4"
    
    # 2. Prepare Subtitle Overlays
    sub_inputs = []
    # Force 10fps for the sequence. Magick extracted ~150 frames for 15s, so 10fps is reasonable.
    filter_parts = ["[0:v]fps=10,scale=2560:-1,pad=2560:3392:0:986:black,crop=1080:1920:740:736[bg]"]
    
    for i, sub in enumerate(subs):
        sub_path = TEMP_DIR / f"{name}_sub_{i}.png"
        create_sub_overlay(sub['text'], sub_path)
        sub_inputs.extend(["-i", str(sub_path)])
        
    last_v = "bg"
    for i, sub in enumerate(subs):
        next_v = f"v{i}"
        filter_parts.append(f"[{last_v}][{i+2}:v]overlay=enable='between(t,{sub['start']},{sub['end']})'[{next_v}]")
        last_v = next_v

    # 3. Assemble Body Video
    cmd = [
        "ffmpeg", "-framerate", "10", "-i", str(frames_dir / "frame-%d.png"), "-i", str(audio_path)
    ] + sub_inputs + [
        "-filter_complex", ";".join(filter_parts),
        "-map", f"[{last_v}]", "-map", "1:a",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-shortest", "-y", str(temp_body)
    ]
    subprocess.run(cmd, check=True)
    
    # 4. Final Concat with End Card
    cmd = [
        "ffmpeg", "-i", str(temp_body), "-i", str(END_CARD),
        "-filter_complex",
        "[0:v]scale=1080:1920,setsar=1/1[v0];"
        "[1:v]scale=1080:1920,setsar=1/1[v1];"
        "[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[outv][outa]",
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-crf", "18", "-y", str(final_output)
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Created {final_output}")

if __name__ == "__main__":
    for cfg in shorts_config:
        assemble_short(cfg)
