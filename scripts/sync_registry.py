import json
import re
import argparse
import subprocess
import sys
from pathlib import Path

# Paths relative to script
ROOT = Path(__file__).parent.parent.resolve()
REGISTRY_DIR = ROOT / ".registry"
VERSION_FILE = REGISTRY_DIR / "version.json"

def preflight_check():
    """Deterministic validation of the entire registry state."""
    if not VERSION_FILE.exists():
        print(f"❌ CRITICAL ERROR: Missing Source of Truth {VERSION_FILE}")
        sys.exit(1)
            
    # Schema Consistency Check (Basic)
    all_manifests = list(REGISTRY_DIR.glob("*.json"))
    if not all_manifests:
        print("❌ CRITICAL ERROR: No manifests found in .registry/")
        sys.exit(1)

    for manifest_file in all_manifests:
        try:
            m = json.loads(manifest_file.read_text())
            if manifest_file.name != "version.json" and ("name" not in m or "version" not in m):
                print(f"❌ SCHEMA VIOLATION in {manifest_file.name}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ JSON CORRUPTION in {manifest_file.name}: {e}")
            sys.exit(1)
    print("🛡️ Pre-Flight Check: PASSED (Deterministic)")

def run_cmd(cmd):
    """Executes system commands with strict error handling."""
    print(f"  [EXEC] {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0: 
        print(f"🚨 SYSTEM PROCESS ERROR: {result.stderr}")
        sys.exit(1)
    return result.stdout

def update_file(path, pattern, replacement, dry_run=False):
    """Stateless patching: finds ANY version-like string and forces parity."""
    if not path.exists(): 
        print(f"⚠️ Warning: File not found {path}")
        return
    content = path.read_text()
    if not re.search(pattern, content):
        print(f"⚠️ Warning: Pattern not found in {path.name}")
        return
    new_content = re.sub(pattern, replacement, content)
    if not dry_run: 
        path.write_text(new_content)
        print(f"  [✓] Updated: {path.relative_to(ROOT)}")
    else:
        print(f"  [SIM] Would update: {path.relative_to(ROOT)}")

def apply_template(target_path, marker, content, dry_run=False):
    """Recursively injects platform-specific blocks into shared files."""
    if not target_path.exists(): return
    text = target_path.read_text()
    pattern = f"<!-- {marker}:START -->.*?<!-- {marker}:END -->"
    if not re.search(pattern, text, flags=re.DOTALL):
        print(f"⚠️ Warning: Template marker {marker} not found in {target_path.name}")
        return
    new_text = re.sub(pattern, f"<!-- {marker}:START -->\n{content}\n<!-- {marker}:END -->", text, flags=re.DOTALL)
    if not dry_run: 
        target_path.write_text(new_text)
        print(f"  [✓] Templated: {target_path.relative_to(ROOT)} ({marker})")
    else:
        print(f"  [SIM] Would template: {target_path.relative_to(ROOT)} ({marker})")

def sync(dry_run=False, release=False):
    preflight_check()
    cfg = json.loads(VERSION_FILE.read_text())
    v = cfg["version"]
    
    print(f"\n🚀 Sentinel: Striking v{v} across 100+ endpoints... [DRY RUN: {dry_run}]")

    # 1. Core Ecosystem Parity (Stateless)
    # PyPI
    update_file(ROOT / "mcp-server-nucleus/pyproject.toml", r'version = "[^"]+"', f'version = "{v}"', dry_run)
    # Source Code
    update_file(ROOT / "mcp-server-nucleus/src/mcp_server_nucleus/__init__.py", r'__version__ = "[^"]+"', f'__version__ = "{v}"', dry_run)
    
    # Dockerfiles (Root and Server)
    update_file(ROOT / "Dockerfile", r'LABEL version="[^"]+"', f'LABEL version="{v}"', dry_run)
    update_file(ROOT / "mcp-server-nucleus/Dockerfile", r'# Version: [^\s]+', f'# Version: {v}', dry_run)
    update_file(ROOT / "mcp-server-nucleus/Dockerfile", r'LABEL version="[^"]+"', f'LABEL version="{v}"', dry_run)
    
    # NPM Targets (Multiple)
    npm_targets = [
        ROOT / "nucleus-mcp/package.json",
        ROOT / "nucleus-mcp/package.json.real",
        ROOT / "mcp-server-nucleus/npm-wrapper/package.json"
    ]
    for npm_path in npm_targets:
        if npm_path.exists():
            data = json.loads(npm_path.read_text())
            data["version"] = v
            if not dry_run: 
                npm_path.write_text(json.dumps(data, indent=4))
                print(f"  [✓] Updated: {npm_path.relative_to(ROOT)}")
            else:
                print(f"  [SIM] Would update: {npm_path.relative_to(ROOT)}")

    # Landing Page (UI Strings)
    update_file(
        ROOT / "nucleus-landing/src/App.jsx", 
        r'v\d+\.\d+\.\d+', 
        f'v{v}', 
        dry_run
    )
    # Also update technical walkthrough reference
    update_file(
        ROOT / "nucleus-landing/src/App.jsx",
        r'Technical Walkthrough \(v\d+\.\d+\.\d+\)',
        f'Technical Walkthrough (v{v})',
        dry_run
    )

    # 2. Registry Manifest Processing
    for manifest_file in REGISTRY_DIR.glob("*.json"):
        if manifest_file.name == "version.json": continue
        m = json.loads(manifest_file.read_text())
        
        # Internal Sync
        m['version'] = v
        if not dry_run: manifest_file.write_text(json.dumps(m, indent=4))
        
        # Mirroring (For Crawlers)
        if m.get("mirror_to_root"):
            root_target = ROOT / manifest_file.name
            if not dry_run:
                root_target.write_text(json.dumps(m, indent=4))
                print(f"  [✓] Mirrored: {manifest_file.name} -> root")

        # Templating (Markdown Injections)
        if "templating" in m:
            for t in m["templating"]:
                apply_template(ROOT / t["file"], t["marker"], t["content"], dry_run)

    # 3. Autonomous Release (Zero-Touch)
    if release and not dry_run:
        print(f"\n🏗️ Sentinel: Executing Autonomous Release Protocol...")
        # Check current branch
        curr_branch = run_cmd("git rev-parse --abbrev-ref HEAD").strip()
        if curr_branch != "main" and curr_branch != "master":
            print(f"❌ RELEASE BLOCKED: Sentinel only strikes from main/master (Current: {curr_branch})")
            sys.exit(1)
            
        run_cmd(f"git add .")
        run_cmd(f"git commit -m 'Release v{v} (Autonomous Sentinel Sync)'")
        run_cmd(f"git tag -a v{v} -m 'Release v{v}'")
        run_cmd("git push origin --tags")
        # Triggering the push is usually enough, but we should push the branch too
        run_cmd(f"git push origin {curr_branch}")

    print(f"\n🛡️ Strike Complete. Ecosystem at Global Parity v{v}.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zero-Touch Registry Sentinel")
    parser.add_argument("--dry-run", action="store_true", help="Simulate changes only")
    parser.add_argument("--release", action="store_true", help="Auto-commit, tag, and push to GitHub")
    args = parser.parse_args()
    
    try:
        sync(dry_run=args.dry_run, release=args.release)
    except Exception as e:
        print(f"❌ FATAL: Sentinel Engine Error: {e}")
        sys.exit(1)
