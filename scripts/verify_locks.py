
import sys
import os
import time
import multiprocessing
import logging

# Add the src directory to the path so we can import the module
sys.path.append(os.path.abspath("mcp-server-nucleus/src"))

from mcp_server_nucleus.runtime.locking import get_lock

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(process)d] %(message)s')
logger = logging.getLogger("LockTest")

def worker_process(worker_id: int, hold_time: int, delay_start: int):
    time.sleep(delay_start)
    lock = get_lock("test_resource", base_dir=None) # Uses default temp dir
    logger.info(f"Worker {worker_id} attempting to acquire lock...")
    
    if lock.acquire(timeout=5.0):
        logger.info(f"Worker {worker_id} ACQUIRED lock! Holding for {hold_time}s...")
        time.sleep(hold_time)
        lock.release()
        logger.info(f"Worker {worker_id} RELEASED lock.")
    else:
        logger.error(f"Worker {worker_id} FAILED to acquire lock (Timeout).")

def main():
    logger.info("Starting BrainLock Verification...")
    
    # Process 1 acquires lock immediately and holds for 2s
    p1 = multiprocessing.Process(target=worker_process, args=(1, 2, 0))
    
    # Process 2 waits 0.5s (so P1 has existing lock) and tries to acquire
    # It should wait until P1 releases it.
    p2 = multiprocessing.Process(target=worker_process, args=(2, 1, 0.5))
    
    p1.start()
    p2.start()
    
    p1.join()
    p2.join()
    
    logger.info("Verification Complete.")

if __name__ == "__main__":
    main()
