"""Generate metrics dashboard HTML"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text
from datetime import datetime, timedelta

def generate_dashboard():
    app = create_app()
    
    with app.app_context():
        # Get metrics
        total_users = db.session.execute(text("SELECT COUNT(*) FROM sessions")).scalar()
        dau = db.session.execute(text("""
            SELECT COUNT(DISTINCT session_id) FROM messages
            WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        """)).scalar() or 0
        wau = db.session.execute(text("""
            SELECT COUNT(DISTINCT session_id) FROM messages
            WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
        """)).scalar() or 0
        crisis_24h = db.session.execute(text("""
            SELECT COUNT(*) FROM counselor_alerts
            WHERE sent_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        """)).scalar() or 0
        pending_alerts = db.session.execute(text("""
            SELECT COUNT(*) FROM counselor_alerts WHERE acknowledged_at IS NULL
        """)).scalar() or 0
        
        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>GentleQuest Metrics Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .metric-card {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 48px; font-weight: bold; color: #667EEA; }}
        .metric-label {{ font-size: 14px; color: #666; text-transform: uppercase; }}
        .status-good {{ color: #10B981; }}
        .status-warning {{ color: #F59E0B; }}
        .status-critical {{ color: #DC2626; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>GentleQuest Metrics Dashboard</h1>
        <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="metric-card">
            <div class="metric-label">Total Users</div>
            <div class="metric-value">{total_users}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Daily Active Users (24h)</div>
            <div class="metric-value {'status-good' if (total_users > 0 and dau/total_users >= 0.30) else 'status-warning'}">{dau}</div>
            <div>{(dau/total_users*100) if total_users > 0 else 0:.1f}% of total</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Weekly Active Users (7d)</div>
            <div class="metric-value {'status-good' if (total_users > 0 and wau/total_users >= 0.40) else 'status-warning'}">{wau}</div>
            <div>{(wau/total_users*100) if total_users > 0 else 0:.1f}% of total</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Crisis Events (24h)</div>
            <div class="metric-value">{crisis_24h}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Pending Alerts</div>
            <div class="metric-value {'status-critical' if pending_alerts > 5 else 'status-good'}">{pending_alerts}</div>
        </div>
    </div>
</body>
</html>
"""
        
        # Save to file
        with open('metrics_dashboard.html', 'w') as f:
            f.write(html)
        
        print("✅ Dashboard generated: metrics_dashboard.html")

if __name__ == '__main__':
    generate_dashboard()
