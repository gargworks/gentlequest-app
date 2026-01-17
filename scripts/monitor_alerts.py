"""Monitor counselor alerts in real-time"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text
from datetime import datetime

def monitor_alerts(interval_seconds=60):
    app = create_app()
    
    print("🚨 ALERT MONITORING")
    print("=" * 80)
    print(f"Checking every {interval_seconds} seconds. Press Ctrl+C to stop.")
    print()
    
    try:
        while True:
            with app.app_context():
                # Pending alerts
                pending = db.session.execute(text("""
                    SELECT id, session_id, severity, trigger_message, sent_at
                    FROM counselor_alerts
                    WHERE acknowledged_at IS NULL
                    ORDER BY sent_at DESC
                    LIMIT 10
                """)).fetchall()
                
                if pending:
                    print(f"\n⚠️  {len(pending)} PENDING ALERTS:")
                    for alert in pending:
                        alert_id, session_id, severity, trigger, sent_at = alert
                        age_minutes = (datetime.utcnow() - sent_at).total_seconds() / 60
                        print(f"  [{severity.upper()}] ID:{alert_id} Session:{session_id[:8]}... Age:{age_minutes:.0f}min")
                        print(f"    Trigger: {trigger[:60]}...")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ No pending alerts")
                
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

if __name__ == '__main__':
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    monitor_alerts(interval)
