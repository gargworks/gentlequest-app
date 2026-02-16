import os
import http.client
import json

def send_outreach_email(api_key, to_email, subject, content_html):
    conn = http.client.HTTPSConnection("api.resend.com")
    
    payload = {
        "from": "The Nucleus Team <hello@nucleusos.dev>",
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
        print(f"Status: {res.status}")
        print(f"Response: {data.decode('utf-8')}")
        return res.status == 200 or res.status == 201
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    API_KEY = os.getenv("RESEND_API_KEY")
    
    if not API_KEY:
        print("❌ Error: RESEND_API_KEY not found in environment.")
        exit(1)
    
    # Send to Arya
    arya_email = "aarya.sadawrate@gmail.com"
    arya_subject = "thanks for the linux xdg fix / nucleus mcp"
    arya_content = """
    <p>Hi Arya,</p>
    <p>Just sending a quick note to say thanks for that XDG contribution you made to nucleus-init. It actually helped get the linux build stable on my end.</p>
    <p>I'm starting a small discord for the few devs using this to help figure out where to take the "engram" persistence stuff next. No marketing, just a place to debug and share setups. Would be cool to have you in there if you're interested.</p>
    <p>Link: <a href="https://discord.gg/RJuBNNJ5MT">https://discord.gg/RJuBNNJ5MT</a></p>
    <p>Cheers,<br>The Nucleus Team</p>
    """
    
    print(f"Sending outreach to Arya ({arya_email})...")
    send_outreach_email(API_KEY, arya_email, arya_subject, arya_content)
