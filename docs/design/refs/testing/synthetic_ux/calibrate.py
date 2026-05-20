#!/usr/bin/env python3
"""
calibrate.py — Find tap coordinates for UI elements via image analysis + Vision.

Given a screenshot of an iOS simulator and a natural-language description of
an element ("profile avatar in the top app bar", "Save check-in button"),
returns the tap coordinate in idb point units (1/3 of pixel on 3x devices).

Two-phase approach:
1. Image analysis — find pixel centroid of saturated/distinct colored regions
   in the requested area (e.g. "top-right" for avatar icons). Works reliably
   when the region contains ONE saturated element (avatar, send button).
2. Vision fallback — if image analysis is ambiguous, send screenshot to
   claude CLI for the element's pixel position.

**Known limitations**:
- Image-analysis returns the saturated-pixel CENTROID. In multi-element
  regions (bottom nav with 4 colored tabs), it returns the average, not the
  individual element. Use --region to narrow, e.g. "bottom" to focus on a
  third of the nav bar.
- Vision fallback frequently returns inaccurate pixel coords because LLMs
  can't reliably read absolute pixel positions without a measurement grid.
  Pending improvement: pre-render a coordinate grid overlay before sending.
  For now, image-analysis path is preferred; Vision is best for sanity-check.

Usage:
    python3 calibrate.py SCREENSHOT_PATH "element description" [--region top|bottom|right|left]

Output: single line "x_pts,y_pts" or "ERROR: reason"
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
    _HAVE_PIL = True
except ImportError:
    _HAVE_PIL = False


# iPhone 16 Pro physical → logical scale (3x retina)
DEFAULT_SCALE = 3


def _find_saturated_blob(
    img_path: Path,
    region: str = "any",
    min_saturation: int = 30,
) -> tuple[int, int] | None:
    """Find centroid of saturated (non-white, non-gray) pixels in a region.

    Returns (x_pixel, y_pixel) centroid, or None if no blob found.
    """
    if not _HAVE_PIL:
        return None
    arr = np.array(Image.open(img_path).convert("RGB"))
    h, w = arr.shape[:2]

    # Region windows (pixel coords)
    if region == "top":
        sub = arr[: h // 4, :, :]
        y_offset = 0
    elif region == "top-right":
        sub = arr[: h // 4, w * 2 // 3 :, :]
        y_offset, x_offset = 0, w * 2 // 3
    elif region == "top-left":
        sub = arr[: h // 4, : w // 3, :]
        y_offset, x_offset = 0, 0
    elif region == "bottom":
        sub = arr[h * 3 // 4 :, :, :]
        y_offset = h * 3 // 4
    elif region == "bottom-right":
        sub = arr[h * 3 // 4 :, w * 2 // 3 :, :]
        y_offset, x_offset = h * 3 // 4, w * 2 // 3
    elif region == "right":
        sub = arr[:, w * 2 // 3 :, :]
        y_offset, x_offset = 0, w * 2 // 3
    else:  # "any"
        sub = arr
        y_offset, x_offset = 0, 0

    if region in ("top", "bottom", "any"):
        x_offset = 0

    saturation = sub.max(axis=2).astype(int) - sub.min(axis=2).astype(int)
    ys, xs = np.where(saturation > min_saturation)
    if len(xs) == 0:
        return None
    return int(xs.mean() + x_offset), int(ys.mean() + y_offset)


def _render_grid_overlay(
    src_path: Path,
    out_path: Path,
    scale: int = DEFAULT_SCALE,
    major_step: int = 50,
    minor_step: int = 10,
) -> bool:
    """Overlay a labeled coordinate grid (in POINTS) on src_path → out_path.

    Without an overlay, Vision LLMs cannot reliably report pixel positions
    on a bare screenshot — they confabulate. With a numbered grid drawn
    directly on the image, the LLM only needs to read labels at the
    intersection of the element's center → which it does reliably.

    Grid is drawn in POINT coordinates (pixel / scale) since that's what
    idb tap consumes. Major lines every `major_step` points are labeled;
    minor lines every `minor_step` points are unlabeled.
    """
    if not _HAVE_PIL:
        return False
    try:
        from PIL import ImageDraw, ImageFont
    except ImportError:
        return False

    img = Image.open(src_path).convert("RGB")
    w_px, h_px = img.size
    w_pt, h_pt = w_px // scale, h_px // scale

    overlay = img.copy()
    draw = ImageDraw.Draw(overlay, "RGBA")

    # Minor grid — light, no labels
    minor_color = (255, 64, 64, 60)
    for x_pt in range(0, w_pt + 1, minor_step):
        x = x_pt * scale
        draw.line([(x, 0), (x, h_px)], fill=minor_color, width=1)
    for y_pt in range(0, h_pt + 1, minor_step):
        y = y_pt * scale
        draw.line([(0, y), (w_px, y)], fill=minor_color, width=1)

    # Major grid — bright red, labeled
    major_color = (255, 0, 0, 180)
    label_bg = (255, 255, 255, 220)
    label_fg = (200, 0, 0, 255)

    # Try to load a reasonable font; fall back to default
    font = None
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        try:
            font = ImageFont.truetype(candidate, 24 * (scale // 2 or 1))
            break
        except (OSError, IOError):
            continue
    if font is None:
        font = ImageFont.load_default()

    for x_pt in range(0, w_pt + 1, major_step):
        x = x_pt * scale
        draw.line([(x, 0), (x, h_px)], fill=major_color, width=2)
        # Label at top edge
        text = str(x_pt)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        bg = (x - tw // 2 - 4, 4, x + tw // 2 + 4, 8 + th + 4)
        draw.rectangle(bg, fill=label_bg)
        draw.text((x - tw // 2, 6), text, font=font, fill=label_fg)

    for y_pt in range(0, h_pt + 1, major_step):
        y = y_pt * scale
        draw.line([(0, y), (w_px, y)], fill=major_color, width=2)
        text = str(y_pt)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        bg = (4, y - th // 2 - 2, 8 + tw + 4, y + th // 2 + 6)
        draw.rectangle(bg, fill=label_bg)
        draw.text((8, y - th // 2), text, font=font, fill=label_fg)

    overlay.save(out_path, "PNG")
    return True


def _vision_locate(
    img_path: Path,
    description: str,
    use_grid: bool = True,
    scale: int = DEFAULT_SCALE,
) -> tuple[int, int] | None:
    """Ask claude CLI to locate an element. Returns (x_pt, y_pt) in POINTS.

    With use_grid=True (default), an overlay with labeled gridlines (in
    point coords) is rendered first; Vision then reads the grid labels
    directly and returns coords in POINTS — far more reliable than asking
    it to estimate pixel positions on a bare screenshot.
    """
    grid_path = img_path.with_suffix(".grid.png")
    if use_grid:
        if not _render_grid_overlay(img_path, grid_path, scale=scale):
            use_grid = False  # PIL missing or font failed

    target = grid_path if use_grid else img_path
    coord_kind = "POINTS (using the red gridline labels)" if use_grid else "image pixels"
    extra = (
        " The image has a red coordinate grid: major lines every 50 points "
        "with the point value labeled, minor lines every 10 points. Read the "
        "labels at the nearest major lines and interpolate to estimate the "
        "element's center in points."
        if use_grid else ""
    )
    prompt = (
        f"Read {target} — iOS simulator screenshot.{extra} "
        f"Find the element described as: '{description}'. "
        f"Respond with ONLY a JSON object: "
        f'{{"x": <int>, "y": <int>, "confidence": "high"|"medium"|"low"}}. '
        f"x and y are the CENTER of the element in {coord_kind}. "
        f"No prose, no markdown, just the JSON."
    )
    try:
        r = subprocess.run(
            ["claude", "-p", "--allowedTools", "Read",
             "--output-format", "text", prompt],
            capture_output=True, text=True, timeout=120,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    raw = r.stdout.strip()
    # Strip ANSI / markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        data = json.loads(raw)
        x, y = int(data["x"]), int(data["y"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return None
    # With grid: x/y are already in points → return as-is, but main() expects
    # pixel coords for consistency, so convert back to pixels here.
    if use_grid:
        return x * scale, y * scale
    return x, y


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("screenshot", type=Path, help="Path to screenshot PNG")
    parser.add_argument("description", help="Natural-language element description")
    parser.add_argument(
        "--region", default="any",
        help="Restrict search: any|top|top-right|top-left|bottom|bottom-right|right",
    )
    parser.add_argument(
        "--scale", type=int, default=DEFAULT_SCALE,
        help="Retina scale factor (default 3 for iPhone Pro models)",
    )
    parser.add_argument(
        "--vision", action="store_true",
        help="Use Vision LLM directly, skip image-analysis phase",
    )
    args = parser.parse_args()

    if not args.screenshot.exists():
        print(f"ERROR: screenshot not found: {args.screenshot}", file=sys.stderr)
        return 2

    result_px: tuple[int, int] | None = None

    if not args.vision:
        result_px = _find_saturated_blob(args.screenshot, args.region)
        if result_px:
            print(
                f"image-analysis: blob at pixel {result_px}, "
                f"point ({result_px[0] // args.scale}, {result_px[1] // args.scale})",
                file=sys.stderr,
            )

    if result_px is None:
        print("falling back to Vision...", file=sys.stderr)
        result_px = _vision_locate(args.screenshot, args.description)
        if result_px:
            print(f"vision: pixel {result_px}", file=sys.stderr)

    if result_px is None:
        print("ERROR: could not locate element", file=sys.stderr)
        return 1

    x_pt = result_px[0] // args.scale
    y_pt = result_px[1] // args.scale
    print(f"{x_pt},{y_pt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
