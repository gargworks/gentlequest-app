import os
import json
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config/university_configs"
TEMPLATE_DIR = BASE_DIR / "outreach_campaign_v1"
OUTPUT_DIR = BASE_DIR / "outreach_campaign_v1/generated"

def load_config(university_slug):
    """Load specific university config."""
    config_path = CONFIG_DIR / f"{university_slug}.json"
    if not config_path.exists():
        logging.error(f"Config not found for: {university_slug}")
        return None
    with open(config_path, 'r') as f:
        return json.load(f)

def load_template(university_name):
    """Load email template."""
    # Mapping simple names to draft files
    file_map = {
        "Yale University": "Draft_Yale_University.txt",
        "Boston University": "Draft_Boston_University.txt",
        "NYU": "Draft_NYU.txt" # Future proofing
    }
    
    filename = file_map.get(university_name)
    if not filename:
        logging.error(f"Template mapping not found for: {university_name}")
        return None
        
    template_path = TEMPLATE_DIR / filename
    if not template_path.exists():
        logging.error(f"Template file not found: {template_path}")
        return None
        
    with open(template_path, 'r') as f:
        return f.read()

def generate_email(config, template):
    """Refine template with config data (Deep Insider Logic)."""
    # Basic replacements would go here if we were using {{variable}} syntax
    # For now, we are verifying that the Deep Insider facts in the config 
    # match what's hardcoded/drafted in the text file, or simply outputting the final artifact.
    
    # In this phase, the drafting is manual-assisted. 
    # This script mainly validates that we have the data we claim to have.
    
    uni_name = config.get('name') or config.get('university_name')
    print(f"--- Generating Outreach for {uni_name} ---")
    print(f"Internal Code: {config.get('internal_code', 'N/A')}")
    
    # Check for Deep Insider data existence
    if 'outreach' in config:
        print("✅ Outreach configuration found.")
        print(f"   Mascot: {config['outreach'].get('mascot_name')}")
        print(f"   Building: {config['outreach'].get('wellness_center_building')}")
    else:
        print("⚠️  MISSING OUTREACH DATA IN CONFIG!")
    
    return template

def main():
    parser = argparse.ArgumentParser(description="Generate Deep Insider Outreach Emails")
    parser.add_argument("--slug", required=True, help="University slug (e.g., yale, boston_university)")
    args = parser.parse_args()
    
    # Ensure output dir exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    config = load_config(args.slug)
    if not config:
        return
    
    # Handle inconsistent naming (name vs university_name)
    uni_name = config.get('name') or config.get('university_name')
    if not uni_name:
        logging.error(f"Config for {args.slug} missing 'name' or 'university_name'")
        return

    template = load_template(uni_name)
    if not template:
        return
        
    final_email = generate_email(config, template)
    
    output_path = OUTPUT_DIR / f"Final_Email_{args.slug}.txt"
    with open(output_path, 'w') as f:
        f.write(final_email)
        
    print(f"\n🚀 Generated email saved to: {output_path}")

if __name__ == "__main__":
    main()
