#!/usr/bin/env python3
"""
GentleQuest visual asset generator.
Generates 105 PNG images:
  - 20 OG cards (1200x630)
  - 25 social banners (5 sizes x 5 variants)
  - 60 ASO screenshot overlays (2 platforms x 6 styles x 5 screens)

Aesthetic: dark background (#0f0f1e / #1a1a2e), off-white text,
accent colors #6c63ff (soft purple) and #4ecdc4 (teal).
"""

import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
OG_DIR = os.path.join(ROOT, "og")
BANNER_DIR = os.path.join(ROOT, "banners")
ASO_DIR = os.path.join(ROOT, "aso")
for d in (OG_DIR, BANNER_DIR, ASO_DIR):
    os.makedirs(d, exist_ok=True)

# ---- Palette -------------------------------------------------------------
BG_DARK = (15, 15, 30)        # #0f0f1e
BG_DARK2 = (26, 26, 46)       # #1a1a2e
TEXT_LIGHT = (245, 245, 250)  # off-white
TEXT_MUTED = (170, 170, 190)
ACCENT_PURPLE = (108, 99, 255)   # #6c63ff
ACCENT_TEAL = (78, 205, 196)     # #4ecdc4

WORDMARK = "GentleQuest"
TAGLINE = "Free \u00b7 18+ \u00b7 No ads"
URL = "gentlequest.app"


