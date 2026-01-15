#!/usr/bin/env python3
"""
verify_fetcher.py

Verification script for Phase 57: Chat 20 - The Fetcher.
Tests GitFetcher for secure Repository Cloning and Commit Verification.
"""

import os
import sys
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.fetcher import GitFetcher

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_FETCHER")

TEST_ROOT = Path("test_fetcher_area")

def run_git(args, cwd):
    subprocess.check_call(["git"] + args, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_git_rev(cwd):
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd).decode().strip()

def setup_test_repo():
    repo_dir = TEST_ROOT / "upstream_repo"
    repo_dir.mkdir(parents=True)
    
    # Init Repo
    run_git(["init"], cwd=repo_dir)
    run_git(["config", "user.email", "test@nucleus.com"], cwd=repo_dir)
    run_git(["config", "user.name", "Nucleus Test"], cwd=repo_dir)
    
    # Commit 1
    (repo_dir / "agent.py").write_text("print('v1')")
    run_git(["add", "."], cwd=repo_dir)
    run_git(["commit", "-m", "Initial commit"], cwd=repo_dir)
    hash_v1 = get_git_rev(repo_dir)
    
    # Commit 2
    (repo_dir / "agent.py").write_text("print('v2')")
    run_git(["add", "."], cwd=repo_dir)
    run_git(["commit", "-m", "Update to v2"], cwd=repo_dir)
    hash_v2 = get_git_rev(repo_dir)
    
    return repo_dir, hash_v1, hash_v2

def verify_fetch_success(repo_path, valid_hash):
    logger.info("Step 1: Testing Successful Fetch (Specific Commit)...")
    
    target_dir = TEST_ROOT / "installed_agents" / "my_agent"
    if target_dir.exists():
        shutil.rmtree(target_dir)
        
    fetcher = GitFetcher()
    
    try:
        fetcher.fetch(
            url=str(repo_path), # Local path acts as URL
            destination=target_dir,
            commit_hash=valid_hash
        )
    except Exception as e:
        logger.error(f"❌ Fetch failed: {e}")
        return False
        
    if not target_dir.exists():
        logger.error("❌ Target directory not created")
        return False
        
    # Check content
    content = (target_dir / "agent.py").read_text()
    if "print('v1')" in content:
        logger.info(f"✅ Successfully fetched commit {valid_hash[:7]} (Content='v1')")
        return True
    else:
        logger.error(f"❌ Content mismatch. Expected 'v1', got: {content}")
        return False

def verify_fetch_update_target(repo_path, valid_hash):
    logger.info("Step 2: Testing Fetch Overwrite (Update)...")
    
    target_dir = TEST_ROOT / "installed_agents" / "my_agent"
    
    fetcher = GitFetcher()
    
    # Fetch v2 to same dir
    try:
        fetcher.fetch(
            url=str(repo_path),
            destination=target_dir,
            commit_hash=valid_hash
        )
    except Exception as e:
        logger.error(f"❌ Update fetch failed: {e}")
        return False
        
    content = (target_dir / "agent.py").read_text()
    if "print('v2')" in content:
        logger.info(f"✅ Successfully updated to commit {valid_hash[:7]} (Content='v2')")
        return True
    else:
        logger.error(f"❌ Content mismatch. Expected 'v2', got: {content}")
        return False

def main():
    if TEST_ROOT.exists():
        shutil.rmtree(TEST_ROOT)
    TEST_ROOT.mkdir()

    try:
        repo_path, hash_v1, hash_v2 = setup_test_repo()
        logger.info(f"Repo setup at {repo_path}")
        logger.info(f"v1: {hash_v1}")
        logger.info(f"v2: {hash_v2}")
        
        if not verify_fetch_success(repo_path.absolute(), hash_v1):
            sys.exit(1)
            
        if not verify_fetch_update_target(repo_path.absolute(), hash_v2):
            sys.exit(1)
            
        logger.info("✨ ALL FETCHER CHECKS PASSED ✨")
        shutil.rmtree(TEST_ROOT)
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        if TEST_ROOT.exists():
            shutil.rmtree(TEST_ROOT)
        sys.exit(1)

if __name__ == "__main__":
    main()
