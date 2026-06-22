#!/usr/bin/env python3
"""Generic GentleQuest YT Short renderer.

Reads a config dict, bakes captions onto source PNGs via Pillow,
renders Ken-Burns clips with ffmpeg, concats to a final .mp4.

A scene is a dict:
  {"kind": "card",  "caption": "...", "dur": 4, "size": 78}        # solid black + centered text
  {"kind": "phone", "src": "I1_chat_home.png", "caption": "...", "dur": 7, "size": 58}  # phone PNG + caption pill

Total duration is sum(scene.dur). Outputs 1080x1920 H.264 yuv420p at 30fps.

Driver: shorts_catalog.py defines NAME -> (scenes, output_path).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BAKE = ROOT / "bake_caption.py"
SCREENSHOTS = Path(__file__).resolve().parents[2] / "docs/design/refs/screenshots/walk-2026-05-19"

W, H = 1080, 1920
FPS = 30


def bake(scene: dict, tmp_dir: Path, idx: int) -> Path:
    out = tmp_dir / f"f{idx}.png"
    if scene["kind"] == "card":
        subprocess.run(
            ["python3", str(BAKE), "--out", str(out), "--caption", scene["caption"],
             "--bg", "black", "--size", str(scene.get("size", 78))],
            check=True,
        )
    elif scene["kind"] == "phone":
        src = SCREENSHOTS / scene["src"]
        subprocess.run(
            ["python3", str(BAKE), "--src", str(src), "--out", str(out),
             "--caption", scene["caption"], "--bg", "phone",
             "--size", str(scene.get("size", 58))],
            check=True,
        )
    else:
        raise ValueError(f"unknown scene kind: {scene['kind']}")
    return out


def mkclip(scene: dict, frame: Path, tmp_dir: Path, idx: int) -> Path:
    out = tmp_dir / f"s{idx}.mp4"
    dur = scene["dur"]
    if scene["kind"] == "card":
        # static still
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(frame),
            "-t", str(dur), "-r", str(FPS), "-vf", f"scale={W}:{H}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
            str(out),
        ], check=True)
    else:
        # Ken-Burns slow zoom
        frames = dur * FPS
        filt = (
            f"[0:v]scale={W*2}:{H*2},"
            f"zoompan=z='min(zoom+0.0008,1.08)':d={frames}:s={W}x{H}:fps={FPS}[v]"
        )
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(frame),
            "-filter_complex", filt, "-map", "[v]", "-t", str(dur), "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
            str(out),
        ], check=True)
    return out


def render(scenes: list[dict], out_path: Path) -> dict:
    tmp = out_path.parent / "_tmp" / out_path.stem
    tmp.mkdir(parents=True, exist_ok=True)
    clips = []
    for i, scene in enumerate(scenes):
        print(f"  [scene {i}/{len(scenes)-1}] {scene['kind']:5s}  dur={scene['dur']}s  cap={scene['caption'][:50]!r}")
        frame = bake(scene, tmp, i)
        clip = mkclip(scene, frame, tmp, i)
        clips.append(clip)

    listfile = tmp / "concat.txt"
    with listfile.open("w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listfile),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
        str(out_path),
    ], check=True)

    total = sum(s["dur"] for s in scenes)
    size_mb = out_path.stat().st_size / (1024 * 1024)
    return {"path": str(out_path), "duration_s": total, "size_mb": round(size_mb, 2)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="path to JSON config: {scenes:[...], out:'...'}")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text())
    out_path = Path(cfg["out"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = render(cfg["scenes"], out_path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
