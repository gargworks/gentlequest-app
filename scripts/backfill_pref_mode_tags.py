#!/usr/bin/env python3
"""Backfill mode tags on existing preference_pairs.jsonl entries.

Existing records often lack `metadata.mode`, which makes /tb/stats report
`by mode: untagged=N` and prevents mode-aware training filters. This script
runs the cheap keyword detector from providers.brain_rag._infer_scope on
each record's prompt to infer "code" or "life", and writes the tag back
into metadata.mode (only when missing — never overwrites an explicit tag).

Usage:
  python scripts/backfill_pref_mode_tags.py            # dry-run, prints diff
  python scripts/backfill_pref_mode_tags.py --apply    # writes in place
  python scripts/backfill_pref_mode_tags.py --residual life  # default for ambiguous
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from providers.brain_rag import _infer_scope  # noqa: E402

PAIRS = ROOT / ".brain" / "training" / "preference_pairs.jsonl"


def infer_mode(record: dict, residual: str) -> str:
    prompt = record.get("prompt") or ""
    chosen = record.get("chosen") or ""
    rejected = record.get("rejected") or ""
    blob = f"{prompt}\n{chosen}\n{rejected}"
    scope = _infer_scope(blob)
    return scope or residual


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write changes in-place (otherwise dry-run)")
    ap.add_argument("--residual", default="life",
                    help="mode to assign when inference is ambiguous (default: life)")
    ap.add_argument("--path", default=str(PAIRS), help="preference_pairs.jsonl path")
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"[backfill] not found: {p}")
        return 1

    lines = p.read_text().splitlines()
    out_lines = []
    counters = {"total": 0, "tagged_existing": 0, "tagged_new_life": 0,
                "tagged_new_code": 0, "skipped_malformed": 0}

    for raw in lines:
        if not raw.strip():
            out_lines.append(raw)
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            counters["skipped_malformed"] += 1
            out_lines.append(raw)
            continue

        counters["total"] += 1
        meta = obj.get("metadata") or {}
        if not isinstance(meta, dict):
            meta = {}

        existing = meta.get("mode")
        if existing in ("life", "code", "work", "business", "design"):
            counters["tagged_existing"] += 1
            out_lines.append(raw)
            continue

        mode = infer_mode(obj, args.residual)
        meta["mode"] = mode
        meta.setdefault("mode_source", "backfill_v1")
        obj["metadata"] = meta
        out_lines.append(json.dumps(obj, ensure_ascii=False))
        counters[f"tagged_new_{mode}"] = counters.get(f"tagged_new_{mode}", 0) + 1

    print(f"[backfill] file:  {p}")
    print(f"[backfill] total: {counters['total']}")
    print(f"[backfill] already tagged:    {counters['tagged_existing']}")
    print(f"[backfill] new tag (life):    {counters.get('tagged_new_life', 0)}")
    print(f"[backfill] new tag (code):    {counters.get('tagged_new_code', 0)}")
    print(f"[backfill] malformed skipped: {counters['skipped_malformed']}")
    print(f"[backfill] residual default:  {args.residual}")

    if not args.apply:
        print("[backfill] DRY RUN — re-run with --apply to write changes")
        return 0

    backup = p.with_suffix(p.suffix + ".bak")
    shutil.copy2(p, backup)
    p.write_text("\n".join(out_lines) + "\n")
    print(f"[backfill] WROTE {p}  (backup at {backup})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
