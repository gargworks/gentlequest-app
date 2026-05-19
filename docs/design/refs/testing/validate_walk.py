#!/usr/bin/env python3
"""
validate_walk.py — check a walk screenshot dir against gq_oracle.json.

Exit code:
  0  all checks pass
  1  one or more failures
  2  no oracle / no screenshots found

Usage:
  python3 validate_walk.py --walk /path/to/walk-dir --oracle gq_oracle.json
  python3 validate_walk.py --walk /path/to/walk-dir --oracle gq_oracle.json --strict
    (strict: fail if a screenshot exists but has no oracle entry)
"""
import argparse
import json
import sys
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

def check(png: Path, spec: dict) -> list[str]:
    failures = []
    size_kb = png.stat().st_size // 1024

    if size_kb < spec["size_kb_min"]:
        failures.append(f"size {size_kb}KB < min {spec['size_kb_min']}KB  (likely blank screen)")

    img = Image.open(png).convert("RGB")
    w, h = img.size
    brightnesses = []
    color_buckets = set()

    for fx, fy in SAMPLE_POINTS:
        r, g, b = img.getpixel((int(w * fx), int(h * fy)))
        br = brightness(r, g, b)
        brightnesses.append(br)
        color_buckets.add((r // 30, g // 30, b // 30))

    br_min, br_max = min(brightnesses), max(brightnesses)
    unique = len(color_buckets)

    if br_max < spec["brightness_min"]:
        failures.append(f"all pixels too dark (max_br={br_max}, expected≥{spec['brightness_min']}) — possible black screen")
    if br_min > spec["brightness_max"]:
        failures.append(f"all pixels too bright (min_br={br_min}, expected≤{spec['brightness_max']}) — possible white/blank screen")
    if unique < spec["unique_color_buckets_min"]:
        failures.append(f"only {unique} color bucket(s), expected≥{spec['unique_color_buckets_min']} — screen looks empty or uniform")

    return failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--walk", required=True)
    parser.add_argument("--oracle", required=True)
    parser.add_argument("--strict", action="store_true",
                        help="Fail on screenshots with no oracle entry")
    args = parser.parse_args()

    walk_dir = Path(args.walk)
    oracle_path = Path(args.oracle)

    if not oracle_path.exists():
        print(f"ERROR: oracle not found: {oracle_path}", file=sys.stderr)
        sys.exit(2)

    oracle = json.loads(oracle_path.read_text())
    pngs = sorted(walk_dir.glob("*.png"))

    if not pngs:
        print(f"ERROR: no screenshots in {walk_dir}", file=sys.stderr)
        sys.exit(2)

    passes = 0
    failures = 0
    warnings = 0

    for png in pngs:
        name = png.stem
        if name not in oracle:
            if args.strict:
                print(f"WARN  {name}  — no oracle entry (--strict: treating as failure)")
                failures += 1
            else:
                warnings += 1
            continue

        errs = check(png, oracle[name])
        if errs:
            for e in errs:
                print(f"FAIL  {name}  — {e}")
            failures += 1
        else:
            print(f"PASS  {name}")
            passes += 1

    print(f"\n{'─'*50}")
    print(f"PASS {passes}  FAIL {failures}  WARN(no-oracle) {warnings}  TOTAL {len(pngs)}")

    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
