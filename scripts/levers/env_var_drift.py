"""Lever — env_var_drift.

Every ``os.environ.get("FOO")`` in code is a promise that ``FOO`` is
documented somewhere a human can configure it. This lever walks the
changed ``.py`` files, AST-extracts every env-var name referenced via
``os.environ.get``, ``os.getenv``, or ``os.environ["…"]``, and flags
any name that doesn't appear in ``.env.example``.

Missing ``.env.example`` → ``skipped`` (the policy isn't in force for
repos without an example file). Non-literal var names (e.g.
``os.getenv(var)``) are ignored — a lint check can only validate what
the AST can read.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Set

from .base import Lever, LeverObservation


class EnvVarDriftLever(Lever):
    name = "env_var_drift"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        example_rel = inputs.get("env_example_path", ".env.example")
        max_findings = int(inputs.get("max_findings", 25))
        project_root = brain_path.parent

        example_path = project_root / example_rel
        try:
            example_src = example_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return self.observation_skipped(
                "no_env_example", path=str(example_path)
            )
        except OSError as e:
            return self.observation_error("env_example", f"read failed: {e}")

        declared = _parse_env_example(example_src)

        try:
            result = self._run_subprocess(
                ["git", "diff", "--name-only", diff_spec, "--", "*.py"],
                timeout=10,
                stage="git_diff",
            )
        except FileNotFoundError:
            return self.observation_error("git_diff", "git not installed")
        except subprocess.TimeoutExpired:
            return self.observation_error(
                "git_diff", "timed out", diff_spec=diff_spec
            )
        if result.returncode != 0:
            return self.observation_error(
                "git_diff",
                result.stderr.strip() or f"git exit {result.returncode}",
                returncode=result.returncode,
            )

        changed = [p.strip() for p in result.stdout.splitlines() if p.strip().endswith(".py")]

        findings: List[str] = []
        for rel_path in changed:
            try:
                src = (project_root / rel_path).read_text(encoding="utf-8")
            except (FileNotFoundError, OSError):
                continue
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for name in _extract_env_names(tree):
                if name in declared:
                    continue
                entry = f"{rel_path}: {name}"
                if entry not in findings:
                    findings.append(entry)
                if len(findings) >= max_findings:
                    break
            if len(findings) >= max_findings:
                break

        base = {
            "diff_spec": diff_spec,
            "declared_vars": len(declared),
            "files_checked": len(changed),
        }
        if findings:
            return self.observation_found({**base, "findings": findings})
        return self.observation_clean(base)


def _parse_env_example(src: str) -> Set[str]:
    out: Set[str] = set()
    for line in src.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, _ = line.partition("=")
        key = key.strip()
        if key:
            out.add(key)
    return out


def _extract_env_names(tree: ast.AST) -> List[str]:
    names: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = _attr_chain(node.func)
            if fn in ("os.getenv", "os.environ.get"):
                literal = _first_string_arg(node)
                if literal is not None:
                    names.append(literal)
        elif isinstance(node, ast.Subscript):
            target = _attr_chain(node.value)
            if target == "os.environ":
                literal = _subscript_string(node.slice)
                if literal is not None:
                    names.append(literal)
    return names


def _attr_chain(node: ast.AST) -> str:
    parts: List[str] = []
    current: Any = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def _first_string_arg(call: ast.Call) -> Any:
    if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
        return call.args[0].value
    return None


def _subscript_string(slice_node: ast.AST) -> Any:
    if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
        return slice_node.value
    return None
