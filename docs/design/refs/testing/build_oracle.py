#!/usr/bin/env python3
"""
build_oracle.py — generate gq_oracle.json from golden screenshots.

For each golden screenshot, samples pixels at a 4×6 grid and records:
  - min/max brightness range (catches blank screens)
  - dominant color zone (catches wrong-screen renders)
  - file size threshold (catches 0-byte / tiny blanks)

Run once after a known-good walk to establish the baseline:
  python3 build_oracle.py --golden /path/to/walk-dir --out gq_oracle.json
"""
import argparse
import json
import os
from pathlib import Path
from PIL import Image

SAMPLE_POINTS = [
    (0.20, 0.15), (0.50, 0.15), (0.80, 0.15),
    (0.20, 0.35), (0.50, 0.35), (0.80, 0.35),
    (0.20, 0.55), (0.50, 0.55), (0.80, 0.55),
    (0.20, 0.75), (0.50, 0.75), (0.80, 0.75),
]

def brightness(r, g, b):
    return (r * 299 + g * 587 + b * 114) // 1000

def analyze(path: Path) -> dict:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    size_kb = path.stat().st_size // 1024

    samples = []
    for fx, fy in SAMPLE_POINTS:
        r, g, b = img.getpixel((int(w * fx), int(h * fy)))
        samples.append({"r": r, "g": g, "b": b, "br": brightness(r, g, b)})

    brightnesses = [s["br"] for s in samples]
    unique_colors = len({(s["r"] // 30, s["g"] // 30, s["b"] // 30) for s in samples})

    return {
        "size_kb_min": max(1, size_kb - 30),    # allow ±30 KB compression variance
        "brightness_min": max(0, min(brightnesses) - 20),
        "brightness_max": min(255, max(brightnesses) + 20),
        "unique_color_buckets_min": max(1, unique_colors - 1),
        "samples": samples,   # stored for debugging; not used by validator
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", required=True, help="Path to golden screenshot dir")
    parser.add_argument("--out", default="gq_oracle.json", help="Output oracle file")
    args = parser.parse_args()

    golden_dir = Path(args.golden)
    oracle = {}

    pngs = sorted(golden_dir.glob("*.png"))
    if not pngs:
        print(f"No PNGs found in {golden_dir}")
        return

    for png in pngs:
        name = png.stem
        spec = analyze(png)
        oracle[name] = spec
        print(f"  {name}: size≥{spec['size_kb_min']}KB  br∈[{spec['brightness_min']},{spec['brightness_max']}]  colors≥{spec['unique_color_buckets_min']}")

    out = Path(args.out)
    out.write_text(json.dumps(oracle, indent=2))
    print(f"\n✓ Oracle written to {out}  ({len(oracle)} screens)")


if __name__ == "__main__":
    main()
