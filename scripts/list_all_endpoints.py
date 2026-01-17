"""List all API endpoints"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

def list_endpoints():
    app = create_app()
    
    print("🔗 API ENDPOINTS")
    print("=" * 80)
    
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            routes.append((rule.rule, methods, rule.endpoint))
    
    routes.sort()
    
    for route, methods, endpoint in routes:
        print(f"{methods:20s} {route:50s} ({endpoint})")
    
    print()
    print(f"Total endpoints: {len(routes)}")
    print("=" * 80)

if __name__ == '__main__':
    list_endpoints()
