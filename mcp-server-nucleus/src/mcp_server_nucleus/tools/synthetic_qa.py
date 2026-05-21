"""
synthetic_qa.py — Nucleus MCP tool: nucleus_synthetic_qa

Exposes the Synthetic QA Framework as an MCP action.
Calls run_synthetic_qa.py via subprocess; streams stdout to caller.

Actions:
  run            Run all UCs for a product.
  run_subset     Run specific UC IDs.
  get_last_backlog   Read the most recent BACKLOG.md from reports/.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Root of the synthetic_ux framework relative to this file
_REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
_SYNTHETIC_UX_DIR = _REPO_ROOT / "docs/design/refs/testing/synthetic_ux"
_RUN_SCRIPT = _SYNTHETIC_UX_DIR / "run_synthetic_qa.py"


def _run_qa(product: str, uc_ids: str | None = None, dry_run: bool = False) -> str:
    cmd = [sys.executable, str(_RUN_SCRIPT), "--product", product]
    if uc_ids:
        cmd += ["--uc-ids", uc_ids]
    if dry_run:
        cmd.append("--dry-run")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(_SYNTHETIC_UX_DIR),
        )
        output = result.stdout + (f"\n[stderr]\n{result.stderr}" if result.stderr.strip() else "")
        exit_note = ""
        if result.returncode == 0:
            exit_note = "\n✓ No BLOCKERs found."
        elif result.returncode == 1:
            exit_note = "\n✗ BLOCKERs present — check BACKLOG.md."
        elif result.returncode == 2:
            exit_note = "\n✗ Walk infrastructure failure."
        return output + exit_note
    except subprocess.TimeoutExpired:
        return "✗ run_synthetic_qa.py timed out (300s)."
    except Exception as e:
        return f"✗ Failed to run synthetic QA: {e}"


def _get_last_backlog(product: str) -> str:
    reports_dir = _SYNTHETIC_UX_DIR / "reports"
    if not reports_dir.exists():
        return "No reports directory found."
    run_dirs = sorted(
        [d for d in reports_dir.iterdir() if d.is_dir() and d.name.startswith(product)],
        reverse=True,
    )
    if not run_dirs:
        return f"No runs found for product '{product}'."
    backlog = run_dirs[0] / "BACKLOG.md"
    if not backlog.exists():
        return f"No BACKLOG.md in most recent run: {run_dirs[0].name}"
    return backlog.read_text(encoding="utf-8")


def register(mcp, helpers):
    @mcp.tool()
    def nucleus_synthetic_qa(action: str, params: dict = {}) -> str:
        """Synthetic QA Framework — AI-driven behavioral + UX testing.

Actions:
  run              Run all UCs for a product.
                   params: {product: str, dry_run?: bool}

  run_subset       Run specific UC IDs.
                   params: {product: str, uc_ids: "UC-I2,UC-M1", dry_run?: bool}

  get_last_backlog Return the most recent BACKLOG.md for a product.
                   params: {product: str}

Returns plain text: per-UC status lines + pattern alerts + BACKLOG path.
Exit codes injected: ✓ no BLOCKERs / ✗ BLOCKERs present / ✗ walk failure.
"""
        product = params.get("product", "gentlequest")
        dry_run = bool(params.get("dry_run", False))

        if action == "run":
            return _run_qa(product, dry_run=dry_run)

        if action == "run_subset":
            uc_ids = params.get("uc_ids")
            if not uc_ids:
                return "✗ run_subset requires params.uc_ids (comma-separated UC IDs)"
            return _run_qa(product, uc_ids=uc_ids, dry_run=dry_run)

        if action == "get_last_backlog":
            return _get_last_backlog(product)

        return json.dumps({
            "ok": False,
            "error": {"code": "UNKNOWN_ACTION", "message": f"Unknown action: {action}"},
        })

    return [("nucleus_synthetic_qa", nucleus_synthetic_qa)]
