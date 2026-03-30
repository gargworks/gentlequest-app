import os
import sys
import json
import subprocess
from pathlib import Path

# Paths
BELIEVE_IT_BOT_DIR = "/Users/lokeshgarg/apps/believe-it-bot"
XTTS_PYTHON = f"{BELIEVE_IT_BOT_DIR}/venv_xtts/bin/python3"

def generate_precise_offsets(audio_path, output_json):
    """
    Uses whisper (from venv_xtts) to generate word-level timestamps.
    """
    print(f"🔍 Transcribing {audio_path} for precise offsets...")
    
    # script to run inside the venv
    transcribe_script = f"""
import whisper
import json
import os

model = whisper.load_model("base.en")
result = model.transcribe("{audio_path}", verbose=False, word_timestamps=True)

words = []
for segment in result['segments']:
    for word in segment['words']:
        words.append({{
            "word": word['word'].strip(),
            "start": word['start'],
            "end": word['end'],
            "time_seconds": word['start']
        }})

with open("{output_json}", "w") as f:
    json.dump(words, f, indent=4)
"""
    
    cmd = [XTTS_PYTHON, "-c", transcribe_script]
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{BELIEVE_IT_BOT_DIR}:{env.get('PYTHONPATH', '')}"
    
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Transcription Failure:\n{result.stderr}")
        return False
        
    print(f"✅ Precise Offsets JSON: {output_json}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 generate_offsets.py <audio_path> <output_json>")
        sys.exit(1)
        
    generate_precise_offsets(sys.argv[1], sys.argv[2])
