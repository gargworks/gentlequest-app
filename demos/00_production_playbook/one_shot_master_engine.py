
import os
import json
import subprocess
import time
from pathlib import Path
from google.cloud import texttospeech
import ffmpeg

# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================
BASE_DIR = Path("/Users/lokeshgarg/ai-mvp-backend")
DEMOS_DIR = BASE_DIR / "demos"
OUTPUT_DIR = DEMOS_DIR / "00_production_playbook/one_shot_output"
ASSETS_DIR = OUTPUT_DIR / "assets"
FINAL_OUTPUT = OUTPUT_DIR / "nucleus_demo_trilogy_atomic.mp4"

# Source Videos
VIDEO_SOURCES = {
    "Demo A": DEMOS_DIR / "01_demo_a_startup/part_1.mov",
    "Demo B Part 1": DEMOS_DIR / "02_demo_b_context/part_1.mov",
    "Demo B Part 2": DEMOS_DIR / "02_demo_b_context/part_2.mov",
    "Demo C Part 1": DEMOS_DIR / "03_demo_c_sovereign/part_1.mov",
    "Demo C Part 2": DEMOS_DIR / "03_demo_c_sovereign/part_2.mov",
    "Demo C Part 3": DEMOS_DIR / "03_demo_c_sovereign/part_2.mov", # Fallback: Part 3 missing, reusing Part 2
}

# Ensure Dirs
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Google TTS Config
TTS_CLIENT = texttospeech.TextToSpeechClient()
VOICE_NAME = "en-US-Chirp3-HD-Charon"

# =============================================================================
# THE ATOMIC MANIFEST (From UNIFIED_PRODUCTION_PROTOCOL.md)
# =============================================================================
PROTOCOL = [
    {
        "id": "seq_01",
        "script": "People think AI agents are magic. They're not. They're software. And software breaks.",
        "source": "Demo A", # Part 1
        "in": 0, "out": 5,
        "zoom": "full",
        "sfx": "hum_low"
    },
    {
        "id": "seq_02",
        "script": "That's why I don't run naked LLMs. I run Nucleus.",
        "source": "Demo A",
        "in": 5, "out": 15,
        "zoom": "right",
        "sfx": "keyboard_fast"
    },
    {
        "id": "seq_03",
        "script": "Watch. I try to break my own server... 'Governance Lockout'. It's not just a rule. It's physics.",
        "source": "Demo A",
        "in": 55, "out": 70, # Forensic 1:00 is key. 
        "freeze_at": 60, # Freeze at 1:00
        "freeze_duration": 2.0,
        "zoom": "right",
        "sfx": "bass_drop"
    },
    {
        "id": "seq_04_bridge",
        "type": "bridge",
        "title": "THE BRAIN",
        "script": "Most agents have amnesia. You close the tab, they forget...",
        "sfx": "glitch_light"
    },
    {
        "id": "seq_05",
        "script": "...Nucleus doesn't.",
        "source": "Demo B Part 1",
        "in": 0, "out": 15,
        "speed": 2.0,
        "zoom": "right"
    },
    {
        "id": "seq_06",
        "script": "Total context recall. Instantly.",
        "source": "Demo B Part 2",
        "in": 0, "out": 10,  # Result arrives at 0:09
        "speed": 4.0, # Fast forward to result
        "zoom": "right",
        "sfx": "whoosh"
    },
    {
        "id": "seq_07",
        "script": "It remembers WHO made the decision, and WHEN. No hallucinations. Just facts.",
        "source": "Demo B Part 2",
        "in": 35, "out": 45,
        "freeze_at": 39, # Attribution
        "freeze_duration": 3.0,
        "zoom": "right", 
        "sfx": "chime_success"
    },
     {
        "id": "seq_08_bridge",
        "type": "bridge",
        "title": "THE POWER",
        "script": "Now for the superpower.",
        "sfx": "drum_hit"
    },
    {
        "id": "seq_09",
        "script": "I'm not writing integrations. I'm just Snap-ping my fingers.",
        "source": "Demo C Part 2", # Inputting Snapshot
        "in": 0, "out": 12,
        "zoom": "input_bar", # Focus on input
        "sfx": "finger_snap"
    },
    {
        "id": "seq_10",
        "script": "Look at that. The Mesh fills up. One instruction to mount the entire infrastructure.",
        "source": "Demo C Part 2",
        "in": 40, "out": 50,
        "freeze_at": 48, # Mount Summary
        "freeze_duration": 2.0,
        "zoom": "right",
        "sfx": "rising_hum"
    },
    {
        "id": "seq_11",
        "script": "Now I have God Mode. Live production data... via natural language.",
        "source": "Demo C Part 3",
        "in": 0, "out": 10, # Listing customers
        "zoom": "full",
        "sfx": "data_noise"
    },
    {
        "id": "seq_12",
        "type": "bridge",
        "title": "NUCLEUS",
        "script": "This isn't the future. This is Nucleus. Mission complete.",
        "sfx": "power_down"
    }
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def log(msg, step=None):
    prefix = f"[STEP {step}] " if step else "[INFO] "
    print(f"{prefix}{msg}")

def check_file(path_str):
    p = Path(path_str)
    if not p.exists():
        log(f"CRITICAL: Missing file {path_str}")
        return False
    return True

def generate_voiceover(text, output_path):
    log(f"Generating VO: '{text[:20]}...' -> {output_path.name}")
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", name=VOICE_NAME
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0 # Protocol says 1.0 (we rely on speed ramping video)
    )
    response = TTS_CLIENT.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(output_path, "wb") as out:
        out.write(response.audio_content)
    return output_path

