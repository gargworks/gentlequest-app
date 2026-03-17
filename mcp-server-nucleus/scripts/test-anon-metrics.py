#!/usr/bin/env python3
"""Test script to verify anonymous metrics export to local collector.

Usage:
    python3 scripts/test-anon-metrics.py

Expected behavior:
    1. Sends test metrics to http://localhost:4318/v1/metrics
    2. Waits for export interval (2 minutes)
    3. Queries Prometheus for nucleus_* metrics
    4. Reports success/failure
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Force local endpoint and enable telemetry
os.environ["NUCLEUS_ANON_TELEMETRY"] = "true"
os.environ["NUCLEUS_ANON_TELEMETRY_ENDPOINT"] = "http://localhost:4318"

print("=" * 60)
print("ANONYMOUS METRICS TEST")
print("=" * 60)
print(f"Endpoint: {os.environ['NUCLEUS_ANON_TELEMETRY_ENDPOINT']}")
print(f"Enabled: {os.environ['NUCLEUS_ANON_TELEMETRY']}")
print()

# Import after env vars are set
from mcp_server_nucleus.runtime.anon_telemetry import (
    record_anon_command,
    _ensure_initialized,
    is_anon_telemetry_enabled,
)

print(f"Telemetry enabled check: {is_anon_telemetry_enabled()}")
print()

# Force initialization to see any errors
print("Initializing telemetry...")
_ensure_initialized()
print("✓ Initialization complete")
print()

# Record test metrics
print("Recording test metrics...")
for i in range(5):
    record_anon_command(
        command=f"test-command-{i}",
        category="test",
        duration_ms=100.0 + (i * 10),
    )
    print(f"  ✓ Recorded test-command-{i}")

print()
print("Metrics recorded. Waiting for export interval (120 seconds)...")
print("You can check collector logs in another terminal:")
print("  docker logs -f nucleus-otel-collector")
print()

# Wait for export
for remaining in range(125, 0, -5):
    print(f"  {remaining}s remaining...", end="\r")
    time.sleep(5)

print("\n")
print("Checking Prometheus for metrics...")

# Query Prometheus
import urllib.request
import json

try:
    prom_url = "http://localhost:9090/api/v1/label/__name__/values"
    req = urllib.request.Request(prom_url)
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read())
        metrics = data.get("data", [])
        nucleus_metrics = [m for m in metrics if m.startswith("nucleus_")]
        
        if nucleus_metrics:
            print("✅ SUCCESS: Found nucleus metrics in Prometheus:")
            for m in nucleus_metrics[:10]:
                print(f"  - {m}")
            if len(nucleus_metrics) > 10:
                print(f"  ... and {len(nucleus_metrics) - 10} more")
        else:
            print("❌ FAILURE: No nucleus_* metrics found in Prometheus")
            print(f"Available metrics: {len(metrics)}")
            print("First 10 metrics:")
            for m in metrics[:10]:
                print(f"  - {m}")
            sys.exit(1)
except Exception as e:
    print(f"❌ ERROR querying Prometheus: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("Test complete!")
print("=" * 60)
