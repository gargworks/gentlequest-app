"""Lever — api_contract_check.

API routes are a contract. Removing or renaming a route silently breaks
every client that depends on it. This lever AST-walks every changed
``.py`` file under the configured ``roots``, extracts the set of
``(method, path)`` tuples declared via common Flask/FastAPI decorators,
and compares that set against the same file at HEAD~1. Routes present
in the previous version but missing in the new one become findings.

Additive route changes are clean. A file that didn't exist at HEAD~1
is skipped (``git show`` non-zero) — there's no old contract to break.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .base import Lever, LeverObservation


class ApiContractCheckLever(Lever):
    name = "api_contract_check"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        roots = [r.rstrip("/") for r in (inputs.get("roots") or []) if r]
        decorator_names = set(
            inputs.get("decorator_names") or []
        )
        project_root = brain_path.parent

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

        changed = [
            p.strip() for p in result.stdout.splitlines()
            if p.strip() and p.strip().endswith(".py")
            and (not roots or any(p.strip().startswith(r + "/") or p.strip() == r for r in roots))
        ]

        prev_ref = _prev_ref_from(diff_spec)
        findings: List[str] = []
        for rel_path in changed:
            current_src = _read_file(project_root / rel_path)
            if current_src is None:
                continue
            previous_src = _show_at_ref(prev_ref, rel_path)
            if previous_src is None:
                continue
            prev_routes = _routes(previous_src, decorator_names)
            cur_routes = _routes(current_src, decorator_names)
            removed = prev_routes - cur_routes
            for method, path in sorted(removed):
                findings.append(f"{rel_path}: removed {method} {path}")

        base = {
            "diff_spec": diff_spec,
            "files_checked": len(changed),
        }
        if findings:
            return self.observation_found({**base, "findings": findings})
        return self.observation_clean(base)


def _prev_ref_from(diff_spec: str) -> str:
    if ".." in diff_spec:
        return diff_spec.split("..", 1)[0] or "HEAD~1"
    return "HEAD~1"


def _read_file(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return None


def _show_at_ref(ref: str, rel_path: str) -> Optional[str]:
    try:
        result = Lever._run_subprocess(
            ["git", "show", f"{ref}:{rel_path}"],
            timeout=10,
            stage="git_show",
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _routes(src: str, decorator_names: Set[str]) -> Set[Tuple[str, str]]:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set()
    routes: Set[Tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            if not isinstance(deco, ast.Call):
                continue
            name = _decorator_name(deco.func)
            if name not in decorator_names:
                continue
            path_arg = _first_string_arg(deco)
            if path_arg is None:
                continue
            if name.endswith(".route"):
                methods = _extract_methods_kw(deco)
                for m in methods or ["GET"]:
                    routes.add((m.upper(), path_arg))
            else:
                method = name.rsplit(".", 1)[-1].upper()
                routes.add((method, path_arg))
    return routes


def _decorator_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        parent = _decorator_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _first_string_arg(call: ast.Call) -> Optional[str]:
    if not call.args:
        return None
    first = call.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


def _extract_methods_kw(call: ast.Call) -> List[str]:
    for kw in call.keywords:
        if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
            out: List[str] = []
            for el in kw.value.elts:
                if isinstance(el, ast.Constant) and isinstance(el.value, str):
                    out.append(el.value)
            return out
    return []
