"""Generate API documentation from endpoints"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

def generate_api_docs():
    app = create_app()
    
    docs = []
    docs.append("# GentleQuest API Documentation")
    docs.append("## Auto-Generated from Endpoints")
    docs.append("")
    
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        if rule.endpoint == 'static':
            continue
        
        methods = sorted(rule.methods - {'HEAD', 'OPTIONS'})
        
        docs.append(f"### {' '.join(methods)} {rule.rule}")
        docs.append(f"**Endpoint:** `{rule.endpoint}`")
        docs.append("")
    
    output = '\n'.join(docs)
    
    with open('API_DOCUMENTATION.md', 'w') as f:
        f.write(output)
    
    print("✅ API documentation generated: API_DOCUMENTATION.md")

if __name__ == '__main__':
    generate_api_docs()
