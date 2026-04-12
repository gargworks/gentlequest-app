"""Lever — a11y_smoke.

Wraps a command-line accessibility scanner (``pa11y`` / ``axe``) against
one URL and reports violations that land in the emitted JSON. The goal
is smoke-grade, not exhaustive: catch the dumb regression
(a button with no label, a missing ``alt``) before prod.

No URL configured → ``skipped`` so the lever is harmless in repos
without a running preview. Binary missing → ``error`` (visible) so
the missing tool surfaces on the ledger.

Output shape is forgiving — pa11y emits ``[{type,code,message,...}]``,
axe emits ``{violations:[{id,description,nodes:[...]}]}``. The
extractor handles both.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .base import Lever, LeverObservation


class A11ySmokeLever(Lever):
    name = "a11y_smoke"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        scanner_bin = inputs.get("scanner_bin", "pa11y")
        url = inputs.get("url") or ""
        extra_args = list(inputs.get("extra_args") or ["--reporter", "json"])
        timeout_seconds = int(inputs.get("timeout_seconds", 60))
        max_findings = int(inputs.get("max_findings", 25))

        if not url:
            return self.observation_skipped("no_url_configured")

        argv = [scanner_bin, url, *extra_args]
        try:
            result = self._run_subprocess(
                argv,
                timeout=timeout_seconds + 5,
                stage="a11y_run",
            )
        except FileNotFoundError:
            return self.observation_error(
                "scanner_missing", f"{scanner_bin} not installed"
            )
        except subprocess.TimeoutExpired:
            return self.observation_error(
                "a11y_run", "timed out", timeout_seconds=timeout_seconds
            )

        stdout = result.stdout.strip()
        if not stdout:
            if result.returncode == 0:
                return self.observation_clean({"url": url, "violations": 0})
            return self.observation_error(
                "a11y_run",
                result.stderr.strip() or f"exit {result.returncode}",
                returncode=result.returncode,
            )

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as e:
            return self.observation_error(
                "parse_a11y", f"invalid json: {e}"
            )

        violations = _extract_violations(payload)
        findings: List[str] = []
        for v in violations:
            vid = v.get("id") or v.get("code") or v.get("type") or "?"
            msg = (v.get("message") or v.get("description") or "").strip()
            findings.append(f"{vid}: {msg[:120]}" if msg else str(vid))
            if len(findings) >= max_findings:
                break

        base = {"url": url, "violations": len(violations)}
        if findings:
            return self.observation_found({**base, "findings": findings})
        return self.observation_clean(base)


def _extract_violations(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [v for v in payload if isinstance(v, dict)]
    if isinstance(payload, dict):
        for key in ("violations", "issues", "results"):
            seq = payload.get(key)
            if isinstance(seq, list):
                return [v for v in seq if isinstance(v, dict)]
    return []
