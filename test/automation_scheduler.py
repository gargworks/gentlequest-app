#!/usr/bin/env python3
"""
Test Automation Scheduler
Schedules and manages automated test runs
"""

import schedule
import time
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

class TestScheduler:
    def __init__(self):
        self.test_dir = Path("test")
        self.log_file = self.test_dir / "scheduler.log"
        self.config_file = self.test_dir / "scheduler_config.json"
        self.load_config()
        
    def load_config(self):
        """Load scheduler configuration"""
        default_config = {
            "daily_health_check": True,
            "daily_health_time": "08:00",
            "weekly_full_test": True,
            "weekly_test_day": "monday",
            "weekly_test_time": "02:00",
            "monthly_cleanup": True,
            "monthly_cleanup_day": 1,
            "notifications": {
                "email": False,
                "slack": False,
                "console": True
            },
            "retry_failed_tests": True,
            "max_retries": 3
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in self.config:
                        self.config[key] = value
            except:
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save scheduler configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def log_message(self, message: str):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def run_health_check(self):
        """Run daily health check"""
        self.log_message("🏥 Running scheduled health check...")
        
        try:
            result = subprocess.run([
                "python3", "test/health_check.py"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log_message("✅ Health check completed successfully")
                self.send_notification("Health Check Passed", result.stdout)
            else:
                self.log_message("❌ Health check failed")
                self.send_notification("Health Check Failed", result.stderr)
                
        except subprocess.TimeoutExpired:
            self.log_message("⏰ Health check timed out")
            self.send_notification("Health Check Timed Out", "Health check exceeded 5 minute timeout")
        except Exception as e:
            self.log_message(f"💥 Health check error: {e}")
            self.send_notification("Health Check Error", str(e))
    
    def run_focused_tests(self):
        """Run focused E2E tests"""
        self.log_message("🎯 Running scheduled focused tests...")
        
        try:
            result = subprocess.run([
                "python3", "test/focused_e2e_test.py"
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                self.log_message("✅ Focused tests completed successfully")
                self.send_notification("Focused Tests Passed", result.stdout)
            else:
                self.log_message("❌ Focused tests failed")
                self.send_notification("Focused Tests Failed", result.stderr)
                
                # Retry logic
                if self.config["retry_failed_tests"]:
                    self.retry_failed_tests("focused")
                    
        except subprocess.TimeoutExpired:
            self.log_message("⏰ Focused tests timed out")
            self.send_notification("Focused Tests Timed Out", "Tests exceeded 10 minute timeout")
        except Exception as e:
            self.log_message(f"💥 Focused tests error: {e}")
            self.send_notification("Focused Tests Error", str(e))
    
    def run_full_test_suite(self):
        """Run complete test suite"""
        self.log_message("🔬 Running scheduled full test suite...")
        
        test_suites = ["focused", "flutter", "comprehensive"]
        results = {}
        
        for suite in test_suites:
            self.log_message(f"🧪 Running {suite} test suite...")
            
            try:
                result = subprocess.run([
                    "python3", f"test/{suite}_e2e_test.py"
                ], capture_output=True, text=True, timeout=600)
                
                results[suite] = {
                    'success': result.returncode == 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
                if result.returncode == 0:
                    self.log_message(f"✅ {suite.title()} tests passed")
                else:
                    self.log_message(f"❌ {suite.title()} tests failed")
                    if self.config["retry_failed_tests"]:
                        self.retry_failed_tests(suite)
                        
            except subprocess.TimeoutExpired:
                self.log_message(f"⏰ {suite.title()} tests timed out")
                results[suite] = {
                    'success': False,
                    'stdout': '',
                    'stderr': 'Test timed out'
                }
            except Exception as e:
                self.log_message(f"💥 {suite.title()} tests error: {e}")
                results[suite] = {
                    'success': False,
                    'stdout': '',
                    'stderr': str(e)
                }
        
        # Generate summary
        passed = sum(1 for r in results.values() if r['success'])
        total = len(results)
        
        summary = f"Full Test Suite Results: {passed}/{total} passed"
        self.log_message(summary)
        
        details = "\n".join([
            f"{suite}: {'✅' if result['success'] else '❌'}"
            for suite, result in results.items()
        ])
        
        self.send_notification("Full Test Suite Results", f"{summary}\n\n{details}")
    
    def retry_failed_tests(self, suite: str):
        """Retry failed tests with exponential backoff"""
        max_retries = self.config["max_retries"]
        
        for attempt in range(max_retries):
            wait_time = 2 ** attempt  # Exponential backoff
            self.log_message(f"🔄 Retrying {suite} tests (attempt {attempt + 1}/{max_retries}) in {wait_time}s...")
            
            time.sleep(wait_time)
            
            try:
                result = subprocess.run([
                    "python3", f"test/{suite}_e2e_test.py"
                ], capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    self.log_message(f"✅ {suite.title()} tests passed on retry {attempt + 1}")
                    self.send_notification(f"{suite.title()} Tests Recovered", f"Tests passed on retry {attempt + 1}")
                    return True
                    
            except Exception as e:
                self.log_message(f"💥 Retry {attempt + 1} failed: {e}")
        
        self.log_message(f"❌ {suite.title()} tests failed after {max_retries} retries")
        return False
    
    def run_maintenance(self):
        """Run scheduled maintenance"""
        self.log_message("🔧 Running scheduled maintenance...")
        
        try:
            result = subprocess.run([
                "python3", "test/maintenance_scripts.py"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log_message("✅ Maintenance completed successfully")
                self.send_notification("Maintenance Completed", result.stdout)
            else:
                self.log_message("❌ Maintenance failed")
                self.send_notification("Maintenance Failed", result.stderr)
                
        except subprocess.TimeoutExpired:
            self.log_message("⏰ Maintenance timed out")
            self.send_notification("Maintenance Timed Out", "Maintenance exceeded 5 minute timeout")
        except Exception as e:
            self.log_message(f"💥 Maintenance error: {e}")
            self.send_notification("Maintenance Error", str(e))
    
    def send_notification(self, title: str, message: str):
        """Send notification based on configuration"""
        if not self.config["notifications"]["console"]:
            return
        
        # Console notification (always enabled for now)
        print(f"\n🔔 {title}")
        print(f"{'='*len(title)}")
        print(message)
        print("=" * 50 + "\n")
        
        # Future: Add email/Slack integrations here
    
    def setup_schedule(self):
        """Setup scheduled tasks"""
        self.log_message("📅 Setting up test automation schedule...")
        
        # Daily health check
        if self.config["daily_health_check"]:
            schedule.every().day.at(self.config["daily_health_time"]).do(self.run_health_check)
            self.log_message(f"✅ Daily health check scheduled at {self.config['daily_health_time']}")
        
        # Weekly full tests
        if self.config["weekly_full_test"]:
            getattr(schedule.every(), self.config["weekly_test_day"]).at(self.config["weekly_test_time"]).do(self.run_full_test_suite)
            self.log_message(f"✅ Weekly full tests scheduled for {self.config['weekly_test_day']}s at {self.config['weekly_test_time']}")
        
        # Monthly maintenance (simplified - run weekly for now)
        if self.config["monthly_cleanup"]:
            schedule.every().sunday.at("03:00").do(self.run_maintenance)
            self.log_message("✅ Weekly maintenance scheduled for Sundays at 03:00")
    
    def run_scheduler(self):
        """Run the scheduler loop"""
        self.log_message("🚀 Starting test automation scheduler...")
        self.setup_schedule()
        
        self.log_message("⏰ Scheduler is running. Press Ctrl+C to stop.")
        self.log_message("📋 Scheduled tasks:")
        
        jobs = schedule.get_jobs()
        for job in jobs:
            self.log_message(f"   • {job}")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.log_message("🛑 Scheduler stopped by user")
    
    def run_once(self, task: str):
        """Run a specific task once"""
        self.log_message(f"🏃 Running {task} task once...")
        
        task_map = {
            "health": self.run_health_check,
            "focused": self.run_focused_tests,
            "full": self.run_full_test_suite,
            "maintenance": self.run_maintenance
        }
        
        if task in task_map:
            task_map[task]()
        else:
            self.log_message(f"❌ Unknown task: {task}")
            self.log_message(f"Available tasks: {', '.join(task_map.keys())}")

def main():
    """Main entry point"""
    import sys
    
    scheduler = TestScheduler()
    
    if len(sys.argv) > 1:
        # Run specific task once
        task = sys.argv[1]
        scheduler.run_once(task)
    else:
        # Run scheduler continuously
        scheduler.run_scheduler()

if __name__ == "__main__":
    main()