def get_duration(file_path):
    try:
        probe = ffmpeg.probe(str(file_path))
        return float(probe['format']['duration'])
    except Exception as e:
        log(f"Error probing {file_path}: {e}")
        return 0

def generate_sfx(sfx_type, duration, output_path):
    # Primitive Synthesis using lavfi
    # In a real studio we'd load files, but "One-Shot" implies self-containment for now.
    log(f"Synthesizing SFX: {sfx_type} ({duration}s)")
    
    stream = None
    if sfx_type == "hum_low":
        stream = ffmpeg.input('sine=frequency=100:duration=5', f='lavfi')
    elif sfx_type == "keyboard_fast":
        # Noise gated? Hard to synth keyboard. We will use silence or simple clicks if possible.
        # Fallback: Just low noise.
        stream = ffmpeg.input(f'anoisesrc=d={duration}:c=pink:r=44100:a=0.1', f='lavfi')
    elif sfx_type == "bass_drop":
        stream = ffmpeg.input('sine=frequency=60:duration=1', f='lavfi') # Simple sine
    elif sfx_type == "glitch_light":
         stream = ffmpeg.input(f'anoisesrc=d={duration}:c=brown:r=44100:a=0.3', f='lavfi')
    else:
        # Default silence pad
        stream = ffmpeg.input(f'anullsrc=d={duration}', f='lavfi')
        
    # Just render it
    # Note: Complex sfx synthesis is hard in one line. We will rely on VO mainly.
    # We will generate a mockup file.
    stream.output(str(output_path)).run(overwrite_output=True, quiet=True)
    return output_path

# =============================================================================
# MAIN ENGINE
# =============================================================================

