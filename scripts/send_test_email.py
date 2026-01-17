"""Send test email to verify SendGrid configuration"""
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_test_email(to_email):
    api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('SENDGRID_FROM_EMAIL', 'alerts@gentlequest.com')
    
    if not api_key:
        print("❌ SENDGRID_API_KEY not set")
        return False
    
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject='GentleQuest Test Email',
        html_content='<p>This is a test email from GentleQuest. If you received this, SendGrid is configured correctly.</p>'
    )
    
    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        if response.status_code == 202:
            print(f"✅ Test email sent to {to_email}")
            print(f"   Status: {response.status_code}")
            return True
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python scripts/send_test_email.py your@email.com")
        sys.exit(1)
    
    send_test_email(sys.argv[1])
