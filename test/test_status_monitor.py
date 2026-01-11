#!/usr/bin/env python3
"""
Test Status Monitor
Real-time monitoring of E2E test infrastructure status
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

class TestStatusMonitor:
    def __init__(self):
        self.test_dir = Path("test")
        
    def check_python_environment(self) -> dict:
        """Check Python environment status"""
        status = {
            "python_available": False,
            "python_version": "",
            "virtual_env": False,
            "playwright": False
        }
        
        try:
            # Check Python
            result = subprocess.run(['python3', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                status["python_available"] = True
                status["python_version"] = result.stdout.strip()
            
            # Check virtual environment
            if (self.test_dir / "test_env").exists():
                status["virtual_env"] = True
            
            # Check Playwright
            result = subprocess.run(['python3', '-c', 'import playwright'], 
                                  capture_output=True, text=True)
            status["playwright"] = result.returncode == 0
            
        except:
            pass
        
        return status
    
    def check_file_structure(self) -> dict:
        """Check test file structure"""
        status = {
            "directories": {},
            "key_files": {},
            "total_files": 0
        }
        
        # Check directories
        important_dirs = [
            "screenshots/e2e", "backups", "archive", "dashboard",
            "__pycache__"
        ]
        
        for dir_name in important_dirs:
            dir_path = self.test_dir / dir_name
            status["directories"][dir_name] = dir_path.exists()
        
        # Count files
        if self.test_dir.exists():
            status["total_files"] = len(list(self.test_dir.glob("**/*.py")))
        
        # Check key files
        key_files = [
            "focused_e2e_test.py", "health_check.py", 
            "test_analytics.py", "dashboard/index.html",
            "README.md", "requirements.txt"
        ]
        
        for file_name in key_files:
            file_path = self.test_dir / file_name
            status["key_files"][file_name] = file_path.exists()
        
        return status
    
    def check_test_results(self) -> dict:
        """Check recent test results"""
        status = {
            "focused_results": False,
            "flutter_results": False,
            "comprehensive_results": False,
            "latest_run": None,
            "pass_rates": {}
        }
        
        # Check result files
        result_files = {
            "focused_results": "focused_e2e_results.json",
            "flutter_results": "flutter_e2e_results.json",
            "comprehensive_results": "e2e_results.json"
        }
        
        for key, filename in result_files.items():
            file_path = self.test_dir / filename
            if file_path.exists():
                status[key] = True
                
                # Extract pass rate
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    pass_rate = data.get('pass_rate', 0)
                    suite_name = filename.replace('_e2e_results.json', '')
                    status["pass_rates"][suite_name] = pass_rate
                    
                    # Track latest run
                    if not status["latest_run"] or data.get('timestamp') > status["latest_run"]:
                        status["latest_run"] = data.get('timestamp')
                except:
                    pass
        
        return status
    
    def check_performance(self) -> dict:
        """Check performance metrics"""
        status = {
            "app_load_time": None,
            "performance_status": "unknown"
        }
        
        try:
            # Quick app load time check
            result = subprocess.run([
                'curl', '-s', '-w', '%{time_total}',
                '-o', '/dev/null',
                'https://gentlequest.onrender.com'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                load_time = float(result.stdout.strip())
                status["app_load_time"] = load_time
                
                if load_time < 1.0:
                    status["performance_status"] = "excellent"
                elif load_time < 2.0:
                    status["performance_status"] = "good"
                elif load_time < 5.0:
                    status["performance_status"] = "slow"
                else:
                    status["performance_status"] = "critical"
        except:
            status["performance_status"] = "error"
        
        return status
    
    def generate_status_report(self) -> dict:
        """Generate complete status report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "operational",
            "components": {
                "python_env": self.check_python_environment(),
                "file_structure": self.check_file_structure(),
                "test_results": self.check_test_results(),
                "performance": self.check_performance()
            }
        }
        
        # Determine overall status
        issues = []
        
        # Check critical components
        if not report["components"]["python_env"]["python_available"]:
            issues.append("Python not available")
        
        if not report["components"]["file_structure"]["key_files"].get("focused_e2e_test.py", False):
            issues.append("Key test files missing")
        
        if not report["components"]["test_results"]["focused_results"]:
            issues.append("No test results found")
        
        if report["components"]["performance"]["performance_status"] == "error":
            issues.append("Performance check failed")
        
        if issues:
            report["overall_status"] = "degraded" if len(issues) <= 2 else "critical"
            report["issues"] = issues
        else:
            report["issues"] = []
        
        return report
    
    def print_status_summary(self, report: dict):
        """Print formatted status summary"""
        print("🏥 E2E Test Infrastructure Status Monitor")
        print("=" * 50)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Overall Status: {report['overall_status'].upper()}")
        print("")
        
        # Python Environment
        python_env = report["components"]["python_env"]
        print("🐍 Python Environment:")
        print(f"   Python: {'✅' if python_env['python_available'] else '❌'} {python_env['python_version']}")
        print(f"   Virtual Env: {'✅' if python_env['virtual_env'] else '⚠️'}")
        print(f"   Playwright: {'✅' if python_env['playwright'] else '⚠️'}")
        print("")
        
        # File Structure
        file_struct = report["components"]["file_structure"]
        print("📁 File Structure:")
        key_files_status = sum(1 for exists in file_struct["key_files"].values() if exists)
        total_key_files = len(file_struct["key_files"])
        print(f"   Key Files: {key_files_status}/{total_key_files} present")
        print(f"   Total Python Files: {file_struct['total_files']}")
        print("")
        
        # Test Results
        test_results = report["components"]["test_results"]
        print("📊 Test Results:")
        for suite, rate in test_results["pass_rates"].items():
            print(f"   {suite.title()}: {rate:.1f}% pass rate")
        if test_results["latest_run"]:
            print(f"   Latest Run: {test_results['latest_run']}")
        print("")
        
        # Performance
        perf = report["components"]["performance"]
        print("⚡ Performance:")
        if perf["app_load_time"]:
            print(f"   App Load Time: {perf['app_load_time']:.2f}s ({perf['performance_status']})")
        else:
            print(f"   App Load Time: Check failed")
        print("")
        
        # Issues
        if report["issues"]:
            print("🚨 Issues Found:")
            for issue in report["issues"]:
                print(f"   • {issue}")
        else:
            print("✅ No critical issues detected")
        
        print("")
        print("💡 Quick Actions:")
        print("   • Run tests: ./test/quick_test.sh")
        print("   • Health check: python3 test/health_check.py")
        print("   • View dashboard: open test/dashboard/index.html")

def main():
    """Run status monitor"""
    monitor = TestStatusMonitor()
    report = monitor.generate_status_report()
    monitor.print_status_summary(report)
    
    # Save report
    report_file = monitor.test_dir / "status_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Status report saved to: {report_file}")
    
    return report

if __name__ == "__main__":
    main()
