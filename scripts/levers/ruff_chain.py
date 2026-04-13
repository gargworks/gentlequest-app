"""Lever — ruff_chain.

Runs ruff on the files changed in a given diff spec and reports findings.
No auto-fix unless the manifest sets check_level=fix. Exists because the
71-idea blitz showed ruff catches real issues on current code (2 F401 in
tests/test_gt40_verification.py at the time of the probe).
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict

from .base import Lever, LeverObservation, SubprocessFailure


class RuffChainLever(Lever):
    name = "ruff_chain"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        check_level = inputs.get("check_level", "warn")

        try:
            files_result = self._run_subprocess(
                ["git", "diff", "--name-only", diff_spec, "--", "*.py"],
                timeout=10,
                stage="git_diff",
            )
        except FileNotFoundError:
            return self.observation_error("git_diff", "git not installed")
        except subprocess.TimeoutExpired:
            return self.observation_error("git_diff", "timed out", diff_spec=diff_spec)
        except SubprocessFailure as e:
            return self.observation_error(
                "git_diff", e.stderr.strip() or f"git exit {e.returncode}",
                returncode=e.returncode,
            )

        files = [f for f in files_result.stdout.strip().splitlines() if f]
        if not files:
            return self.observation_clean({"files_checked": 0, "diff_spec": diff_spec})

        cmd = ["ruff", "check"]
        if check_level == "fix":
            cmd.append("--fix")
        cmd.extend(files)

        try:
            ruff_result = self._run_subprocess(cmd, timeout=30, stage="ruff")
        except FileNotFoundError:
            return self.observation_error("ruff", "ruff not installed")
        except subprocess.TimeoutExpired:
            return self.observation_error("ruff", "timed out", files=len(files))

        findings = [line for line in ruff_result.stdout.splitlines() if line.strip()]
        if ruff_result.returncode == 0:
            return self.observation_clean(
                {"files_checked": len(files), "diff_spec": diff_spec}
            )

        return self.observation_found({
            "files_checked": len(files),
            "diff_spec": diff_spec,
            "check_level": check_level,
            "exit_code": ruff_result.returncode,
            "findings": findings[:20],
        })
