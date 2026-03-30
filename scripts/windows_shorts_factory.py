import os
import subprocess
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from google.cloud import texttospeech

# CONFIGURATION
BASE_DIR = Path("/Users/lokeshgarg/ai-mvp-backend")
DEMOS_DIR = BASE_DIR / "demos"
SOVEREIGN_DIR = DEMOS_DIR / "sovereign-control-campaign/assets"
TEMP_DIR = SOVEREIGN_DIR / "temp_shorts"
TEMP_DIR.mkdir(exist_ok=True)

LOGO_PATH = Path("/Users/lokeshgarg/.gemini/antigravity/brain/6c3f8018-b6eb-4dae-9476-ed32eb313b95/nucleus_logo_sovereign_v2_1771899913460.png")
CONFIG_PATH = SOVEREIGN_DIR / "WINDOWS_AUDIO_CONFIG.json"
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"

TTS_CLIENT = texttospeech.TextToSpeechClient()

DIRECTOR_SHEET = {
    "target_resolution": (1080, 1920),
    "end_card": {
        "duration": 4.0,
        "tagline": "Sovereign Control. Local Intelligence.",
        "cta": "nucleus-os.dev", # Actual URL
        "voice": "en-US-Chirp3-HD-Charon"
    }
}

def generate_tts(text, voice_name, output_path, speaking_rate=1.05):
    print(f"[TTS] Generating: {text}")
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=voice_name)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=speaking_rate)
    response = TTS_CLIENT.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(output_path, "wb") as out:
        out.write(response.audio_content)

