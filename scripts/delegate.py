#!/usr/bin/env python3
"""Thin CLI wrapper around `runtime.org_delegate.assemble_prompt`.

Usage:
    scripts/delegate.py --role sonnet_structure --brief brief.md [--dry-run]
    scripts/delegate.py --role sonnet_behavior --brief - < brief.md

Opus invokes this to assemble a Sonnet prompt from a charter + brief, then
passes the result to `Agent(subagent_type="general-purpose", model="sonnet",
prompt=<assembled>)`. Event emission (`agent_spawn` / `agent_return`) is
Opus's responsibility, not this script's.
"""
import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "mcp-server-nucleus" / "src"))

from mcp_server_nucleus.runtime.org_delegate import assemble_prompt  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Assemble a Sonnet persona prompt from charter + brief."
    )
    p.add_argument("--role", required=True,
                   help="e.g. sonnet_structure | sonnet_behavior | sonnet_narrative | opus_master")
    p.add_argument("--brief", required=True,
                   help="Path to brief file, or '-' for stdin")
    p.add_argument("--charters-dir", default=None,
                   help="Override charter dir (default: docs/org/charters)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print metadata + prompt; never used beyond print in this script")
    args = p.parse_args(argv)
    brief = sys.stdin.read() if args.brief == "-" else Path(args.brief).read_text(encoding="utf-8")
    charters_dir = Path(args.charters_dir) if args.charters_dir else None
    prompt, meta = assemble_prompt(args.role, brief, charters_dir=charters_dir)
    if args.dry_run:
        print("=== METADATA ===")
        for k, v in meta.items():
            print(f"  {k}: {v}")
        print("\n=== PROMPT ===")
    print(prompt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
