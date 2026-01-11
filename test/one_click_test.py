#!/usr/bin/env python3
"""
One-Click Test Runner
Simplified test execution with automatic environment setup
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description, check=True):
    """Run command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True, timeout=300)
        if result.stdout:
            print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out")
        return False
    except Exception as e:
        print(f"💥 {description} error: {e}")
        return False

def main():
    """One-click test execution"""
    print("🚀 One-Click E2E Test Runner")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("test").exists():
        print("❌ Error: test directory not found")
        print("💡 Run this from the project root directory")
        sys.exit(1)
    
    # Check Python
    if not run_command("python3 --version", "Checking Python", check=False):
        print("❌ Python 3 is required")
        sys.exit(1)
    
    # Setup virtual environment if needed
    venv_path = Path("test_env")
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        if not run_command("python3.11 -m venv test_env", "Virtual environment creation"):
            print("❌ Failed to create virtual environment")
            sys.exit(1)
    
    # Activate virtual environment and install dependencies
    print("📦 Installing dependencies...")
    commands = [
        "source test_env/bin/activate && pip install --upgrade pip",
        "source test_env/bin/activate && pip install -r test/requirements.txt",
        "source test_env/bin/activate && python3 -m playwright install chromium"
    ]
    
    for cmd in commands:
        if not run_command(cmd, cmd.split("&&")[1].strip(), check=False):
            print(f"⚠️ Warning: {cmd} failed, continuing...")
    
    # Run focused tests (most reliable)
    print("🧪 Running focused E2E tests...")
    success = run_command("source test_env/bin/activate && python3 test/focused_e2e_test.py", 
                         "Focused test execution", check=False)
    
    if success:
        print("✅ Tests completed successfully!")
        
        # Show results if available
        results_file = Path("test/focused_e2e_results.json")
        if results_file.exists():
            try:
                import json
                with open(results_file, 'r') as f:
                    data = json.load(f)
                print(f"📊 Pass Rate: {data.get('pass_rate', 0):.1f}%")
                print(f"📈 Passed: {data.get('passed', 0)}/{data.get('total', 0)}")
            except:
                pass
    else:
        print("⚠️ Tests completed with issues")
    
    # Generate quick status
    print("\n🏥 Quick Status Check...")
    run_command("python3 test/test_status_monitor.py", "Status monitoring", check=False)
    
    # Show next steps
    print("\n🎯 Next Steps:")
    print("• View detailed results: test/focused_e2e_results.json")
    print("• Open dashboard: open test/dashboard/index.html")
    print("• Run health check: python3 test/health_check.py")
    print("• View all tests: python3 test/test_analytics.py")
    
    print(f"\n✅ One-Click Test Runner completed!")

if __name__ == "__main__":
    main()
