import os
import http.client
import json
import sys
import argparse

def send_outreach_email(api_key, to_email, subject, content_html, from_email):
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
    
    try:
        conn.request("POST", "/emails", json.dumps(payload), headers)
        res = conn.getresponse()
        data = res.read()
        if res.status in [200, 201]:
            print(f"✅ Success: Email sent to {to_email} (ID: {json.loads(data).get('id', 'N/A')})")
            return True
        else:
            print(f"❌ Failed: HTTP {res.status}")
            print(f"Response: {data.decode('utf-8')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def load_env():
    # Use absolute path for .env
    env_path = "/Users/lokeshgarg/ai-mvp-backend/.env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value

def main():
    load_env()
    parser = argparse.ArgumentParser(description="Nucleus Outreach CLI")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--type", choices=["arya", "stargazer", "manual"], default="manual", help="Pre-defined template type")
    parser.add_argument("--name", help="Recipient name (optional)")
    parser.add_argument("--subject", help="Custom subject (for manual type)")
    parser.add_argument("--body", help="Custom HTML body (for manual type)")
    parser.add_argument("--sender", choices=["admin", "hello"], default="hello", help="Sender identifier")
    
    args = parser.parse_args()
    
    API_KEY = os.getenv("RESEND_API_KEY")
    if not API_KEY:
        print("❌ Error: RESEND_API_KEY not found in .env or environment.")
        sys.exit(1)

    from_emails = {
        "admin": "The Nucleus Team <admin@nucleusos.dev>",
        "hello": "The Nucleus Team <hello@nucleusos.dev>"
    }
    from_email = from_emails.get(args.sender)

    # Templates
    templates = {
        "arya": {
            "subject": "thanks for the linux xdg fix / nucleus mcp",
            "content": """
                <p>Hi Arya,</p>
                <p>Just sending a quick note to say thanks for that XDG contribution you made to nucleus-init. It actually helped get the linux build stable on my end.</p>
                <p>I'm starting a small discord for the few devs using this to help figure out where to take the "engram" persistence stuff next.</p>
                <p>Link: <a href="https://discord.gg/RJuBNNJ5MT">https://discord.gg/RJuBNNJ5MT</a></p>
                <p>Cheers,<br>The Nucleus Team</p>
            """
        },
        "stargazer": {
            "subject": "saw you starred nucleus-mcp",
            "content": """
                <p>Hey {name},</p>
                <p>I'm one of the devs behind Nucleus MCP. Saw you starred the repo recently—thanks for that.</p>
                <p>We're trying to figure out the best way to sync shared memory between Cursor and Claude. If you're using it and have feedback, I'd love to hear it.</p>
                <p>Discord: <a href="https://discord.gg/RJuBNNJ5MT">https://discord.gg/RJuBNNJ5MT</a></p>
                <p>Best,<br>The Nucleus Team</p>
            """.format(name=args.name if args.name else "")
        },
        "manual": {
            "subject": args.subject,
            "content": args.body
        }
    }

    t = templates.get(args.type)
    if not t["subject"] or not t["content"]:
        print("❌ Error: Subject and Body are required for manual type.")
        sys.exit(1)

    send_outreach_email(API_KEY, args.to, t["subject"], t["content"], from_email)

if __name__ == "__main__":
    main()
