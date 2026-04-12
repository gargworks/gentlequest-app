"""Shared diff-walker for levers.

Multiple levers (todo_chain, secret_scan, license_header_check,
diff_size_check, ...) all need to iterate newly-added lines from a
``git diff`` output. Without this helper each lever reimplements the
same ``+++ b/`` parser — the same class of bug in N places. Keep the
parser in one place; every lever that needs added-line iteration uses
``iter_added_lines``.

The parser is deliberately conservative:
  - yields only lines that start with ``+`` (but not the ``+++`` header)
  - tracks current file from the ``+++ b/<path>`` header
  - yields the stripped content (without the leading ``+``)
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, List, NamedTuple, Optional

from .base import Lever, SubprocessFailure


class AddedLine(NamedTuple):
    path: str
    content: str


def iter_added_lines(
    diff_spec: str,
    *,
    cwd: Optional[Path] = None,
    timeout: float = 10.0,
    unified: int = 0,
) -> Iterator[AddedLine]:
    """Yield ``(path, content)`` for each added line in the diff.

    ``diff_spec`` is passed verbatim to ``git diff``, e.g. ``HEAD~1..HEAD``
    or ``--cached``. Raises ``FileNotFoundError`` if git is missing or
    ``SubprocessFailure`` if git itself returned non-zero.
    """
    result = Lever._run_subprocess(
        ["git", "diff", f"--unified={unified}", diff_spec],
        timeout=timeout,
        stage="git_diff",
        cwd=cwd,
    )
    if result.returncode != 0:
        raise SubprocessFailure(
            stage="git_diff",
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    yield from _parse_added_lines(result.stdout)


def _parse_added_lines(diff_text: str) -> Iterator[AddedLine]:
    current_file = ""
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if not line.startswith("+"):
            continue
        yield AddedLine(path=current_file, content=line[1:])


def added_lines(diff_text: str) -> List[AddedLine]:
    """Synchronous convenience — parse a pre-fetched diff string."""
    return list(_parse_added_lines(diff_text))
