"""Lever dispatcher.

Usage:
    python -m scripts.levers.run_lever <lever_name>

Reads scripts/levers/manifests/<name>.yaml, loads scripts/levers/<name>.py,
runs the Lever subclass, and appends an observation to
.brain/ledger/events.jsonl. That ledger IS the compounding substrate — any
other lever or feature reading the ledger sees this observation.
"""

import argparse
import importlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BRAIN_PATH = PROJECT_ROOT / ".brain"
LEDGER_PATH = BRAIN_PATH / "ledger" / "events.jsonl"
MANIFESTS_DIR = Path(__file__).resolve().parent / "manifests"

from .base import Lever


def load_manifest(name: str, manifests_dir: Path = MANIFESTS_DIR) -> Dict[str, Any]:
    path = manifests_dir / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No manifest at {path}")
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_lever(name: str) -> Lever:
    module = importlib.import_module(f"scripts.levers.{name}")
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (isinstance(attr, type) and attr is not Lever
                and issubclass(attr, Lever)
                and getattr(attr, "name", "") == name):
            return attr()
    raise ValueError(f"No Lever subclass with name={name!r} in scripts.levers.{name}")


def append_observation(lever_name: str, observation: Dict[str, Any],
                       ledger_path: Path = LEDGER_PATH) -> Dict[str, Any]:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now().isoformat(),
        "type": f"lever.{lever_name}.observation",
        "lever": lever_name,
        "outcome": observation.get("outcome", "unknown"),
        "detail": observation.get("detail", {}),
    }
    with open(ledger_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def run(name: str, manifests_dir: Optional[Path] = None,
        ledger_path: Optional[Path] = None) -> Dict[str, Any]:
    manifest = load_manifest(name, manifests_dir or MANIFESTS_DIR)
    effective_ledger = ledger_path or LEDGER_PATH
    if not manifest.get("enabled", True):
        observation = {"outcome": "skipped", "detail": {"reason": "disabled in manifest"}}
        append_observation(name, observation, effective_ledger)
        return observation
    lever = load_lever(name)
    observation = lever.run(manifest, BRAIN_PATH)
    append_observation(name, observation, effective_ledger)
    return observation


def run_trigger(trigger: str, manifests_dir: Optional[Path] = None,
                ledger_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Fire every enabled lever whose manifest lists the given trigger.

    Lever failures are caught and printed — they must never break the caller
    (the driver), because lever auto-fire is a supporting mechanism, not a
    precondition.

    Returns a list of {"lever": name, "observation": obs} entries, one per
    lever that actually ran.
    """
    mdir = manifests_dir or MANIFESTS_DIR
    if not mdir.exists():
        return []

    results: List[Dict[str, Any]] = []
    for manifest_file in sorted(mdir.glob("*.yaml")):
        name = manifest_file.stem
        try:
            manifest = load_manifest(name, mdir)
        except Exception as e:
            print(f"[LEVER] skipping {name} — manifest load failed: {e}")
            continue
        if not manifest.get("enabled", True):
            continue
        triggers = manifest.get("triggers", []) or []
        trigger_names = set()
        for t in triggers:
            if isinstance(t, str):
                trigger_names.add(t)
            elif isinstance(t, dict):
                # Legacy/alternate form — also accept {"trigger": "name"}.
                # (Do NOT use {"on": "name"} — YAML parses `on` as boolean.)
                val = t.get("trigger") or t.get("name")
                if val:
                    trigger_names.add(val)
        if trigger not in trigger_names:
            continue
        try:
            obs = run(name, mdir, ledger_path)
            results.append({"lever": name, "observation": obs})
        except Exception as e:
            print(f"[LEVER] {name} failed (non-fatal): {e}")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a lever by name.")
    parser.add_argument("name", help="Lever name (matches manifest filename)")
    args = parser.parse_args()

    obs = run(args.name)
    outcome = obs.get("outcome", "unknown")
    print(f"[LEVER] {args.name}: {outcome}")
    detail = obs.get("detail", {})
    if outcome == "found":
        for finding in detail.get("findings", [])[:5]:
            print(f"  - {finding}")
    elif outcome == "error":
        print(f"  error: {detail.get('error', detail)}")

    return 0 if outcome in ("clean", "skipped") else 1


if __name__ == "__main__":
    sys.exit(main())
