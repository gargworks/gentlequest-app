import logging
import subprocess
import os
from PIL import Image, ImageDraw, ImageFont
from scripts.video_engine.config import NUCLEUS_BRAND_CONFIG
from pathlib import Path

def get_output_dir():
    return Path("/Users/lokeshgarg/ai-mvp-backend/test_output")

logger = logging.getLogger(__name__)

BRAND_CONFIGS = {
    "nucleus": NUCLEUS_BRAND_CONFIG
}

def synthesize_end_card(brand_id="nucleus", output_path=None):
    """
    Generates a branded end-card video clip.
    """
    config = BRAND_CONFIGS.get(brand_id, BRAND_CONFIGS["nucleus"])
    output_dir = get_output_dir() / "branding"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not output_path:
        output_path = output_dir / f"{brand_id}_end_card.mp4"
    
    logger.info(f"Synthesizing End-Card for: {brand_id}")
    
    # 1. GENERATE AUDIO (Using a simple fallback or reusing audio_provider if needed)
    vo_path = output_dir / f"{brand_id}_vo.mp3"
    # For now, we'll assume the user has the Google Cloud TTS environment or we use an existing clip.
    # In a real integration, we'd call audio_provider.generate_narration.
    # For this refactor, we provide the logic to be hooked in.
    
    # 2. CREATE IMAGE
    width, height = 1080, 1920
    canvas = Image.new('RGBA', (width, height), config["bg_color"])
    draw = ImageDraw.Draw(canvas)
    
    # Font setup
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "Arial"
    ]
    font_bold = None
    font_reg = None
    for p in font_paths:
        try:
            font_bold = ImageFont.truetype(p, 80)
            font_reg = ImageFont.truetype(p, 60)
            break
        except: continue

    # Paste Logo
    if config["logo_path"] and os.path.exists(config["logo_path"]):
        logo = Image.open(config["logo_path"]).convert("RGBA")
        logo = logo.resize((600, 600), Image.LANCZOS)
        canvas.paste(logo, (240, 400), logo)
    
    # Draw Text
    tagline_parts = config["tagline"].split(". ")
    draw.text((width//2, 1100), tagline_parts[0], font=font_bold, fill=config["text_color"], anchor="mm")
    if len(tagline_parts) > 1:
        draw.text((width//2, 1200), tagline_parts[1], font=font_reg, fill=config["text_color"], anchor="mm")
    
    draw.text((width//2, 1500), config["cta"], font=font_bold, fill=config["cta_color"], anchor="mm")
    
    frame_path = output_dir / f"{brand_id}_frame.png"
    canvas.save(frame_path)
    
    # 3. ASSEMBLE CLIP (Placeholder silence if VO generation is pending)
    # We use a 4s fixed duration for end-cards.
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(frame_path),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-t", "4", "-pix_fmt", "yuv420p", "-shortest",
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True)
    
    return str(output_path)
