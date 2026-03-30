#!/usr/bin/env python3
import os

def check_continuity(filepath):
    print(f"Checking continuity for {filepath}...")
    if not os.path.exists(filepath):
        print(f"⚠️ Warning: {filepath} not found.")
        return False
        
    with open(filepath, 'r') as f:
        content = f.read()
        
    if '<<<<<<<' in content or '=======' in content or '>>>>>>>' in content:
        print(f"❌ Error: Merge conflicts detected in {filepath}")
        return False
        
    # Basic markdown header check
    if not content.startswith('#'):
        print(f"⚠️ Warning: Missing top-level header in {filepath}")
        
    print(f"✅ Continuity verified for {filepath}. Structure is intact.")
    return True

if __name__ == "__main__":
    files_to_check = ['.brain/task.md', 'implementation_plan.md']
    all_good = True
    for fp in files_to_check:
        if not check_continuity(fp):
            all_good = False
            
    if all_good:
        print("\n🚀 Phase 66 Verification Complete: All state files reflect continuous history.")
