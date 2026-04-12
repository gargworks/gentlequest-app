"""Lever #15 — ruff_chain.

Runs ruff on the files changed in a given diff spec and reports findings.
No auto-fix unless the manifest sets check_level=fix. Exists because the
71-idea blitz showed ruff catches real issues on current code (2 F401 in
tests/test_gt40_verification.py at the time of the probe).
"""

import subprocess
from pathlib import Path
from typing import Any, Dict

from .base import Lever


class RuffChainLever(Lever):
    name = "ruff_chain"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> Dict[str, Any]:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        check_level = inputs.get("check_level", "warn")

        try:
            files_result = subprocess.run(
                ["git", "diff", "--name-only", diff_spec, "--", "*.py"],
                capture_output=True, text=True, timeout=10,
            )
        except Exception as e:
            return {"outcome": "error", "detail": {"stage": "git_diff", "error": str(e)}}

        files = [f for f in files_result.stdout.strip().splitlines() if f]
        if not files:
            return {"outcome": "clean", "detail": {"files_checked": 0, "diff_spec": diff_spec}}

        cmd = ["ruff", "check"]
        if check_level == "fix":
            cmd.append("--fix")
        cmd.extend(files)

        try:
            ruff_result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        except FileNotFoundError:
            return {"outcome": "error", "detail": {"stage": "ruff", "error": "ruff not installed"}}
        except Exception as e:
            return {"outcome": "error", "detail": {"stage": "ruff", "error": str(e)}}

        findings = [line for line in ruff_result.stdout.splitlines() if line.strip()]
        if ruff_result.returncode == 0:
            return {"outcome": "clean", "detail": {"files_checked": len(files), "diff_spec": diff_spec}}

        return {
            "outcome": "found",
            "detail": {
                "files_checked": len(files),
                "diff_spec": diff_spec,
                "check_level": check_level,
                "exit_code": ruff_result.returncode,
                "findings": findings[:20],
            },
        }
