
import os
import shutil
import zipfile
import datetime

# Configuration
VERSION = "v1.0"
RELEASE_DIR = f"release_{VERSION}_gentlequest"
OUTPUT_ZIP = f"RELEASE_{VERSION}_PILOT_READY.zip"

# Include Patterns (Files/Dirs to copy)
INCLUDES = [
    "app.py",
    "models.py",
    "config.py",
    "requirements.txt",
    "requirements-cloudrun.txt",
    "Procfile",
    "Dockerfile",
    "Makefile",
    ".env.example",
    "migrations",
    "providers",
    "templates",
    "static",
    "scripts",
    "docs",
    "demo_package",
    "ai_buddy_web", # Flutter Source
    ".brain/artifacts/implementation/EXECUTIVE_SUMMARY_AND_RECOMMENDATIONS.md" # Key Context
]

# Exclude Patterns (Common junk)
EXCLUDES = [
    "__pycache__",
    ".DS_Store",
    ".git",
    ".venv",
    ".idea",
    "ai_buddy_web/build", # Don't ship build artifacts, just source
    ".brain/brain", # Too big/sensitive
    "venv"
]

def create_install_guide(target_dir):
    """Creates a simple INSTALL.md for the recipient."""
    content = """# GentleQuest v1.0 - Pilot Release
**Ready for Deployment**

## Quick Start (Production)
1. **Unzip** this package.
2. **Setup Env:** `cp .env.example .env` and fill in secrets.
3. **Deploy (Cloud Run):** 
   ```bash
   gcloud run deploy gentlequest-prod --source .
   ```

## Development
1. **Backend:** `pip install -r requirements.txt && python app.py`
2. **Frontend:** `cd ai_buddy_web && flutter run`

## Contents
- `app.py`: Backend Entrypoint
- `ai_buddy_web/`: Flutter Frontend
- `docs/`: Operational Manuals
- `demo_package/`: Press Kit (Video/Screenshots)

**Support:** contact@gentlequest.app
"""
    with open(os.path.join(target_dir, "INSTALL.md"), "w") as f:
        f.write(content)

def copy_item(src, dst):
    if os.path.isdir(src):
        # We use shutil.copytree but need to filter excludes manually 
        # simpler to just walk and copy? Or use copytree with ignore.
        # Let's use robust manual walk for precise control.
        if not os.path.exists(dst):
            os.makedirs(dst)
        
        for root, dirs, files in os.walk(src):
            # Filtering dirs
            dirs[:] = [d for d in dirs if d not in EXCLUDES]
            
            # Create dest dirs
            rel_path = os.path.relpath(root, src)
            dest_dir = os.path.join(dst, rel_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            
            for file in files:
                if file not in EXCLUDES and not file.endswith(".pyc"):
                    shutil.copy2(os.path.join(root, file), os.path.join(dest_dir, file))
    else:
        if os.path.exists(src):
            if not os.path.exists(os.path.dirname(dst)):
                os.makedirs(os.path.dirname(dst))
            shutil.copy2(src, dst)
        else:
            print(f"⚠️ Warning: Source {src} not found.")

def main():
    print(f"📦 Packaging GentleQuest {VERSION}...")
    
    # 1. Cleanup old
    if os.path.exists(RELEASE_DIR):
        shutil.rmtree(RELEASE_DIR)
    if os.path.exists(OUTPUT_ZIP):
        os.remove(OUTPUT_ZIP)
        
    os.makedirs(RELEASE_DIR)
    
    # 2. Copy Files
    for item in INCLUDES:
        src = item
        dst = os.path.join(RELEASE_DIR, item)
        print(f"  - Copying {item}...")
        copy_item(src, dst)
        
    # 3. Create Install Guide
    create_install_guide(RELEASE_DIR)
    
    # 4. Zip it
    print(f"🗜️ Zipping to {OUTPUT_ZIP}...")
    shutil.make_archive(RELEASE_DIR, 'zip', RELEASE_DIR)
    
    # Needs rename because make_archive adds .zip extension
    if os.path.exists(RELEASE_DIR + ".zip"):
         shutil.move(RELEASE_DIR + ".zip", OUTPUT_ZIP)
         
    # 5. Cleanup Dir
    shutil.rmtree(RELEASE_DIR)
    
    print(f"✅ Success! Package Ready: {OUTPUT_ZIP}")

if __name__ == "__main__":
    main()
