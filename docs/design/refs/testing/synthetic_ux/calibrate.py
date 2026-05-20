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


def _vision_locate(
    img_path: Path,
    description: str,
) -> tuple[int, int] | None:
    """Ask claude CLI to locate an element. Returns (x_px, y_px) or None."""
    prompt = (
        f"Read {img_path} — it is an iOS simulator screenshot at 3x scale "
        f"(physical pixels). Find the element described as: '{description}'. "
        f"Respond with ONLY a JSON object: "
        f'{{"x_px": <int>, "y_px": <int>, "confidence": "high"|"medium"|"low"}}. '
        f"x_px and y_px are the CENTER of the element in image pixel coordinates. "
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
        return int(data["x_px"]), int(data["y_px"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


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
