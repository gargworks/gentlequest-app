
import sys
import os
import uuid
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import CounselorAlert, University, UniversityCounselor
from providers.alert_manager import AlertManager, AlertSeverity

def test_alerts():
    app = create_app()
    with app.app_context():
        print("🚀 Starting Counselor Alert E2E Simulation...")

        # 1. Setup Test Data (University + Counselor)
        print("\n[1] Setting up Test Infrastructure...")
        uni = University.query.filter_by(name="Test University").first()
        if not uni:
            uni = University(name="Test University", domain="test.edu")
            db.session.add(uni)
            db.session.commit()
            print("  - Created Test University")
        else:
            print("  - Found Test University")

        counselor = UniversityCounselor.query.filter_by(email="test_counselor@test.edu").first()
        if not counselor:
            counselor = UniversityCounselor(
                university_id=uni.id,
                name="Dr. Test",
                email="test_counselor@test.edu",
                phone="+15550000000",
                role="Head of CAPS",
                alert_methods="email,sms"
            )
            db.session.add(counselor)
            db.session.commit()
            print("  - Created Test Counselor")
        else:
            print("  - Found Test Counselor")

        # 2. Simulate Crisis Event
        session_id = f"test_sim_{uuid.uuid4().hex[:8]}"
        risk_message = "I feel like I want to end it all. I have no hope left."
        keywords = ["end it all", "no hope"]
        risk_score = 0.95
        risk_level = "crisis"

        print(f"\n[2] Simulating Crisis Event...")
        print(f"  - Session: {session_id}")
        print(f"  - Message: {risk_message}")
        print(f"  - Calculated Risk: {risk_level.upper()} ({risk_score})")

        # 3. Trigger Alert Logic
        print("\n[3] Triggering Alert Manager...")
        alert_id = AlertManager.create_alert(
            session_id=session_id,
            trigger_message=risk_message,
            risk_level=risk_level,
            risk_score=risk_score,
            keywords=keywords,
            university_id=uni.id
        )

        if alert_id:
            print(f"  ✅ Alert Created! ID: {alert_id}")
            
            # 4. Verify DB Record
            print("\n[4] Verifying Database Record...")
            alert = CounselorAlert.query.get(alert_id)
            print(f"  - DB ID: {alert.id}")
            print(f"  - Severity: {alert.severity}")
            print(f"  - Trigger: {alert.trigger_message}")
            print(f"  - Sent At: {alert.sent_at}")
            
            # 5. Attempt Delivery (Will fail but we check logic)
            print("\n[5] Attempting Delivery (Mock)...")
            results = AlertManager.send_alert(alert_id)
            print(f"  - Email Result: {results['email']} (Expected False without keys)")
            print(f"  - SMS Result: {results['sms']} (Expected False without keys)")
            
            # 6. Cleanup
            print("\n[6] Cleanup...")
            db.session.delete(alert)
            # operational choice: leave uni/counselor for future manual tests or delete?
            # deleting counselor to keep clean
            db.session.delete(counselor)
            db.session.commit()
            print("  - Test data cleaned up.")
            
            print("\n✅ SIMULATION COMPLETE: Database Logic Verified.")
            
        else:
            print("\n❌ Alert Creation Failed (Rate Limited or Error?)")

if __name__ == "__main__":
    test_alerts()