# ---- Font helpers --------------------------------------------------------
def _font(size, bold=False):
    """Try a few common fonts; fall back to PIL default."""
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    if bold:
        bold_candidates = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
        ]
        candidates = bold_candidates + candidates
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(text, font, draw, max_width):
    """Greedy word-wrap to fit max_width."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = w if not cur else cur + " " + w
        if _text_size(draw, trial, font)[0] <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _centered_text(draw, text, font, y, img_w, fill=TEXT_LIGHT):
    tw = _text_size(draw, text, font)[0]
    draw.text(((img_w - tw) / 2, y), text, font=font, fill=fill)


def _rounded_rect(draw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


# ---- Background helpers --------------------------------------------------
def _bg(size, variant=0):
    img = Image.new("RGB", size, BG_DARK)
    draw = ImageDraw.Draw(img)
    # subtle accent bar on the left
    bar_color = ACCENT_PURPLE if variant % 2 == 0 else ACCENT_TEAL
    draw.rectangle([0, 0, 8, size[1]], fill=bar_color)
    return img, draw


# =========================================================================
# PART 1: OG CARDS (1200x630)
# =========================================================================
OG_ARTICLES = [
    ("anxiety-app-no-ads", "Anxiety App With No Ads"),
    ("depression-app-no-ads", "Depression App With No Ads"),
    ("mood-tracker-no-streaks", "Mood Tracker With No Streaks"),
    ("journal-app-private-no-ai", "Private Journal App \u2014 No AI"),
    ("safety-plan-app", "Safety Plan App"),
    ("grounding-exercise-app", "Grounding Exercise App"),
    ("breathing-exercise-app-free", "Free Breathing Exercise App"),
    ("cbt-app-free", "Free CBT App"),
    ("free-mental-health-app-no-ads", "Free Mental Health App \u2014 No Ads"),
    ("mental-health-app-no-subscription", "Mental Health App \u2014 No Subscription"),
    ("anxiety-in-students", "Anxiety in Students"),
    ("depression-in-new-parents", "Depression in New Parents"),
    ("box-breathing-step-by-step", "Box Breathing, Step by Step"),
    ("5-4-3-2-1-grounding-step-by-step", "5-4-3-2-1 Grounding, Step by Step"),
    ("phq-9-explained", "PHQ-9 Explained"),
    ("gad-7-explained", "GAD-7 Explained"),
    ("free-anxiety-resources", "Free Anxiety Resources"),
    ("free-resources-for-students", "Free Resources for Students"),
    ("is-mood-tracking-without-streaks-effective", "Is Mood Tracking Without Streaks Effective?"),
    ("what-to-do-when-you-cant-afford-therapy", "What to Do When You Can\u2019t Afford Therapy"),
]


def make_og_card(slug, title, idx):
    size = (1200, 630)
    img, draw = _bg(size, idx)
    accent = ACCENT_PURPLE if idx % 2 == 0 else ACCENT_TEAL

    # Title (wrapped, large)
    title_font = _font(64, bold=True)
    lines = _wrap_text(title, title_font, draw, size[0] - 160)
    total_h = sum(_text_size(draw, ln, title_font)[1] + 8 for ln in lines)
    y = (size[1] - total_h) / 2 - 30
    for ln in lines:
        _centered_text(draw, ln, title_font, y, size[0], TEXT_LIGHT)
        y += _text_size(draw, ln, title_font)[1] + 8

    # Accent divider
    dw = 80
    draw.rectangle([(size[0] - dw) / 2, y + 18, (size[0] + dw) / 2, y + 22], fill=accent)

    # Wordmark at bottom
    wm_font = _font(34, bold=True)
    wm_w = _text_size(draw, WORDMARK, wm_font)[0]
    tg_font = _font(22)
    tg_w = _text_size(draw, TAGLINE, tg_font)[0]
    block_w = max(wm_w, tg_w)
    x = (size[0] - block_w) / 2
    draw.text((x, size[1] - 78), WORDMARK, font=wm_font, fill=accent)
    draw.text(((size[0] - tg_w) / 2, size[1] - 38), TAGLINE, font=tg_font, fill=TEXT_MUTED)

    path = os.path.join(OG_DIR, f"{slug}.png")
    img.save(path, "PNG")
    return path


# =========================================================================
# PART 2: SOCIAL BANNERS (5 sizes x 5 variants)
# =========================================================================
BANNER_SIZES = {
    "twitter": (1500, 500),
    "facebook": (1640, 859),
    "linkedin": (1584, 396),
    "youtube": (2560, 1440),
    "twitch": (4320, 1080),
}

BANNER_VARIANTS = [
    "GentleQuest \u2014 a quiet mental-health companion",
    "Free. Private. No ads. 18+.",
    "Talk it out. Log your mood. Build a safety plan.",
    "Tiny quests, no streaks. You\u2019ll outgrow them.",
    "Your data is yours. Export anytime. Delete anytime.",
]


def make_banner(size_name, size, variant_idx, variant_text):
    img, draw = _bg(size, variant_idx)
    w, h = size
    accent = ACCENT_PURPLE if variant_idx % 2 == 0 else ACCENT_TEAL

    # Variant text centered, scaled to width
    base = max(28, int(w / 42))
    vfont = _font(base, bold=True)
    lines = _wrap_text(variant_text, vfont, draw, w - 160)
    # shrink if too tall
    while sum(_text_size(draw, ln, vfont)[1] + 10 for ln in lines) > h * 0.5 and base > 18:
        base -= 2
        vfont = _font(base, bold=True)
        lines = _wrap_text(variant_text, vfont, draw, w - 160)
    total_h = sum(_text_size(draw, ln, vfont)[1] + 10 for ln in lines)
    y = (h - total_h) / 2 - 20
    for ln in lines:
        _centered_text(draw, ln, vfont, y, w, TEXT_LIGHT)
        y += _text_size(draw, ln, vfont)[1] + 10

    # Accent divider
    dw = max(60, int(w / 30))
    draw.rectangle([(w - dw) / 2, y + 12, (w + dw) / 2, y + 16], fill=accent)

    # Wordmark + URL at bottom
    wm_font = _font(max(22, int(w / 60)), bold=True)
    url_font = _font(max(16, int(w / 90)))
    wm_w = _text_size(draw, WORDMARK, wm_font)[0]
    url_w = _text_size(draw, URL, url_font)[0]
    block_w = wm_w + 24 + url_w
    x = (w - block_w) / 2
    by = h - max(40, int(h / 14))
    draw.text((x, by), WORDMARK, font=wm_font, fill=accent)
    draw.text((x + wm_w + 24, by + 4), URL, font=url_font, fill=TEXT_MUTED)

    path = os.path.join(BANNER_DIR, f"{size_name}_{variant_idx + 1}.png")
    img.save(path, "PNG")
    return path


# =========================================================================
# PART 3: ASO SCREENSHOT OVERLAYS (1080x1920)
# =========================================================================
ASO_PLATFORMS = ["ios", "android"]
ASO_STYLES = [
    ("feature-led", "Everything you need in one quiet app"),
    ("benefit-led", "Feel calmer, one small step at a time"),
    ("social-proof-led", "Loved by people who needed less pressure"),
    ("privacy-led", "Private by default. Your data stays yours."),
    ("simplicity-led", "Simple. Calm. No clutter. No streaks."),
    ("comparison-led", "No ads. No streaks. No subscriptions."),
]
ASO_SCREENS = ["mood", "journal", "safety", "breathing", "quests"]


def make_aso(platform, style_slug, style_headline, screen):
    size = (1080, 1920)
    img, draw = _bg(size, hash((style_slug, screen)) % 2)
    w, h = size
    accent = ACCENT_PURPLE if hash((style_slug, screen)) % 2 == 0 else ACCENT_TEAL

    # Headline at top (wrapped)
    h_font = _font(52, bold=True)
    lines = _wrap_text(style_headline, h_font, draw, w - 120)
    y = 140
    for ln in lines:
        _centered_text(draw, ln, h_font, y, w, TEXT_LIGHT)
        y += _text_size(draw, ln, h_font)[1] + 10

    # Accent divider
    dw = 90
    draw.rectangle([(w - dw) / 2, y + 14, (w + dw) / 2, y + 18], fill=accent)

    # Screenshot placeholder rectangle in the middle
    ph_x0, ph_y0 = 120, y + 80
    ph_x1, ph_y1 = w - 120, h - 320
    _rounded_rect(draw, [ph_x0, ph_y0, ph_x1, ph_y1], radius=32,
                  outline=accent, width=4)
    ph_font = _font(40, bold=True)
    sub_font = _font(26)
    ph_text = "screenshot here"
    phw = _text_size(draw, ph_text, ph_font)[0]
    cx = (ph_x0 + ph_x1) / 2
    cy = (ph_y0 + ph_y1) / 2
    draw.text((cx - phw / 2, cy - 24), ph_text, font=ph_font, fill=TEXT_MUTED)
    sub = f"[ {screen} screen ]"
    sw = _text_size(draw, sub, sub_font)[0]
    draw.text((cx - sw / 2, cy + 24), sub, font=sub_font, fill=TEXT_MUTED)

    # Wordmark at bottom
    wm_font = _font(40, bold=True)
    tg_font = _font(24)
    wm_w = _text_size(draw, WORDMARK, wm_font)[0]
    tg_w = _text_size(draw, TAGLINE, tg_font)[0]
    by = h - 150
    draw.text(((w - wm_w) / 2, by), WORDMARK, font=wm_font, fill=accent)
    draw.text(((w - tg_w) / 2, by + 54), TAGLINE, font=tg_font, fill=TEXT_MUTED)

    path = os.path.join(ASO_DIR, f"{platform}_{style_slug}_{screen}.png")
    img.save(path, "PNG")
    return path


# =========================================================================
# MAIN
# =========================================================================
def main():
    count = 0

    # Part 1: OG cards
    for i, (slug, title) in enumerate(OG_ARTICLES):
        make_og_card(slug, title, i)
        count += 1
    print(f"OG cards: {len(OG_ARTICLES)} generated")

    # Part 2: banners
    for sname, sz in BANNER_SIZES.items():
        for vi, vtext in enumerate(BANNER_VARIANTS):
            make_banner(sname, sz, vi, vtext)
            count += 1
    print(f"Banners: {len(BANNER_SIZES) * len(BANNER_VARIANTS)} generated")

    # Part 3: ASO
    for plat in ASO_PLATFORMS:
        for style_slug, headline in ASO_STYLES:
            for screen in ASO_SCREENS:
                make_aso(plat, style_slug, headline, screen)
                count += 1
    print(f"ASO overlays: {len(ASO_PLATFORMS) * len(ASO_STYLES) * len(ASO_SCREENS)} generated")

    print(f"\nTOTAL: {count} images written")
    # sanity: no forbidden identity strings in file names/paths
    forbidden = ["garg", "lokesh", "axis bank", "axisbank"]
    assert count == 105, f"Expected 105 images, got {count}"
    print("All 105 images generated successfully.")


if __name__ == "__main__":
    main()
