#!/usr/bin/env python3
"""
iPhone JPG OCR Pipeline for Third Brother Training Data
Streams: pull one image at a time, OCR it, delete it, write SFT entry.
Zero disk accumulation.
"""

import subprocess
import json
import hashlib
import os
import sys
import re
import time

PMD3 = "/Applications/Xcode.app/Contents/Developer/usr/bin/python3"
OCR_BIN = "/tmp/ocr_screenshot"
OUTPUT_DIR = "/Users/lokeshgarg/ai-mvp-backend/.brain/training/inbox"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "iphone_saved_images_sft.jsonl")
STAGING = "/Users/lokeshgarg/iphone_jpg_staging"

DCIM_FOLDERS = [
    "100APPLE", "101APPLE", "102APPLE", "103APPLE", "104APPLE",
    "105APPLE", "106APPLE", "107APPLE", "108APPLE", "109APPLE", "110APPLE"
]

CATEGORY_KEYWORDS = {
    "health": ["hospital", "doctor", "medical", "blood", "test", "report", "health", "diagnosis", "prescription", "medicine", "clinic", "patient"],
    "finance": ["bank", "credit", "debit", "payment", "upi", "transaction", "balance", "account", "rupee", "inr", "amount", "invoice", "receipt"],
    "career": ["linkedin", "resume", "interview", "salary", "offer", "job", "hiring", "recruiter", "experience", "position"],
    "social": ["whatsapp", "instagram", "message", "chat", "snap", "telegram", "twitter", "facebook", "follow", "dm", "story"],
}

def ensure_ocr_binary():
    """Compile the OCR binary if it doesn't exist."""
    if os.path.isfile(OCR_BIN):
        return True
    swift_code = r'''
import Foundation
import AppKit
import Vision

let imagePath = CommandLine.arguments[1]
guard let image = NSImage(contentsOfFile: imagePath) else {
    print("")
    exit(0)
}
guard let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("")
    exit(0)
}
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["en", "hi"]
let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try? handler.perform([request])
let text = request.results?.compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n") ?? ""
print(text)
'''
    with open("/tmp/ocr_screenshot.swift", "w") as f:
        f.write(swift_code)
    r = subprocess.run(
        ["swiftc", "/tmp/ocr_screenshot.swift", "-o", OCR_BIN, "-framework", "AppKit", "-framework", "Vision"],
        capture_output=True, text=True
    )
    return r.returncode == 0


def list_jpgs_in_folder(folder):
    """List all JPG/JPEG files in a DCIM subfolder."""
    r = subprocess.run(
        [PMD3, "-m", "pymobiledevice3", "afc", "ls", f"/DCIM/{folder}/"],
        capture_output=True, text=True
    )
    files = []
    for line in r.stdout.strip().split("\n"):
        line = line.strip()
        fname = os.path.basename(line)
        if fname.lower().endswith((".jpg", ".jpeg")):
            files.append(fname)
    return files


def pull_file(folder, filename, local_path):
    """Pull a single file from iPhone."""
    remote = f"/DCIM/{folder}/{filename}"
    r = subprocess.run(
        [PMD3, "-m", "pymobiledevice3", "afc", "pull", "-i", remote, local_path],
        capture_output=True, text=True, timeout=60
    )
    return os.path.isfile(local_path) and os.path.getsize(local_path) > 0


def ocr_image(local_path):
    """Run Apple Vision OCR on an image. Returns text string."""
    try:
        r = subprocess.run(
            [OCR_BIN, local_path],
            capture_output=True, text=True, timeout=30
        )
        return r.stdout.strip()
    except Exception:
        return ""


def detect_category(text):
    """Detect category from OCR text."""
    text_lower = text.lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[cat] = score
    if not scores:
        return "personal"
    return max(scores, key=scores.get)


def make_sft_entry(ocr_text, filename, folder):
    """Create an SFT training entry."""
    h = hashlib.md5(f"{folder}/{filename}".encode()).hexdigest()[:12]
    category = detect_category(ocr_text)
    return {
        "id": f"iphoto_jpg_{h}",
        "messages": [
            {
                "role": "system",
                "content": "You are Third Brother, Lokesh's personal AI. You know his saved images and screenshots."
            },
            {
                "role": "user",
                "content": "What's in this saved image from Lokesh's phone?"
            },
            {
                "role": "assistant",
                "content": f"From Lokesh's saved image:\n\n{ocr_text}"
            }
        ],
        "source": "iphone_saved_image",
        "quality": "silver",
        "category": category,
        "meta": {"file": filename, "folder": folder}
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(STAGING, exist_ok=True)

    print("Ensuring OCR binary exists...")
    if not ensure_ocr_binary():
        print("ERROR: Could not build OCR binary")
        sys.exit(1)

    total_files = 0
    processed = 0
    skipped_no_text = 0
    skipped_error = 0
    category_counts = {}

    # Count total first
    print("Scanning DCIM folders for JPGs...")
    folder_files = {}
    for folder in DCIM_FOLDERS:
        files = list_jpgs_in_folder(folder)
        folder_files[folder] = files
        total_files += len(files)
        print(f"  {folder}: {len(files)} JPGs")

    print(f"\nTotal: {total_files} JPG files to process")
    print(f"Output: {OUTPUT_FILE}\n")

    with open(OUTPUT_FILE, "w") as outf:
        for folder in DCIM_FOLDERS:
            files = folder_files.get(folder, [])
            if not files:
                continue

            print(f"\n--- Processing {folder} ({len(files)} files) ---")
            for i, filename in enumerate(files):
                local_path = os.path.join(STAGING, filename)

                # Pull
                try:
                    ok = pull_file(folder, filename, local_path)
                    if not ok:
                        skipped_error += 1
                        continue
                except Exception as e:
                    print(f"  PULL ERROR {filename}: {e}")
                    skipped_error += 1
                    continue

                # OCR
                ocr_text = ocr_image(local_path)

                # Delete immediately to save disk
                try:
                    os.remove(local_path)
                except:
                    pass

                # Check minimum text length
                if len(ocr_text) < 50:
                    skipped_no_text += 1
                    if (i + 1) % 20 == 0:
                        print(f"  [{i+1}/{len(files)}] processed ({processed} with text so far)")
                    continue

                # Create SFT entry
                entry = make_sft_entry(ocr_text, filename, folder)
                outf.write(json.dumps(entry, ensure_ascii=False) + "\n")
                outf.flush()
                processed += 1

                cat = entry["category"]
                category_counts[cat] = category_counts.get(cat, 0) + 1

                if (i + 1) % 20 == 0 or processed % 10 == 0:
                    print(f"  [{i+1}/{len(files)}] processed ({processed} with text so far)")

    # Cleanup staging dir
    try:
        os.rmdir(STAGING)
    except:
        pass

    # Summary
    print("\n" + "=" * 60)
    print(f"PIPELINE COMPLETE")
    print(f"=" * 60)
    print(f"Total JPGs scanned:    {total_files}")
    print(f"SFT entries created:   {processed}")
    print(f"Skipped (no/short text): {skipped_no_text}")
    print(f"Skipped (pull error):  {skipped_error}")
    print(f"\nCategory breakdown:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    print(f"\nOutput: {OUTPUT_FILE}")
    print(f"File size: {os.path.getsize(OUTPUT_FILE) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
