"""
GentleQuest Outreach Readiness Audit
Analyzes the gap between Outreach Drafts and University Configurations.
Useful for Phase 36: Outreach Execution.
"""
import os
import re

DRAFTS_DIR = "outreach_campaign_v1"
CONFIGS_DIR = "config/university_configs"

def get_drafts():
    if not os.path.exists(DRAFTS_DIR):
        return []
    return [f for f in os.listdir(DRAFTS_DIR) if f.startswith("Draft_") and f.endswith(".txt")]

def get_configs():
    if not os.path.exists(CONFIGS_DIR):
        return []
    return [f for f in os.listdir(CONFIGS_DIR) if f.endswith(".json")]

def normalize_name(name):
    # Remove extension and prefix
    name = name.replace("Draft_", "").replace(".txt", "").replace(".json", "")
    # Normalize spaces and lower case
    name = name.replace("_", " ").strip().lower()
    # Aliases
    aliases = {
        "umich": "university of michigan",
        "stanford university": "stanford",
        "new york university": "nyu"
    }
    return aliases.get(name, name)

def run_audit():
    print("📢 OUTREACH READINESS AUDIT")
    print("=" * 80)
    
    drafts = get_drafts()
    configs = get_configs()
    
    draft_names = {normalize_name(d): d for d in drafts}
    config_names = {normalize_name(c): c for c in configs}
    
    all_unis = sorted(list(set(draft_names.keys()) | set(config_names.keys())))
    
    print(f"{'University':<30} | {'Draft?':<10} | {'Config?':<10} | {'Status'}")
    print("-" * 80)
    
    for uni in all_unis:
        has_draft = "✅ YES" if uni in draft_names else "❌ NO"
        has_config = "✅ YES" if uni in config_names else "❌ NO"
        
        status = "🟢 READY" if (uni in draft_names and uni in config_names) else "🟡 INCOMPLETE"
        if uni not in draft_names:
            status = "🔴 MISSING DRAFT"
        elif uni not in config_names:
            status = "🟠 MISSING CONFIG"
            
        print(f"{uni.title():<30} | {has_draft:<10} | {has_config:<10} | {status}")
    
    print("-" * 80)
    print(f"Total Universities: {len(all_unis)}")
    print(f"Drafts missing Configs: {len([u for u in draft_names if u not in config_names])}")
    print("=" * 80)
    print("\n💡 Recommendation:")
    print("  For colleges with 'MISSING CONFIG', create a JSON file in config/university_configs/")
    print("  based on doc/UNIVERSITY_CUSTOMIZATION_TEMPLATES.md to enable data-loading.")

if __name__ == "__main__":
    run_audit()
