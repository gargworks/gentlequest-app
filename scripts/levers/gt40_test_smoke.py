"""Lever — gt40_test_smoke.

Wraps ``nucleus verify --tiers 0,1,2,3 --json`` (GT40 chain through the
test tier) as a lever so periodic test failures land in the ledger
without waiting for full verify. The historical ``--smoke`` flag was
bogus — nucleus verify never accepted it; argparse rejected it with
exit 2, polluting the ledger with usage findings. Removed entirely.
The "smoke" naming is preserved for the lever identity (cron-friendly
test wrapper) but the chain runs the full test tier.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict

from .base import Lever, LeverObservation
from ._gt40 import build_argv, classify_receipt, parse_receipt


class Gt40TestSmokeLever(Lever):
    name = "gt40_test_smoke"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        nucleus_bin = inputs.get("nucleus_bin", "nucleus")
        timeout_seconds = int(inputs.get("timeout_seconds", 60))
        target_tier = int(inputs.get("tier", 3))
        chain = inputs.get("tier_chain") or list(range(0, target_tier + 1))

        argv = build_argv(nucleus_bin, chain, timeout_seconds)

        try:
            result = self._run_subprocess(
                argv, timeout=timeout_seconds + 10, stage=self.name
            )
        except FileNotFoundError:
            return self.observation_error(
                "nucleus_missing", f"executable not found: {nucleus_bin}",
                tier=target_tier,
            )
        except subprocess.TimeoutExpired:
            return self.observation_error(
                "timeout", f"exceeded {timeout_seconds}s", tier=target_tier,
            )

        receipt = parse_receipt(result.stdout or "", result.stderr or "")
        if receipt is None:
            return self.observation_error(
                "parse_receipt",
                f"no JSON receipt in nucleus stdout (returncode={result.returncode})",
                tier=target_tier,
            )

        outcome, detail = classify_receipt(receipt, target_tier, findings_limit=30)
        if outcome == "found":
            return self.observation_found(detail)
        if outcome == "skipped":
            reason = detail.pop("reason", "skipped")
            return self.observation_skipped(reason, **detail)
        return self.observation_clean(detail)
