#!/usr/bin/env python3
"""
RUNBOOK: Production Deployment to Render

Description:
    Deploy GentleQuest backend to Render production environment.
    This is an EXECUTABLE runbook - it performs actual deployment steps.

Prerequisites:
    - Git access to main branch
    - All tests passing
    - No pending critical issues
    
Estimated Time: 5-10 minutes
Risk Level: MEDIUM
Rollback Time: 2-5 minutes (Render dashboard or git revert)

Usage:
    # Dry run (see what would happen):
    python runbooks/deploy_production.py --dry-run
    
    # Execute deployment:
    python runbooks/deploy_production.py --execute
    
    # Skip tests (use with caution):
    python runbooks/deploy_production.py --execute --skip-tests

Author: GentleQuest Team
Last Updated: January 16, 2026
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configuration
PRODUCTION_URL = "https://gentlequest.onrender.com"
HEALTH_ENDPOINT = "/api/health"
PING_ENDPOINT = "/api/ping"
DEPLOY_WAIT_SECONDS = 120  # Time to wait for Render deploy


class Colors:
    """Terminal colors for output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def log(message: str, level: str = "info"):
    """Log a message with color."""
    colors = {
        "info": Colors.BLUE,
        "success": Colors.GREEN,
        "warning": Colors.YELLOW,
        "error": Colors.RED,
        "header": Colors.HEADER,
    }
    color = colors.get(level, "")
    print(f"{color}{message}{Colors.END}")


from typing import Optional

def run_command(cmd: list[str], dry_run: bool = False, check: bool = True) -> Optional[subprocess.CompletedProcess]:
    """Run a shell command."""
    cmd_str = ' '.join(cmd)
    
    if dry_run:
        log(f"  [DRY RUN] Would execute: {cmd_str}", "warning")
        return None
    
    log(f"  Executing: {cmd_str}", "info")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        log(f"  Command failed: {e.stderr}", "error")
        if check:
            raise
        return None


