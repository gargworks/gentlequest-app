
import os
import json
import subprocess
import time
from pathlib import Path
from google.cloud import texttospeech
import ffmpeg

# =============================================================================
# STRATEGY B: FRANKIE ENGINE CONFIGURATION
# =============================================================================
BASE_DIR = Path("/Users/lokeshgarg/ai-mvp-backend")
DEMOS_DIR = BASE_DIR / "demos"
PLAYBOOK_DIR = DEMOS_DIR / "00_production_playbook"
OUTPUT_DIR = PLAYBOOK_DIR / "one_shot_output"
ASSETS_DIR = OUTPUT_DIR / "assets_strategy_b" # Dedicated assets dir
FINAL_OUTPUT = OUTPUT_DIR / "nucleus_demo_trilogy_strategy_b.mp4" # Dedicated output
CONFIG_FILE = PLAYBOOK_DIR / "STRATEGY_B_CONFIG.json"

# Ensure Dirs
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Google TTS Config
TTS_CLIENT = texttospeech.TextToSpeechClient()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def log(msg, step=None):
    prefix = f"[STRATEGY B::{step}] " if step else "[STRATEGY B] "
    print(f"{prefix}{msg}")

def check_file(path_str):
    p = Path(path_str)
    if not p.exists():
        log(f"CRITICAL: Missing file {path_str}")
        return False
    return True

def generate_voiceover(text, voice_name, rate, output_path):
    log(f"Generating VO: '{text[:20]}...' -> {output_path.name}")
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", name=voice_name
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=rate
    )
    response = TTS_CLIENT.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(output_path, "wb") as out:
        out.write(response.audio_content)
    return output_path

def generate_sfx(sfx_type, duration, output_path, vol_dict=None):
    # Retrieve specific volume
    vol = 1.0
    if vol_dict and sfx_type in vol_dict:
        vol = vol_dict[sfx_type].get('vol', 1.0)
        
    log(f"Synthesizing SFX: {sfx_type} (dur={duration}s, vol={vol})")
    
    stream = None
    if sfx_type == "hum_low":
        stream = ffmpeg.input('sine=frequency=100:duration=5', f='lavfi')
    elif sfx_type == "keyboard_fast":
        stream = ffmpeg.input(f'anoisesrc=d={duration}:c=pink:r=44100:a=0.1', f='lavfi')
    elif sfx_type == "bass_drop":
        stream = ffmpeg.input('sine=frequency=60:duration=1', f='lavfi') 
    elif sfx_type == "glitch_light":
         stream = ffmpeg.input(f'anoisesrc=d={duration}:c=brown:r=44100:a=0.3', f='lavfi')
    elif sfx_type == "whoosh":
         stream = ffmpeg.input(f'anoisesrc=d={duration}:c=white:r=44100:a=0.5', f='lavfi') 
    elif sfx_type == "chime_success":
         stream = ffmpeg.input('sine=frequency=880:duration=0.5', f='lavfi')
    elif sfx_type == "drum_hit":
         stream = ffmpeg.input('anoisesrc=d=0.2:c=brown:r=44100:a=1', f='lavfi')
    elif sfx_type == "finger_snap":
         stream = ffmpeg.input('anoisesrc=d=0.1:c=blue:r=44100:a=1', f='lavfi')
    elif sfx_type == "rising_hum":
         stream = ffmpeg.input('sine=frequency=200:duration=2', f='lavfi')
    elif sfx_type == "data_noise":
         stream = ffmpeg.input('anoisesrc=d=2:c=pink:r=44100:a=0.1', f='lavfi')
    elif sfx_type == "power_down":
         stream = ffmpeg.input('sine=frequency=50:duration=1', f='lavfi')
    else:
        stream = ffmpeg.input(f'anullsrc=d={duration}', f='lavfi')
        
    stream.output(str(output_path)).run(overwrite_output=True, quiet=True)
    return output_path

# =============================================================================
# MAIN ENGINE
# =============================================================================

def run_strategy_b_engine():
    log("==================================================")
    log("NUCLEUS STRATEGY B ENGINE STARTING")
    log("==================================================")

    # 1. LOAD CONFIG
    log("Loading Config...", step=1)
    if not CONFIG_FILE.exists():
         raise FileNotFoundError(f"Missing Config: {CONFIG_FILE}")

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        
    master_video_path = BASE_DIR / config['master_video']
    if not check_file(master_video_path):
        raise FileNotFoundError(f"Missing Master Video: {master_video_path}")

    cues = config['cues']
    voice_name = config.get('voice_name', "en-US-Chirp3-HD-Charon")
    speaking_rate = config.get('speaking_rate', 1.0)
    sfx_config = config.get('sfx_config', {})
    
    # 2. GENERATE ASSETS
    log("Generating Assets...", step=2)
    audio_streams = []
    
    for cue in cues:
        cue_id = cue['id']
        start_time = cue['time']
        delay_ms = int(start_time * 1000)
        
        # A. Voiceover
        vo_path = ASSETS_DIR / f"{cue_id}_vo.mp3"
        generate_voiceover(cue['text'], voice_name, speaking_rate, vo_path)
        
        # Create Delayed Stream for VO
        vo_stream = ffmpeg.input(str(vo_path)).filter('adelay', f"{delay_ms}|{delay_ms}")
        audio_streams.append(vo_stream)
        
        # B. SFX (Optional)
        if cue.get('sfx_under'):
            sfx_type = cue['sfx_under']
            sfx_path = ASSETS_DIR / f"{cue_id}_sfx_{sfx_type}.mp3"
            
            # Generate Raw SFX
            generate_sfx(sfx_type, 2.0, sfx_path, sfx_config) 
            
            # Create Delayed Stream
            sfx_stream = ffmpeg.input(str(sfx_path)).filter('adelay', f"{delay_ms}|{delay_ms}")
            
            # Apply subtle volume from config
            vol_lvl = sfx_config.get(sfx_type, {}).get('vol', 0.5)
            sfx_stream = sfx_stream.filter('volume', volume=vol_lvl)
            
            audio_streams.append(sfx_stream)
            
    # 3. MIXING & MUXING
    log(f"Mixing {len(audio_streams)} audio streams onto Master Video...", step=3)
    
    # Input Master Video
    input_video = ffmpeg.input(str(master_video_path))
    
    # Mix filter
    mixed_audio = ffmpeg.filter(audio_streams, 'amix', inputs=len(audio_streams), dropout_transition=0)
    
    # Output
    output = ffmpeg.output(
        input_video.video,
        mixed_audio,
        str(FINAL_OUTPUT),
        vcodec='copy',
        acodec='aac',
        audio_bitrate='192k'
    )
    
    log(f"Rendering to {FINAL_OUTPUT}...")
    output.run(overwrite_output=True)
    
    log("SUCCESS: Strategy B Generation Complete.")

if __name__ == "__main__":
    run_strategy_b_engine()
