#!/usr/bin/env python3
"""Auto-fire ship-report relay to Cowork on PR creation/push.

Closes the GitHub-event → relay-bus gap demonstrated by PR #83 (Phase 1 wedge):
ship event happened, but Cowork was blind until next CC turn manually fired
a ship-report. This wrapper reads PR metadata via `gh pr view` and posts via
runtime.relay_ops.relay_post — same path /to-cowork uses, so envelope and
sender-routing match exactly.

Idempotent on PR number via sentinel file
(.brain/relay/cowork/.pr_shipped_<N>): re-running for the same PR is a no-op.

Usage:
    relay_pr_ship.py                # auto-detect PR for current branch
    relay_pr_ship.py <PR_NUMBER>    # explicit PR
    relay_pr_ship.py --dry-run      # print envelope, no write, no sentinel

Env:
    NUCLEUS_BRAIN_PATH   — overrides repo-root .brain (symmetric with relay_judge)
    CC_SESSION_ROLE      — main|peer (default: main); stamps sender accordingly
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "mcp-server-nucleus" / "src"))

from mcp_server_nucleus.runtime.relay_ops import relay_post  # noqa: E402

GH_FIELDS = "number,title,baseRefName,headRefName,headRefOid,additions,deletions,changedFiles,url"


def _gh_pr_meta(pr: str | None) -> dict:
    args = ["gh", "pr", "view"]
    if pr:
        args.append(pr)
    args += ["--json", GH_FIELDS]
    return json.loads(subprocess.check_output(args, text=True))


def _resolve_session_id() -> str | None:
    base = Path.home() / ".claude" / "projects" / "-Users-lokeshgarg-ai-mvp-backend"
    if not base.exists():
        return None
    files = sorted(base.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0].stem if files else None


def _brain_path() -> Path:
    env = os.environ.get("NUCLEUS_BRAIN_PATH")
    return Path(env) if env else _REPO_ROOT / ".brain"


def _build_envelope(meta: dict, sess: str | None) -> tuple[str, str]:
    pr = meta["number"]
    summary = (
        f"Shipped PR#{pr} ({meta['headRefName']} → {meta['baseRefName']}): "
        f"{meta['title']}. SHA: {meta['headRefOid'][:12]}. "
        f"Diff: +{meta['additions']}/-{meta['deletions']} across "
        f"{meta['changedFiles']} files. URL: {meta['url']}"
    )
    body = json.dumps(
        {
            "summary": summary,
            "tags": ["ship-report"],
            "artifact_refs": [f"PR#{pr}", meta["url"], meta["headRefOid"]],
            "receiver_interest_match": f"thread-reply: PR#{pr}",
            "auto_generated": True,
            "in_reply_to": None,
            "from_session_id": sess,
        }
    )
    subject = f"ship-report: PR#{pr} — {meta['title']}"
    return subject, body


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("pr", nargs="?", help="PR number (default: auto-detect from current branch)")
    parser.add_argument("--dry-run", action="store_true", help="Print envelope; do not write or set sentinel.")
    args = parser.parse_args()

    meta = _gh_pr_meta(args.pr)
    pr_num = meta["number"]
    sentinel = _brain_path() / "relay" / "cowork" / f".pr_shipped_{pr_num}"

    if sentinel.exists() and not args.dry_run:
        print(f"PR#{pr_num} already shipped (sentinel: {sentinel.relative_to(_brain_path())})")
        return 0

    sess = _resolve_session_id()
    role = os.environ.get("CC_SESSION_ROLE", "main")
    sender = f"claude_code_{role}"
    subject, body = _build_envelope(meta, sess)

    if args.dry_run:
        print(json.dumps({"sender": sender, "subject": subject, "body": json.loads(body)}, indent=2))
        return 0

    result = relay_post(
        to="cowork",
        subject=subject,
        body=body,
        priority="normal",
        sender=sender,
        from_session_id=sess,
    )
    if not result.get("sent"):
        print(f"ship-report failed: {result}", file=sys.stderr)
        return 1

    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.touch()
    print(f"ship-report fired: {result['message_id']} → {result['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
