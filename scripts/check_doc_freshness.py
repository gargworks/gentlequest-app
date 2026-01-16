#!/usr/bin/env python3
"""
Check documentation freshness and alert on stale docs.

Usage:
    python scripts/check_doc_freshness.py --dir .brain/artifacts/synthesis/ --max-age 90

Exit codes:
    0 - All documents fresh
    1 - Stale documents found (CI should fail)
"""
import re
import sys
from datetime import datetime
from pathlib import Path
import argparse

# Default thresholds
MAX_AGE_DAYS = 90
WARN_AGE_DAYS = 60


def parse_date(date_str: str) -> datetime:
    """Parse date from various formats."""
    formats = [
        '%Y-%m-%d',           # 2026-01-16
        '%B %d, %Y',          # January 16, 2026
        '%b %d, %Y',          # Jan 16, 2026
        '%d/%m/%Y',           # 16/01/2026
        '%m/%d/%Y',           # 01/16/2026
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Cannot parse date: {date_str}")


def extract_last_updated(content: str) -> str | None:
    """Extract last_updated date from document content."""
    # Try YAML frontmatter
    yaml_match = re.search(r'^---\s*\n.*?last_updated:\s*["\']?([^"\'}\n]+)', content, re.DOTALL | re.MULTILINE)
    if yaml_match:
        return yaml_match.group(1)
    
    # Try markdown format
    md_patterns = [
        r'\*\*Last Updated:\*\*\s*(\w+ \d+, \d{4})',
        r'Last Updated:\s*(\w+ \d+, \d{4})',
        r'Last Updated:\s*(\d{4}-\d{2}-\d{2})',
        r'Updated:\s*(\w+ \d+, \d{4})',
    ]
    
    for pattern in md_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def check_freshness(docs_dir: Path, max_age: int = MAX_AGE_DAYS, warn_age: int = WARN_AGE_DAYS) -> tuple[list, list, list]:
    """
    Check document freshness.
    
    Returns:
        Tuple of (stale, warnings, fresh) lists
    """
    stale = []
    warnings = []
    fresh = []
    now = datetime.now()
    
    for md_file in sorted(docs_dir.glob('*.md')):
        # Skip digest files and session files
        if md_file.name.startswith('digest_') or md_file.name.startswith('session_'):
            continue
            
        content = md_file.read_text()
        date_str = extract_last_updated(content)
        
        if not date_str:
            warnings.append({
                'file': md_file.name,
                'issue': 'No last_updated date found',
                'age': None
            })
            continue
        
        try:
            doc_date = parse_date(date_str)
        except ValueError:
            warnings.append({
                'file': md_file.name,
                'issue': f'Invalid date format: {date_str}',
                'age': None
            })
            continue
        
        age = (now - doc_date).days
        
        if age > max_age:
            stale.append({
                'file': md_file.name,
                'age': age,
                'last_updated': date_str,
                'max_age': max_age
            })
        elif age > warn_age:
            warnings.append({
                'file': md_file.name,
                'issue': f'{age} days old (warning at {warn_age})',
                'age': age
            })
        else:
            fresh.append({
                'file': md_file.name,
                'age': age,
                'last_updated': date_str
            })
    
    return stale, warnings, fresh


def print_report(stale: list, warnings: list, fresh: list, verbose: bool = False):
    """Print freshness report."""
    print("\n" + "=" * 60)
    print("📋 DOCUMENTATION FRESHNESS REPORT")
    print("=" * 60)
    
    if fresh and verbose:
        print(f"\n✅ FRESH DOCUMENTS ({len(fresh)})")
        for doc in fresh:
            print(f"   {doc['file']}: {doc['age']} days old")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)})")
        for doc in warnings:
            print(f"   {doc['file']}: {doc['issue']}")
    
    if stale:
        print(f"\n❌ STALE DOCUMENTS ({len(stale)}) - ACTION REQUIRED")
        for doc in stale:
            print(f"   {doc['file']}: {doc['age']} days old (max: {doc['max_age']})")
    
    print("\n" + "-" * 60)
    print(f"Summary: {len(fresh)} fresh, {len(warnings)} warnings, {len(stale)} stale")
    print("-" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dir', default='.brain/artifacts/synthesis/', help='Directory to check')
    parser.add_argument('--max-age', type=int, default=MAX_AGE_DAYS, help='Max age in days before stale')
    parser.add_argument('--warn-age', type=int, default=WARN_AGE_DAYS, help='Age in days to warn')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show all documents')
    parser.add_argument('--ci', action='store_true', help='CI mode: exit 1 if any stale')
    args = parser.parse_args()
    
    docs_dir = Path(args.dir)
    if not docs_dir.exists():
        print(f"❌ Directory not found: {docs_dir}")
        sys.exit(1)
    
    stale, warnings, fresh = check_freshness(docs_dir, args.max_age, args.warn_age)
    print_report(stale, warnings, fresh, args.verbose)
    
    if args.ci and stale:
        print("CI check failed: stale documents found")
        sys.exit(1)
    elif stale:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
