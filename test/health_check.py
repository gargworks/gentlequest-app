#!/usr/bin/env python3
"""
Test Health Check Monitor
Monitors test infrastructure health and alerts on issues
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

class TestHealthMonitor:
    def __init__(self):
        self.test_dir = Path("test")
        self.health_issues = []
        self.performance_thresholds = {
            'max_load_time': 2.0,  # seconds
            'min_pass_rate': 70.0,  # percentage
            'max_execution_time': 300  # seconds
        }
    
    def check_environment_health(self) -> Dict[str, bool]:
        """Check test environment setup"""
        checks = {
            'python_available': False,
            'playwright_installed': False,
            'test_files_exist': False,
            'screenshots_writable': False,
            'results_readable': False
        }
        
        # Check Python
        try:
            result = subprocess.run(['python3', '--version'], 
                                  capture_output=True, text=True)
            checks['python_available'] = result.returncode == 0
        except:
            pass
        
        # Check Playwright
        try:
            result = subprocess.run(['python3', '-c', 'import playwright'], 
                                  capture_output=True, text=True)
            checks['playwright_installed'] = result.returncode == 0
        except:
            pass
        
        # Check test files
        required_files = [
            'focused_e2e_test.py',
            'flutter_web_e2e_test.py',
            'e2e_test_suite.py'
        ]
        checks['test_files_exist'] = all(
            (self.test_dir / f).exists() for f in required_files
        )
        
        # Check screenshots directory
        screenshots_dir = self.test_dir / 'screenshots' / 'e2e'
        checks['screenshots_writable'] = screenshots_dir.exists()
        
        # Check results files
        results_files = [
            'focused_e2e_results.json',
            'flutter_e2e_results.json'
        ]
        checks['results_readable'] = any(
            (self.test_dir / f).exists() for f in results_files
        )
        
        return checks
    
    def check_performance_health(self) -> Dict[str, float]:
        """Check performance metrics"""
        metrics = {
            'app_load_time': 0.0,
            'test_execution_time': 0.0,
            'disk_usage': 0.0
        }
        
        # Check app load time
        try:
            start_time = time.time()
            result = subprocess.run([
                'curl', '-s', '-w', '%{time_total}',
                '-o', '/dev/null',
                'https://gentlequest.onrender.com'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                metrics['app_load_time'] = float(result.stdout.strip())
        except:
            metrics['app_load_time'] = float('inf')
        
        # Check disk usage for test directory
        try:
            result = subprocess.run([
                'du', '-sk', str(self.test_dir)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                metrics['disk_usage'] = float(result.stdout.split()[0])  # KB
        except:
            pass
        
        return metrics
    
    def check_test_results_health(self) -> Dict[str, any]:
        """Check test results for health issues"""
        health = {
            'pass_rates': {},
            'failing_tests': [],
            'flaky_tests': [],
            'trend_analysis': 'stable'
        }
        
        # Check each test suite
        suites = ['focused', 'flutter', 'comprehensive']
        
        for suite in suites:
            result_file = self.test_dir / f'{suite}_e2e_results.json'
            if result_file.exists():
                try:
                    with open(result_file, 'r') as f:
                        data = json.load(f)
                    
                    pass_rate = data.get('pass_rate', 0)
                    health['pass_rates'][suite] = pass_rate
                    
                    if pass_rate < self.performance_thresholds['min_pass_rate']:
                        health['failing_tests'].append(suite)
                    
                    # Check for flaky tests (partial results)
                    if data.get('partial', 0) > 2:
                        health['flaky_tests'].append(suite)
                        
                except:
                    health['pass_rates'][suite] = 0
                    health['failing_tests'].append(suite)
        
        return health
    
    def diagnose_issues(self) -> List[str]:
        """Diagnose health issues and provide solutions"""
        issues = []
        
        # Check environment
        env_health = self.check_environment_health()
        
        if not env_health['python_available']:
            issues.append("🐍 Python 3 not available - install Python 3.11+")
        
        if not env_health['playwright_installed']:
            issues.append("🎭 Playwright not installed - run: pip install playwright && playwright install chromium")
        
        if not env_health['test_files_exist']:
            issues.append("📁 Test files missing - check test directory structure")
        
        if not env_health['screenshots_writable']:
            issues.append("📸 Screenshots directory not writable - check permissions")
        
        # Check performance
        perf_health = self.check_performance_health()
        
        if perf_health['app_load_time'] > self.performance_thresholds['max_load_time']:
            issues.append(f"⚡ App load time slow: {perf_health['app_load_time']:.2f}s (threshold: {self.performance_thresholds['max_load_time']}s)")
        
        if perf_health['disk_usage'] > 100000:  # 100MB
            issues.append(f"💾 Test directory large: {perf_health['disk_usage']/1024:.1f}MB - consider cleanup")
        
        # Check test results
        results_health = self.check_test_results_health()
        
        for suite, rate in results_health['pass_rates'].items():
            if rate < self.performance_thresholds['min_pass_rate']:
                issues.append(f"❌ {suite.title()} suite pass rate low: {rate:.1f}% (threshold: {self.performance_thresholds['min_pass_rate']}%)")
        
        for failing in results_health['failing_tests']:
            issues.append(f"🚨 {failing.title()} test suite failing - immediate attention needed")
        
        for flaky in results_health['flaky_tests']:
            issues.append(f"⚠️ {flaky.title()} test suite flaky - review test stability")
        
        return issues
    
    def generate_health_report(self) -> str:
        """Generate comprehensive health report"""
        report = []
        report.append("🏥 Test Infrastructure Health Check")
        report.append("=" * 50)
        report.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Environment Health
        env_health = self.check_environment_health()
        report.append("🔧 Environment Health:")
        
        for check, status in env_health.items():
            icon = "✅" if status else "❌"
            report.append(f"   {icon} {check.replace('_', ' ').title()}")
        
        report.append("")
        
        # Performance Health
        perf_health = self.check_performance_health()
        report.append("⚡ Performance Metrics:")
        
        for metric, value in perf_health.items():
            if metric == 'app_load_time':
                status = "✅" if value < self.performance_thresholds['max_load_time'] else "⚠️"
                report.append(f"   {status} App Load Time: {value:.2f}s")
            elif metric == 'disk_usage':
                status = "✅" if value < 50000 else "⚠️"
                report.append(f"   {status} Disk Usage: {value/1024:.1f}MB")
        
        report.append("")
        
        # Test Results Health
        results_health = self.check_test_results_health()
        report.append("📊 Test Results Health:")
        
        for suite, rate in results_health['pass_rates'].items():
            if rate >= self.performance_thresholds['min_pass_rate']:
                icon = "✅"
            elif rate >= 50:
                icon = "⚠️"
            else:
                icon = "❌"
            report.append(f"   {icon} {suite.title()}: {rate:.1f}% pass rate")
        
        report.append("")
        
        # Issues and Recommendations
        issues = self.diagnose_issues()
        
        if issues:
            report.append("🚨 Issues Found:")
            for issue in issues:
                report.append(f"   {issue}")
            report.append("")
        else:
            report.append("✅ No critical issues found!")
            report.append("")
        
        # Recommendations
        report.append("💡 Recommendations:")
        report.append("   1. Run health check weekly to monitor infrastructure")
        report.append("   2. Set up automated alerts for performance degradation")
        report.append("   3. Archive old screenshots to save disk space")
        report.append("   4. Monitor test pass rates for trend analysis")
        
        return "\n".join(report)
    
    def save_health_report(self, filename: str = "test_health_report.txt"):
        """Save health report to file"""
        report = self.generate_health_report()
        
        report_file = self.test_dir / filename
        with open(report_file, 'w') as f:
            f.write(report)
        
        return str(report_file)
    
    def run_quick_check(self) -> bool:
        """Run quick health check and return status"""
        env_health = self.check_environment_health()
        
        # Critical checks
        critical_checks = [
            env_health['python_available'],
            env_health['playwright_installed'],
            env_health['test_files_exist']
        ]
        
        return all(critical_checks)

def main():
    """Run health check monitor"""
    monitor = TestHealthMonitor()
    
    print("🏥 Running Test Infrastructure Health Check...")
    
    # Generate and display report
    report = monitor.generate_health_report()
    print(report)
    
    # Save report
    report_file = monitor.save_health_report()
    print(f"\n📄 Health report saved to: {report_file}")
    
    # Quick check status
    is_healthy = monitor.run_quick_check()
    status = "✅ Healthy" if is_healthy else "⚠️ Needs Attention"
    print(f"\n🎯 Overall Status: {status}")
    
    return {
        'healthy': is_healthy,
        'report': report,
        'report_file': report_file
    }

if __name__ == "__main__":
    main()
