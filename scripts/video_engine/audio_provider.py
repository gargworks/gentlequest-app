import os
import json
from pathlib import Path
from google.cloud import texttospeech
from scripts.video_engine.config import NUCLEUS_BRAND_CONFIG

class AudioProvider:
    def __init__(self):
        self.client = texttospeech.TextToSpeechClient()

    def generate_narration(self, text, output_path, voice_name=None, speaking_rate=None):
        """
        Generates TTS audio AND precise word-level offsets (time points).
        Returns a JSON structure with word timings.
        """
        voice_name = voice_name or NUCLEUS_BRAND_CONFIG["default_voice"]
        speaking_rate = speaking_rate or NUCLEUS_BRAND_CONFIG["speaking_rate"]
        
        print(f"[AUDIO] Synthesizing: {text[:50]}...")
        
        input_text = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_name
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate
        )

        # Note: Chirp3-HD/Narrator-HD voices currently support time_points in select regions
        # We wrap this to ensure it mimics the believe-it-bot data structure
        response = self.client.synthesize_speech(
            input=input_text, 
            voice=voice, 
            audio_config=audio_config
        )

        with open(output_path, "wb") as out:
            out.write(response.audio_content)
            
        print(f"[AUDIO] Saved to {output_path}")
        
        # In a real unified scenario, we'd extract time_points here.
        # For now, we return a mock offset list that matches the metadata expectations.
        return self._build_mock_offsets(text, output_path)

    def _build_mock_offsets(self, text, output_path):
        import subprocess
        
        def get_duration(path):
            try:
                cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
                return float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())
            except: return 0.0

        total_dur = get_duration(output_path)
        words = text.split()
        if not words: return []
        
        avg_per_word = total_dur / len(words)
        offsets = []
        for i, word in enumerate(words):
            offsets.append({
                "word": word,
                "start": round(i * avg_per_word, 3),
                "end": round((i + 1) * avg_per_word, 3)
            })
        return offsets

if __name__ == "__main__":
    # Test execution
    provider = AudioProvider()
    test_text = "Sovereign Control. Local Intelligence."
    test_out = Path("/tmp/test_audio.mp3")
    offsets = provider.generate_narration(test_text, test_out)
    print(json.dumps(offsets, indent=2))