def create_text_overlay(text, font_size, color=(255, 255, 255, 255), box_mode=True):
    img = Image.new('RGBA', DIRECTOR_SHEET['target_resolution'], (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except:
        font = ImageFont.load_default()
    
    # Text size
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    w, h = right - left, bottom - top
    
    x = (DIRECTOR_SHEET['target_resolution'][0] - w) // 2
    y = (DIRECTOR_SHEET['target_resolution'][1] - h) // 2
    
    if box_mode: # Yellow on Black Box (Intern Style)
        y = DIRECTOR_SHEET['target_resolution'][1] - 400
        draw.rectangle([x-20, y-10, x+w+20, y+h+10], fill=(0, 0, 0, 180))
        draw.text((x, y), text, font=font, fill=(255, 255, 0, 255))
    else:
        draw.text((x, y), text, font=font, fill=color)
    
    return img

def synthesize_end_card(short_id):
    print(f"[EC] Synthesizing Branded End-Card for {short_id}...")
    vo_path = TEMP_DIR / f"end_card_vo_{short_id}.mp3"
    full_cta_text = f"{DIRECTOR_SHEET['end_card']['tagline']} Join the Vanguard at nucleusos.dev"
    # CTA audio fix: say "nucleus o s dot dev" phonetically in the TTS
    phonetic_cta = f"{DIRECTOR_SHEET['end_card']['tagline']} Join the Vanguard at Nucleus O S dot dev"
    generate_tts(phonetic_cta, DIRECTOR_SHEET['end_card']['voice'], vo_path)
    
    logo = Image.open(LOGO_PATH).convert("RGBA")
    logo = logo.resize((800, 800), Image.LANCZOS)
    
    canvas = Image.new('RGBA', (1080, 1920), (10, 10, 15, 255))
    canvas.paste(logo, (140, 320), logo)
    
    draw = ImageDraw.Draw(canvas)
    f1 = ImageFont.truetype(FONT_PATH, 80)
    f2 = ImageFont.truetype(FONT_PATH, 60)
    f3 = ImageFont.truetype(FONT_PATH, 70)
    
    draw.text((540, 1200), "Sovereign Control", font=f1, fill="white", anchor="mm")
    draw.text((540, 1300), "Local Intelligence", font=f2, fill="white", anchor="mm")
    draw.text((540, 1600), DIRECTOR_SHEET['end_card']['cta'], font=f3, fill=(0, 255, 255, 255), anchor="mm")
    
    card_img_path = TEMP_DIR / f"end_card_frame_{short_id}.png"
    canvas.save(card_img_path)
    
    logo_video = TEMP_DIR / f"logo_static_{short_id}.mp4"
    cmd = [
        "ffmpeg", "-loop", "1", "-i", str(card_img_path), "-i", str(vo_path),
        "-c:v", "libx264", "-t", str(DIRECTOR_SHEET['end_card']['duration']),
        "-pix_fmt", "yuv420p", "-y", str(logo_video)
    ]
    subprocess.run(cmd, check=True)
    return logo_video

def produce_short(config):
    short_id = config['id']
    print(f"[FACTORY] Producing {short_id}...")
    
    # 1. Generate Full VO
    vo_path = TEMP_DIR / f"{short_id}_full_vo.mp3"
    full_text = " ".join([c['text'] for c in config['cues']])
    generate_tts(full_text, config['voice'], vo_path, config['speaking_rate'])
    
    # 2. Setup end card
    end_card_video = synthesize_end_card(short_id)
    
    # 3. Process subs as overlays
    sub_overlays = []
    # We'll use 2-second windows for cues if not specified, 
    # but AUDIO_CONFIG usually needs precise times.
    for i, cue in enumerate(config['cues']):
        # Find end time (next cue start or +3s)
        end_time = config['cues'][i+1]['time'] if i+1 < len(config['cues']) else 30.0
        img = create_text_overlay(cue['text'], 50, box_mode=True) # Slightly smaller than intern to fit tech text
        path = TEMP_DIR / f"{short_id}_sub_{i}.png"
        img.save(path)
        sub_overlays.append({"path": path, "start": cue['time'], "end": end_time})

    # 4. Prepare Base Video (from WebP frames)
    # The frames exist from previous V2 attempt. I'll re-extract them just to be sure.
    shot_path_map = {
        "short_2_atomic": "/Users/lokeshgarg/.gemini/antigravity/brain/6c3f8018-b6eb-4dae-9476-ed32eb313b95/windows_atomic_setup_v5_nuclear_1772025988466.webp",
        "short_3_shield": "/Users/lokeshgarg/.gemini/antigravity/brain/6c3f8018-b6eb-4dae-9476-ed32eb313b95/windows_git_shield_v5_nuclear_1772026021111.webp"
    }
    shot_path = shot_path_map[short_id]
    frames_dir = TEMP_DIR / f"{short_id}_factory_frames"
    frames_dir.mkdir(exist_ok=True)
    # Simple name, let magick add -0, -1, etc.
    subprocess.run(["magick", shot_path, str(frames_dir / "frame.png")], check=True)
    
    main_vertical = TEMP_DIR / f"{short_id}_main_vertical.mp4"
    
    # Filter: Scale to fit 1080 width, then pad height to 1920
    # Input 1280x800 -> Scale to 1080x675
    filter_parts = [
        "[0:v]fps=25,scale=1080:-1,pad=1080:1920:0:(1920-675)/2:color=#0a0a0f[bg]"
    ]
    inputs = ["-framerate", "25", "-i", str(frames_dir / "frame-%d.png"), "-i", str(vo_path)]
    
    last_v = "bg"
    for i, sub in enumerate(sub_overlays):
        inputs.extend(["-i", str(sub['path'])])
        next_v = f"v{i}"
        filter_parts.append(f"[{last_v}][{i+2}:v]overlay=enable='between(t,{sub['start']},{sub['end']})'[{next_v}]")
        last_v = next_v
    
    cmd = ["ffmpeg"] + inputs + [
        "-filter_complex", ";".join(filter_parts),
        "-map", f"[{last_v}]", "-map", "1:a",
        "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.1", "-pix_fmt", "yuv420p", "-crf", "18", 
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-y", str(main_vertical)
    ]
    subprocess.run(cmd, check=True)
    
    # 5. Final Concat
    output_path = SOVEREIGN_DIR / f"{short_id}_v5_FINAL.mp4"
    cmd = [
        "ffmpeg", "-i", str(main_vertical), "-i", str(end_card_video),
        "-filter_complex", 
        "[0:v]scale=1080:1920,setsar=1/1[v0];"
        "[1:v]scale=1080:1920,setsar=1/1[v1];"
        "[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[outv][outa]",
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-crf", "18", "-y", str(output_path)
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ SUCCESS: {short_id} produced at {output_path}")

if __name__ == "__main__":
    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
    for cfg in data['shorts']:
        produce_short(cfg)
