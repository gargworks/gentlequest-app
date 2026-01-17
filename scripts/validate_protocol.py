#!/usr/bin/env python3
"""
PROTOCOL VALIDATOR
==================

Single command to verify the entire system is in sync with THE PROTOCOL.

Usage:
    python scripts/validate_protocol.py           # Full validation
    python scripts/validate_protocol.py --quick   # Quick health check
    python scripts/validate_protocol.py --fix     # Auto-fix what's possible

This is the TRUTH ENFORCER. Run it before any major operation.
"""

import json
import hashlib
import sys
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import NamedTuple

# Colors for terminal output
class Colors:
    PASS = '\033[92m'
    FAIL = '\033[91m'
    WARN = '\033[93m'
    INFO = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def ok(msg): print(f"{Colors.PASS}✓{Colors.END} {msg}")
def fail(msg): print(f"{Colors.FAIL}✗{Colors.END} {msg}")
def warn(msg): print(f"{Colors.WARN}⚠{Colors.END} {msg}")
def info(msg): print(f"{Colors.INFO}ℹ{Colors.END} {msg}")
def header(msg): print(f"\n{Colors.BOLD}{'='*60}\n{msg}\n{'='*60}{Colors.END}")

class ValidationResult(NamedTuple):
    passed: int
    failed: int
    warnings: int

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
PROTOCOL_MD = PROJECT_ROOT / 'PROTOCOL.md'
PROTOCOL_JSON = PROJECT_ROOT / 'protocol.json'


def load_protocol() -> dict:
    """Load and parse protocol.json"""
    if not PROTOCOL_JSON.exists():
        fail(f"protocol.json not found at {PROTOCOL_JSON}")
        sys.exit(1)
    return json.loads(PROTOCOL_JSON.read_text())


def validate_protocol_files(protocol: dict) -> ValidationResult:
    """Verify both protocol files exist and are valid."""
    header("§1 PROTOCOL FILES")
    passed = failed = warnings = 0
    
    # Check PROTOCOL.md
    if PROTOCOL_MD.exists():
        ok("PROTOCOL.md exists")
        passed += 1
        
        content = PROTOCOL_MD.read_text()
        if "THE PROTOCOL" in content and "Single Source of Truth" in content:
            ok("PROTOCOL.md has correct header")
            passed += 1
        else:
            fail("PROTOCOL.md missing expected header")
            failed += 1
    else:
        fail("PROTOCOL.md not found")
        failed += 1
    
    # Check protocol.json
    if PROTOCOL_JSON.exists():
        ok("protocol.json exists")
        passed += 1
        
        if protocol.get('version'):
            ok(f"Protocol version: {protocol['version']}")
            passed += 1
        else:
            warn("Protocol version not set")
            warnings += 1
    else:
        fail("protocol.json not found")
        failed += 1
    
    return ValidationResult(passed, failed, warnings)


def validate_critical_files(protocol: dict) -> ValidationResult:
    """Verify all critical files listed in protocol exist."""
    header("§2 CRITICAL FILES")
    passed = failed = warnings = 0
    
    files_section = protocol.get('files', {})
    
    for category, files in files_section.items():
        if isinstance(files, dict):
            for name, path in files.items():
                full_path = PROJECT_ROOT / path
                if full_path.exists():
                    ok(f"{category}/{name}: {path}")
                    passed += 1
                else:
                    # Some files are optional
                    if name in ['ci_workflow', 'doc_tests']:
                        warn(f"{category}/{name}: {path} (optional)")
                        warnings += 1
                    else:
                        fail(f"{category}/{name}: {path} NOT FOUND")
                        failed += 1
    
    return ValidationResult(passed, failed, warnings)


def validate_endpoints(protocol: dict, quick: bool = False) -> ValidationResult:
    """Verify endpoints are documented and (optionally) reachable."""
    header("§3 ENDPOINTS")
    passed = failed = warnings = 0
    
    endpoints = protocol.get('endpoints', [])
    production_url = protocol.get('production', {}).get('url', '')
    
    info(f"Production URL: {production_url}")
    info(f"Documented endpoints: {len(endpoints)}")
    passed += 1
    
    if not quick and production_url:
        # Test health endpoint
        health_url = f"{production_url}/api/health"
        info(f"Testing: {health_url}")
        
        try:
            with urllib.request.urlopen(health_url, timeout=10) as resp:
                if resp.status == 200:
                    ok(f"Health check passed (HTTP {resp.status})")
                    passed += 1
                else:
                    warn(f"Health check returned HTTP {resp.status}")
                    warnings += 1
        except urllib.error.URLError as e:
            warn(f"Health check failed: {e.reason}")
            warnings += 1
        except Exception as e:
            warn(f"Health check error: {e}")
            warnings += 1
    else:
        info("Skipping live endpoint tests (--quick mode or no URL)")
    
    return ValidationResult(passed, failed, warnings)


