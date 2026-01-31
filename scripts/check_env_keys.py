
import os
import sys
from dotenv import load_dotenv

def check_keys():
    # Load .env explicitly
    load_dotenv()
    print("Checking Gemini API Keys Configuration...")
    
    primary = os.getenv("GEMINI_API_KEY") or ""
    alias = os.getenv("GEMINI_API_KEYS") or ""
    
    # Masking for security in logs
    print(f"GEMINI_API_KEY present: {bool(primary)}")
    print(f"GEMINI_API_KEYS present: {bool(alias)}")
    
    keys = []
    if primary:
        keys.extend([k.strip() for k in primary.split(",") if k.strip()])
    if alias:
        keys.extend([k.strip() for k in alias.split(",") if k.strip()])
        
    # De-dupe
    unique_keys = []
    seen = set()
    for k in keys:
        if k not in seen:
            unique_keys.append(k)
            seen.add(k)
            
    print(f"\nTotal Unique Keys Found: {len(unique_keys)}")
    
    for i, key in enumerate(unique_keys):
        masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "****"
        print(f"Key {i}: {masked}")

    if len(unique_keys) < 2:
        print("\nWARNING: Less than 2 keys found. Failover strategy will not work effectively.")
    else:
        print("\nSUCCESS: Multiple keys detected. Backup strategy viable.")

if __name__ == "__main__":
    check_keys()
