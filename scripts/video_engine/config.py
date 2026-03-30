from pathlib import Path

BASE_DIR = Path("/Users/lokeshgarg/ai-mvp-backend")
SOVEREIGN_ASSETS = BASE_DIR / "demos/sovereign-control-campaign/assets"

NUCLEUS_BRAND_CONFIG = {
    "id": "nucleus",
    "logo_path": "/Users/lokeshgarg/.gemini/antigravity/brain/6c3f8018-b6eb-4dae-9476-ed32eb313b95/nucleus_logo_sovereign_v2_1771899913460.png",
    "tagline": "Sovereign Control. Local Intelligence.",
    "cta": "nucleusos.dev",
    "bg_color": (10, 10, 15, 255),
    "text_color": "white",
    "cta_color": (0, 255, 255, 255), # Cyan
    "default_voice": "en-US-Chirp3-HD-Charon",
    "speaking_rate": 1.05,
    "font_path": "/System/Library/Fonts/Supplemental/Arial.ttf"
}

# Mapping of simulation IDs to their high-fidelity recordings
SIMULATION_MAP = {
    "short_2_atomic": "/Users/lokeshgarg/.gemini/antigravity/brain/6c3f8018-b6eb-4dae-9476-ed32eb313b95/windows_atomic_setup_v4_recording_1772025009217.webp", # Will try v4 webp or just use raw html if this fails
    "short_3_shield": "/Users/lokeshgarg/ai-mvp-backend/demos/sovereign-control-campaign/assets/git_shield_sim.mp4",
    "short_sovereign_vision": "/Users/lokeshgarg/ai-mvp-backend/demos/sovereign-control-campaign/assets/sovereign_test/kill_shot_simulation_v2.mp4"
}
