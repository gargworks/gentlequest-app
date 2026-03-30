import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from google.cloud import texttospeech

# CONFIGURATION
BASE_DIR = Path("/Users/lokeshgarg/ai-mvp-backend")
DEMOS_DIR = BASE_DIR / "demos"
SOVEREIGN_DIR = DEMOS_DIR / "sovereign-control-campaign/assets"
LOGO_PATH = Path("/Users/lokeshgarg/.gemini/antigravity/brain/6c3f8018-b6eb-4dae-9476-ed32eb313b95/nucleus_logo_sovereign_v2_1771899913460.png")
INPUT_VIDEO = SOVEREIGN_DIR / "intern_who_acts_final_mix.mp4"
OUTPUT_SHORT = SOVEREIGN_DIR / "intern_short_FINAL.mp4"
TEMP_DIR = SOVEREIGN_DIR / "temp_shorts"
TEMP_DIR.mkdir(exist_ok=True)

TTS_CLIENT = texttospeech.TextToSpeechClient()
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"

DIRECTOR_SHEET = {
    "target_resolution": (1080, 1920),
    "subtitles": [],
    "end_card": {
        "duration": 4.0,
        "tagline": "Sovereign Control. Local Intelligence.",
        "cta": "Get Started at nucleusos.dev",
        "voice": "en-US-Chirp3-HD-Charon"
    }
}

def generate_tts(text, voice_name, output_path):
    print(f"[TTS] Generating: {text}")
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=voice_name)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=1.05)
    response = TTS_CLIENT.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(output_path, "wb") as out:
        out.write(response.audio_content)

def create_text_overlay(text, font_size, color=(255, 255, 255, 255), box_mode=False):
    img = Image.new('RGBA', DIRECTOR_SHEET['target_resolution'], (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, font_size)
    
    # Text size
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    w, h = right - left, bottom - top
    
    x = (DIRECTOR_SHEET['target_resolution'][0] - w) // 2
    y = (DIRECTOR_SHEET['target_resolution'][1] - h) // 2
    
    if box_mode: # For subtitles at bottom
        y = DIRECTOR_SHEET['target_resolution'][1] - 300
        # Draw black box
        draw.rectangle([x-20, y-20, x+w+20, y+h+20], fill=(0, 0, 0, 180))
        draw.text((x, y), text, font=font, fill=(255, 255, 0, 255)) # Yellow
    else:
        draw.text((x, y), text, font=font, fill=color)
    
    return img

def synthesize_end_card():
    print("[STEP] Synthesizing Branded End-Card (PIL Fallback)...")
    vo_path = TEMP_DIR / "end_card_vo.mp3"
    # Regenerate VO with CTA
    full_cta_text = f"{DIRECTOR_SHEET['end_card']['tagline']} {DIRECTOR_SHEET['end_card']['cta']}"
    generate_tts(full_cta_text, DIRECTOR_SHEET['end_card']['voice'], vo_path)
    
    # 1. Base Logo
    logo = Image.open(LOGO_PATH).convert("RGBA")
    logo = logo.resize((800, 800), Image.LANCZOS)
    
    # 2. Build Canvas
    canvas = Image.new('RGBA', (1080, 1920), (10, 10, 15, 255)) # Dark obsidian
    canvas.paste(logo, (140, 320), logo)
    
    # 3. Add Text
    draw = ImageDraw.Draw(canvas)
    f1 = ImageFont.truetype(FONT_PATH, 80)
    f2 = ImageFont.truetype(FONT_PATH, 60)
    f3 = ImageFont.truetype(FONT_PATH, 70) # CTA font
    
    draw.text((540, 1200), "Sovereign Control", font=f1, fill="white", anchor="mm")
    draw.text((540, 1300), "Local Intelligence", font=f2, fill="white", anchor="mm")
    draw.text((540, 1600), DIRECTOR_SHEET['end_card']['cta'], font=f3, fill=(0, 255, 255, 255), anchor="mm") # Cyan CTA
    
    card_img_path = TEMP_DIR / "end_card_frame.png"
    canvas.save(card_img_path)
    
    logo_video = TEMP_DIR / "logo_static.mp4"
    cmd = [
        "ffmpeg", "-loop", "1", "-i", str(card_img_path), "-i", str(vo_path),
        "-c:v", "libx264", "-t", str(DIRECTOR_SHEET['end_card']['duration']),
        "-pix_fmt", "yuv420p", "-y", str(logo_video)
    ]
    subprocess.run(cmd, check=True)
    return logo_video

def produce_short():
    print("[STEP] Producing Sovereign Short v2 (PIL Overlay Engine)...")
    
    # 1. Setup end card
    end_card_video = synthesize_end_card()
    
    # 2. Process subs as overlays
    sub_overlays = []
    for i, sub in enumerate(DIRECTOR_SHEET['subtitles']):
        img = create_text_overlay(sub['text'], 60, box_mode=True)
        path = TEMP_DIR / f"sub_{i}.png"
        img.save(path)
        sub_overlays.append({"path": path, "start": sub['start'], "end": sub['end']})
        
    # 3. Apply Main Vertical Crop + Subtitle Overlays
    main_vertical = TEMP_DIR / "main_vertical.mp4"
    
    # [FIX] Do NOT slow down here; simple_overlay_engine.py already matched video to audio.
    # [FIX] Removed drawbox highlight as requested.
    filter_parts = [
        "[0:v]scale=3590:1920,crop=1080:1920:0:0[bg]"
    ]
    inputs = ["-i", str(INPUT_VIDEO)]
    
    last_v = "bg"
    for i, sub in enumerate(sub_overlays):
        inputs.extend(["-i", str(sub['path'])])
        next_v = f"v{i}"
        filter_parts.append(f"[{last_v}][{i+1}:v]overlay=enable='between(t,{sub['start']},{sub['end']})'[{next_v}]")
        last_v = next_v
    
    cmd = ["ffmpeg"] + inputs + [
        "-filter_complex", ";".join(filter_parts),
        "-map", f"[{last_v}]", "-map", "0:a",
        "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
        "-y", str(main_vertical)
    ]
    subprocess.run(cmd, check=True)
    
    # 4. Final Concat
    print("[STEP] Concatenating Final Short (Normalizing SAR)...")
    # Using filter_complex to normalize and then concat
    cmd = [
        "ffmpeg", "-i", str(main_vertical), "-i", str(end_card_video),
        "-filter_complex", 
        "[0:v]scale=1080:1920,setsar=1/1[v0];"
        "[1:v]scale=1080:1920,setsar=1/1[v1];"
        "[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[outv][outa]",
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
        "-y", str(OUTPUT_SHORT)
    ]
    subprocess.run(cmd, check=True)
    
    print(f"✅ SUCCESS: Short produced at {OUTPUT_SHORT}")

if __name__ == "__main__":
    produce_short()