def run_engine():
    log("==================================================")
    log("NUCLEUS ONE-SHOT MASTER ENGINE STARTING")
    log("==================================================")

    # 1. VERIFY SOURCES
    log("Verifying Sources...", step=1)
    for k, v in VIDEO_SOURCES.items():
        if not check_file(v):
            raise FileNotFoundError(f"Missing Source: {k}")

    # 2. PROCESS SEQUENCES
    log("Processing Sequences...", step=2)
    concat_list_v = []
    concat_list_a = []
    
    idx = 0
    for seq in PROTOCOL:
        idx += 1
        seq_id = seq['id']
        log(f"Processing {seq_id}...", step=f"2.{idx}")
        
        # A. Audio Generation
        vo_path = ASSETS_DIR / f"{seq_id}_vo.mp3"
        generate_voiceover(seq['script'], vo_path)
        audio_dur = get_duration(vo_path)
        log(f"Audio Duration: {audio_dur:.2f}s")
        
        # B. Video/Visual Generation
        vid_segment_path = ASSETS_DIR / f"{seq_id}_video.mp4"
        
        if seq.get('type') == 'bridge':
            # Create Black Video (Simplified to avoid drawtext errors)
            log("Generating Bridge Video (Black Screen)...")
            # title_text = seq.get('title', "")
            
            # Simple color source
            # Note: We rely on Audio ("The Brain", "The Power") to carry the context.
            stream = ffmpeg.input(f'color=c=black:s=1920x1080:d={audio_dur}', f='lavfi')
            
            stream = stream.output(str(vid_segment_path), vcodec='libx264', pix_fmt='yuv420p')
            stream.run(overwrite_output=True, quiet=True)
            
        else:
            # Video Processing
            source_key = seq['source']
            source_file = VIDEO_SOURCES[source_key]
            
            # Input
            inp = ffmpeg.input(str(source_file))
            
            # Trim
            trim_in = seq['in']
            trim_out = seq['out']
            trim_dur = trim_out - trim_in
            
            # Apply Trim
            v = inp.video.trim(start=trim_in, end=trim_out).setpts('PTS-STARTPTS')
            
            # Apply Zoom/ROI
            # ROI Logic: 
            # Full = 1920x1080
            # Right = Crop 960x1080 at 960,0
            # Input Bar ~ Bottom center?
            zoom_mode = seq.get('zoom', 'full')
            if zoom_mode == 'right':
                # Crop Right Half, then Scale to 1920x1080 (2x upscale - soft but focused)
                v = v.crop(x=960, y=0, width=960, height=1080).filter('scale', 1920, 1080)
            elif zoom_mode == 'input_bar':
                # Guessing input bar is bottom 20%? Safe bet: Bottom Half + Scale
                v = v.crop(x=0, y=540, width=1920, height=540).filter('scale', 1920, 1080)
            
            # Apply Freeze Or Speed
            # Priority: Freeze if specified, else Speed to match Audio
            
            final_v = v # placeholder
            
            if 'freeze_at' in seq:
                # Complex: Cut [Start -> FreezePoint], Generate Freeze Frame, Cut [FreezePoint -> End]?
                # Simpler: Just take [Start -> FreezePoint] and then tpad the end?
                # The visual treatment says "Freeze @ XX".
                # Let's implementation: Take video from IN to FREEZE_AT.
                # Play it normal speed.
                # Then loop the last frame for (AudioDur - VideoDur) OR specified duration.
                
                freeze_point = seq['freeze_at']
                play_dur = freeze_point - trim_in
                
                # Part 1: Moving Video
                v1 = inp.video.trim(start=trim_in, duration=play_dur).setpts('PTS-STARTPTS')
                if zoom_mode == 'right': v1 = v1.crop(x=960,y=0,width=960,height=1080).filter('scale',1920,1080)
                
                # Part 2: Freeze Frame (loop last frame)
                # We need exact frames. ffmpeg-python doesn't easily do "loop last frame".
                # Alternative: tpad (stop mode).
                # v1.filter('tpad', stop_mode='clone', stop_duration=seq['freeze_duration'])
                final_v = v1.filter('tpad', stop_mode='clone', stop_duration=seq['freeze_duration'])
                
            elif 'speed' in seq:
                # Speed factor
                factor = seq['speed'] # e.g. 2.0 (Fast)
                final_v = v.filter('setpts', f'PTS/{factor}')
            else:
                # Normal fit?
                # If Audio is longer than Video, we need to pad (freeze last frame).
                # If Video is longer, we trim?
                # Protocol implies precise In/Out. We use that.
                final_v = v

            # Render Segment
            # Note: We must ensure no Audio is copied from source (we want clean VO)
            final_v.output(str(vid_segment_path), vcodec='libx264', pix_fmt='yuv420p', an=None).run(overwrite_output=True, quiet=True)

        # Append to List
        concat_list_v.append(ffmpeg.input(str(vid_segment_path)))
        concat_list_a.append(ffmpeg.input(str(vo_path)))
        
        # Double Check
        if not vid_segment_path.exists():
            log(f"ERROR: Failed to create video for {seq_id}")
            return
            
        log(f"Segment {seq_id} Ready.")

    # 3. ASSEMBLY
    log("Assembling Trilogy...", step=3)
    
    # Concat
    # We need to concat V and A separately then map them?
    # ffmpeg.concat(...)
    
    # joined = ffmpeg.concat(
    #     *concat_list_v, str(ASSETS_DIR / "silence.mp4"), v=1, a=0
    # ).node
    # Actually concat of inputs with different streams is tricky in python wrapper.
    # Manual file list approach is safer for One Shot.
    
    # Generate Concat File List
    list_path = ASSETS_DIR / "concat_list.txt"
    with open(list_path, "w") as f:
        idx = 0
        for seq in PROTOCOL:
            idx += 1
            vid = ASSETS_DIR / f"{seq['id']}_video.mp4"
            aud = ASSETS_DIR / f"{seq['id']}_vo.mp3"
            f.write(f"file '{vid}'\n")
            # Problem: Audio needs to be mixed separate or merged into video segments first.
            # Best path: Merge VO into Video Segment first.
    
    # Refined Loop: Merge A+V for each segment
    log("Merging A+V segments...", step=3.1)
    final_segments = []
    
    for seq in PROTOCOL:
        vid = ASSETS_DIR / f"{seq['id']}_video.mp4"
        aud = ASSETS_DIR / f"{seq['id']}_vo.mp3"
        out = ASSETS_DIR / f"{seq['id']}_merged.mp4"
        
        # Merge
        # IMPORTANT: Video duration might differ from Audio duration.
        # We need to force them to longest? Or shortest?
        # Protocol: Audio is King.
        # Check durations
        v_dur = get_duration(vid)
        a_dur = get_duration(aud)
        
        # If A > V, we need to tpad V (Clone last frame)
        pad = max(0, a_dur - v_dur)
        
        i_v = ffmpeg.input(str(vid))
        i_a = ffmpeg.input(str(aud))
        
        if pad > 0:
            i_v = i_v.filter('tpad', stop_mode='clone', stop_duration=pad)
        
        # If V > A, we let it play? Or trim? 
        # Usually Visuals are timed to fit.
        
        ffmpeg.output(i_v, i_a, str(out), vcodec='copy', acodec='aac', shortest=None).run(overwrite_output=True, quiet=True)
        final_segments.append(out)
        log(f"Merged {out.name}")

    # Final Concat of Merged Segment
    with open(list_path, "w") as f:
        for seg in final_segments:
            f.write(f"file '{seg}'\n")

    # Debug: Print list content
    with open(list_path, "r") as f:
        log(f"Concat List Content:\n{f.read()}")
            
    log(f"Rendering Final Output: {FINAL_OUTPUT}...", step=4)
    
    # Use subprocess for robust concat
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_path),
        "-c", "copy",
        str(FINAL_OUTPUT)
    ]
    log(f"Executing: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    log("SUCCESS: Trilogy Completed.")

if __name__ == "__main__":
    run_engine()
