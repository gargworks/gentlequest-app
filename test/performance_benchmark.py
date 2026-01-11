#!/usr/bin/env python3
"""
Performance Benchmark Suite
Establishes and tracks performance benchmarks for E2E tests
"""

import time
import json
import statistics
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

class PerformanceBenchmark:
    def __init__(self):
        self.test_dir = Path("test")
        self.benchmarks_file = self.test_dir / "performance_benchmarks.json"
        self.results_file = self.test_dir / "performance_results.json"
        self.load_benchmarks()
        
    def load_benchmarks(self):
        """Load existing benchmarks or create defaults"""
        default_benchmarks = {
            "app_load_time": {
                "target": 1.0,  # seconds
                "warning": 2.0,
                "critical": 3.0
            },
            "test_execution_time": {
                "focused": {"target": 60, "warning": 120, "critical": 180},
                "flutter": {"target": 90, "warning": 150, "critical": 240},
                "comprehensive": {"target": 120, "warning": 200, "critical": 300}
            },
            "memory_usage": {
                "target": 100,  # MB
                "warning": 200,
                "critical": 500
            },
            "disk_usage": {
                "target": 10,   # MB
                "warning": 50,
                "critical": 100
            }
        }
        
        if self.benchmarks_file.exists():
            try:
                with open(self.benchmarks_file, 'r') as f:
                    self.benchmarks = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_benchmarks.items():
                    if key not in self.benchmarks:
                        self.benchmarks[key] = value
            except:
                self.benchmarks = default_benchmarks
        else:
            self.benchmarks = default_benchmarks
            self.save_benchmarks()
    
    def save_benchmarks(self):
        """Save benchmarks to file"""
        with open(self.benchmarks_file, 'w') as f:
            json.dump(self.benchmarks, f, indent=2)
    
    def measure_app_load_time(self, url: str = "https://gentlequest.onrender.com") -> float:
        """Measure application load time"""
        try:
            start_time = time.time()
            result = subprocess.run([
                'curl', '-s', '-w', '%{time_total}',
                '-o', '/dev/null',
                url
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                return float('inf')
        except:
            return float('inf')
    
    def measure_test_execution_time(self, test_suite: str) -> float:
        """Measure test suite execution time"""
        try:
            start_time = time.time()
            result = subprocess.run([
                'python3', f'test/{test_suite}_e2e_test.py'
            ], capture_output=True, text=True, timeout=600)
            
            execution_time = time.time() - start_time
            return execution_time
        except subprocess.TimeoutExpired:
            return 600.0  # Timeout value
        except:
            return float('inf')
    
    def measure_memory_usage(self) -> float:
        """Measure current memory usage"""
        try:
            result = subprocess.run([
                'ps', '-o', 'rss=', '-p', str(time.getpid())
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                rss_kb = float(result.stdout.strip())
                return rss_kb / 1024  # Convert to MB
            else:
                return 0.0
        except:
            return 0.0
    
    def measure_disk_usage(self) -> float:
        """Measure test directory disk usage"""
        try:
            result = subprocess.run([
                'du', '-sk', str(self.test_dir)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                disk_kb = float(result.stdout.split()[0])
                return disk_kb / 1024  # Convert to MB
            else:
                return 0.0
        except:
            return 0.0
    
    def run_benchmark_suite(self) -> Dict[str, any]:
        """Run complete benchmark suite"""
        print("🏁 Running Performance Benchmark Suite...")
        print("=" * 50)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
            "comparisons": {},
            "status": "unknown"
        }
        
        # App Load Time
        print("⚡ Measuring app load time...")
        load_time = self.measure_app_load_time()
        results["metrics"]["app_load_time"] = load_time
        
        load_bench = self.benchmarks["app_load_time"]
        if load_time <= load_bench["target"]:
            load_status = "✅ Excellent"
        elif load_time <= load_bench["warning"]:
            load_status = "⚠️ Good"
        elif load_time <= load_bench["critical"]:
            load_status = "❌ Poor"
        else:
            load_status = "🚨 Critical"
        
        print(f"   Load Time: {load_time:.2f}s {load_status}")
        
        # Test Execution Times
        test_suites = ["focused", "flutter", "comprehensive"]
        for suite in test_suites:
            print(f"🧪 Measuring {suite} test execution time...")
            exec_time = self.measure_test_execution_time(suite)
            results["metrics"][f"{suite}_execution_time"] = exec_time
            
            exec_bench = self.benchmarks["test_execution_time"][suite]
            if exec_time <= exec_bench["target"]:
                exec_status = "✅ Excellent"
            elif exec_time <= exec_bench["warning"]:
                exec_status = "⚠️ Good"
            elif exec_time <= exec_bench["critical"]:
                exec_status = "❌ Poor"
            else:
                exec_status = "🚨 Critical"
            
            print(f"   {suite.title()}: {exec_time:.1f}s {exec_status}")
        
        # Memory Usage
        print("💾 Measuring memory usage...")
        memory_usage = self.measure_memory_usage()
        results["metrics"]["memory_usage"] = memory_usage
        
        mem_bench = self.benchmarks["memory_usage"]
        if memory_usage <= mem_bench["target"]:
            mem_status = "✅ Excellent"
        elif memory_usage <= mem_bench["warning"]:
            mem_status = "⚠️ Good"
        elif memory_usage <= mem_bench["critical"]:
            mem_status = "❌ Poor"
        else:
            mem_status = "🚨 Critical"
        
        print(f"   Memory: {memory_usage:.1f}MB {mem_status}")
        
        # Disk Usage
        print("💿 Measuring disk usage...")
        disk_usage = self.measure_disk_usage()
        results["metrics"]["disk_usage"] = disk_usage
        
        disk_bench = self.benchmarks["disk_usage"]
        if disk_usage <= disk_bench["target"]:
            disk_status = "✅ Excellent"
        elif disk_usage <= disk_bench["warning"]:
            disk_status = "⚠️ Good"
        elif disk_usage <= disk_bench["critical"]:
            disk_status = "❌ Poor"
        else:
            disk_status = "🚨 Critical"
        
        print(f"   Disk: {disk_usage:.1f}MB {disk_status}")
        
        # Overall Status
        critical_count = 0
        for metric, value in results["metrics"].items():
            if metric == "app_load_time":
                bench = self.benchmarks["app_load_time"]
            elif metric.endswith("_execution_time"):
                suite = metric.replace("_execution_time", "")
                bench = self.benchmarks["test_execution_time"][suite]
            elif metric == "memory_usage":
                bench = self.benchmarks["memory_usage"]
            elif metric == "disk_usage":
                bench = self.benchmarks["disk_usage"]
            else:
                continue
                
            if value > bench["critical"]:
                critical_count += 1
        
        if critical_count == 0:
            results["status"] = "✅ Healthy"
        elif critical_count <= 2:
            results["status"] = "⚠️ Needs Attention"
        else:
            results["status"] = "🚨 Critical"
        
        print(f"\n🎯 Overall Status: {results['status']}")
        
        return results
    
    def compare_with_historical(self, current_results: Dict) -> Dict:
        """Compare current results with historical data"""
        comparisons = {}
        
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r') as f:
                    historical_data = json.load(f)
                
                # Get last 5 results for comparison
                recent_results = historical_data.get("results", [])[-5:]
                
                if recent_results:
                    for metric, current_value in current_results["metrics"].items():
                        historical_values = [r.get("metrics", {}).get(metric, 0) for r in recent_results]
                        
                        if historical_values:
                            avg_historical = statistics.mean(historical_values)
                            change = current_value - avg_historical
                            change_percent = (change / avg_historical) * 100 if avg_historical > 0 else 0
                            
                            comparisons[metric] = {
                                "current": current_value,
                                "historical_avg": avg_historical,
                                "change": change,
                                "change_percent": change_percent,
                                "trend": "improving" if change < 0 else "degrading" if change > 0 else "stable"
                            }
            except:
                pass
        
        return comparisons
    
    def save_results(self, results: Dict):
        """Save benchmark results"""
        # Load existing results
        all_results = {"results": []}
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r') as f:
                    all_results = json.load(f)
            except:
                pass
        
        # Add new results
        all_results["results"].append(results)
        
        # Keep only last 30 results
        if len(all_results["results"]) > 30:
            all_results["results"] = all_results["results"][-30:]
        
        # Save
        with open(self.results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
    
    def generate_report(self, results: Dict, comparisons: Dict) -> str:
        """Generate performance benchmark report"""
        report = []
        report.append("🏁 Performance Benchmark Report")
        report.append("=" * 50)
        report.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"🎯 Overall Status: {results['status']}")
        report.append("")
        
        # Current Metrics
        report.append("📊 Current Performance Metrics:")
        for metric, value in results["metrics"].items():
            # Get benchmark for this metric
            if metric == "app_load_time":
                bench = self.benchmarks["app_load_time"]
                name = "App Load Time"
                unit = "s"
            elif metric.endswith("_execution_time"):
                suite = metric.replace("_execution_time", "")
                bench = self.benchmarks["test_execution_time"][suite]
                name = f"{suite.title()} Test Execution"
                unit = "s"
            elif metric == "memory_usage":
                bench = self.benchmarks["memory_usage"]
                name = "Memory Usage"
                unit = "MB"
            elif metric == "disk_usage":
                bench = self.benchmarks["disk_usage"]
                name = "Disk Usage"
                unit = "MB"
            else:
                continue
            
            # Determine status
            if value <= bench["target"]:
                status = "✅ Excellent"
            elif value <= bench["warning"]:
                status = "⚠️ Good"
            elif value <= bench["critical"]:
                status = "❌ Poor"
            else:
                status = "🚨 Critical"
            
            report.append(f"   {name}: {value:.2f}{unit} {status}")
        
        report.append("")
        
        # Historical Comparisons
        if comparisons:
            report.append("📈 Historical Comparisons:")
            for metric, comp in comparisons.items():
                trend_icon = "📈" if comp["trend"] == "improving" else "📉" if comp["trend"] == "degrading" else "➡️"
                change_str = f"{comp['change']:+.2f}{unit} ({comp['change_percent']:+.1f}%)"
                report.append(f"   {metric}: {trend_icon} {change_str} vs historical avg")
            report.append("")
        
        # Recommendations
        report.append("💡 Performance Recommendations:")
        
        # Check for issues
        issues = []
        for metric, value in results["metrics"].items():
            if metric == "app_load_time" and value > self.benchmarks["app_load_time"]["warning"]:
                issues.append("App load time is slow - consider optimization")
            elif metric.endswith("_execution_time") and value > self.benchmarks["test_execution_time"][metric.split('_')[0]]["warning"]:
                issues.append(f"{metric.split('_')[0].title()} tests running slow - optimize test efficiency")
            elif metric == "disk_usage" and value > self.benchmarks["disk_usage"]["warning"]:
                issues.append("Disk usage high - consider cleanup")
        
        if issues:
            for issue in issues:
                report.append(f"   ⚠️ {issue}")
        else:
            report.append("   ✅ All metrics within acceptable ranges")
        
        report.append("")
        report.append("🔄 Run benchmarks weekly to track performance trends")
        
        return "\n".join(report)

def main():
    """Run performance benchmarks"""
    benchmark = PerformanceBenchmark()
    
    # Run benchmark suite
    results = benchmark.run_benchmark_suite()
    
    # Compare with historical data
    comparisons = benchmark.compare_with_historical(results)
    
    # Generate report
    report = benchmark.generate_report(results, comparisons)
    print("\n" + report)
    
    # Save results and report
    benchmark.save_results(results)
    
    report_file = benchmark.test_dir / "performance_benchmark_report.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Benchmark report saved to: {report_file}")
    print(f"📊 Historical data saved to: {benchmark.results_file}")
    
    return results

if __name__ == "__main__":
    main()
