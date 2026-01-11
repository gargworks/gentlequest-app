#!/usr/bin/env python3
"""
Test Dashboard Generator
Creates HTML dashboard for visualizing test results and metrics
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class TestDashboardGenerator:
    def __init__(self):
        self.test_dir = Path("test")
        self.output_dir = self.test_dir / "dashboard"
        self.output_dir.mkdir(exist_ok=True)
        
    def load_all_results(self) -> Dict[str, any]:
        """Load all test results and metrics"""
        data = {
            "test_results": {},
            "performance_data": {},
            "health_data": {},
            "analytics_data": {}
        }
        
        # Load test results
        result_files = {
            "focused": "focused_e2e_results.json",
            "flutter": "flutter_e2e_results.json", 
            "comprehensive": "e2e_results.json"
        }
        
        for suite, filename in result_files.items():
            file_path = self.test_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        data["test_results"][suite] = json.load(f)
                except:
                    data["test_results"][suite] = None
        
        # Load performance data
        perf_file = self.test_dir / "performance_results.json"
        if perf_file.exists():
            try:
                with open(perf_file, 'r') as f:
                    perf_data = json.load(f)
                    data["performance_data"] = perf_data.get("results", [])[-5:]  # Last 5
            except:
                pass
        
        # Load health data
        health_file = self.test_dir / "test_health_report.txt"
        if health_file.exists():
            try:
                with open(health_file, 'r') as f:
                    data["health_data"]["report"] = f.read()
                    data["health_data"]["timestamp"] = datetime.now().isoformat()
            except:
                pass
        
        # Load analytics data
        metrics_file = self.test_dir / "test_metrics.json"
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    data["analytics_data"] = json.load(f)
            except:
                pass
        
        return data
    
    def generate_html_dashboard(self, data: Dict) -> str:
        """Generate HTML dashboard"""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GentleQuest E2E Test Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        
        .header h1 {{
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            color: #666;
            font-size: 1.1em;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
        }}
        
        .card h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .status-indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }}
        
        .status-excellent {{ background: #4CAF50; }}
        .status-good {{ background: #FF9800; }}
        .status-poor {{ background: #F44336; }}
        .status-unknown {{ background: #9E9E9E; }}
        
        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        
        .metric:last-child {{
            border-bottom: none;
        }}
        
        .metric-label {{
            color: #666;
            font-weight: 500;
        }}
        
        .metric-value {{
            font-weight: bold;
            color: #333;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #eee;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #8BC34A);
            transition: width 0.3s ease;
        }}
        
        .alert {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            color: #856404;
        }}
        
        .alert.success {{
            background: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
        }}
        
        .alert.error {{
            background: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }}
        
        .timestamp {{
            color: #999;
            font-size: 0.9em;
            text-align: center;
            margin-top: 20px;
        }}
        
        .chart-container {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }}
        
        .mini-chart {{
            display: flex;
            align-items: flex-end;
            height: 60px;
            gap: 3px;
            margin: 15px 0;
        }}
        
        .chart-bar {{
            flex: 1;
            background: linear-gradient(180deg, #667eea, #764ba2);
            border-radius: 3px 3px 0 0;
            min-height: 5px;
        }}
        
        @media (max-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 GentleQuest E2E Test Dashboard</h1>
            <p>Real-time test results and performance metrics</p>
            <div class="timestamp">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <div class="grid">
            {self._generate_test_results_cards(data["test_results"])}
            {self._generate_performance_card(data["performance_data"])}
            {self._generate_health_card(data["health_data"])}
        </div>
        
        {self._generate_analytics_section(data["analytics_data"])}
        {self._generate_performance_trends(data["performance_data"])}
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => {{
            location.reload();
        }}, 30000);
        
        // Add interactive animations
        document.addEventListener('DOMContentLoaded', () => {{
            const cards = document.querySelectorAll('.card');
            cards.forEach((card, index) => {{
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {{
                    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }}, index * 100);
            }});
        }});
    </script>
</body>
</html>
        """
        
        return html
    
    def _generate_test_results_cards(self, test_results: Dict) -> str:
        """Generate HTML for test results cards"""
        cards = ""
        
        for suite, data in test_results.items():
            if not data:
                continue
            
            pass_rate = data.get('pass_rate', 0)
            passed = data.get('passed', 0)
            total = data.get('total', data.get('total_tests', 0))
            failed = data.get('failed', 0)
            partial = data.get('partial', 0)
            
            # Determine status
            if pass_rate >= 80:
                status = "excellent"
            elif pass_rate >= 60:
                status = "good"
            elif pass_rate >= 40:
                status = "poor"
            else:
                status = "unknown"
            
            # Progress bar
            progress_width = pass_rate
            
            cards += f"""
            <div class="card">
                <h2>
                    <span class="status-indicator status-{status}"></span>
                    {suite.title()} Tests
                </h2>
                <div class="metric">
                    <span class="metric-label">Pass Rate</span>
                    <span class="metric-value">{pass_rate:.1f}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {progress_width}%"></div>
                </div>
                <div class="metric">
                    <span class="metric-label">Tests Passed</span>
                    <span class="metric-value">{passed}/{total}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Failed</span>
                    <span class="metric-value">{failed}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Partial</span>
                    <span class="metric-value">{partial}</span>
                </div>
            </div>
            """
        
        return cards
    
    def _generate_performance_card(self, performance_data: List) -> str:
        """Generate HTML for performance card"""
        if not performance_data:
            return ""
        
        latest = performance_data[-1]
        metrics = latest.get('metrics', {})
        
        card = """
        <div class="card">
            <h2>
                <span class="status-indicator status-excellent"></span>
                Performance Metrics
            </h2>
        """
        
        # App Load Time
        load_time = metrics.get('app_load_time', 0)
        card += f"""
        <div class="metric">
            <span class="metric-label">App Load Time</span>
            <span class="metric-value">{load_time:.2f}s</span>
        </div>
        """
        
        # Test Execution Times
        for suite in ['focused', 'flutter', 'comprehensive']:
            exec_time = metrics.get(f'{suite}_execution_time', 0)
            card += f"""
            <div class="metric">
                <span class="metric-label">{suite.title()} Execution</span>
                <span class="metric-value">{exec_time:.1f}s</span>
            </div>
            """
        
        # Resource Usage
        memory = metrics.get('memory_usage', 0)
        disk = metrics.get('disk_usage', 0)
        
        card += f"""
        <div class="metric">
            <span class="metric-label">Memory Usage</span>
            <span class="metric-value">{memory:.1f}MB</span>
        </div>
        <div class="metric">
            <span class="metric-label">Disk Usage</span>
            <span class="metric-value">{disk:.1f}MB</span>
        </div>
        """
        
        card += "</div>"
        
        return card
    
    def _generate_health_card(self, health_data: Dict) -> str:
        """Generate HTML for health card"""
        if not health_data:
            return ""
        
        report = health_data.get('report', '')
        
        # Extract status from report (simplified)
        if '✅ Healthy' in report:
            status = "excellent"
        elif '⚠️ Needs Attention' in report:
            status = "good"
        else:
            status = "poor"
        
        card = f"""
        <div class="card">
            <h2>
                <span class="status-indicator status-{status}"></span>
                Infrastructure Health
            </h2>
            <div class="alert {'success' if status == 'excellent' else 'error' if status == 'poor' else ''}">
                System Status: {status.replace('-', ' ').title()}
            </div>
        </div>
        """
        
        return card
    
    def _generate_analytics_section(self, analytics_data: Dict) -> str:
        """Generate analytics section"""
        if not analytics_data:
            return ""
        
        overall_health = analytics_data.get('overall_health', 'Unknown')
        pass_rate = analytics_data.get('average_pass_rate', 0)
        
        section = f"""
        <div class="chart-container">
            <h2>📊 Test Analytics Overview</h2>
            <div class="grid">
                <div class="metric">
                    <span class="metric-label">Overall Health</span>
                    <span class="metric-value">{overall_health}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Average Pass Rate</span>
                    <span class="metric-value">{pass_rate:.1f}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Test Suites</span>
                    <span class="metric-value">{len(analytics_data.get('pass_rates', {}))}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Critical Failures</span>
                    <span class="metric-value">{analytics_data.get('critical_failures', 0)}</span>
                </div>
            </div>
        </div>
        """
        
        return section
    
    def _generate_performance_trends(self, performance_data: List) -> str:
        """Generate performance trends section"""
        if len(performance_data) < 2:
            return ""
        
        # Create mini chart for load times
        load_times = [d.get('metrics', {}).get('app_load_time', 0) for d in performance_data[-5:]]
        max_time = max(load_times) if load_times else 1
        
        chart_bars = ""
        for time_val in load_times:
            height = (time_val / max_time) * 100 if max_time > 0 else 0
            chart_bars += f'<div class="chart-bar" style="height: {height}%"></div>'
        
        section = f"""
        <div class="chart-container">
            <h2>📈 Performance Trends (Last 5 Runs)</h2>
            <div class="metric">
                <span class="metric-label">App Load Time Trend</span>
                <span class="metric-value">{load_times[-1]:.2f}s (latest)</span>
            </div>
            <div class="mini-chart">
                {chart_bars}
            </div>
        </div>
        """
        
        return section
    
    def generate_dashboard(self) -> str:
        """Generate complete dashboard"""
        print("📊 Generating Test Dashboard...")
        
        # Load all data
        data = self.load_all_results()
        
        # Generate HTML
        html = self.generate_html_dashboard(data)
        
        # Save dashboard
        dashboard_file = self.output_dir / "index.html"
        with open(dashboard_file, 'w') as f:
            f.write(html)
        
        print(f"✅ Dashboard generated: {dashboard_file}")
        print(f"🌐 Open in browser: file://{dashboard_file.absolute()}")
        
        return str(dashboard_file)

def main():
    """Generate test dashboard"""
    generator = TestDashboardGenerator()
    return generator.generate_dashboard()

if __name__ == "__main__":
    main()
