#!/usr/bin/env python3
"""
Nucleus Demo Trilogy Assembly Script (v1.0.5)

This script implements the "Modular Master" assembly strategy:
1.  Takes 3 Video Parts (A, B, C)
2.  Takes 3 Audio Parts (Hook, Brain, Power)
3.  Concatenates them into a single continuous timeline (~2m 15s)
4.  Ensures "Clean Breakers" (silence/black) between parts if needed.

Usage:
    python3 assemble_trilogy.py
"""

import os
import subprocess
import sys
from pathlib import Path

# --- Configuration ---
ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / "00_production_playbook" / "output"
ASSETS_DIR = ROOT_DIR / "assets" # User should place raw assets here if not in subfolders

# Expected Input Parts
# Expected Input Parts (Trimmed)
VIDEO_A_PARTS = [
    ROOT_DIR / "01_demo_a_startup" / "part_1_trimmed.mp4",
    ROOT_DIR / "01_demo_a_startup" / "part_2_trimmed.mp4"
]
VIDEO_B_PARTS = [
    ROOT_DIR / "02_demo_b_context" / "part_1_trimmed.mp4",
    ROOT_DIR / "02_demo_b_context" / "part_2_trimmed.mp4"
]
VIDEO_C_PARTS = [
    ROOT_DIR / "03_demo_c_sovereign" / "part_1_trimmed.mp4",
    ROOT_DIR / "03_demo_c_sovereign" / "part_2_trimmed.mp4"
]

# Temp Joined Files
VIDEO_A_MASTER = OUTPUT_DIR / "video_a_temp_joined.mp4"
VIDEO_B_MASTER = OUTPUT_DIR / "video_b_temp_joined.mp4"
VIDEO_C_MASTER = OUTPUT_DIR / "video_c_temp_joined.mp4"

AUDIO_A = OUTPUT_DIR / "audio" / "demo_a_hook_narration.mp3"
AUDIO_B = OUTPUT_DIR / "audio" / "demo_b_brain_narration.mp3"
AUDIO_C = OUTPUT_DIR / "audio" / "demo_c_power_narration.mp3"

FINAL_OUTPUT = OUTPUT_DIR / "nucleus_demo_master_v105.mp4"

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ Error: ffmpeg is not installed or not in PATH.")
        return False

def verify_assets():
    missing = []
    # Check Video Parts
    for p in VIDEO_A_PARTS:
        if not p.exists(): missing.append(f"A Part: {p.name}")
    for p in VIDEO_B_PARTS:
        if not p.exists(): missing.append(f"B Part: {p.name}")
    for p in VIDEO_C_PARTS:
        if not p.exists(): missing.append(f"C Part: {p.name}")
    
    # Check Audios
    if not AUDIO_A.exists(): missing.append(f"Audio A: {AUDIO_A.name}")
    if not AUDIO_B.exists(): missing.append(f"Audio B: {AUDIO_B.name}")
    if not AUDIO_C.exists(): missing.append(f"Audio C: {AUDIO_C.name}")

    if missing:
        print("⚠️  Missing Assets:")
        for m in missing:
            print(f"   - {m}")
        return False
    return True

def join_parts(part_paths, output_path):
    print(f"🔗 Joining sub-parts into: {output_path.name}")
    # Create temp concat list
    list_path = output_path.with_suffix(".txt")
    with open(list_path, "w") as f:
        for p in part_paths:
            f.write(f"file '{p}'\n")
    
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_path),
        "-c", "copy",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    list_path.unlink()

def assemble_trilogy():
    if not check_ffmpeg():
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("🎬 Starting Assembly...")
    
    # Prerequisite: Join parts for A, B, C
    join_parts(VIDEO_A_PARTS, VIDEO_A_MASTER)
    join_parts(VIDEO_B_PARTS, VIDEO_B_MASTER)
    join_parts(VIDEO_C_PARTS, VIDEO_C_MASTER)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(VIDEO_A_MASTER),
        "-i", str(VIDEO_B_MASTER),
        "-i", str(VIDEO_C_MASTER),
        "-i", str(AUDIO_A),
        "-i", str(AUDIO_B),
        "-i", str(AUDIO_C),
        "-filter_complex",
        "".join([
            "[0:v][3:a]", # Pair V1+A1
            "[1:v][4:a]", # Pair V2+A2
            "[2:v][5:a]", # Pair V3+A3
            "concat=n=3:v=1:a=1[v][a]" # Concat the 3 pairs
        ]),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        str(FINAL_OUTPUT)
    ]
    
    print(f"Running master assembly: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Success! Master output: {FINAL_OUTPUT}")
        # Clean up temp files if desired
        # VIDEO_A_MASTER.unlink()
        # VIDEO_B_MASTER.unlink()
        # VIDEO_C_MASTER.unlink()
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Assembly failed: {e}")


if __name__ == "__main__":
    if verify_assets():
        assemble_trilogy()
    else:
        print("\n❌ Cannot proceed without all assets. Please place files in expected paths.")
        print("Expected Parts:")
        for p in VIDEO_A_PARTS + VIDEO_B_PARTS + VIDEO_C_PARTS:
            print(f"  - {p}")
        print(f"  - {AUDIO_A}")
        print(f"  - {AUDIO_B}")
        print(f"  - {AUDIO_C}")
