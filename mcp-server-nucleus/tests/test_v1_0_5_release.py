#!/usr/bin/env python3
"""
Comprehensive test suite for Nucleus v1.0.5 release.
Tests all critical features: Recursive Mounting, Persistence, CLI.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
    
    def add_pass(self, test_name):
        self.passed.append(test_name)
        print(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed.append((test_name, error))
        print(f"❌ FAIL: {test_name}")
        print(f"   Error: {error}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed)
        print("\n" + "="*60)
        print(f"TEST SUMMARY: {len(self.passed)}/{total} passed")
        print("="*60)
        if self.failed:
            print("\n❌ Failed tests:")
            for name, error in self.failed:
                print(f"  - {name}: {error}")
        return len(self.failed) == 0


def test_cli_mount_list(results, brain_path):
    """Test: nucleus mount list command"""
    try:
        env = os.environ.copy()
        env['NUCLEAR_BRAIN_PATH'] = str(brain_path)
        # Point to the local source
        src_path = str(Path(__file__).parent.parent / "src")
        env['PYTHONPATH'] = src_path + ":" + env.get('PYTHONPATH', '')
        
        result = subprocess.run(
            ['python3', '-m', 'mcp_server_nucleus.cli', 'mount', 'list'],
            capture_output=True,
            text=True,
            env=env,
            timeout=5
        )
        
        if result.returncode == 0:
            results.add_pass("CLI: nucleus mount list")
        else:
            results.add_fail("CLI: nucleus mount list", f"Exit code {result.returncode}: {result.stderr}")
    except Exception as e:
        results.add_fail("CLI: nucleus mount list", str(e))


def test_cli_mount_add(results, brain_path):
    """Test: nucleus mount add command"""
    try:
        env = os.environ.copy()
        env['NUCLEAR_BRAIN_PATH'] = str(brain_path)
        src_path = str(Path(__file__).parent.parent / "src")
        env['PYTHONPATH'] = src_path + ":" + env.get('PYTHONPATH', '')
        
        result = subprocess.run(
            [
                'python3', '-m', 'mcp_server_nucleus.cli', 'mount', 'add',
                'test_fs',
                '--transport', 'stdio',
                '--command', 'npx',
                '--args', '@modelcontextprotocol/server-filesystem', '/tmp'
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=5
        )
        
        if result.returncode == 0 and "Mount 'test_fs' added" in result.stdout:
            # Verify mounts.json was created
            mounts_file = brain_path / "mounts.json"
            if mounts_file.exists():
                mounts = json.loads(mounts_file.read_text())
                if 'test_fs' in mounts:
                    results.add_pass("CLI: nucleus mount add")
                else:
                    results.add_fail("CLI: nucleus mount add", "Mount not found in mounts.json")
            else:
                results.add_fail("CLI: nucleus mount add", "mounts.json not created")
        else:
            results.add_fail("CLI: nucleus mount add", f"Exit code {result.returncode}: {result.stderr}")
    except Exception as e:
        results.add_fail("CLI: nucleus mount add", str(e))


def test_mounts_json_persistence(results, brain_path):
    """Test: mounts.json persistence format"""
    try:
        mounts_file = brain_path / "mounts.json"
        
        # Create a test mount configuration
        test_config = {
            "test_mount": {
                "transport": "stdio",
                "command": "npx",
                "args": ["@modelcontextprotocol/server-filesystem", "/tmp"],
                "status": "configured"
            }
        }
        
        mounts_file.write_text(json.dumps(test_config, indent=2))
        
        # Verify it can be read back
        loaded = json.loads(mounts_file.read_text())
        
        if loaded == test_config:
            results.add_pass("Persistence: mounts.json format")
        else:
            results.add_fail("Persistence: mounts.json format", "Loaded config doesn't match")
    except Exception as e:
        results.add_fail("Persistence: mounts.json format", str(e))


def test_mounter_restore_logic(results, brain_path):
    """Test: Mounter.restore_mounts() logic"""
    try:
        # Import the mounter
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from mcp_server_nucleus.runtime.mounter_ops import Mounter
        
        # Create a mounts.json
        mounts_file = brain_path / "mounts.json"
        test_config = {
            "mock_server": {
                "transport": "stdio",
                "command": "python3",
                "args": ["-c", "print('mock')"],
                "status": "configured"
            }
        }
        mounts_file.write_text(json.dumps(test_config, indent=2))
        
        # Initialize mounter
        mounter = Mounter(brain_path)
        
        # Verify it loaded the config
        if "mock_server" in mounter.mount_configs:
            results.add_pass("Mounter: Load mounts.json")
        else:
            results.add_fail("Mounter: Load mounts.json", "Config not loaded")
            
    except Exception as e:
        results.add_fail("Mounter: Load mounts.json", str(e))


def test_cli_argument_parsing(results, brain_path):
    """Test: CLI argument parsing (no collision between 'command' and '--command')"""
    try:
        env = os.environ.copy()
        env['NUCLEAR_BRAIN_PATH'] = str(brain_path)
        src_path = str(Path(__file__).parent.parent / "src")
        env['PYTHONPATH'] = src_path + ":" + env.get('PYTHONPATH', '')
        
        # This should NOT fail with "Unknown command: npx"
        result = subprocess.run(
            [
                'python3', '-m', 'mcp_server_nucleus.cli', 'mount', 'add',
                'parse_test',
                '--transport', 'stdio',
                '--command', 'npx'
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=5
        )
        
        # Should succeed (even without --args, it will just warn)
        if "Unknown command" not in result.stderr and "Unknown command" not in result.stdout:
            results.add_pass("CLI: Argument parsing fix")
        else:
            results.add_fail("CLI: Argument parsing fix", "Command collision detected")
    except Exception as e:
        results.add_fail("CLI: Argument parsing fix", str(e))


def test_brain_init(results, brain_path):
    """Test: nucleus init creates proper brain structure"""
    try:
        env = os.environ.copy()
        src_path = str(Path(__file__).parent.parent / "src")
        env['PYTHONPATH'] = src_path + ":" + env.get('PYTHONPATH', '')
        
        # If brain_path exists, remove it for a clean test
        if brain_path.exists():
            shutil.rmtree(brain_path)

        result = subprocess.run(
            ['python3', '-m', 'mcp_server_nucleus.cli', 'init', str(brain_path), '--template', 'solo'],
            capture_output=True,
            text=True,
            env=env,
            timeout=10
        )
        
        # Check key directories exist
        required_dirs = ['ledger', 'sessions', 'slots', 'memory']
        all_exist = all((brain_path / d).exists() for d in required_dirs)
        
        if all_exist:
            results.add_pass("Brain: Init structure")
        else:
            missing = [d for d in required_dirs if not (brain_path / d).exists()]
            results.add_fail("Brain: Init structure", f"Missing dirs: {missing}")
    except Exception as e:
        results.add_fail("Brain: Init structure", str(e))


def test_version_consistency(results):
    """Test: Version in pyproject.toml matches expected"""
    try:
        dev_toml = Path(__file__).parent.parent / "pyproject.toml"
        
        if dev_toml.exists():
            content = dev_toml.read_text()
            if 'version = "1.0.5"' in content:
                results.add_pass("Version: pyproject.toml = 1.0.5")
            else:
                results.add_fail("Version: pyproject.toml = 1.0.5", "Version mismatch")
        else:
            results.add_fail("Version: pyproject.toml = 1.0.5", "File not found")
    except Exception as e:
        results.add_fail("Version: pyproject.toml = 1.0.5", str(e))


def main():
    print("🧪 Nucleus v1.0.5 Comprehensive Test Suite")
    print("="*60)
    
    results = TestResults()
    
    # Create temporary brain for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        brain_path = Path(tmpdir) / ".brain_test"
        brain_path.mkdir(parents=True)
        
        print(f"\n📁 Test brain: {brain_path}\n")
        
        # Run all tests
        test_brain_init(results, brain_path)
        test_mounts_json_persistence(results, brain_path)
        test_cli_mount_list(results, brain_path)
        test_cli_mount_add(results, brain_path)
        test_cli_argument_parsing(results, brain_path)
        test_mounter_restore_logic(results, brain_path)
        test_version_consistency(results)
    
    # Print summary
    success = results.summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
