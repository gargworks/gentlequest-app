"""Lever — gt40_typecheck.

Wraps ``nucleus verify --tiers 0,1,2 --json`` (GT40's import/type
resolution tier with preconditions) as a lever so its structured receipt
lands in the ledger. Uses the JSON receipt — NOT stdout scraping —
because tier 2 silently skips when called alone, and stdout warnings
(INSECURE MODE, urllib3 NotOpenSSLWarning) used to pollute findings.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict

from .base import Lever, LeverObservation
from ._gt40 import build_argv, classify_receipt, parse_receipt


class Gt40TypecheckLever(Lever):
    name = "gt40_typecheck"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        nucleus_bin = inputs.get("nucleus_bin", "nucleus")
        timeout_seconds = int(inputs.get("timeout_seconds", 30))
        target_tier = int(inputs.get("tier", 2))
        chain = inputs.get("tier_chain") or list(range(0, target_tier + 1))

        argv = build_argv(nucleus_bin, chain, timeout_seconds)

        try:
            result = self._run_subprocess(
                argv, timeout=timeout_seconds + 5, stage=self.name
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

        outcome, detail = classify_receipt(receipt, target_tier)
        if outcome == "found":
            return self.observation_found(detail)
        if outcome == "skipped":
            reason = detail.pop("reason", "skipped")
            return self.observation_skipped(reason, **detail)
        return self.observation_clean(detail)