class DeployRunbook:
    """Executable deployment runbook."""
    
    def __init__(self, dry_run: bool = True, skip_tests: bool = False):
        self.dry_run = dry_run
        self.skip_tests = skip_tests
        self.start_time = datetime.now()
        self.steps_completed = []
        self.steps_failed = []
    
    def run(self):
        """Execute the deployment runbook."""
        log("\n" + "=" * 60, "header")
        log("🚀 PRODUCTION DEPLOYMENT RUNBOOK", "header")
        log("=" * 60, "header")
        log(f"Started: {self.start_time.isoformat()}")
        log(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        log(f"Skip tests: {self.skip_tests}")
        log("")
        
        try:
            self.step_1_pre_checks()
            self.step_2_run_tests()
            self.step_3_push_to_main()
            self.step_4_wait_for_deploy()
            self.step_5_smoke_test()
            self.step_6_summary()
        except Exception as e:
            log(f"\n❌ DEPLOYMENT FAILED: {e}", "error")
            self.step_rollback_instructions()
            sys.exit(1)
    
    def step_1_pre_checks(self):
        """Pre-deployment checks."""
        log("\n📍 STEP 1: Pre-deployment Checks", "header")
        
        # Check git status
        log("  Checking git status...")
        result = run_command(['git', 'status', '--porcelain'], self.dry_run, check=False)
        if result and result.stdout.strip():
            log("  ⚠️ Uncommitted changes detected!", "warning")
            if not self.dry_run:
                response = input("  Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    raise Exception("Uncommitted changes - aborting")
        
        # Check current branch
        log("  Checking current branch...")
        result = run_command(['git', 'branch', '--show-current'], self.dry_run, check=False)
        if result and result.stdout.strip() != 'main':
            log(f"  ⚠️ Not on main branch (on: {result.stdout.strip()})", "warning")
        
        # Check remote
        log("  Checking remote status...")
        run_command(['git', 'fetch', 'origin', 'main'], self.dry_run, check=False)
        
        self.steps_completed.append("Pre-checks")
        log("  ✅ Pre-checks complete", "success")
    
    def step_2_run_tests(self):
        """Run test suite."""
        log("\n📍 STEP 2: Run Tests", "header")
        
        if self.skip_tests:
            log("  ⚠️ SKIPPING TESTS (--skip-tests flag)", "warning")
            return
        
        log("  Running pytest...")
        test_path = Path(__file__).parent.parent / 'tests'
        
        if not test_path.exists():
            log("  ⚠️ Tests directory not found, skipping", "warning")
            return
        
        result = run_command(['pytest', str(test_path), '-v', '--tb=short'], self.dry_run, check=False)
        
        if result and result.returncode != 0:
            log("  ❌ Tests failed!", "error")
            if not self.dry_run:
                response = input("  Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    raise Exception("Tests failed - aborting")
        
        self.steps_completed.append("Tests")
        log("  ✅ Tests complete", "success")
    
    def step_3_push_to_main(self):
        """Push to main branch to trigger Render deploy."""
        log("\n📍 STEP 3: Push to Main", "header")
        
        log("  Pushing to origin/main...")
        run_command(['git', 'push', 'origin', 'main'], self.dry_run)
        
        self.steps_completed.append("Push")
        log("  ✅ Push complete - Render deploy triggered", "success")
    
    def step_4_wait_for_deploy(self):
        """Wait for Render deployment to complete."""
        log("\n📍 STEP 4: Wait for Deploy", "header")
        
        if self.dry_run:
            log(f"  [DRY RUN] Would wait {DEPLOY_WAIT_SECONDS}s for deploy", "warning")
            return
        
        log(f"  Waiting {DEPLOY_WAIT_SECONDS}s for Render deploy...")
        log("  (Monitor at: https://dashboard.render.com)")
        
        for i in range(0, DEPLOY_WAIT_SECONDS, 10):
            remaining = DEPLOY_WAIT_SECONDS - i
            print(f"\r  Waiting... {remaining}s remaining", end="", flush=True)
            time.sleep(10)
        
        print()  # New line after countdown
        
        self.steps_completed.append("Wait")
        log("  ✅ Wait complete", "success")
    
    def step_5_smoke_test(self):
        """Verify deployment with smoke tests."""
        log("\n📍 STEP 5: Smoke Tests", "header")
        
        if self.dry_run:
            log(f"  [DRY RUN] Would hit {PRODUCTION_URL}{HEALTH_ENDPOINT}", "warning")
            log(f"  [DRY RUN] Would hit {PRODUCTION_URL}{PING_ENDPOINT}", "warning")
            self.steps_completed.append("Smoke test")
            return
        
        import urllib.request
        import json
        
        # Test ping endpoint
        log(f"  Testing {PING_ENDPOINT}...")
        try:
            with urllib.request.urlopen(f"{PRODUCTION_URL}{PING_ENDPOINT}", timeout=10) as resp:
                data = json.loads(resp.read().decode())
                log(f"    Status: {data.get('status', 'unknown')}", "success")
        except Exception as e:
            log(f"    ❌ Ping failed: {e}", "error")
            self.steps_failed.append("Ping test")
        
        # Test health endpoint
        log(f"  Testing {HEALTH_ENDPOINT}...")
        try:
            with urllib.request.urlopen(f"{PRODUCTION_URL}{HEALTH_ENDPOINT}", timeout=10) as resp:
                data = json.loads(resp.read().decode())
                status = data.get('status', 'unknown')
                log(f"    Status: {status}", "success" if status == 'healthy' else "warning")
                if 'database' in data:
                    log(f"    Database: {data['database']}", "info")
                if 'redis' in data:
                    log(f"    Redis: {data['redis']}", "info")
        except Exception as e:
            log(f"    ❌ Health check failed: {e}", "error")
            self.steps_failed.append("Health test")
        
        self.steps_completed.append("Smoke test")
        log("  ✅ Smoke tests complete", "success")
    
    def step_6_summary(self):
        """Print deployment summary."""
        log("\n" + "=" * 60, "header")
        log("📋 DEPLOYMENT SUMMARY", "header")
        log("=" * 60, "header")
        
        duration = datetime.now() - self.start_time
        
        log(f"Duration: {duration.seconds}s")
        log(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTED'}")
        log(f"Steps completed: {', '.join(self.steps_completed)}")
        
        if self.steps_failed:
            log(f"Steps failed: {', '.join(self.steps_failed)}", "warning")
        
        if not self.dry_run and not self.steps_failed:
            log("\n✅ DEPLOYMENT SUCCESSFUL", "success")
            log(f"   Production URL: {PRODUCTION_URL}")
        elif self.dry_run:
            log("\n✅ DRY RUN COMPLETE - No changes made", "success")
        else:
            log("\n⚠️ DEPLOYMENT COMPLETED WITH WARNINGS", "warning")
    
    def step_rollback_instructions(self):
        """Print rollback instructions on failure."""
        log("\n" + "=" * 60, "error")
        log("🔙 ROLLBACK INSTRUCTIONS", "error")
        log("=" * 60, "error")
        log("""
1. Via Render Dashboard (fastest):
   - Go to https://dashboard.render.com
   - Select gentlequest service
   - Click "Manual Deploy" → select previous commit
   
2. Via Git (if code issue):
   git revert HEAD
   git push origin main
   
3. Via Render API:
   curl -X POST https://api.render.com/v1/services/{SERVICE_ID}/deploys \\
     -H "Authorization: Bearer {RENDER_API_KEY}" \\
     -d '{"clearCache": "do_not_clear"}'
""", "warning")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Show what would happen without executing (default)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually execute the deployment'
    )
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip running tests (use with caution!)'
    )
    args = parser.parse_args()
    
    # --execute overrides --dry-run
    dry_run = not args.execute
    
    if not dry_run:
        log("\n⚠️  WARNING: This will deploy to PRODUCTION!", "warning")
        response = input("Are you sure you want to continue? (yes/N): ")
        if response.lower() != 'yes':
            log("Aborted.", "info")
            sys.exit(0)
    
    runbook = DeployRunbook(dry_run=dry_run, skip_tests=args.skip_tests)
    runbook.run()


if __name__ == '__main__':
    main()
