"""Generate project statistics"""
import os
import subprocess

def count_files_by_type():
    stats = {
        'Python files': 0,
        'Dart files': 0,
        'SQL files': 0,
        'Shell scripts': 0,
        'Markdown docs': 0,
        'JSON configs': 0,
        'YAML configs': 0,
    }
    
    for root, dirs, files in os.walk('.'):
        # Skip venv and checkpoints
        if 'venv' in root or 'checkpoints' in root or '.git' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                stats['Python files'] += 1
            elif file.endswith('.dart'):
                stats['Dart files'] += 1
            elif file.endswith('.sql'):
                stats['SQL files'] += 1
            elif file.endswith('.sh'):
                stats['Shell scripts'] += 1
            elif file.endswith('.md'):
                stats['Markdown docs'] += 1
            elif file.endswith('.json'):
                stats['JSON configs'] += 1
            elif file.endswith(('.yml', '.yaml')):
                stats['YAML configs'] += 1
    
    return stats

def main():
    print("📊 PROJECT STATISTICS")
    print("=" * 80)
    
    stats = count_files_by_type()
    
    print("\nFILE COUNTS:")
    for file_type, count in stats.items():
        print(f"  {file_type:20s} {count:>6d}")
    
    print(f"\n  {'Total files':20s} {sum(stats.values()):>6d}")
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()
