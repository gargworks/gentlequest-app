"""Lever — gt40_test_smoke.

Wraps ``nucleus verify --tiers 3 --smoke`` — GT40's smoke-subset of the
test tier. Slimmer than a full test run so it can fire on cron_15m
without burning CI; runs long enough that a regression caught here still
beats the full verify at post_commit time.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict

from .base import Lever, LeverObservation


class Gt40TestSmokeLever(Lever):
    name = "gt40_test_smoke"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        nucleus_bin = inputs.get("nucleus_bin", "nucleus")
        timeout_seconds = int(inputs.get("timeout_seconds", 60))
        tier = int(inputs.get("tier", 3))
        smoke_flag = inputs.get("smoke_flag", "--smoke")

        argv = [
            nucleus_bin,
            "verify",
            "--tiers",
            str(tier),
            smoke_flag,
            "--timeout",
            str(timeout_seconds),
        ]

        try:
            result = self._run_subprocess(
                argv, timeout=timeout_seconds + 10, stage=self.name
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
            return self.observation_clean({"tier": tier, "ran": "smoke"})

        findings = _tail_nonempty(
            (result.stdout or "") + "\n" + (result.stderr or ""), limit=30
        )
        return self.observation_found({
            "tier": tier,
            "ran": "smoke",
            "returncode": result.returncode,
            "findings": findings,
        })


def _tail_nonempty(blob: str, *, limit: int) -> list:
    lines = [ln.rstrip() for ln in blob.splitlines() if ln.strip()]
    return lines[-limit:]
