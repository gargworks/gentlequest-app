import os
from pathlib import Path
from google.cloud import texttospeech

TTS_CLIENT = texttospeech.TextToSpeechClient()
VOICE_NAME = "en-US-Chirp3-HD-Charon"
TEMP_DIR = Path("/Users/lokeshgarg/ai-mvp-backend/demos/sovereign-control-campaign/assets/temp_shorts")
TEMP_DIR.mkdir(exist_ok=True, parents=True)

def generate_tts(text, voice_name, output_path):
    print(f"[TTS] Generating: {text}")
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=voice_name)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3, 
        speaking_rate=0.95 # Slightly slower for "Sovereign" weight
    )
    response = TTS_CLIENT.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(output_path, "wb") as out:
        out.write(response.audio_content)

scripts = {
    "short_2_atomic": "Daily Orientation. Topic: The Windows Gap. Most agents fail on Windows because the environment is non-deterministic. We fixed this with the Atomic Setup. One command. Winget acquisition of Git, Python 3.11, and FFmpeg. Zero manual path editing. Zero 'DLL not found' errors. Windows is now a first-class citizen of the Sovereign Monolith. Atomic Ignition. Local control. Start now at Nucleus dash O S dot dev.",
    "short_3_shield": "System Warning. There is a silent killer in your local repo. CRLF line endings. If your agent writes Mac-style code on Windows, the build dies. We deployed the Git Shield to stop it. Atomic enforcement of LF endings via git-attributes. Universal repo health, regardless of the host OS. Protect the logic. Maintain the Monolith. Nucleus dash O S dot dev."
}

for key, text in scripts.items():
    output = TEMP_DIR / f"{key}_vo.mp3"
    generate_tts(text, VOICE_NAME, output)
    print(f"Generated {output}")
