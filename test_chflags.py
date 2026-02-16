
import os
import subprocess
import time

TEST_FILE = "lock_test.txt"

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def test_locking():
    print(f"Creating test file: {TEST_FILE}")
    with open(TEST_FILE, "w") as f:
        f.write("Initial Content")
    
    print("Applying Lock (chflags uchg)...")
    res = run_cmd(f"chflags uchg {TEST_FILE}")
    if res.returncode != 0:
        print(f"❌ Failed to lock: {res.stderr}")
        return

    print("Attempting to overwrite (should fail)...")
    try:
        with open(TEST_FILE, "w") as f:
            f.write("Hacked Content")
        print("❌ FAILED: File was overwritten! Lock didn't work.")
    except PermissionError:
        print("✅ SUCCESS: PermissionError caught! File is locked.")
    except Exception as e:
        print(f"⚠️ Unexpected Error: {e}")

    print("Unlocking (chflags nouchg)...")
    res = run_cmd(f"chflags nouchg {TEST_FILE}")
    if res.returncode != 0:
        print(f"❌ Failed to unlock: {res.stderr}")

    print("Attempting to overwrite (should succeed)...")
    try:
        with open(TEST_FILE, "w") as f:
            f.write("Authorized Content")
        print("✅ SUCCESS: File overwritten after unlock.")
    except Exception as e:
        print(f"❌ FAILED: Could not write after unlock: {e}")

    # Cleanup
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

if __name__ == "__main__":
    test_locking()
