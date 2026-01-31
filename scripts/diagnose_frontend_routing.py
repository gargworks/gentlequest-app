#!/usr/bin/env python3
"""
Diagnostic: Production Frontend SSL/404 Issue
Purpose: Identify why app.gentlequest.ai returns Marketing Dashboard instead of Flutter app
"""

import requests
import sys

def diagnose_production_frontend():
    """Run diagnostics on production frontend routing"""
    
    print("=" * 70)
    print("PRODUCTION FRONTEND DIAGNOSTIC")
    print("=" * 70)
    
    # Test URLs - GCLOUD PRODUCTION (Correct)
    urls = [
        "https://app.gentlequest.app",      # Should serve Flutter app
        "https://www.gentlequest.app",       # Should serve Marketing landing page
        "https://gentlequest.app",           # Test root domain
        "http://app.gentlequest.app",        # Test HTTP redirect
    ]
    
    for url in urls:
        print(f"\n\n🔍 Testing: {url}")
        print("-" * 70)
        
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Final URL: {response.url}")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"   Content-Length: {len(response.content)} bytes")
            
            # Check for Flutter indicators
            content = response.text.lower()
            indicators = {
                "Flutter App": "flutter" in content or "main.dart.js" in content,
                "Marketing Page": "quiet launch" in content or "landing" in content,
                "API JSON": response.headers.get('Content-Type', '').startswith('application/json'),
                "Index.html": "<html" in content and "index" in content,
            }
            
            print("\n   Content Indicators:")
            for indicator, present in indicators.items():
                emoji = "✅" if present else "❌"
                print(f"      {emoji} {indicator}")
            
            # Check redirects
            if response.history:
                print(f"\n   Redirects ({len(response.history)}):")
                for i, redirect in enumerate(response.history, 1):
                    print(f"      {i}. {redirect.status_code} → {redirect.url}")
                    
        except requests.exceptions.RequestException as e:
            print(f"   ❌ ERROR: {e}")
    
    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    diagnose_production_frontend()
