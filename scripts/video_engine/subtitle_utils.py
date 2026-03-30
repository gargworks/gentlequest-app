"""
PNG Overlay Generation Utility for Synced Captions.
Fallback for FFmpeg installations without 'subtitles' or 'drawtext' filters.
"""

import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def generate_caption_overlays(offsets: list, output_dir: str, video_width=1080, video_height=1920, style="standard"):
    """
    Generates individual PNG images for each word with timing metadata.
    Each image is a full transparent frame with the word centered/styled.
    - style: "standard" (Yellow text, shadow) or "intern" (Yellow text, opaque black box)
    Returns: List of dicts {path, start, end}
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # 1. SETUP STYLING
    # Try to find a nice font, fallback to default
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",  # Mac
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", # Linux
        "Arial"
    ]
    font = None
    font_size = 100
    for p in font_paths:
        try:
            font = ImageFont.truetype(p, font_size)
            break
        except: continue
    
    if not font:
        font = ImageFont.load_default()

    caption_images = []
    
    # 2. GENERATE FRAMES
    for i, entry in enumerate(offsets):
        word = entry["word"].upper()
        start_time = entry["time_seconds"]
        
        # End time logic
        if i < len(offsets) - 1:
            end_time = offsets[i+1]["time_seconds"]
        else:
            end_time = start_time + 1.2 # Buffer for last word
            
        # Create transparent frame
        img = Image.new("RGBA", (video_width, video_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Text positioning (Center bottom-ish)
        # In modern PIL, textbbox returns (left, top, right, bottom)
        bbox = draw.textbbox((0, 0), word, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        x = (video_width - w) / 2
        y = (video_height * 0.7) - (h / 2) # 70% down the screen
        
        if style == "intern":
            # Opaque black box background
            padding = 20
            draw.rectangle(
                [x - padding, y - padding, x + w + padding, y + h + padding],
                fill=(0, 0, 0, 180)
            )
            # Bright Yellow Text
            draw.text((x, y), word, font=font, fill=(255, 255, 0, 255))
        else:
            # Standard: Draw Shadow (Subtle lift)
            shadow_offset = 6
            draw.text((x + shadow_offset, y + shadow_offset), word, font=font, fill=(0, 0, 0, 180))
            
            # Draw Primary Text (Bright Yellow / High Contrast)
            draw.text((x, y), word, font=font, fill=(255, 255, 0, 255))
        
        # Save PNG
        frame_name = f"word_{i:04d}.png"
        frame_path = out_path / frame_name
        img.save(frame_path)
        
        caption_images.append({
            "path": str(frame_path),
            "start": start_time,
            "end": end_time
        })
        
    return caption_images
def generate_final_highlight(text: str, output_path: str, video_width=1080, video_height=1920):
    """
    Generates a single PNG with a stylized highlight text (e.g. for loop closure).
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. SETUP STYLING (Larger, bold font for highlight)
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "Arial"
    ]
    font = None
    font_size = 80 # Slightly smaller than word captions but bold
    for p in font_paths:
        try:
            font = ImageFont.truetype(p, font_size)
            break
        except: continue
    
    if not font:
        font = ImageFont.load_default()

    # Create transparent frame
    img = Image.new("RGBA", (video_width, video_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Text positioning (Center-weighted)
    # Split text into lines if too long
    words = text.split()
    lines = []
    current_line = []
    for w in words:
        current_line.append(w)
        test_line = " ".join(current_line)
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) > (video_width * 0.8):
            lines.append(" ".join(current_line[:-1]))
            current_line = [w]
    lines.append(" ".join(current_line))

    # Calculate total height of block
    line_height = font_size + 10
    total_h = len(lines) * line_height
    curr_y = (video_height - total_h) / 2 # Dead center
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        curr_x = (video_width - line_w) / 2
        
        # Draw Background Box for Readability (Semi-transparent black)
        padding = 20
        draw.rectangle(
            [curr_x - padding, curr_y - padding, curr_x + line_w + padding, curr_y + font_size + padding], 
            fill=(0, 0, 0, 160)
        )
        
        # Draw Text (White)
        draw.text((curr_x, curr_y), line, font=font, fill=(255, 255, 255, 255))
        curr_y += line_height

    # Save PNG
    img.save(out_file)
    return str(out_file)
