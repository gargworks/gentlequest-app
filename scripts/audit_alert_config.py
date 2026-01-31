
import os
from dotenv import load_dotenv

def audit_config():
    load_dotenv()
    print("Auditing Alert Configuration...")
    
    # SendGrid
    sg_key = os.getenv('SENDGRID_API_KEY')
    sg_from = os.getenv('SENDGRID_FROM_EMAIL')
    
    print(f"\n[SendGrid]")
    print(f"API Key Present: {bool(sg_key)}")
    if sg_key:
        print(f"API Key Masked: {sg_key[:4]}...{sg_key[-4:]}")
    print(f"From Email: {sg_from or 'Not Set'}")
    
    # Twilio
    tw_sid = os.getenv('TWILIO_ACCOUNT_SID')
    tw_token = os.getenv('TWILIO_AUTH_TOKEN')
    tw_phone = os.getenv('TWILIO_PHONE_NUMBER')
    
    print(f"\n[Twilio]")
    print(f"Account SID Present: {bool(tw_sid)}")
    if tw_sid:
        print(f"SID Masked: {tw_sid[:4]}...{tw_sid[-4:]}")
    print(f"Auth Token Present: {bool(tw_token)}")
    print(f"Phone Number: {tw_phone or 'Not Set'}")
    
    # Summary
    missing = []
    if not sg_key: missing.append("SENDGRID_API_KEY")
    if not tw_sid: missing.append("TWILIO_ACCOUNT_SID")
    if not tw_token: missing.append("TWILIO_AUTH_TOKEN")
    
    if missing:
        print(f"\n❌ Configuration Incomplete. Missing: {', '.join(missing)}")
        print("Alerts may fail to send.")
    else:
        print("\n✅ Configuration Complete. Ready for testing.")

if __name__ == "__main__":
    audit_config()
