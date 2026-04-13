"""Lever — gt40_typecheck.

Wraps ``nucleus verify --tiers 2`` (GT40's import/type resolution tier)
as a lever so its exit status and tail output land in the ledger. Same
contract shape as gt40_lint, higher default timeout because tier 2 is
import-graph heavier.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict

from .base import Lever, LeverObservation


class Gt40TypecheckLever(Lever):
    name = "gt40_typecheck"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        nucleus_bin = inputs.get("nucleus_bin", "nucleus")
        timeout_seconds = int(inputs.get("timeout_seconds", 30))
        tier = int(inputs.get("tier", 2))

        argv = [
            nucleus_bin,
            "verify",
            "--tiers",
            str(tier),
            "--timeout",
            str(timeout_seconds),
        ]

        try:
            result = self._run_subprocess(
                argv, timeout=timeout_seconds + 5, stage=self.name
            )
        except FileNotFoundError:
            return self.observation_error(
                "nucleus_missing", f"executable not found: {nucleus_bin}", tier=tier
            )
        except subprocess.TimeoutExpired:
            return self.observation_error(
                "timeout", f"exceeded {timeout_seconds}s", tier=tier
            )

        if result.returncode == 0:
            return self.observation_clean({"tier": tier})

        findings = _tail_nonempty(
            (result.stdout or "") + "\n" + (result.stderr or ""), limit=20
        )
        return self.observation_found({
            "tier": tier,
            "returncode": result.returncode,
            "findings": findings,
        })


def _tail_nonempty(blob: str, *, limit: int) -> list:
    lines = [ln.rstrip() for ln in blob.splitlines() if ln.strip()]
    return lines[-limit:]
