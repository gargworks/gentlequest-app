#!/usr/bin/env python3
"""
Test script for brain_import_tasks_from_jsonl patch.
Tests Patch 1: Task ledger sync (tasks.jsonl -> brain database)
"""

import os
import sys
import json

# Set brain path
os.environ["NUCLEUS_BRAIN_PATH"] = "/Users/lokeshgarg/ai-mvp-backend/.brain"

# Add mcp-server-nucleus to path
sys.path.insert(0, "/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src")

from mcp_server_nucleus import _import_tasks_from_jsonl, _get_tasks_list

def main():
    print("=" * 60)
    print("🧪 Testing brain_import_tasks_from_jsonl (Patch 1)")
    print("=" * 60)
    
    # Check current tasks before import
    print("\n📋 Current tasks in brain database:")
    current_tasks = _get_tasks_list()
    print(f"   Total: {len(current_tasks)} tasks")
    for task in current_tasks[:5]:
        print(f"   - {task.get('id')}: {task.get('description', '')[:50]}...")
    if len(current_tasks) > 5:
        print(f"   ... and {len(current_tasks) - 5} more")
    
    # Check tasks.jsonl content
    jsonl_path = "/Users/lokeshgarg/ai-mvp-backend/.brain/ledger/tasks.jsonl"
    print(f"\n📄 Reading tasks.jsonl:")
    if os.path.exists(jsonl_path):
        with open(jsonl_path) as f:
            lines = [l for l in f.readlines() if l.strip()]
        print(f"   Found {len(lines)} tasks in JSONL file")
        for line in lines[:5]:
            task = json.loads(line)
            print(f"   - {task.get('id')}: {task.get('description', '')[:40]}...")
    else:
        print(f"   ❌ File not found: {jsonl_path}")
        return 1
    
    # Run import (merge mode - don't clear existing)
    print("\n🚀 Running import (merge mode)...")
    result = _import_tasks_from_jsonl("ledger/tasks.jsonl", clear_existing=False)
    
    print(f"\n📊 Import Result:")
    print(f"   Success: {result.get('success')}")
    print(f"   Imported: {result.get('imported')}")
    print(f"   Skipped: {result.get('skipped')}")
    print(f"   Total tasks: {result.get('total_tasks')}")
    if result.get('errors'):
        print(f"   Errors: {result.get('errors')}")
    if result.get('error'):
        print(f"   Error: {result.get('error')}")
    
    # Verify tasks after import
    print("\n✅ Tasks after import:")
    tasks_after = _get_tasks_list()
    print(f"   Total: {len(tasks_after)} tasks")
    
    # Check for GTM tasks (task_001, task_002, etc.)
    gtm_tasks = [t for t in tasks_after if t.get('id', '').startswith('task_')]
    print(f"   GTM tasks (semantic IDs): {len(gtm_tasks)}")
    for task in gtm_tasks:
        status = task.get('status', 'UNKNOWN')
        env = task.get('environment', 'N/A')
        print(f"   - {task.get('id')}: {task.get('description', '')[:40]}... [{status}] ({env})")
    
    # Verify we can now claim a GTM task
    print("\n🎯 Verification: Can we find task_002?")
    task_002 = next((t for t in tasks_after if t.get('id') == 'task_002'), None)
    if task_002:
        print(f"   ✅ Found task_002: {task_002.get('description')}")
        print(f"      Status: {task_002.get('status')}")
        print(f"      Environment: {task_002.get('environment')}")
        print(f"      Model: {task_002.get('model')}")
    else:
        print(f"   ❌ task_002 not found!")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ PATCH 1 TEST COMPLETE: Task ledger sync working!")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
