
import ffmpeg
import sys
from pathlib import Path

OUTPUT_DIR = Path("/Users/lokeshgarg/ai-mvp-backend/demos/00_production_playbook/one_shot_output/assets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEST_FILE_NO_TEXT = OUTPUT_DIR / "test_bridge_no_text.mp4"
TEST_FILE_TEXT = OUTPUT_DIR / "test_bridge_text.mp4"

def test_bridge_generation():
    print("Testing Bridge Video Generation...")
    
    # Test 1: Simple Black Video (No Text)
    print(f"Test 1: Black Video -> {TEST_FILE_NO_TEXT}")
    try:
        stream = ffmpeg.input('color=c=black:s=1920x1080:d=4', f='lavfi')
        stream = stream.output(str(TEST_FILE_NO_TEXT), vcodec='libx264', pix_fmt='yuv420p')
        out, err = stream.run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
        print("Success: Test 1")
    except ffmpeg.Error as e:
        print(f"Failed: Test 1. Error: {e.stderr.decode('utf8')}")
        return

    # Test 2: Text Overlay
    print(f"Test 2: Text Overlay -> {TEST_FILE_TEXT}")
    try:
        stream = ffmpeg.input('color=c=black:s=1920x1080:d=4', f='lavfi')
        # Simplified drawtext: use default font? Or specify a system font.
        # Check standard mac font path
        font_path = "/System/Library/Fonts/Helvetica.ttc" 
        # Note: on some systems .ttc might need index? 
        
        # Try without fontfile first (rely on fontconfig?)
        # stream = stream.filter('drawtext', text="THE BRAIN", fontcolor='white', fontsize=100, x='(w-text_w)/2', y='(h-text_h)/2')
        
        # ffmpeg often fails without fontfile. specifying one is safer.
        stream = stream.filter('drawtext', fontfile='/System/Library/Fonts/Helvetica.ttc', text='THE BRAIN', fontcolor='white', fontsize=100, x='(w-text_w)/2', y='(h-text_h)/2')
        
        stream = stream.output(str(TEST_FILE_TEXT), vcodec='libx264', pix_fmt='yuv420p')
        out, err = stream.run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
        print("Success: Test 2")
    except ffmpeg.Error as e:
        print(f"Failed: Test 2. Error: {e.stderr.decode('utf8')}")

if __name__ == "__main__":
    test_bridge_generation()
