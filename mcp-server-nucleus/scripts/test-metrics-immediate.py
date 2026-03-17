#!/usr/bin/env python3
"""Test metrics export with immediate flush."""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

os.environ["NUCLEUS_ANON_TELEMETRY"] = "true"
os.environ["NUCLEUS_ANON_TELEMETRY_ENDPOINT"] = "http://localhost:4318"

print("Testing immediate metrics export...")

from opentelemetry import metrics as otel_metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

# Create a simple test setup
resource = Resource.create({"service.name": "nucleus-test-immediate"})
exporter = OTLPMetricExporter(endpoint="http://localhost:4318")

# Use a very short export interval for testing (5 seconds)
reader = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
provider = MeterProvider(resource=resource, metric_readers=[reader])
meter = provider.get_meter("test", "1.0.0")

# Create and record metrics
counter = meter.create_counter("nucleus.anon.commands", unit="1")
histogram = meter.create_histogram("nucleus.anon.command_duration_ms", unit="ms")

print("Recording metrics...")
for i in range(5):
    counter.add(1, {"nucleus.command": f"test-{i}", "nucleus.category": "test"})
    histogram.record(100.0 + i*10, {"nucleus.command": f"test-{i}", "nucleus.category": "test"})
    print(f"  Recorded test-{i}")

print("\nWaiting 10 seconds for export...")
time.sleep(10)

print("\nForcing shutdown to flush remaining metrics...")
provider.shutdown()

print("\nChecking collector...")
import urllib.request
try:
    with urllib.request.urlopen("http://localhost:8889/metrics", timeout=5) as resp:
        content = resp.read().decode()
        nucleus_lines = [line for line in content.split('\n') if 'nucleus_nucleus_anon' in line and not line.startswith('#')]
        if nucleus_lines:
            print(f"✅ Found {len(nucleus_lines)} nucleus metric lines:")
            for line in nucleus_lines[:10]:
                print(f"  {line}")
        else:
            print("❌ No nucleus_nucleus_anon metrics found")
            print("\nAll nucleus_ metrics:")
            nucleus_all = [line for line in content.split('\n') if line.startswith('nucleus_') and not line.startswith('#')]
            for line in nucleus_all[:20]:
                print(f"  {line}")
except Exception as e:
    print(f"❌ Error: {e}")
