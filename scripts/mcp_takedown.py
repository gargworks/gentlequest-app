from execute_outreach import send_outreach_email
import os

# Manual .env loading since we might not have python-dotenv
def load_env():
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value

def send_takedown_request():
    load_env()
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("❌ Error: RESEND_API_KEY not found in .env or environment.")
        return

    recipient = "support@mcp.so"
    subject = "Duplicate/Legacy Listing Removal Request: Nucleus Brain"
    
    # User requested admin@nucleusos.dev
    from_email = "The Nucleus Team <admin@nucleusos.dev>"
    
    content_html = f"""
    <p>Hello,</p>
    <p>I am writing from the <strong>Nucleus Team</strong>. We have identified a legacy/duplicate listing of our server on your registry: 
    <a href="https://mcp.so/server/mcp-server-nucleus/LKGargProjects">https://mcp.so/server/mcp-server-nucleus/LKGargProjects</a></p>
    
    <p>This entry is outdated and points to a personal testing repository. We are already maintaining the official, verified listing here: 
    <a href="https://mcp.so/server/nucleus-mcp">https://mcp.so/server/nucleus-mcp</a></p>
    
    <p>Please <strong>remove</strong> the <code>LKGargProjects</code> listing entirely to prevent user confusion and maintain security standards during our public launch phase.</p>
    
    <p>Thank you,<br><strong>The Nucleus Team</strong></p>
    """

    print(f"🚀 Sending takedown request to {recipient} via Resend ({from_email})...")
    
    # We need to monkey-patch or modify execute_outreach to accept 'from_email'
    # Actually execute_outreach has it hardcoded, let's fix that too.
    import execute_outreach
    original_send = execute_outreach.send_outreach_email
    
    def patched_send(api_key, to_email, subject, content_html):
        import http.client
        import json
        conn = http.client.HTTPSConnection("api.resend.com")
        payload = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": content_html
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        conn.request("POST", "/emails", json.dumps(payload), headers)
        res = conn.getresponse()
        print(f"Status: {res.status}")
        return res.status in [200, 201]

    success = patched_send(api_key, recipient, subject, content_html)
    
    if success:
        print("✅ Takedown request sent successfully.")
    else:
        print("❌ Failed to send request.")

if __name__ == "__main__":
    send_takedown_request()
