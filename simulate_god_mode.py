
import os
import time
import shutil
import logging
import threading
from pathlib import Path
from mcp_server_nucleus.hypervisor.locker import Locker
from mcp_server_nucleus.hypervisor.watchdog import Watchdog

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("simulation")

TEST_DIR = Path("god_mode_test").resolve()
TEST_FILE = TEST_DIR / "secret.txt"

def setup():
    if TEST_DIR.exists():
        # Unlock everything first so we can delete
        Locker().unlock(str(TEST_DIR))
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir()
    TEST_FILE.write_text("Top Secret Data")
    logger.info(f"✅ Setup: Created {TEST_FILE}")

def attack_standard():
    logger.info("\n⚔️  ATTACK 1: Standard Write (Script Kiddie)")
    try:
        TEST_FILE.write_text("HACKED!")
        logger.error("❌ FAILURE: File was overwritten! Lock didn't work.")
    except PermissionError:
        logger.info("🛡️  DEFENSE SUCCESS: PermissionError caught! (Layer 4 Active)")
    except Exception as e:
        logger.error(f"⚠️ Unexpected Error: {e}")

def attack_advanced(locker):
    logger.info("\n⚔️  ATTACK 2: Advanced (Root Override + Watchdog Test)")
    
    # 1. Simulating Root Override (Manually Unlocking)
    logger.info("🔓 Attacker manually removes flags...")
    locker.unlock(str(TEST_FILE))
    
    # 2. Modify File
    logger.info("✍️  Attacker modifying file...")
    TEST_FILE.write_text("HACKED BY ROOT")
    logger.info("✅ Attack successful (Configuration Drift created).")
    
    # 3. Wait for Watchdog
    logger.info("⏳ Waiting for Watchdog (Layer 1)...")
    time.sleep(2) # Give watchdog time to react
    
    # 4. Try to write again (Should be locked again)
    logger.info("✍️  Attacker trying to write AGAIN...")
    try:
        TEST_FILE.write_text("DOUBLE HACK")
        logger.error("❌ FAILURE: Watchdog did NOT re-lock the file!")
    except PermissionError:
        logger.info("🛡️  DEFENSE SUCCESS: PermissionError caught! Watchdog healing confirmed.")
    except Exception as e:
        logger.error(f"⚠️ Unexpected Error: {e}")


def main():
    logger.info("🚀 STARTING GOD MODE SIMULATION")
    
    # Force enable logging for Watchdog
    w_logger = logging.getLogger("mcp_server_nucleus.hypervisor.watchdog")
    w_logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    w_logger.addHandler(console_handler)

    setup()
    

    # Initialize Hypervisor
    from mcp_server_nucleus import _watchdog
    locker = Locker()
    watchdog = _watchdog
    
    # Watchdog is auto-started by __init__.py, but we can ensure it's running
    if not watchdog.observer.is_alive():
        logger.info("Starting Watchdog...")
        watchdog.start()
    
    # Protect Resource
    logger.info(f"🔒 Engaging Hypervisor on {TEST_DIR}")
    watchdog.protect(str(TEST_DIR))
    
    # Validating Lock
    if locker.is_locked(str(TEST_FILE)):
        logger.info("✅ Lock Verified (System Flag Set)")
    else:
        logger.error("❌ Lock NOT set!")

    # Run Attacks
    attack_standard()
    attack_advanced(locker)
    
    # Cleanup
    logger.info("\n🧹 Cleanup...")
    watchdog.stop()
    locker.unlock(str(TEST_DIR))
    # shutil.rmtree(TEST_DIR) # Leave for manual inspection if needed
    logger.info("🏁 SIMULATION COMPLETE")

if __name__ == "__main__":
    main()
