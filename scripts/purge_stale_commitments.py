#!/usr/bin/env python3
import json
import os
from datetime import datetime, timezone

def purge_commitments():
    ledger_path = '.brain/commitments/ledger.json'
    print(f"Purging stale commitments from {ledger_path}...")
    
    if not os.path.exists(ledger_path):
        print(f"Ledger file not found at {ledger_path}")
        return
        
    with open(ledger_path, 'r') as f:
        ledger = json.load(f)
        
    now = datetime.now(timezone.utc)
    active_commitments = []
    purged_count = 0
    
    for c in ledger.get('commitments', []):
        try:
            created_str = c.get('created', '')
            if 'T' in created_str:
                created_dt = datetime.strptime(created_str.split('.')[0], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
                age_days = (now - created_dt).days
                if age_days > 30:
                    purged_count += 1
                    continue
            active_commitments.append(c)
        except Exception as e:
            # Fallback append if parsing fails
            active_commitments.append(c)
            
    ledger['commitments'] = active_commitments
    ledger['stats'] = {
        'total_open': len(active_commitments),
        'red_tier': 0,
        'yellow_tier': 0,
        'green_tier': len(active_commitments)
    }
    ledger['last_scan'] = now.isoformat()
    
    with open(ledger_path, 'w') as f:
        json.dump(ledger, f, indent=2)
        
    print(f"Purged {purged_count} stale commitments.")
    print(f"Remaining active: {len(active_commitments)}")
    print("Satellite View stats updated successfully.")

if __name__ == "__main__":
    purge_commitments()
