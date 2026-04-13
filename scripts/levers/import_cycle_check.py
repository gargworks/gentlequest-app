"""Lever — import_cycle_check.

Detects direct circular imports (A ↔ B only) in Python files touched by
the active diff. Long cycles (A→B→C→A) are out of scope — most real
cycles are direct, and cycle-detection over the full import graph is
an order of magnitude more work. This lever covers the 80% case.

Module resolution is anchored to ``roots`` from the manifest
(``scripts``, ``backend``, ``tests``) — imports from stdlib or
third-party packages are ignored.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .base import Lever, LeverObservation


class ImportCycleCheckLever(Lever):
    name = "import_cycle_check"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        diff_spec = inputs.get("diff_spec", "HEAD~1..HEAD")
        roots = list(inputs.get("roots") or ["scripts", "backend", "tests"])
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

        changed = [p.strip() for p in result.stdout.splitlines() if p.strip().endswith(".py")]

        graph: Dict[str, Set[str]] = {}
        for rel_path in changed:
            abs_path = project_root / rel_path
            try:
                source = abs_path.read_text(encoding="utf-8")
            except (FileNotFoundError, OSError):
                continue
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            graph[rel_path] = _collect_project_imports(tree, roots, project_root)

        findings: List[str] = []
        seen = set()
        for a, a_imports in graph.items():
            for b in a_imports:
                if b in graph and a in graph[b]:
                    pair = tuple(sorted([a, b]))
                    if pair not in seen:
                        seen.add(pair)
                        findings.append(f"{pair[0]} <-> {pair[1]}")

        if not findings:
            return self.observation_clean({
                "diff_spec": diff_spec,
                "files_checked": len(graph),
            })
        return self.observation_found({
            "diff_spec": diff_spec,
            "findings": findings,
        })


def _collect_project_imports(
    tree: ast.AST, roots: List[str], project_root: Path
) -> Set[str]:
    modules: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module)
            for alias in node.names:
                modules.add(f"{node.module}.{alias.name}")
    resolved: Set[str] = set()
    for mod in modules:
        path = _resolve_module(mod, roots, project_root)
        if path:
            resolved.add(path)
    return resolved


def _resolve_module(module: str, roots: List[str], project_root: Path) -> Optional[str]:
    parts = module.split(".")
    if not parts or parts[0] not in roots:
        return None
    file_candidate = "/".join(parts) + ".py"
    init_candidate = "/".join(parts) + "/__init__.py"
    if (project_root / file_candidate).exists():
        return file_candidate
    if (project_root / init_candidate).exists():
        return init_candidate
    return None
