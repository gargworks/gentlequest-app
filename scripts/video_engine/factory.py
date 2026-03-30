import json
from pathlib import Path
from scripts.video_engine.config import NUCLEUS_BRAND_CONFIG, SIMULATION_MAP
from scripts.video_engine.audio_provider import AudioProvider
from scripts.video_engine.media_engine import MediaEngine
from scripts.video_engine.subtitle_utils import generate_caption_overlays

def produce_nucleus_short(short_id, audio_config_path):
    """
    Produces a Nucleus 'Intern' short using the Unified Sovereign Media Engine.
    """
    print(f"🎬 Starting Production: {short_id}")
    
    # 1. Load Config
    with open(audio_config_path, 'r') as f:
        config = json.load(f)
    
    short_meta = next((s for s in config['shorts'] if s['id'] == short_id), None)
    if not short_meta:
        raise ValueError(f"Short ID {short_id} not found in {audio_config_path}")

    # 2. Setup paths
    output_dir = Path("/Users/lokeshgarg/ai-mvp-backend/test_output") / short_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    vo_path = output_dir / "narration.mp3"
    final_mp4 = Path("/Users/lokeshgarg/ai-mvp-backend/test_output") / f"{short_id}_UNIFIED_v6.mp4"
    
    # 3. Generate Audio + Word Offsets
    audio_provider = AudioProvider()
    full_text = " ".join([c['text'] for c in short_meta['cues']])
    
    # For the unified engine, we need time_seconds in the offsets
    raw_offsets = audio_provider.generate_narration(full_text, vo_path)
    
    # Map 'start' to 'time_seconds' for subtitle_utils compatibility
    offsets = []
    for o in raw_offsets:
        o['time_seconds'] = o['start']
        offsets.append(o)

    # 4. Generate 'Intern Style' Captions
    caption_images = generate_caption_overlays(
        offsets=offsets,
        output_dir=str(output_dir / "captions"),
        style="intern"
    )

    # 5. Assemble Final Cut
    engine = MediaEngine()
    engine.assemble_final_cut(
        video_source=SIMULATION_MAP[short_id],
        audio_path=str(vo_path),
        output_path=str(final_mp4),
        caption_images=caption_images,
        source_type="simulation",
        brand_id="nucleus"
    )

    print(f"✅ Production Complete: {final_mp4}")
    return final_mp4

if __name__ == "__main__":
    CONFIG_PATH = "/Users/lokeshgarg/ai-mvp-backend/demos/sovereign-control-campaign/assets/WINDOWS_AUDIO_CONFIG.json"
    
    # Build Short #2: Atomic Ignition
    produce_nucleus_short("short_2_atomic", CONFIG_PATH)
