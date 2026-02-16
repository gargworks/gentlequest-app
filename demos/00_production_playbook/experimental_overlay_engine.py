
import os
import json
import subprocess
import time
from pathlib import Path
from google.cloud import texttospeech
import ffmpeg

# =============================================================================
# EXPERIMENTAL CONFIGURATION
# =============================================================================
BASE_DIR = Path("/Users/lokeshgarg/ai-mvp-backend")
DEMOS_DIR = BASE_DIR / "demos"
PLAYBOOK_DIR = DEMOS_DIR / "00_production_playbook"
OUTPUT_DIR = PLAYBOOK_DIR / "one_shot_output"
ASSETS_DIR = OUTPUT_DIR / "assets_experimental" # Separate assets dir
FINAL_OUTPUT = OUTPUT_DIR / "nucleus_demo_trilogy_experimental.mp4" # Separate output file
CONFIG_FILE = PLAYBOOK_DIR / "CONTINUOUS_SCRIPT_CONFIG.json"

# Ensure Dirs
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Google TTS Config
TTS_CLIENT = texttospeech.TextToSpeechClient()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def log(msg, step=None):
    prefix = f"[PRECISION-EXP STEP {step}] " if step else "[PRECISION-EXP] "
    print(f"{prefix}{msg}")

def check_file(path_str):
    p = Path(path_str)
    if not p.exists():
        log(f"CRITICAL: Missing file {path_str}")
        return False
    return True

def generate_voiceover(text, voice_name, rate, output_path):
    log(f"Generating VO: '{text[:20]}...' (Rate={rate}) -> {output_path.name}")
    
    if not text.startswith("<speak>"):
        ssml_text = f"<speak>{text}</speak>"
    else:
        ssml_text = text
        
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=voice_name)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=rate)
    
    try:
        response = TTS_CLIENT.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        with open(output_path, "wb") as out:
            out.write(response.audio_content)
        return output_path
    except Exception as e:
        log(f"TTS ERROR: {e}")
        raise e

def generate_sfx(sfx_type, duration, output_path, sfx_config=None):
    log(f"Synthesizing SFX: {sfx_type} (dur={duration}s)")
    
    stream = None
    if sfx_type == "dark_drone":
        # Keep as silent/minimal placeholder since muted in config
        stream = ffmpeg.input('sine=f=40:d={dur}'.format(dur=duration), f='lavfi')
    elif sfx_type == "ui_glitch":
        stream = ffmpeg.input(f'anoisesrc=d={duration}:c=pink:r=44100:a=0.5', f='lavfi').filter('highpass', f=1000)
    elif sfx_type == "ui_chime":
        c1 = ffmpeg.input(f'sine=f=880:d={duration}', f='lavfi')
        c2 = ffmpeg.input(f'sine=f=1760:d={duration}', f='lavfi')
        stream = ffmpeg.filter([c1, c2], 'amix', inputs=2).filter('afade', t='out', st=0.05, d=0.05)
    elif sfx_type == "tech_snap":
        # Sharper, louder snap: Bandpass + high-volume white noise burst
        stream = ffmpeg.input(f'anoisesrc=d=0.1:c=white:r=44100:a=1.0', f='lavfi').filter('bandpass', f=4000, w=1000).filter('afade', t='out', st=0, d=0.1)
    elif sfx_type == "bass_thud":
        stream = ffmpeg.input('sine=f=50:d=0.5', f='lavfi').filter('afade', t='out', st=0.1, d=0.4)
    else:
        stream = ffmpeg.input(f'anullsrc=d={duration}', f='lavfi')
        
    stream.output(str(output_path)).run(overwrite_output=True, quiet=True)
    return output_path

# =============================================================================
# MAIN ENGINE
# =============================================================================

def run_overlay_engine():
    log("==================================================")
    log("NUCLEUS PRECISION 'SOVEREIGN' ENGINE STARTING V15 (VOLUME FIX)")
    log("==================================================")

    # 1. LOAD CONFIG
    log("Loading Precision Config...", step=1)
    if not CONFIG_FILE.exists():
         raise FileNotFoundError(f"Missing Config: {CONFIG_FILE}")

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        
    master_video_path = BASE_DIR / config['master_video']
    cues = config['cues']
    voice_name = config.get('voice_name', "en-US-Chirp3-HD-Charon")
    default_rate = config.get('speaking_rate', 1.0)
    sfx_config = config.get('sfx_config', {})
    
    # 2. GENERATE ASSETS
    log("Generating Precision Assets...", step=2)
    audio_streams = []
    
    for cue in cues:
        cue_id = cue['id']
        start_time = cue['time']
        delay_ms = int(start_time * 1000)
        
        # A. Voiceover
        if cue.get('text'):
            vo_path = ASSETS_DIR / f"{cue_id}_vo.mp3"
            cue_rate = cue.get('rate', default_rate)
            generate_voiceover(cue['text'], voice_name, cue_rate, vo_path)
            
            # Create Delayed Stream for VO
            vo_stream = ffmpeg.input(str(vo_path)).filter('adelay', f"{delay_ms}|{delay_ms}")
            audio_streams.append(vo_stream)
        
        # B. SFX (Optional)
        if cue.get('sfx_under'):
            sfx_type = cue['sfx_under']
            sfx_dur = cue.get('sfx_duration', 2.0)
            sfx_path = ASSETS_DIR / f"{cue_id}_sfx_{sfx_type}.mp3"
            
            generate_sfx(sfx_type, sfx_dur, sfx_path, sfx_config) 
            
            # Create Delayed Stream for SFX
            sfx_stream = ffmpeg.input(str(sfx_path)).filter('adelay', f"{delay_ms}|{delay_ms}")
            
            # Apply subtle volume
            vol_lvl = sfx_config.get(sfx_type, {}).get('vol', 0.5)
            sfx_stream = sfx_stream.filter('volume', volume=vol_lvl)
            
            audio_streams.append(sfx_stream)
            
    # 3. MIXING & MUXING
    log(f"Mixing {len(audio_streams)} audio streams onto Master Video...", step=3)
    
    # Input Master Video
    input_video = ffmpeg.input(str(master_video_path))
    
    # Mix filter
    # amix squashes volume by 1/N. We compensate by restored collective gains.
    mixed_audio = ffmpeg.filter(audio_streams, 'amix', inputs=len(audio_streams), dropout_transition=0)
    mixed_audio = mixed_audio.filter('volume', volume=f"{len(audio_streams)}") 
    
    # Output
    output = ffmpeg.output(
        input_video.video,
        mixed_audio,
        str(FINAL_OUTPUT),
        vcodec='copy', # COPY VIDEO
        acodec='aac',
        audio_bitrate='192k'
    )
    
    log(f"Rendering to {FINAL_OUTPUT}...")
    output.run(overwrite_output=True)
    
    log("SUCCESS: Precision Overlay Complete (V15).")

if __name__ == "__main__":
    run_overlay_engine()
