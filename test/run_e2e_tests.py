#!/usr/bin/env python3
"""
Quick runner for GentleQuest E2E tests
Installs dependencies and runs the test suite
"""

import subprocess
import sys
import asyncio
from pathlib import Path

async def main():
    print("🚀 GentleQuest E2E Test Runner")
    print("=" * 50)
    
    # Install Playwright browsers
    print("📦 Installing Playwright browsers...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                      check=True, capture_output=True)
        print("✅ Playwright browsers installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Playwright: {e}")
        return
    
    # Run the test suite
    print("\n🧪 Running E2E tests...")
    try:
        from e2e_test_suite import main as run_tests
        results = await run_tests()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {results['total_tests']}")
        print(f"✅ Passed: {results['passed']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"⚠️ Partial: {results['partial']}")
        print(f"📈 Pass Rate: {results['pass_rate']:.1f}%")
        
        if results['failed'] > 0:
            print("\n❌ FAILED TESTS:")
            for result in results['results']:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['details']}")
        
        print(f"\n📸 Screenshots: {results['screenshots_dir']}")
        print(f"📄 Results: test/e2e_results.json")
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
