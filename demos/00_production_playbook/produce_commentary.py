import subprocess
from pathlib import Path
import json
import os

# Configuration
ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / "00_production_playbook" / "output"
ASSETS_DIR = ROOT_DIR / "assets"
FFMPEG = "ffmpeg"

# The "Minimalist Assertion" Script Map
SCRIPT_MAP = [
    {
        "id": "vo_01_physics",
        "text": "The Governance Layer isn't just a setting... It's physics.",
        "start_time": "00:00:08", # Sync with "NONE are safe"
        "sfx": "sub_drop"
    },
    {
        "id": "vo_02_recall",
        "text": "Total context recall. Instantly.",
        "start_time": "00:00:30", # Sync with List
        "sfx": "none"
    },
    {
        "id": "vo_03_provenance",
        "text": "Full provenance. It remembers *who* made the decision, and *when*.",
        "start_time": "00:00:38", # Sync with "Architect Agent"
        "sfx": "none"
    },
    {
        "id": "vo_04_sovereign",
        "text": "The Sovereign Command.",
        "start_time": "00:00:46", # Sync with start of Demo C
        "sfx": "none"
    },
    {
        "id": "vo_05_mount",
        "text": "One instruction to mount the entire infrastructure.",
        "start_time": "00:01:10", # Sync with Spinner
        "sfx": "riser"
    },
    {
        "id": "vo_06_aggregated",
        "text": "Stripe. Postgres. Search... Aggregated.",
        "start_time": "00:01:25", # Sync with "Demonstration Complete"
        "sfx": "none"
    },
    {
        "id": "vo_07_live_data",
        "text": "Live production data. Natural language. Zero API keys.",
        "start_time": "00:01:35", # Sync with Stripe List
        "sfx": "none"
    },
    {
        "id": "vo_08_mission_complete",
        "text": "Mission complete. Trace deleted.",
        "start_time": "00:01:50", # Sync with Unmount
        "sfx": "power_down"
    }
]

from google.cloud import texttospeech

def check_gcp_credentials():
    """Checks for GCP credentials or active gcloud session."""
    try:
        # Check for GOOGLE_APPLICATION_CREDENTIALS
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            return True
        
        # Check for gcloud auth
        result = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True)
        if result.returncode == 0:
            return True
            
        print("❌ No valid GCP credentials found.")
        print("Please run: gcloud auth application-default login")
        return False
    except FileNotFoundError:
        print("❌ gcloud command not found.")
        return False

def generate_voiceover(item):
    """Generates voiceover using Google Cloud TTS Chirp 3."""
    client = texttospeech.TextToSpeechClient()
    
    input_text = texttospeech.SynthesisInput(text=item['text'])
    
    # User requested en-US-Chirp3-HD-Charon
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Chirp3-HD-Charon"
    )
    
    # Pace control: 0.9 for "Deep/Onyx" gravitas
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.9
    )
    
    print(f"🎙️ Cloud TTS Request: {item['text']} (Voice: Charon, Rate: 0.9)")
    response = client.synthesize_speech(
        input=input_text,
        voice=voice,
        audio_config=audio_config
    )
    
    output_path = ASSETS_DIR / f"{item['id']}.mp3"
    with open(output_path, "wb") as out:
        out.write(response.audio_content)
        print(f"✅ Generated: {output_path.name}")

def check_assets():
    """Verifies that VO and SFX files exist."""
    
    if not check_gcp_credentials():
        return False
        
    # Generate VOs if missing
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for item in SCRIPT_MAP:
        vo_path = ASSETS_DIR / f"{item['id']}.mp3"
        if not vo_path.exists():
            print(f"🎙️ Generating VO: {item['id']}...")
            try:
                generate_voiceover(item)
            except Exception as e:
                print(f"❌ Failed to generate {item['id']}: {e}")
                return False
            
    # Check SFX (Mock check for now)
    # sfx_keyboard.mp3, sfx_snap.mp3, etc.
    
    return True

def mix_audio():
    """Mixes the VO and SFX into a single track using FFmpeg."""
    print("🎛️  Mixing Audio Track...")
    
    # Constructing the complex filter
    inputs = []
    filter_parts = []
    
    # 1. Background Ambience (Server Hum) - Loop it?
    # inputs.append("-i", str(ASSETS_DIR / "sfx_server_hum.mp3"))
    
    # 2. Add VOs
    for i, item in enumerate(SCRIPT_MAP):
        vo_path = ASSETS_DIR / f"{item['id']}.mp3"
        inputs.extend(["-i", str(vo_path)])
        
        # Delay filter (adelay uses milliseconds)
        # Parse start_time "HH:MM:SS" -> ms
        h, m, s = map(float, item['start_time'].split(':'))
        delay_ms = int((h*3600 + m*60 + s) * 1000)
        
        filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}]")
        
    # Mix all [aX] streams
    mix_input = "".join([f"[a{i}]" for i in range(len(SCRIPT_MAP))])
    filter_parts.append(f"{mix_input}amix=inputs={len(SCRIPT_MAP)}:dropout_transition=2[out]")
    
    cmd = [
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", ";".join(filter_parts),
        "-map", "[out]",
        str(OUTPUT_DIR / "nucleus_demo_commentary_final.mp3")
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def merge_with_video():
    """Merges the new audio mix with the LOCKED video."""
    print("🎬 Merging with LOCKED Video...")
    
    video_path = OUTPUT_DIR / "nucleus_demo_master_LOCKED.mp4"
    audio_path = OUTPUT_DIR / "nucleus_demo_commentary_final.mp3"
    final_output = OUTPUT_DIR / "nucleus_demo_trilogy_final.mp4"
    
    if not video_path.exists():
        print(f"❌ Video not found: {video_path}")
        return

    # Complex filter to replace audio
    # -map 0:v (Video from file 0)
    # -map 1:a (Audio from file 1)
    # -shortest (End when shortest stream ends, just in case)
    
    cmd = [
        FFMPEG, "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "copy", # No re-encoding of video!
        "-c:a", "aac", "-b:a", "192k",
        str(final_output)
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"\n✅ SUCCESS: {final_output}")

if __name__ == "__main__":
    if check_assets():
        mix_audio()
        merge_with_video()
    else:
        # Create a generation manifest for the user
        manifest_path = ROOT_DIR / "00_production_playbook" / "VO_GENERATION_MANIFEST.json"
        with open(manifest_path, "w") as f:
            json.dump(SCRIPT_MAP, f, indent=4)
        print(f"\n✅ Created Generation Manifest: {manifest_path}")
        print("Run this list through your TTS provider.")
