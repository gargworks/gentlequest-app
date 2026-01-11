#!/usr/bin/env python3
"""
Test Infrastructure Maintenance Scripts
Automated maintenance tasks for E2E testing
"""

import os
import shutil
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

class TestMaintenance:
    def __init__(self):
        self.test_dir = Path("test")
        self.archive_dir = self.test_dir / "archive"
        self.screenshots_dir = self.test_dir / "screenshots" / "e2e"
        
    def cleanup_old_screenshots(self, days_old: int = 7) -> int:
        """Archive screenshots older than specified days"""
        archived_count = 0
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        if not self.screenshots_dir.exists():
            return 0
            
        # Create archive directory for today
        today_archive = self.archive_dir / datetime.now().strftime("%Y%m%d")
        today_archive.mkdir(parents=True, exist_ok=True)
        
        # Move old screenshots to archive
        for screenshot_path in self.screenshots_dir.glob("*.png"):
            # Get file modification time
            mod_time = datetime.fromtimestamp(screenshot_path.stat().st_mtime)
            
            if mod_time < cutoff_date:
                archive_path = today_archive / screenshot_path.name
                shutil.move(str(screenshot_path), str(archive_path))
                archived_count += 1
                
        return archived_count
    
    def cleanup_old_logs(self, days_old: int = 30) -> int:
        """Clean up old log files"""
        cleaned_count = 0
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        log_files = [
            self.test_dir / "test_analytics_report.txt",
            self.test_dir / "test_health_report.txt",
            self.test_dir / "test_metrics.json"
        ]
        
        for log_file in log_files:
            if log_file.exists():
                mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if mod_time < cutoff_date:
                    # Archive instead of delete
                    archive_path = self.archive_dir / "logs" / log_file.name
                    archive_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(log_file), str(archive_path))
                    cleaned_count += 1
                    
        return cleaned_count
    
    def update_test_dependencies(self) -> bool:
        """Update test dependencies to latest versions"""
        try:
            # Update pip
            subprocess.run(["python3", "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # Update requirements
            requirements_file = self.test_dir / "requirements.txt"
            if requirements_file.exists():
                subprocess.run(["python3", "-m", "pip", "install", "-r", str(requirements_file), "--upgrade"], 
                             check=True, capture_output=True)
            
            # Reinstall Playwright browsers
            subprocess.run(["python3", "-m", "playwright", "install", "chromium"], 
                         check=True, capture_output=True)
            
            return True
        except subprocess.CalledProcessError:
            return False
    
    def backup_test_configurations(self) -> str:
        """Backup all test configurations"""
        backup_dir = self.test_dir / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Files to backup
        config_files = [
            "requirements.txt",
            "requirements_lock.txt",
            "quick_test.sh",
            "README.md",
            "troubleshooting_guide.md",
            "ci_cd_integration.md"
        ]
        
        for config_file in config_files:
            src = self.test_dir / config_file
            if src.exists():
                dst = backup_dir / config_file
                shutil.copy2(str(src), str(dst))
        
        return str(backup_dir)
    
    def validate_test_integrity(self) -> dict:
        """Validate test file integrity"""
        validation = {
            'missing_files': [],
            'corrupted_files': [],
            'permission_issues': []
        }
        
        # Check essential test files
        essential_files = [
            "focused_e2e_test.py",
            "flutter_web_e2e_test.py", 
            "e2e_test_suite.py",
            "requirements.txt"
        ]
        
        for file_name in essential_files:
            file_path = self.test_dir / file_name
            
            if not file_path.exists():
                validation['missing_files'].append(file_name)
                continue
                
            # Check if file is readable
            try:
                with open(file_path, 'r') as f:
                    f.read(100)  # Try to read first 100 chars
            except (IOError, UnicodeDecodeError):
                validation['corrupted_files'].append(file_name)
            
            # Check permissions
            if not os.access(file_path, os.R_OK):
                validation['permission_issues'].append(file_name)
        
        return validation
    
    def generate_maintenance_report(self) -> str:
        """Generate maintenance report"""
        report = []
        report.append("🔧 Test Infrastructure Maintenance Report")
        report.append("=" * 50)
        report.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Cleanup statistics
        archived_screenshots = self.cleanup_old_screenshots()
        cleaned_logs = self.cleanup_old_logs()
        
        report.append("🧹 Cleanup Summary:")
        report.append(f"   📸 Screenshots archived: {archived_screenshots}")
        report.append(f"   📝 Logs cleaned: {cleaned_logs}")
        report.append("")
        
        # Disk usage
        try:
            result = subprocess.run(["du", "-sk", str(self.test_dir)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                disk_usage = float(result.stdout.split()[0])
                report.append(f"💾 Current disk usage: {disk_usage/1024:.1f}MB")
        except:
            pass
        
        report.append("")
        
        # Validation results
        validation = self.validate_test_integrity()
        
        report.append("🔍 Integrity Check:")
        if not validation['missing_files']:
            report.append("   ✅ No missing files")
        else:
            report.append(f"   ❌ Missing files: {', '.join(validation['missing_files'])}")
        
        if not validation['corrupted_files']:
            report.append("   ✅ No corrupted files")
        else:
            report.append(f"   ❌ Corrupted files: {', '.join(validation['corrupted_files'])}")
        
        if not validation['permission_issues']:
            report.append("   ✅ No permission issues")
        else:
            report.append(f"   ❌ Permission issues: {', '.join(validation['permission_issues'])}")
        
        report.append("")
        
        # Recommendations
        report.append("💡 Maintenance Recommendations:")
        
        if archived_screenshots > 10:
            report.append("   📸 Consider more frequent screenshot cleanup")
        
        if disk_usage > 50000:  # 50MB
            report.append("   💾 Test directory getting large - consider archive cleanup")
        
        if validation['missing_files']:
            report.append("   📁 Restore missing test files from backup")
        
        report.append("   🔄 Schedule weekly maintenance runs")
        report.append("   📊 Monitor test performance trends")
        
        return "\n".join(report)
    
    def run_full_maintenance(self) -> dict:
        """Run complete maintenance routine"""
        print("🔧 Running Test Infrastructure Maintenance...")
        
        # Cleanup
        archived_screenshots = self.cleanup_old_screenshots()
        cleaned_logs = self.cleanup_old_logs()
        
        # Dependencies
        deps_updated = self.update_test_dependencies()
        
        # Backup
        backup_path = self.backup_test_configurations()
        
        # Validation
        validation = self.validate_test_integrity()
        
        # Generate report
        report = self.generate_maintenance_report()
        
        # Save report
        report_file = self.test_dir / "maintenance_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n📄 Maintenance report saved to: {report_file}")
        print(f"💾 Configuration backup: {backup_path}")
        
        return {
            'screenshots_archived': archived_screenshots,
            'logs_cleaned': cleaned_logs,
            'dependencies_updated': deps_updated,
            'backup_path': backup_path,
            'validation': validation,
            'report_file': str(report_file)
        }

def main():
    """Run maintenance scripts"""
    maintenance = TestMaintenance()
    return maintenance.run_full_maintenance()

if __name__ == "__main__":
    main()
