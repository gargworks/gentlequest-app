#!/usr/bin/env python3
"""
Knowledge Indexer: Scans all markdown files and creates a structured index.
Part of the "Knowledge University" activation system.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent
BRAIN_PATH = PROJECT_ROOT / ".brain"
DOCS_PATH = PROJECT_ROOT / "docs"
INDEX_OUTPUT = BRAIN_PATH / "knowledge_index.json"

# Faculty classification rules (path patterns -> faculty)
FACULTY_RULES = {
    "operations": [
        r"^DEVELOPMENT_RULES\.md$",
        r"^DEPLOYMENT.*\.md$",
        r"^TESTING.*\.md$",
        r"^.*PROTOCOL.*\.md$",
        r"^.*RULES.*\.md$",
    ],
    "agents": [
        r"^\.brain/agents/.*\.md$",
    ],
    "research": [
        r"^\.brain/artifacts/research/.*\.md$",
        r".*competitive.*\.md$",
        r".*market.*\.md$",
        r".*benchmark.*\.md$",
    ],
    "strategy": [
        r"^\.brain/artifacts/strategy/.*\.md$",
        r"^docs/.*strategy.*\.md$",
        r"^docs/NUCLEAR.*\.md$",
        r"^docs/AGENTIC.*\.md$",
    ],
    "execution": [
        r"^\.brain/artifacts/test/.*\.md$",
        r"^\.brain/artifacts/synthesis/.*\.md$",
        r"^\.brain/ledger/.*\.md$",
        r".*checklist.*\.md$",
        r".*log.*\.md$",
    ],
    "architecture": [
        r"^\.brain/artifacts/architecture/.*\.md$",
        r"^docs/.*spec.*\.md$",
        r"^docs/API.*\.md$",
    ],
    "marketing": [
        r"^\.brain/artifacts/marketing/.*\.md$",
        r".*launch.*\.md$",
        r".*growth.*\.md$",
    ],
}


def classify_faculty(relative_path: str) -> str:
    """Classify a file into a faculty based on path patterns."""
    for faculty, patterns in FACULTY_RULES.items():
        for pattern in patterns:
            if re.search(pattern, relative_path, re.IGNORECASE):
                return faculty
    return "general"


def extract_title(content: str, filename: str) -> str:
    """Extract title from markdown content (first # heading or filename)."""
    lines = content.split('\n')
    for line in lines[:10]:  # Check first 10 lines
        if line.startswith('# '):
            return line[2:].strip()
    return filename.replace('.md', '').replace('_', ' ').title()


def extract_summary(content: str, max_chars: int = 200) -> str:
    """Extract a summary from the first paragraph after the title."""
    lines = content.split('\n')
    summary_lines = []
    started = False
    
    for line in lines:
        # Skip title and empty lines at start
        if not started:
            if line.startswith('#') or line.strip() == '':
                continue
            started = True
        
        # Stop at next heading or after enough content
        if started:
            if line.startswith('#'):
                break
            summary_lines.append(line.strip())
            if len(' '.join(summary_lines)) > max_chars:
                break
    
    summary = ' '.join(summary_lines)[:max_chars]
    if len(summary) == max_chars:
        summary += '...'
    return summary


def extract_rules_from_dev_rules(content: str) -> list:
    """Special parser for DEVELOPMENT_RULES.md to extract individual rules."""
    rules = []
    current_section = None
    
    for line in content.split('\n'):
        # Track section headers
        if line.startswith('### '):
            current_section = line[4:].strip()
        # Extract rules (lines starting with - ✅)
        elif line.strip().startswith('- ✅') and current_section:
            rule_text = line.strip()[4:].strip()  # Remove "- ✅ "
            rules.append({
                "section": current_section,
                "rule": rule_text
            })
    
    return rules


def scan_directory(base_path: Path, relative_to: Path) -> list:
    """Recursively scan a directory for markdown files."""
    files = []
    
    if not base_path.exists():
        return files
    
    for item in base_path.rglob('*.md'):
        # Skip hidden and common exclusions
        if any(part.startswith('.') and part != '.brain' for part in item.parts):
            continue
        if 'node_modules' in item.parts or 'venv' in item.parts:
            continue
        
        try:
            relative_path = str(item.relative_to(relative_to))
            content = item.read_text(encoding='utf-8', errors='ignore')
            
            file_info = {
                "path": relative_path,
                "absolute_path": str(item),
                "faculty": classify_faculty(relative_path),
                "title": extract_title(content, item.name),
                "summary": extract_summary(content),
                "size_bytes": item.stat().st_size,
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
            }
            
            # Special handling for DEVELOPMENT_RULES.md
            if item.name == 'DEVELOPMENT_RULES.md':
                file_info["extracted_rules"] = extract_rules_from_dev_rules(content)
                file_info["rules_count"] = len(file_info["extracted_rules"])
            
            files.append(file_info)
            
        except Exception as e:
            print(f"Warning: Could not process {item}: {e}")
    
    return files


def build_index() -> dict:
    """Build the complete knowledge index."""
    print("🔍 Scanning for markdown files...")
    
    all_files = []
    
    # Scan .brain/
    all_files.extend(scan_directory(BRAIN_PATH, PROJECT_ROOT))
    
    # Scan docs/
    all_files.extend(scan_directory(DOCS_PATH, PROJECT_ROOT))
    
    # Scan root directory (non-recursive)
    for item in PROJECT_ROOT.glob('*.md'):
        if item.is_file():
            try:
                relative_path = item.name
                content = item.read_text(encoding='utf-8', errors='ignore')
                
                file_info = {
                    "path": relative_path,
                    "absolute_path": str(item),
                    "faculty": classify_faculty(relative_path),
                    "title": extract_title(content, item.name),
                    "summary": extract_summary(content),
                    "size_bytes": item.stat().st_size,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                }
                
                # Special handling for DEVELOPMENT_RULES.md
                if item.name == 'DEVELOPMENT_RULES.md':
                    file_info["extracted_rules"] = extract_rules_from_dev_rules(content)
                    file_info["rules_count"] = len(file_info["extracted_rules"])
                
                all_files.append(file_info)
                
            except Exception as e:
                print(f"Warning: Could not process {item}: {e}")
    
    # Build faculty summaries
    faculties = {}
    for file in all_files:
        faculty = file["faculty"]
        if faculty not in faculties:
            faculties[faculty] = {"count": 0, "files": []}
        faculties[faculty]["count"] += 1
        faculties[faculty]["files"].append(file["path"])
    
    # Count total rules extracted
    total_rules = sum(
        f.get("rules_count", 0) for f in all_files 
        if "rules_count" in f
    )
    
    index = {
        "generated_at": datetime.now().isoformat(),
        "total_files": len(all_files),
        "total_rules_extracted": total_rules,
        "faculties": faculties,
        "files": all_files,
    }
    
    return index


def main():
    """Main entry point."""
    print("📚 Knowledge Indexer Starting...")
    
    index = build_index()
    
    # Save index
    INDEX_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n✅ Index complete!")
    print(f"   📄 Total files: {index['total_files']}")
    print(f"   📜 Rules extracted: {index['total_rules_extracted']}")
    print(f"   📁 Faculties: {', '.join(index['faculties'].keys())}")
    print(f"   💾 Saved to: {INDEX_OUTPUT}")
    
    # Print faculty breakdown
    print("\n📊 Faculty Breakdown:")
    for faculty, data in sorted(index['faculties'].items(), key=lambda x: -x[1]['count']):
        print(f"   {faculty}: {data['count']} files")


if __name__ == "__main__":
    main()
