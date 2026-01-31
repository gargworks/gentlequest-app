import csv
import os
import datetime
import re
import json

# Configuration
LEADS_FILE = "data/outreach_leads.csv"
TEMPLATE_FILE = "docs/OUTREACH_STRATEGY_KIT.md"
OUTPUT_DIR = "outreach_campaign_v1"
COMPLIANCE_FILE = ".brain/knowledge/ANTI_HALLUCINATION_PROTOCOL.md"

def load_template():
    """Extracts the email template from the Strategy Kit."""
    # In a real scenario, we'd parse the MD. 
    # For now, we hardcode the approved template to ensure safety 
    # and avoid parsing complex markdown issues.
    return """Subject: 5-minute safety demo for {University} waitlist

Dr. {Last_Name},
{Custom_Intro}
I know your team is overwhelmed. The industry standard is 1 counselor per 1,500 students, but demand is 3x that.

We built GentleQuest specifically for the students sitting on your waitlist. It’s an AI resilience tool that bridges the gap between intake and their first appointment.

Is it safe?
Yes. Unlike generic chatbots, we do not hallucinate medical advice. I’ve attached a 2-minute video proving strictly safe crisis escalation:
[LINK: CAPS_Demo_Video.webp]

The Data:
- Engagement: Students complete "Daily Quests" (CBT-lite) 4x/week.
- Safety: 100% of crisis keywords escalate to your crisis line immediately.
- Visuals: See the attached "Crisis Response" screenshot.

I've also attached a 1-page Pilot Proposal outlining our "Zero-Cost, 90-Day" program for waitlisted students.

Can we chat for 10 minutes next Tuesday to see if this could relieve pressure on your staff?

Best,
{Your_Name}
Founder, GentleQuest
[Attachment: PILOT_PROPOSAL_ONE_PAGER.pdf]
{Signoff_Note}
"""

def check_compliance(text):
    """
    Mock Anti-Hallucination Check.
    In a real agent, this would call an LLM to verify.
    Here, we regex for dangerous keywords.
    """
    dangerous_terms = ["medical diagnosis", "cure", "treatment plan", "I am a doctor"]
    for term in dangerous_terms:
        if term.lower() in text.lower():
            return False, f"Found dangerous term: {term}"
    return True, "Safe"

def main():
    print("📧 Starting Outreach Automation...")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. Load Leads from Configs
    leads = []
    config_dir = "config/university_configs"
    
    if not os.path.exists(config_dir):
        print(f"⚠️ Config dir not found: {config_dir}")
        return

    print(f"📂 Scanning {config_dir} for university profiles...")
    
    for filename in os.listdir(config_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(config_dir, filename)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                    # Hybrid Schema Support
                    uni_name = data.get("university_name") or data.get("name")
                    
                    # Decision Maker Logic
                    dec_maker = data.get("decision_maker", {})
                    caps_contact = data.get("caps_contact", {})
                    
                    last_name = "Director"
                    email = "contact@university.edu"
                    
                    if dec_maker.get("name"):
                        last_name = dec_maker.get("name").split()[-1]
                        email = dec_maker.get("email")
                    elif caps_contact.get("director"):
                        last_name = caps_contact.get("director").split()[-1]
                        email = caps_contact.get("email")
                    
                    if not uni_name:
                         print(f"⚠️ Skipping {filename}: No name found")
                         continue

                    # Normalize keys for the template
                    outreach_data = data.get("outreach", {})
                    mascot = outreach_data.get("mascot", "")
                    
                    signoff_note = ""
                    if mascot:
                        signoff_note = f"\n(Go {mascot}!)"

                    lead = {
                        "University": uni_name,
                        "Last_Name": last_name,
                        "Email": email,
                        "Stats_Ratio": "1/1500",
                        "Signoff_Note": signoff_note,
                        "Custom_Intro": outreach_data.get("custom_intro", "") + ("\n" if outreach_data.get("custom_intro") else "")
                    }
                    leads.append(lead)
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")
    
    template = load_template()
    
    print(f"📋 Processing {len(leads)} leads found in configs...")
    
    for lead in leads:
        lead["Your_Name"] = "Lokesh Garg" # Config
        
        # Merge
        email_body = template.format(**lead)
        
        # Verify
        is_safe, msg = check_compliance(email_body)
        if not is_safe:
            print(f"❌ SKIPPED {lead['University']}: {msg}")
            continue
            
        # Save
        filename = f"{OUTPUT_DIR}/Draft_{lead['University'].replace(' ', '_')}.txt"
        with open(filename, "w") as f:
            f.write(email_body)
            
        print(f"✅ Generated: {filename}")

if __name__ == "__main__":
    main()
