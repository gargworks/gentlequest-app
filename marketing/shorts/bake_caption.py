#!/usr/bin/env python3
"""Bake a caption + source image into a 1080x1920 PNG frame for the Short.

Usage:
  bake_caption.py --src SRC --out OUT --caption TEXT [--bg black|phone] [--size N]

phone mode: crops/scales SRC to fit 1080x1920, places caption with semi-trans pill at bottom.
black mode: solid black BG, centered caption (for title/end cards).
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1080, 1920
FONT = "/System/Library/Fonts/Avenir.ttc"


def load_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT, size, index=0)
    except OSError:
        return ImageFont.load_default()


def measure(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    return r - l, b - t


def make_phone_frame(src: Path, out: Path, caption: str, font_size: int = 58) -> None:
    img = Image.open(src).convert("RGB")
    # Fit src to fill 1080x1920 centered, preserving aspect ratio (cover, not contain)
    iw, ih = img.size
    src_aspect = iw / ih
    dst_aspect = W / H
    if src_aspect > dst_aspect:
        # source is wider — fit height, crop width
        new_h = H
        new_w = int(new_h * src_aspect)
    else:
        # source is taller/equal — fit width, crop height
        new_w = W
        new_h = int(new_w / src_aspect)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - W) // 2
    top = (new_h - H) // 2
    img = img.crop((left, top, left + W, top + H))

    draw = ImageDraw.Draw(img, "RGBA")
    font = load_font(font_size)
    tw, th = measure(draw, caption, font)
    pad_x, pad_y = 32, 22
    box_w = tw + pad_x * 2
    box_h = th + pad_y * 2
    box_x = (W - box_w) // 2
    box_y = H - 320

    draw.rounded_rectangle(
        [(box_x, box_y), (box_x + box_w, box_y + box_h)],
        radius=18,
        fill=(0, 0, 0, 160),
    )
    text_x = (W - tw) // 2
    text_y = box_y + pad_y - 4
    draw.text((text_x, text_y), caption, font=font, fill=(255, 255, 255, 255))

    img.save(out, "PNG")


def make_card(out: Path, caption: str, font_size: int = 78) -> None:
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = load_font(font_size)
    tw, th = measure(draw, caption, font)
    draw.text(((W - tw) // 2, (H - th) // 2 - 6), caption, font=font, fill=(255, 255, 255))
    img.save(out, "PNG")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src")
    ap.add_argument("--out", required=True)
    ap.add_argument("--caption", required=True)
    ap.add_argument("--bg", choices=["black", "phone"], default="phone")
    ap.add_argument("--size", type=int, default=58)
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.bg == "black":
        make_card(out, args.caption, args.size)
    else:
        if not args.src:
            raise SystemExit("--src required for phone bg")
        make_phone_frame(Path(args.src), out, args.caption, args.size)


if __name__ == "__main__":
    main()