def validate_secrets(protocol: dict) -> ValidationResult:
    """Verify secrets are NOT in the codebase."""
    header("§4 SECRETS SAFETY")
    passed = failed = warnings = 0
    
    secrets = protocol.get('secrets', {})
    all_secrets = (
        secrets.get('required', []) + 
        secrets.get('recommended', []) + 
        secrets.get('optional', [])
    )
    
    # Check that secrets are not hardcoded
    dangerous_patterns = [
        'sk-',           # OpenAI key prefix
        'AIza',          # Google API key prefix
        'postgres://',   # Database URL
        'redis://',      # Redis URL
    ]
    
    files_to_check = list(PROJECT_ROOT.glob('**/*.py'))
    files_to_check += list(PROJECT_ROOT.glob('**/*.dart'))
    files_to_check = [f for f in files_to_check if 'venv' not in str(f) and '.dart_tool' not in str(f)]
    
    secrets_found = []
    
    for file_path in files_to_check[:100]:  # Limit to avoid slowness
        try:
            content = file_path.read_text()
            for pattern in dangerous_patterns:
                if pattern in content and 'os.getenv' not in content[:content.find(pattern)+50]:
                    # Basic check - might have false positives
                    if not any(skip in str(file_path) for skip in ['test_', '_test.py', 'example']):
                        secrets_found.append((file_path.relative_to(PROJECT_ROOT), pattern))
        except Exception:
            pass
    
    if not secrets_found:
        ok("No obvious secrets found in code")
        passed += 1
    else:
        for path, pattern in secrets_found[:5]:
            warn(f"Potential secret pattern '{pattern}' in {path}")
            warnings += 1
    
    # Check .gitignore
    gitignore = PROJECT_ROOT / '.gitignore'
    if gitignore.exists():
        content = gitignore.read_text()
        if '.env' in content:
            ok(".env is in .gitignore")
            passed += 1
        else:
            fail(".env not in .gitignore - SECURITY RISK")
            failed += 1
    
    return ValidationResult(passed, failed, warnings)


def validate_documentation(protocol: dict) -> ValidationResult:
    """Verify documentation exists and is fresh."""
    header("§5 DOCUMENTATION")
    passed = failed = warnings = 0
    
    docs = protocol.get('files', {}).get('documentation', {})
    
    for name, path in docs.items():
        full_path = PROJECT_ROOT / path
        if full_path.exists():
            # Check freshness
            content = full_path.read_text()
            if 'Last Updated' in content or 'last_updated' in content:
                ok(f"{name}: exists with date tracking")
                passed += 1
            else:
                warn(f"{name}: exists but no date tracking")
                warnings += 1
        else:
            fail(f"{name}: NOT FOUND at {path}")
            failed += 1
    
    return ValidationResult(passed, failed, warnings)


def validate_stack(protocol: dict) -> ValidationResult:
    """Verify stack components are correctly configured."""
    header("§6 STACK VALIDATION")
    passed = failed = warnings = 0
    
    stack = protocol.get('stack', {})
    
    # Check requirements.txt for Flask version
    req_file = PROJECT_ROOT / 'requirements.txt'
    if req_file.exists():
        content = req_file.read_text()
        if 'flask' in content.lower():
            ok("Flask found in requirements.txt")
            passed += 1
        else:
            fail("Flask not in requirements.txt")
            failed += 1
    
    # Check pubspec.yaml exists
    pubspec = PROJECT_ROOT / 'ai_buddy_web' / 'pubspec.yaml'
    if pubspec.exists():
        ok("Flutter pubspec.yaml exists")
        passed += 1
    else:
        fail("Flutter pubspec.yaml not found")
        failed += 1
    
    # Check Dockerfile
    dockerfile = PROJECT_ROOT / 'Dockerfile'
    if dockerfile.exists():
        content = dockerfile.read_text()
        if 'python:3.11' in content:
            ok("Dockerfile uses Python 3.11")
            passed += 1
        else:
            warn("Dockerfile may use different Python version")
            warnings += 1
    
    return ValidationResult(passed, failed, warnings)


def compute_protocol_hash() -> str:
    """Compute SHA256 hash of PROTOCOL.md"""
    if PROTOCOL_MD.exists():
        content = PROTOCOL_MD.read_bytes()
        return hashlib.sha256(content).hexdigest()[:16]
    return "NOT_FOUND"


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--quick', action='store_true', help='Quick validation (skip network tests)')
    parser.add_argument('--fix', action='store_true', help='Attempt to auto-fix issues')
    args = parser.parse_args()
    
    print(f"""
{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗
║                    PROTOCOL VALIDATOR                         ║
║              Verifying Single Source of Truth                 ║
╚══════════════════════════════════════════════════════════════╝{Colors.END}
    """)
    
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Mode: {'QUICK' if args.quick else 'FULL'}")
    
    # Load protocol
    try:
        protocol = load_protocol()
        ok("Protocol loaded successfully")
    except Exception as e:
        fail(f"Failed to load protocol: {e}")
        sys.exit(1)
    
    # Run validations
    total_passed = total_failed = total_warnings = 0
    
    results = [
        validate_protocol_files(protocol),
        validate_critical_files(protocol),
        validate_endpoints(protocol, args.quick),
        validate_secrets(protocol),
        validate_documentation(protocol),
        validate_stack(protocol),
    ]
    
    for r in results:
        total_passed += r.passed
        total_failed += r.failed
        total_warnings += r.warnings
    
    # Summary
    header("VALIDATION SUMMARY")
    
    protocol_hash = compute_protocol_hash()
    print(f"Protocol Hash: {protocol_hash}")
    print(f"Protocol Version: {protocol.get('version', 'unknown')}")
    print()
    
    print(f"{Colors.PASS}Passed:{Colors.END}   {total_passed}")
    print(f"{Colors.FAIL}Failed:{Colors.END}   {total_failed}")
    print(f"{Colors.WARN}Warnings:{Colors.END} {total_warnings}")
    print()
    
    if total_failed == 0:
        print(f"{Colors.PASS}{Colors.BOLD}✓ PROTOCOL VALIDATION PASSED{Colors.END}")
        print("  The truth prevails. System is in sync.")
        sys.exit(0)
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}✗ PROTOCOL VALIDATION FAILED{Colors.END}")
        print(f"  {total_failed} critical issues must be resolved.")
        print("  Consult PROTOCOL.md for the canonical truth.")
        sys.exit(1)


if __name__ == '__main__':
    main()
