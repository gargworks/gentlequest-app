from PIL import Image, ImageDraw, ImageFont

# Create 1200x630 image
width, height = 1200, 630
img = Image.new('RGB', (width, height), color='#0a0a1a')
draw = ImageDraw.Draw(img)

# Gradient background
for i in range(height):
    shade = int(10 + (i / height) * 15)
    draw.rectangle([(0, i), (width, i+1)], fill=f'#{shade:02x}{shade:02x}{min(shade+20, 255):02x}')

# Glowing circles
for (cx, cy), radius, color in [((300, 315), 120, '#3d5afe'), ((900, 315), 120, '#d500f9'), ((600, 315), 80, '#ffd600')]:
    for r in range(radius, 0, -10):
        draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], outline=color, width=2)

# Fonts
try:
    title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
    subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
except:
    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()
    small_font = ImageFont.load_default()

# Text
title_bbox = draw.textbbox((0, 0), "NUCLEUS OS", font=title_font)
draw.text(((width - (title_bbox[2] - title_bbox[0])) // 2, 100), "NUCLEUS OS", font=title_font, fill='#ffffff')

subtitle_bbox = draw.textbbox((0, 0), "The Sovereign Agent Control Plane", font=subtitle_font)
draw.text(((width - (subtitle_bbox[2] - subtitle_bbox[0])) // 2, 200), "The Sovereign Agent Control Plane", font=subtitle_font, fill='#b388ff')

tagline_bbox = draw.textbbox((0, 0), "Own your Agent Context with Low-Level Sovereignty", font=small_font)
draw.text(((width - (tagline_bbox[2] - tagline_bbox[0])) // 2, 520), "Own your Agent Context with Low-Level Sovereignty", font=small_font, fill='#9e9e9e')

# Save
img.save('nucleus-social.jpg', 'JPEG', quality=95)
print("✅ Saved: nucleus-social.jpg")

