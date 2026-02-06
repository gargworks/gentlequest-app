import os
from PIL import Image, ImageDraw, ImageFont

def process_raw():
    raw_dir = "raw"
    ios_dir = "ios/screenshots/framed"
    android_dir = "android/screenshots/framed"
    
    os.makedirs(ios_dir, exist_ok=True)
    os.makedirs(android_dir, exist_ok=True)
    
    if not os.path.exists(raw_dir):
        return
    
    for f in os.listdir(raw_dir):
        if f.endswith(".png"):
            # For now, just copy to framed as a placeholder for the framing logic
            # In a real scenario, we'd add frames here.
            img = Image.open(os.path.join(raw_dir, f))
            img.save(os.path.join(ios_dir, f))
            img.save(os.path.join(android_dir, f))
            print(f"Processed {f}")

if __name__ == "__main__":
    process_raw()
